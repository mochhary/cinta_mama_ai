"""
Script Scraper Dokumentasi Resmi Python (cpython Docs - Python 3.12 / 3.13)
Mencakup Sintaks Modern, Control Flow, Data Structures, OOP, Error Handling,
Virtual Environments (venv/pip), serta Fitur Baru Python 3.12 & 3.13 (Type Parameter Syntax, Pattern Matching, Exception Groups).
"""

import os
import re
import csv
import urllib.request
from pathlib import Path
from typing import Dict, List, Any

try:
    from scripts.pdf_exporter import export_records_to_pdf
except ImportError:
    from pdf_exporter import export_records_to_pdf

RAW_DOCS_BASE = "https://raw.githubusercontent.com/python/cpython/main/Doc"
WEB_DOCS_BASE = "https://docs.python.org/3"

DOC_TARGETS = [
    {
        "category": "Getting Started & Basics",
        "path": "tutorial/introduction.rst",
        "web_path": "tutorial/introduction.html",
        "title": "An Informal Introduction to Python",
    },
    {
        "category": "Control Flow & Pattern Matching",
        "path": "tutorial/controlflow.rst",
        "web_path": "tutorial/controlflow.html",
        "title": "More Control Flow Tools (if, for, match-case, functions)",
    },
    {
        "category": "Data Structures",
        "path": "tutorial/datastructures.rst",
        "web_path": "tutorial/datastructures.html",
        "title": "Data Structures (Lists, Tuples, Sets, Dicts, Comprehensions)",
    },
    {
        "category": "Modules & Packages",
        "path": "tutorial/modules.rst",
        "web_path": "tutorial/modules.html",
        "title": "Modules and Packages",
    },
    {
        "category": "Input & Output (F-Strings)",
        "path": "tutorial/inputoutput.rst",
        "web_path": "tutorial/inputoutput.html",
        "title": "Input and Output (Formatted String Literals, Files)",
    },
    {
        "category": "Error Handling & Exception Groups",
        "path": "tutorial/errors.rst",
        "web_path": "tutorial/errors.html",
        "title": "Errors and Exceptions (try-except, ExceptionGroup, except*)",
    },
    {
        "category": "Object-Oriented Programming",
        "path": "tutorial/classes.rst",
        "web_path": "tutorial/classes.html",
        "title": "Classes, Inheritance, Iterators & Generators",
    },
    {
        "category": "Environment & Package Management",
        "path": "tutorial/venv.rst",
        "web_path": "tutorial/venv.html",
        "title": "Virtual Environments and Packages (venv & pip)",
    },
    {
        "category": "Modern Features - Python 3.12",
        "path": "whatsnew/3.12.rst",
        "web_path": "whatsnew/3.12.html",
        "title": "What's New in Python 3.12 (PEP 695 Type Parameters, F-String Syntax)",
    },
    {
        "category": "Modern Features - Python 3.13",
        "path": "whatsnew/3.13.rst",
        "web_path": "whatsnew/3.13.html",
        "title": "What's New in Python 3.13 (Free-threaded GIL-free, JIT, Enhanced REPL)",
    },
]


def fetch_file(rel_path: str) -> str:
    """Mengunduh file RST dari repositori resmi cpython di GitHub."""
    url = f"{RAW_DOCS_BASE}/{rel_path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Python Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_rst_text(text: str) -> str:
    """Membersihkan format reStructuredText agar teks bersih untuk RAG."""
    # Hapus roles Sphinx: :role:`!text` atau :role:`text <target>`
    text = re.sub(r':[a-zA-Z0-9_]+:`!?(?:[^`<]*<)?([^`>]*)>?`', r'\1', text)
    # Hapus directives: .. directive::
    text = re.sub(r'^\.\.\s+[a-zA-Z0-9_-]+::.*$', '', text, flags=re.MULTILINE)
    # Hapus garis heading (===, ---, ~~~, ^^^, """)
    text = re.sub(r'^[=\-~^\*\"#]{3,}$', '', text, flags=re.MULTILINE)
    # Hapus referensi internal Sphinx .. _label:
    text = re.sub(r'^\.\.\s+_[a-zA-Z0-9_\-]+:.*$', '', text, flags=re.MULTILINE)
    # Hapus trailing whitespace berlebih
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_rst_sections(raw_rst: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    """Memecah dokumen RST cpython menjadi section-section yang terstruktur."""
    main_title = target["title"]
    category = target["category"]
    learn_url = f"{WEB_DOCS_BASE}/{target['web_path']}"

    # Cari section berdasarkan pola: Baris Judul diikuti garis bawah (===, ---, atau ~~~)
    pattern = r'\n(?=([^\n]+)\n([=\-~]{3,})\n)'
    raw_sections = re.split(pattern, raw_rst)

    sections = []
    # Jika split menghasilkan bagian-bagian
    i = 0
    current_sec_title = "Overview"
    current_content = ""

    # Pendekatan sederhana: pisahkan berdasarkan heading level 2/3
    lines = raw_rst.splitlines()
    sec_title = "Overview"
    buffer_lines = []
    blocks = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        # Cek apakah baris berikutnya adalah penanda heading (=== atau ---)
        if idx + 1 < len(lines) and lines[idx + 1].strip() and all(c in "=-~" for c in lines[idx + 1].strip()) and len(lines[idx + 1].strip()) >= 3:
            # Simpan blok sebelumnya
            if buffer_lines:
                blocks.append((sec_title, "\n".join(buffer_lines)))
                buffer_lines = []
            sec_title = re.sub(r':[a-zA-Z0-9_]+:`!?(.*?)`', r'\1', line).strip()
            idx += 2
            continue
        buffer_lines.append(line)
        idx += 1

    if buffer_lines:
        blocks.append((sec_title, "\n".join(buffer_lines)))

    records = []
    for section_name, content in blocks:
        # Ekstrak contoh kode Python: :: diikuti baris berindentasi atau .. code-block:: python
        code_snippets = []

        # Ekstrak blok kode bertanda ::
        code_matches = re.findall(r'::\s*\n\n((?:(?:\s{3,}[^\n]*|\s*)\n)+)', content)
        for cm in code_matches:
            cleaned_cm = "\n".join(l.strip() for l in cm.splitlines() if l.strip())
            if cleaned_cm and ("def " in cleaned_cm or ">>> " in cleaned_cm or "class " in cleaned_cm or "import " in cleaned_cm or "=" in cleaned_cm):
                code_snippets.append(cleaned_cm)

        # Hapus blok kode dari teks narasi
        text_without_code = re.sub(r'::\s*\n\n(?:(?:\s{3,}[^\n]*|\s*)\n)+', '\n', content)
        cleaned_text = clean_rst_text(text_without_code)

        # Lewati section yang terlalu pendek atau hanya boilerplate whatsnew
        if len(cleaned_text) < 40 and not code_snippets:
            continue

        combined_code = "\n\n# -----------------------------------------\n\n".join(code_snippets[:3])

        records.append({
            "category": category,
            "main_title": main_title,
            "section_title": section_name,
            "source_url": learn_url,
            "text_content": cleaned_text[:1800],  # Chunk optimal untuk LLM / RAG
            "code_snippet": combined_code,
        })

    return records


def main():
    print("=" * 75)
    print("🐍 SCRAPING DOKUMENTASI RESMI PYTHON (3.12 / 3.13 MODERN SYNTAX & TOOLS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "python_docs.pdf"
    csv_file = output_dir / "python_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_rst = fetch_file(target["path"])
        if not raw_rst:
            print(f"       [!] Skip: File tidak ditemukan")
            continue

        sections = parse_rst_sections(raw_rst, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"python_{idx:03d}",
            "language": "Python",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk Python ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Python (3.12/3.13 Up-to-Date)",
        language="Python",
    )

    # Simpan backup CSV
    fieldnames = [
        "doc_id",
        "language",
        "category",
        "main_title",
        "section_title",
        "source_url",
        "text_content",
        "code_snippet",
    ]
    with open(csv_file, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(formatted_records)

    print(f"\n🎉 DATASET PYTHON BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk Python")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

