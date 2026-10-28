"""
Script Scraper Dokumentasi Resmi Swift (swiftlang/swift-book - Swift 5.10 / Swift 6 Modern Guide)
Mencakup The Basics, Optionals, Control Flow, Functions, Classes & Structures (Value vs Reference),
Protocols, Generics, Error Handling, Concurrency (async/await, Task Groups, Actors, Sendable), serta Swift Macros.
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

SWIFT_RAW_BASE = "https://raw.githubusercontent.com/swiftlang/swift-book/main/TSPL.docc/LanguageGuide"
SWIFT_WEB_BASE = "https://docs.swift.org/swift-book/documentation/the-swift-programming-language"

DOC_TARGETS = [
    {
        "category": "The Basics & Optionals",
        "path": "TheBasics.md",
        "web_url": f"{SWIFT_WEB_BASE}/thebasics",
        "title": "The Basics (Constants let, Variables var, Type Annotations, Optionals ?/!, Nil-Coalescing)",
    },
    {
        "category": "Control Flow & Pattern Matching",
        "path": "ControlFlow.md",
        "web_url": f"{SWIFT_WEB_BASE}/controlflow",
        "title": "Control Flow (for-in, while, if, guard let, switch with tuples & where clauses)",
    },
    {
        "category": "Functions & Parameters",
        "path": "Functions.md",
        "web_url": f"{SWIFT_WEB_BASE}/functions",
        "title": "Functions (Argument Labels, Default Parameter Values, inout parameters, Function Types)",
    },
    {
        "category": "Structures and Classes",
        "path": "ClassesAndStructures.md",
        "web_url": f"{SWIFT_WEB_BASE}/classesandstructures",
        "title": "Structures and Classes (Value Types vs Reference Types, Mutating methods, Identity operators)",
    },
    {
        "category": "Protocols & Polymorphism",
        "path": "Protocols.md",
        "web_url": f"{SWIFT_WEB_BASE}/protocols",
        "title": "Protocols (Property/Method requirements, Protocol Inheritance, Delegation, any/some)",
    },
    {
        "category": "Generics & Associated Types",
        "path": "Generics.md",
        "web_url": f"{SWIFT_WEB_BASE}/generics",
        "title": "Generics (Type Constraints, Associated Types, where clauses, Generic Subscripts)",
    },
    {
        "category": "Error Handling",
        "path": "ErrorHandling.md",
        "web_url": f"{SWIFT_WEB_BASE}/errorhandling",
        "title": "Error Handling (Representing Errors, throws, do-catch, try?, try!, defer)",
    },
    {
        "category": "Modern Concurrency (Swift 6 Strict)",
        "path": "Concurrency.md",
        "web_url": f"{SWIFT_WEB_BASE}/concurrency",
        "title": "Concurrency (async/await, Task and TaskGroup, Actors data isolation, Sendable types)",
    },
    {
        "category": "Modern Metaprogramming - Swift Macros",
        "path": "Macros.md",
        "web_url": f"{SWIFT_WEB_BASE}/macros",
        "title": "Macros (Freestanding Macros #, Attached Macros @, Compiler AST Transformation)",
    },
]


def fetch_swift_file(path: str) -> str:
    url = f"{SWIFT_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Swift Book Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_swift_markdown(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_swift_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
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
        code_blocks = re.findall(r'```(?:swift)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_swift_markdown(text_only)

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
    print(" SCRAPING DOKUMENTASI RESMI SWIFT (SWIFT 5.10 / SWIFT 6 CONCURRENCY & MACROS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "swift_docs.pdf"
    csv_file = output_dir / "swift_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_swift_file(target["path"])
        if not raw_md:
            continue

        sections = parse_swift_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode Swift)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"swift_{idx:03d}",
            "language": "Swift",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk Swift ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Swift (Swift 5.10/Swift 6 Up-to-Date)",
        language="Swift",
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

    print(f"\n DATASET SWIFT BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk Swift")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode Swift")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

