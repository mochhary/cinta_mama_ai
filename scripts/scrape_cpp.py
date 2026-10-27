"""
Script Scraper Dokumentasi Resmi C++ (MicrosoftDocs/cpp-docs - Modern C++20 / C++23)
Mencakup Welcome to Modern C++, Modern Type System, Smart Pointers (unique_ptr, shared_ptr),
RAII & Exception Handling, Lambda Expressions, Move Semantics, Class Templates, serta C++20 Modules.
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

CPP_RAW_BASE = "https://raw.githubusercontent.com/MicrosoftDocs/cpp-docs/main/docs/cpp"
CPP_WEB_BASE = "https://learn.microsoft.com/en-us/cpp/cpp"

DOC_TARGETS = [
    {
        "category": "Modern C++ Overview",
        "path": "welcome-back-to-cpp-modern-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/welcome-back-to-cpp-modern-cpp",
        "title": "Welcome Back to C++ - Modern C++ (C++20/23 Idioms, RAII, auto)",
    },
    {
        "category": "Modern Type System",
        "path": "cpp-type-system-modern-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/cpp-type-system-modern-cpp",
        "title": "C++ Type System (Fundamental types, const, auto, decltype, Value categories)",
    },
    {
        "category": "Memory Management - Smart Pointers",
        "path": "smart-pointers-modern-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/smart-pointers-modern-cpp",
        "title": "Smart Pointers (std::unique_ptr, std::shared_ptr, std::weak_ptr, make_unique)",
    },
    {
        "category": "Exception Handling & RAII",
        "path": "errors-and-exception-handling-modern-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/errors-and-exception-handling-modern-cpp",
        "title": "Modern C++ Best Practices for Exceptions and Error Handling",
    },
    {
        "category": "Modern Features - C++20 Modules",
        "path": "import-export-module.md",
        "web_url": f"{CPP_WEB_BASE}/import-export-module",
        "title": "C++20 Modules (export module, import, Module partitions, Global module)",
    },
    {
        "category": "Lambda Expressions",
        "path": "lambda-expressions-in-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/lambda-expressions-in-cpp",
        "title": "Lambda Expressions (Capture clauses, Parameter lists, Mutable, Generic lambdas)",
    },
    {
        "category": "Move Semantics & Rvalue References",
        "path": "move-constructors-and-move-assignment-operators-cpp.md",
        "web_url": f"{CPP_WEB_BASE}/move-constructors-and-move-assignment-operators-cpp",
        "title": "Move Constructors and Move Assignment Operators (std::move, Rvalue references &&)",
    },
    {
        "category": "Templates & Generic Programming",
        "path": "class-templates.md",
        "web_url": f"{CPP_WEB_BASE}/class-templates",
        "title": "Class Templates & Generic Programming (template parameters, Specialization)",
    },
]


def fetch_cpp_file(path: str) -> str:
    url = f"{CPP_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (C++ Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_cpp_markdown(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_cpp_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    clean_md = re.sub(r'^---[\s\S]*?---\s*', '', raw_md)
    sections = re.split(r'\n(?=#{2,3}\s+)', clean_md)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r'^#{2,3}\s+(.+)$', sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        snippets = []
        code_blocks = re.findall(r'```(?:cpp|c\+\+|csharp)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_cpp_markdown(text_only)

        if len(cleaned_text) < 35 and not snippets:
            continue

        combined_code = "\n\n// -----------------------------------------\n\n".join(snippets[:3])

        records.append({
            "category": category,
            "main_title": main_title,
            "section_title": section_name,
            "source_url": learn_url,
            "text_content": cleaned_text[:1800],
            "code_snippet": combined_code,
        })

    return records


def main():
    print("=" * 75)
    print("⚡ SCRAPING DOKUMENTASI RESMI C++ (MODERN C++20 / C++23 - MICROSOFT DOCS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "cpp_docs.pdf"
    csv_file = output_dir / "cpp_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_cpp_file(target["path"])
        if not raw_md:
            continue

        sections = parse_cpp_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode C++)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"cpp_{idx:03d}",
            "language": "C++",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk C++ ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks C++ (Modern C++20/C++23 Up-to-Date)",
        language="C++",
    )

    # Backup CSV
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

    print(f"\n🎉 DATASET C++ BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk C++")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode C++")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

