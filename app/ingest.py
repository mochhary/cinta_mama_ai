from pathlib import Path
import glob
import json
import os
import re
import time
from typing import Any, Dict, List
from pypdf import PdfReader
from app.embeddings import embed_text
from app.vector_store import VectorStore
from app.tokens import count_tokens

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
    """Mengekstrak teks mentah secara lengkap dari file PDF atau Markdown."""
    if file_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def ingest_documents(
    knowledge_base_path: str,
    vector_store: VectorStore,
    index_name: str,
    ollama_base_url: str,
) -> int:
    """Menyimpan seluruh berkas SOP pemrograman dari knowledge-base ke OpenSearch."""
    vector_store.ensure_index(index_name)
    count = 0

    # Cari berkas SOP (sop-*.md) di root knowledge-base atau di subfolder programming/
    sop_files = sorted(glob.glob(os.path.join(knowledge_base_path, "sop-*.md")))
    if not sop_files:
        sop_files = sorted(glob.glob(os.path.join(knowledge_base_path, "programming", "sop-*.md")))
    if not sop_files and os.path.exists(knowledge_base_path):
        sop_files = sorted(glob.glob(os.path.join(knowledge_base_path, "*.md")))

    for file_path in sop_files:
        filename = os.path.basename(file_path)
        text = extract_text(file_path)
        if not text or len(text.strip()) < 10:
            continue
        # Buat vektor embedding dokumen utuh
        embedding = embed_text(text[:3000], base_url=ollama_base_url)
        vector_store.index_document(
            index_name,
            doc_id=filename,
            text=text,
            embedding=embedding,
            metadata={"source": filename, "category": "programming-sop"},
        )
        count += 1
    return count


def parse_sop(file_path: str) -> Dict[str, Any]:
    """Mengekstrak berkas SOP markdown menjadi entitas dokumen utuh berstruktur."""
    filename = os.path.basename(file_path)
    slug = filename.replace("sop-setup-environment-", "").replace(".md", "").lower()
    language = LANG_MAP.get(slug, slug.title())

    content = extract_text(file_path)
    doc_title_m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = doc_title_m.group(1).strip() if doc_title_m else f"SOP Setup {language}"

    return {
        "id": f"sop_{slug}",
        "doc_id": filename,
        "doc_type": "sop",
        "language": language,
        "category": "SOP Setup & Environment",
        "title": doc_title,
        "source": file_path,
        "source_url": None,
        "content": content,
        "char_count": len(content),
        "token_count": count_tokens(content),
    }


def parse_pdf(file_path: str) -> Dict[str, Any]:
    """Mengekstrak berkas PDF dokumentasi resmi menjadi entitas dokumen utuh."""
    filename = os.path.basename(file_path)
    slug = filename.replace("_docs.pdf", "").lower()
    if "mdn" in slug:
        language = "JavaScript"
        title = "Dokumentasi Resmi JavaScript (MDN Web Docs)"
    else:
        language = LANG_MAP.get(slug, slug.title())
        title = f"Dokumentasi Resmi Bahasa Pemrograman {language}"

    content = extract_text(file_path)

    return {
        "id": f"doc_{slug}",
        "doc_id": filename,
        "doc_type": "documentation",
        "language": language,
        "category": "Dokumentasi Resmi",
        "title": title,
        "source": file_path,
        "source_url": None,
        "content": content,
        "char_count": len(content),
        "token_count": count_tokens(content),
    }


def ingest_all(
    kb_dir: str = DEFAULT_KB_PATH,
    data_dir: str = "data",
    output_file: str = None,
    summary_file: str = None,
) -> Dict[str, Any]:
    """
    Menjalankan proses ingesti dokumen utuh dan SOP ke dalam format data terstandarisasi.
    Hasil penyimpanan diarahkan ke direktori knowledge-base.
    """
    if output_file is None:
        output_file = os.path.join(kb_dir, "ingested_documents.json")
    if summary_file is None:
        summary_file = os.path.join(kb_dir, "ingested_summary.json")

    start_time = time.time()
    documents: List[Dict[str, Any]] = []

    # Ingest SOP (dari knowledge-base atau knowledge-base/programming)
    sop_files = sorted(glob.glob(os.path.join(kb_dir, "sop-*.md")))
    if not sop_files:
        sop_files = sorted(glob.glob(os.path.join(kb_dir, "programming", "sop-*.md")))
    for path in sop_files:
        documents.append(parse_sop(path))

    # Ingest PDF (prioritas di knowledge-base/docs, fallback ke data/)
    pdf_files = sorted(glob.glob(os.path.join(kb_dir, "docs", "*_docs.pdf")))
    if not pdf_files:
        pdf_files = sorted(glob.glob(os.path.join(kb_dir, "*_docs.pdf")))
    if not pdf_files and os.path.exists(data_dir):
        pdf_files = sorted(glob.glob(os.path.join(data_dir, "*_docs.pdf")))

    for path in pdf_files:
        documents.append(parse_pdf(path))

    duration = round(time.time() - start_time, 2)
    sop_count = sum(1 for d in documents if d["doc_type"] == "sop")
    doc_count = sum(1 for d in documents if d["doc_type"] == "documentation")
    total_chars = sum(d["char_count"] for d in documents)
    total_tokens = sum(d["token_count"] for d in documents)

    # Breakdown per bahasa
    lang_summary: Dict[str, Dict[str, int]] = {}
    for d in documents:
        lang = d["language"]
        if lang not in lang_summary:
            lang_summary[lang] = {"sop": 0, "docs": 0, "total": 0, "chars": 0, "tokens": 0}
        if d["doc_type"] == "sop":
            lang_summary[lang]["sop"] += 1
        else:
            lang_summary[lang]["docs"] += 1
        lang_summary[lang]["total"] += 1
        lang_summary[lang]["chars"] += d["char_count"]
        lang_summary[lang]["tokens"] += d["token_count"]

    summary = {
        "status": "success",
        "ingestion_mode": "document_level_ingestion",
        "storage_folder": os.path.abspath(kb_dir),
        "total_files": len(sop_files) + len(pdf_files),
        "total_documents": len(documents),
        "sop_documents": sop_count,
        "doc_documents": doc_count,
        "total_characters": total_chars,
        "total_tokens": total_tokens,
        "duration_seconds": duration,
        "languages": lang_summary,
    }

    # Simpan hasil utama ke folder knowledge-base
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary


def main():
    print("[INFO] Memulai proses ingesti dokumen utuh...")
    summary = ingest_all()

    print("[INFO] Ingesti selesai dalam {} detik.".format(summary["duration_seconds"]))
    print(f"Folder Tujuan  : {summary['storage_folder']}")
    print(f"Total Berkas   : {summary['total_files']} (15 SOP + 16 PDF)")
    print(f"Total Dokumen  : {summary['total_documents']} (SOP: {summary['sop_documents']}, Docs: {summary['doc_documents']})")
    print(f"Total Karakter : {summary['total_characters']} karakter")
    print(f"Total Token    : {summary['total_tokens']} token")
    print("-" * 55)
    print(f"{'Bahasa':<12} | {'SOP':<5} | {'Docs':<5} | {'Total':<5} | {'Karakter':<10}")
    print("-" * 55)
    for lang, st in sorted(summary["languages"].items()):
        print(f"{lang:<12} | {st['sop']:<5} | {st['docs']:<5} | {st['total']:<5} | {st['chars']:<10}")
    print("-" * 55)
    print(f"[OK] Berkas hasil ingest tersimpan di: {os.path.join(DEFAULT_KB_PATH, 'ingested_documents.json')}")


if __name__ == "__main__":
    main()
