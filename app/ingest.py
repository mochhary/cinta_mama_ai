from pathlib import Path
import glob
import json
import os
import re
import time
from typing import Any, Dict, List
from pypdf import PdfReader

# Resolusi path knowledge-base (mendukung eksekusi lokal dan dalam container Docker)
DEFAULT_KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "knowledge-base")

LANG_MAP = {
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "golang": "Go",
    "go": "Go",
    "csharp": "C#",
    "cpp": "C++",
    "c": "C",
    "python": "Python",
    "java": "Java",
    "kotlin": "Kotlin",
    "php": "PHP",
    "ruby": "Ruby",
    "rust": "Rust",
    "sql": "SQL",
    "swift": "Swift",
    "dart": "Dart",
}


def extract_text(file_path: str) -> str:
    """Mengekstrak teks mentah dari file PDF atau teks."""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_sop(file_path: str) -> List[Dict[str, Any]]:
    """Mengekstrak file SOP markdown menjadi chunk per tahapan."""
    filename = os.path.basename(file_path)
    slug = filename.replace("sop-setup-environment-", "").replace(".md", "")
    language = LANG_MAP.get(slug.lower(), slug.title())

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    doc_title_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = doc_title_m.group(1).strip() if doc_title_m else f"SOP Setup {language}"

    chunks = []
    sections = re.split(r"\n(?=#{2,3}\s+)", content)
    chunk_idx = 1

    for sec in sections:
        sec = sec.strip()
        if not sec or sec.startswith("# "):
            continue

        header_m = re.match(r"^(#{2,3})\s+(.+)$", sec, re.MULTILINE)
        if not header_m:
            continue

        header = header_m.group(2).strip()
        body = sec[header_m.end():].strip()
        if len(body) < 20:
            continue

        chunk_id = f"sop_{slug}_{chunk_idx:02d}"
        chunk_content = (
            f"[{chunk_id}] {language} - SOP: {header}\n"
            f"Dokumen: {doc_title}\n"
            f"Kategori: SOP Setup & Environment\n"
            f"Sumber: {file_path}\n\n"
            f"{body}"
        )

        chunks.append({
            "id": chunk_id,
            "doc_id": chunk_id,
            "doc_type": "sop",
            "language": language,
            "category": "Environment Setup SOP",
            "title": header,
            "source": file_path,
            "source_url": None,
            "content": chunk_content,
            "char_count": len(chunk_content),
        })
        chunk_idx += 1

    return chunks


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Mengekstrak file PDF dokumentasi menjadi chunk terstruktur."""
    raw_text = extract_text(file_path)
    raw_chunks = re.split(r"\n(?=\[[a-zA-Z0-9_\-]+\]\s+[A-Za-z0-9#+]+\s+-\s+)", raw_text)

    chunks = []
    # Skip chunk 0 (header/cover halaman)
    for section in raw_chunks[1:]:
        sec = section.strip()
        lines = [line.strip() for line in sec.splitlines() if line.strip()]
        if not lines:
            continue

        m = re.match(r"^\[([a-zA-Z0-9_\-]+)\]\s+([A-Za-z0-9#+]+)\s+-\s+(.+)$", lines[0])
        if not m:
            continue

        doc_id, raw_lang, category = m.group(1), m.group(2), m.group(3)
        language = LANG_MAP.get(raw_lang.lower(), raw_lang)

        url_m = re.search(r"^Sumber:\s*(\S+)", sec, re.MULTILINE)
        source_url = url_m.group(1).strip() if url_m else None

        title = category
        if len(lines) > 1 and not lines[1].startswith("Sumber:"):
            title = lines[1]

        chunks.append({
            "id": f"doc_{doc_id}",
            "doc_id": doc_id,
            "doc_type": "documentation",
            "language": language,
            "category": category,
            "title": title,
            "source": file_path,
            "source_url": source_url,
            "content": sec,
            "char_count": len(sec),
        })

    return chunks


def ingest_all(
    kb_dir: str = DEFAULT_KB_PATH,
    data_dir: str = "data",
    output_file: str = None,
    summary_file: str = None,
) -> Dict[str, Any]:
    """
    Menjalankan proses ingesti dokumen dan SOP tanpa proses embedding.
    Hasil simpanan utama diarahkan ke direktori knowledge-base (folder yang semestinya untuk RAG).
    """
    if output_file is None:
        output_file = os.path.join(kb_dir, "ingested_chunks.json")
    if summary_file is None:
        summary_file = os.path.join(kb_dir, "ingested_summary.json")

    start_time = time.time()
    chunks: List[Dict[str, Any]] = []

    # Ingest SOP (dari knowledge-base)
    sop_files = sorted(glob.glob(os.path.join(kb_dir, "sop-*.md")))
    for path in sop_files:
        chunks.extend(parse_sop(path))

    # Ingest PDF (prioritas di knowledge-base/docs, fallback ke data/)
    pdf_files = sorted(glob.glob(os.path.join(kb_dir, "docs", "*_docs.pdf")))
    if not pdf_files:
        pdf_files = sorted(glob.glob(os.path.join(kb_dir, "*_docs.pdf")))
    if not pdf_files and os.path.exists(data_dir):
        pdf_files = sorted(glob.glob(os.path.join(data_dir, "*_docs.pdf")))

    for path in pdf_files:
        chunks.extend(parse_pdf(path))

    duration = round(time.time() - start_time, 2)
    sop_count = sum(1 for c in chunks if c["doc_type"] == "sop")
    doc_count = sum(1 for c in chunks if c["doc_type"] == "documentation")
    total_chars = sum(c["char_count"] for c in chunks)

    # Breakdown per bahasa
    lang_summary: Dict[str, Dict[str, int]] = {}
    for c in chunks:
        lang = c["language"]
        if lang not in lang_summary:
            lang_summary[lang] = {"sop": 0, "docs": 0, "total": 0, "chars": 0}
        if c["doc_type"] == "sop":
            lang_summary[lang]["sop"] += 1
        else:
            lang_summary[lang]["docs"] += 1
        lang_summary[lang]["total"] += 1
        lang_summary[lang]["chars"] += c["char_count"]

    summary = {
        "status": "success",
        "ingestion_mode": "chunking_only_no_embedding",
        "storage_folder": os.path.abspath(kb_dir),
        "total_files": len(sop_files) + len(pdf_files),
        "total_chunks": len(chunks),
        "sop_chunks": sop_count,
        "doc_chunks": doc_count,
        "total_characters": total_chars,
        "duration_seconds": duration,
        "languages": lang_summary,
    }

    # Simpan hasil utama ke folder knowledge-base (folder yang semestinya)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main():
    print("[INFO] Memulai proses ingesti dokumen (ingest saja, tanpa embed)...")
    summary = ingest_all()

    print("[INFO] Ingesti selesai dalam {} detik.".format(summary["duration_seconds"]))
    print(f"Folder Tujuan: {summary['storage_folder']}")
    print(f"Total Berkas : {summary['total_files']} (15 SOP + 15 PDF)")
    print(f"Total Chunk  : {summary['total_chunks']} (SOP: {summary['sop_chunks']}, Docs: {summary['doc_chunks']})")
    print(f"Total Huruf  : {summary['total_characters']} karakter")
    print("-" * 55)
    print(f"{'Bahasa':<12} | {'SOP':<5} | {'Docs':<5} | {'Total':<5} | {'Karakter':<10}")
    print("-" * 55)
    for lang, st in sorted(summary["languages"].items()):
        print(f"{lang:<12} | {st['sop']:<5} | {st['docs']:<5} | {st['total']:<5} | {st['chars']:<10}")
    print("-" * 55)
    print(f"[OK] Berkas hasil ingest tersimpan di: {os.path.join(DEFAULT_KB_PATH, 'ingested_chunks.json')}")


if __name__ == "__main__":
    main()
