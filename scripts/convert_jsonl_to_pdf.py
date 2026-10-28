"""
Script konverter untuk mengubah data/js_documentation.jsonl ke PDF terstruktur.
Menghasilkan data/javascript_mdn_docs.pdf dan menyalinnya ke knowledge-base/docs/javascript_mdn_docs.pdf.
"""

import json
import os
import re
import shutil
import time
import sys
from pathlib import Path

# Tambahkan direktori root workspace ke sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fpdf import FPDF
from scripts.pdf_exporter import RAGDocsPDF, sanitize_text


def parse_mdn_record(line: str, index: int) -> Dict[str, Any]:
    """Menguraikan satu baris JSONL MDN ke struktur metadata dan konten bersih."""
    raw = json.loads(line)
    text = raw.get("text", "")
    file_path = raw.get("file_path", "")

    # Ekstraksi YAML Frontmatter
    title = ""
    slug = ""
    page_type = ""
    body = text

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if fm_match:
        fm_content = fm_match.group(1)
        body = text[fm_match.end():]

        t_m = re.search(r"^title:\s*(.+)$", fm_content, re.MULTILINE)
        if t_m:
            title = t_m.group(1).strip().strip('"').strip("'")

        s_m = re.search(r"^slug:\s*(.+)$", fm_content, re.MULTILINE)
        if s_m:
            slug = s_m.group(1).strip()

        pt_m = re.search(r"^page-type:\s*(.+)$", fm_content, re.MULTILINE)
        if pt_m:
            page_type = pt_m.group(1).strip()

    if not title:
        # Fallback dari heading pertama di body
        h1_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = h1_m.group(1).strip() if h1_m else Path(file_path).stem.replace("_", " ").title()

    if not slug:
        clean_fp = file_path.replace("\\", "/").replace("content/files/en-us/", "")
        slug = clean_fp.replace("/index.md", "").replace(".md", "")

    # Penentuan Kategori Terstruktur
    slug_parts = slug.split("/")
    if "Global_Objects" in slug_parts:
        g_idx = slug_parts.index("Global_Objects")
        if len(slug_parts) > g_idx + 1:
            obj_name = slug_parts[g_idx + 1].replace("_", " ")
            category = f"Standard Built-in Objects ({obj_name})"
        else:
            category = "Standard Built-in Objects"
    elif "Errors" in slug_parts:
        category = "Error Handling & Diagnostic"
    elif "Operators" in slug_parts:
        category = "Operators & Expressions"
    elif "Statements" in slug_parts:
        category = "Statements & Control Flow"
    elif "Classes" in slug_parts:
        category = "Classes & OOP"
    elif "Functions" in slug_parts:
        category = "Functions & Scope"
    elif "Regular_expressions" in slug_parts:
        category = "Regular Expressions"
    elif "Guide" in slug_parts:
        category = "JavaScript Guide"
    else:
        category = "JavaScript Language Reference"

    source_url = f"https://developer.mozilla.org/en-US/docs/{slug}"

    # Pembersihan Markdown & MDN Macro
    compat_idx = body.find("## Browser compatibility")
    if compat_idx != -1:
        body = body[:compat_idx]

    specs_idx = body.find("## Specifications")
    if specs_idx != -1:
        body = body[:specs_idx]

    # Hapus macro MDN spesifik {{...}}
    body = re.sub(r'\{\{[a-zA-Z0-9_-]+\(\s*\"([^\"]+)\"[^)]*\)\}\}', r'\1', body)
    body = re.sub(r'\{\{[a-zA-Z0-9_-]+\}\}', '', body)

    # Batasi panjang maksimal per dokumen agar tetap proporsional untuk RAG
    if len(body) > 7500:
        body = body[:7500].rstrip() + "\n\n...(konten dokumentasi berlanjut di MDN Web Docs)"

    doc_id = f"js_mdn_{index:04d}"

    return {
        "doc_id": doc_id,
        "title": title,
        "slug": slug,
        "category": category,
        "source_url": source_url,
        "body": body.strip(),
    }


def convert_jsonl_to_pdf(jsonl_path: Path, output_pdf: Path, max_docs: int = None) -> int:
    """Mengonversi berkas jsonl ke PDF standar knowledge-base RAG."""
    print(f"Membaca dataset dari: {jsonl_path}")
    records: List[Dict[str, Any]] = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if not line.strip():
                continue
            rec = parse_mdn_record(line, idx)
            records.append(rec)
            if max_docs and len(records) >= max_docs:
                break

    total = len(records)
    print(f"Total dokumen berhasil diparsing: {total}")
    print(f"Menyusun dokumen PDF ke: {output_pdf}...")

    pdf = RAGDocsPDF(doc_title="JavaScript MDN Web Docs RAG Knowledge Base")
    pdf.add_page()

    # Cover Banner
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 40, "F")

    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "JavaScript MDN Web Docs", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(15, 22)
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 6, f"Bahasa: JavaScript | Total Dokumen: {total} | Sumber: MDN Web Docs", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(48)

    t0 = time.time()
    for idx, rec in enumerate(records, start=1):
        if pdf.get_y() > 240:
            pdf.add_page()

        doc_id = rec["doc_id"]
        category = rec["category"]
        title = rec["title"]
        source_url = rec["source_url"]
        body = rec["body"]

        # 1. Badge & Kategori
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 5, sanitize_text(f"[{doc_id}] JavaScript - {category}"), new_x="LMARGIN", new_y="NEXT")

        # 2. Judul Dokumen
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, sanitize_text(title))

        # 3. URL Sumber
        if source_url:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 4, f"Sumber: {sanitize_text(source_url)}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(2)

        # 4. Konten Teks
        if body:
            pdf.set_font("Helvetica", size=9)
            pdf.set_text_color(51, 65, 85)
            # Pisahkan blok kode jika ada tanda ```
            parts = re.split(r"(```[\s\S]*?```)", body)
            for part in parts:
                if part.startswith("```"):
                    # Code block
                    code_lines = part.strip("`").strip().splitlines()
                    # Skip nama bahasa jika di baris pertama (misal: js, javascript)
                    if code_lines and code_lines[0].strip().lower() in ("js", "javascript", "ts", "html", "css", "json"):
                        code_lines = code_lines[1:]
                    code_text = "\n".join(code_lines[:40])  # Maksimal 40 baris kode
                    if code_text:
                        pdf.set_font("Courier", size=8)
                        pdf.set_fill_color(248, 250, 252)
                        pdf.set_text_color(30, 41, 59)
                        pdf.set_draw_color(226, 232, 240)
                        pdf.multi_cell(0, 4.2, sanitize_text(code_text), fill=True, border=1)
                        pdf.ln(2)
                else:
                    clean_prose = sanitize_text(part.strip())
                    if clean_prose:
                        pdf.set_font("Helvetica", size=9)
                        pdf.set_text_color(51, 65, 85)
                        pdf.multi_cell(0, 4.5, clean_prose)
                        pdf.ln(2)

        # Garis pemisah antar dokumen
        pdf.set_draw_color(241, 245, 249)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

        if idx % 200 == 0 or idx == total:
            print(f"  Progress PDF: {idx}/{total} dokumen ({(idx/total*100):.1f}%)")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_pdf))
    duration = round(time.time() - t0, 2)
    file_size_mb = output_pdf.stat().st_size / (1024 * 1024)
    print(f"Konversi selesai dalam {duration}s! Ukuran file: {file_size_mb:.2f} MB")
    return total


def main():
    base_dir = Path(__file__).resolve().parent.parent
    jsonl_path = base_dir / "data" / "js_documentation.jsonl"
    data_pdf = base_dir / "data" / "javascript_mdn_docs.pdf"
    kb_pdf = base_dir / "knowledge-base" / "docs" / "javascript_mdn_docs.pdf"

    if not jsonl_path.exists():
        print(f"Berkas {jsonl_path} tidak ditemukan!")
        return

    count = convert_jsonl_to_pdf(jsonl_path, data_pdf)

    # Salin ke knowledge-base/docs/ agar otomatis diindeks oleh pipeline RAG
    print(f"Menyalin {data_pdf.name} ke {kb_pdf}...")
    kb_pdf.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(data_pdf, kb_pdf)
    print("Salinan berhasil!")


if __name__ == "__main__":
    main()
