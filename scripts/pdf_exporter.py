"""
Utility modul untuk mengekspor dokumen dan dataset RAG ke format PDF.
Mendukung pembuatan dokumen langsung dari list of records maupun konversi dari file CSV.
Kompatibel dengan library `fpdf2` (disarankan) serta memiliki fallback pure-Python jika fpdf2 belum terpasang.
"""

import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Any

UNICODE_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2014": " -- ",
    "\u2013": " - ",
    "\u2026": "...",
    "\u00a0": " ",
    "\u2009": " ",
    "\u2192": " -> ",
    "\u2190": " <- ",
    "\u2193": " | ",
    "\u21a6": " |-> ",
    "\u2713": "[OK]",
    "\u2714": "[OK]",
    "\u274c": "[X]",
    "\u00a7": "Section ",
    "\u00a9": "(c)",
    "\u00b7": "*",
    "\ufeff": "",
    "\u200b": "",
}


def sanitize_text(text: str) -> str:
    """Membersihkan karakter unicode agar kompatibel dengan standard Latin-1 PDF."""
    if not text:
        return ""
    for char, rep in UNICODE_REPLACEMENTS.items():
        text = text.replace(char, rep)
    # Ganti karakter di luar cakupan Latin-1 dengan representasi terdekat / tanda tanya
    return text.encode("latin-1", "replace").decode("latin-1")


try:
    from fpdf import FPDF

    class RAGDocsPDF(FPDF):
        def __init__(self, doc_title: str = "Dokumentasi Bahasa Pemrograman"):
            super().__init__(orientation="P", unit="mm", format="A4")
            self.doc_title = doc_title
            self.set_auto_page_break(auto=True, margin=15)
            self.set_margins(15, 15, 15)

        def header(self):
            if self.page_no() == 1:
                return
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, sanitize_text(self.doc_title), border="B", align="L")
            self.ln(6)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(0, 10, f"Halaman {self.page_no()}", align="C")

    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def export_records_to_pdf_fpdf(records: List[Dict[str, Any]], output_pdf_path: Path, title: str, language: str):
    """Mengekspor records ke PDF menggunakan fpdf2 dengan styling terstruktur."""
    pdf = RAGDocsPDF(doc_title=f"{language} Documentation & Syntax RAG Knowledge Base")
    pdf.add_page()

    # Cover Header Banner
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 40, "F")

    pdf.set_xy(15, 10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, sanitize_text(title), ln=True)

    pdf.set_xy(15, 22)
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(203, 213, 225)
    pdf.cell(0, 6, f"Bahasa: {language} | Total Chunk/Dokumen: {len(records)} | Disiapkan untuk RAG System", ln=True)

    pdf.set_y(48)

    for idx, rec in enumerate(records, 1):
        # Cek jika sisa halaman terlalu sedikit untuk section baru
        if pdf.get_y() > 240:
            pdf.add_page()

        doc_id = rec.get("doc_id", f"doc_{idx:03d}")
        cat = rec.get("category", "General")
        main_title = rec.get("main_title", "")
        sec_title = rec.get("section_title", "")
        source_url = rec.get("source_url", "")
        text_content = rec.get("text_content", "")
        code_snippet = rec.get("code_snippet", "")

        # 1. Badge & Kategori
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(37, 99, 235)  # Blue Accent
        badge_text = f"[{doc_id}] {language} - {cat}"
        pdf.cell(0, 5, sanitize_text(badge_text), ln=True)

        # 2. Judul Section
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(15, 23, 42)
        full_title = f"{main_title}: {sec_title}" if main_title != sec_title else main_title
        pdf.multi_cell(0, 6, sanitize_text(full_title))

        # 3. URL Sumber
        if source_url:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(0, 4, f"Sumber: {sanitize_text(source_url)}", ln=True)

        pdf.ln(2)

        # 4. Teks Konten
        if text_content:
            pdf.set_font("Helvetica", size=9.5)
            pdf.set_text_color(51, 65, 85)
            clean_content = sanitize_text(text_content)
            pdf.multi_cell(0, 5, clean_content)
            pdf.ln(2)

        # 5. Blok Kode (Monospace)
        if code_snippet:
            clean_code = sanitize_text(code_snippet)
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(0, 4, "Contoh Kode / Perintah CLI:", ln=True)

            pdf.set_font("Courier", size=8)
            pdf.set_fill_color(248, 250, 252)
            pdf.set_text_color(30, 41, 59)
            pdf.set_draw_color(226, 232, 240)
            pdf.multi_cell(0, 4.2, clean_code, fill=True, border=1)
            pdf.ln(3)

        # Garis pemisah antar dokumen
        pdf.set_draw_color(241, 245, 249)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_pdf_path))


def export_records_to_pdf_fallback(records: List[Dict[str, Any]], output_pdf_path: Path, title: str, language: str):
    """Fallback generator PDF murni Python jika fpdf2 tidak terpasang."""
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    lines_to_print = [
        f"=== {title.upper()} ===",
        f"Language: {language} | Total Records: {len(records)}",
        "=" * 60,
        "",
    ]
    for idx, rec in enumerate(records, 1):
        doc_id = rec.get("doc_id", f"doc_{idx:03d}")
        cat = rec.get("category", "")
        main_title = rec.get("main_title", "")
        sec_title = rec.get("section_title", "")
        source_url = rec.get("source_url", "")
        text_content = rec.get("text_content", "")
        code_snippet = rec.get("code_snippet", "")

        lines_to_print.append(f"[{doc_id}] {language} - {cat} | {main_title}: {sec_title}")
        if source_url:
            lines_to_print.append(f"Source: {source_url}")
        lines_to_print.append("-" * 40)
        if text_content:
            for l in text_content.splitlines():
                if l.strip():
                    lines_to_print.append(l.strip())
        if code_snippet:
            lines_to_print.append("--- CODE SNIPPET ---")
            for l in code_snippet.splitlines():
                lines_to_print.append(l)
        lines_to_print.append("")
        lines_to_print.append("=" * 60)
        lines_to_print.append("")

    # Split lines into pages (approx 55 lines per page)
    LINES_PER_PAGE = 55
    pages_lines = [lines_to_print[i:i + LINES_PER_PAGE] for i in range(0, len(lines_to_print), LINES_PER_PAGE)]
    if not pages_lines:
        pages_lines = [["(Empty Document)"]]

    objects = []
    # 1: Catalog, 2: Pages
    page_obj_ids = []
    current_obj_id = 3

    # Buat objek Font F1 (Helvetica)
    font_obj_id = current_obj_id
    current_obj_id += 1

    content_obj_ids = []
    for _ in pages_lines:
        page_obj_ids.append(current_obj_id)
        current_obj_id += 1
        content_obj_ids.append(current_obj_id)
        current_obj_id += 1

    catalog_obj = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    pages_obj = f"<< /Type /Pages /Kids [{kids_str}] /Count {len(pages_lines)} >>".encode("ascii")
    font_obj = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    all_objects = {1: catalog_obj, 2: pages_obj, font_obj_id: font_obj}

    for idx, page_lines in enumerate(pages_lines):
        pid = page_obj_ids[idx]
        cid = content_obj_ids[idx]

        stream_cmds = ["BT", f"/F1 9 Tf", "40 800 Td", "13 TL"]
        for line in page_lines:
            clean = sanitize_text(line[:90]).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_cmds.append(f"({clean}) Tj")
            stream_cmds.append("T*")
        stream_cmds.append("ET")
        stream_bytes = "\n".join(stream_cmds).encode("latin-1")

        content_obj = f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream"
        page_obj = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 {font_obj_id} 0 R >> >> /Contents {cid} 0 R >>".encode("ascii")

        all_objects[pid] = page_obj
        all_objects[cid] = content_obj

    with open(output_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n")
        offsets = {}
        for obj_idx in range(1, current_obj_id):
            offsets[obj_idx] = f.tell()
            f.write(f"{obj_idx} 0 obj\n".encode("ascii") + all_objects[obj_idx] + b"\nendobj\n")
        xref_offset = f.tell()
        f.write(f"xref\n0 {current_obj_id}\n0000000000 65535 f \n".encode("ascii"))
        for obj_idx in range(1, current_obj_id):
            f.write(f"{offsets[obj_idx]:010d} 00000 n \n".encode("ascii"))
        f.write(f"trailer\n<< /Size {current_obj_id} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))


def export_records_to_pdf(records: List[Dict[str, Any]], output_pdf_path: Path, title: str, language: str):
    """Mengekspor records data ke format PDF."""
    if FPDF_AVAILABLE:
        export_records_to_pdf_fpdf(records, output_pdf_path, title, language)
    else:
        export_records_to_pdf_fallback(records, output_pdf_path, title, language)


def convert_csv_to_pdf(csv_path: str | Path, pdf_path: str | Path, default_language: str = ""):
    """Mengonversi file CSV dataset dokumentasi yang sudah ada menjadi file PDF."""
    csv_file = Path(csv_path)
    pdf_file = Path(pdf_path)

    if not csv_file.exists():
        raise FileNotFoundError(f"File CSV tidak ditemukan: {csv_file}")

    records = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    detected_lang = default_language
    if records and "language" in records[0] and records[0]["language"]:
        detected_lang = records[0]["language"]

    title = f"Dokumentasi Resmi & Sintaks {detected_lang}"
    export_records_to_pdf(records, pdf_file, title=title, language=detected_lang)
    return len(records), pdf_file

