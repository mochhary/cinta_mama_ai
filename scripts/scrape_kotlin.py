"""
Script Scraper Dokumentasi Resmi Kotlin (JetBrains/kotlin-web-site - Kotlin 2.0+ K2 Compiler & Modern Features)
Mencakup Basic Syntax, Control Flow (when, if), Null Safety, Classes & Constructors, Data Classes, Sealed Classes & Interfaces,
Extension Functions, Coroutines Concurrency, serta Fitur Rilis Terkini Kotlin 2.0.0 (K2 Compiler, Smart Casts 2.0).
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

KOTLIN_RAW_BASE = "https://raw.githubusercontent.com/JetBrains/kotlin-web-site/master/docs/topics"
KOTLIN_WEB_BASE = "https://kotlinlang.org/docs"

DOC_TARGETS = [
    {
        "category": "Basic Syntax & Idioms",
        "path": "basic-syntax.md",
        "web_url": f"{KOTLIN_WEB_BASE}/basic-syntax.html",
        "title": "Basic Syntax (Variables, Functions, String templates, Collections)",
    },
    {
        "category": "Control Flow & Pattern Matching",
        "path": "control-flow.md",
        "web_url": f"{KOTLIN_WEB_BASE}/control-flow.html",
        "title": "Control Flow (when Expression, if expression, for & while loops, Ranges)",
    },
    {
        "category": "Null Safety & Type System",
        "path": "null-safety.md",
        "web_url": f"{KOTLIN_WEB_BASE}/null-safety.html",
        "title": "Null Safety (Nullable types ?, Safe calls ?., Elvis operator ?:, Safe casts)",
    },
    {
        "category": "Classes & Modern OOP",
        "path": "classes.md",
        "web_url": f"{KOTLIN_WEB_BASE}/classes.html",
        "title": "Classes and Inheritance (Primary/Secondary Constructors, Init blocks, Abstract classes)",
    },
    {
        "category": "Modern Data Carriers - Data Classes",
        "path": "data-classes.md",
        "web_url": f"{KOTLIN_WEB_BASE}/data-classes.html",
        "title": "Data Classes (copy(), Destructuring declarations, componentN() functions)",
    },
    {
        "category": "Hierarchies - Sealed Classes & Interfaces",
        "path": "sealed-classes.md",
        "web_url": f"{KOTLIN_WEB_BASE}/sealed-classes.html",
        "title": "Sealed Classes and Interfaces (Restricted class hierarchies, Exhaustive when)",
    },
    {
        "category": "Extension Functions & Properties",
        "path": "extensions.md",
        "web_url": f"{KOTLIN_WEB_BASE}/extensions.html",
        "title": "Extensions (Extension functions, Extension properties, Scope of extensions)",
    },
    {
        "category": "Asynchronous Programming - Coroutines",
        "path": "coroutines-overview.md",
        "web_url": f"{KOTLIN_WEB_BASE}/coroutines-overview.html",
        "title": "Coroutines (Lightweight threads, Suspending functions, Structured concurrency)",
    },
    {
        "category": "Modern Features - Kotlin 2.0 (K2 Compiler)",
        "path": "whatsnew/whatsnew20.md",
        "web_url": f"{KOTLIN_WEB_BASE}/whatsnew20.html",
        "title": "What's New in Kotlin 2.0 (K2 Compiler GA, Smart Casts 2.0, Data Objects, Multiplatform)",
    },
]


def fetch_kotlin_file(path: str) -> str:
    url = f"{KOTLIN_RAW_BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Kotlin Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_kotlin_markdown(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_kotlin_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
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
        code_blocks = re.findall(r'```(?:kotlin|groovy)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_kotlin_markdown(text_only)

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
    print("🟣 SCRAPING DOKUMENTASI RESMI KOTLIN (2.0+ K2 COMPILER & MODERN LANGUAGE)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "kotlin_docs.pdf"
    csv_file = output_dir / "kotlin_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_kotlin_file(target["path"])
        if not raw_md:
            continue

        sections = parse_kotlin_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode Kotlin)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"kotlin_{idx:03d}",
            "language": "Kotlin",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk Kotlin ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Kotlin (Kotlin 2.0+ Up-to-Date)",
        language="Kotlin",
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

    print(f"\n🎉 DATASET KOTLIN BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk Kotlin")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode Kotlin")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

