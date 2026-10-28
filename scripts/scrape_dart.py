"""
Script Scraper Dokumentasi Resmi Dart (dart-lang/site-www - Dart 3.x Modern Language & Sound Null Safety)
Mencakup Variables, Types, Control Flow, Functions, Classes & Mixins, Asynchronous (Future, async/await, Streams),
serta Fitur Unggulan Dart 3 (Records, Pattern Matching, Class Modifiers: sealed/final/base/interface, Extension Types).
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

DART_RAW_BASE = "https://raw.githubusercontent.com/dart-lang/site-www/main/src/content/language"
DART_WEB_BASE = "https://dart.dev/language"

DOC_TARGETS = [
    {
        "category": "Variables & Sound Type System",
        "path": "variables.md",
        "web_url": f"{DART_WEB_BASE}/variables",
        "title": "Variables & Sound Null Safety (var, Object, Null safety ?/!, late, final, const)",
    },
    {
        "category": "Built-in Types & Collections",
        "path": "built-in-types.md",
        "web_url": f"{DART_WEB_BASE}/built-in-types",
        "title": "Built-in Types (Numbers int/double, Strings, Booleans, Runes, Symbols)",
    },
    {
        "category": "Collections & Collection-If/For",
        "path": "collections.md",
        "web_url": f"{DART_WEB_BASE}/collections",
        "title": "Collections (Lists, Sets, Maps, Spread operators ..., Control-flow operators)",
    },
    {
        "category": "Functions & First-Class Functions",
        "path": "functions.md",
        "web_url": f"{DART_WEB_BASE}/functions",
        "title": "Functions (Named/Optional parameters, Arrow syntax =>, Anonymous functions, Closures)",
    },
    {
        "category": "Branches & Loops",
        "path": "branches.md",
        "web_url": f"{DART_WEB_BASE}/branches",
        "title": "Branches and Loops (if-case, switch expressions, Exhaustiveness checking)",
    },
    {
        "category": "Classes, Constructors & Mixins",
        "path": "classes.md",
        "web_url": f"{DART_WEB_BASE}/classes",
        "title": "Classes and Objects (Named constructors, Initializer lists, Factory constructors)",
    },
    {
        "category": "Modern OOP - Mixins",
        "path": "mixins.md",
        "web_url": f"{DART_WEB_BASE}/mixins",
        "title": "Mixins (Code reuse across multiple class hierarchies with on & mixin class)",
    },
    {
        "category": "Asynchronous Programming (Future & Stream)",
        "path": "async.md",
        "web_url": f"{DART_WEB_BASE}/async",
        "title": "Asynchronous Support (async, await, Future<T>, Stream<T>, Error handling)",
    },
    {
        "category": "Modern Features - Dart 3: Records",
        "path": "records.md",
        "web_url": f"{DART_WEB_BASE}/records",
        "title": "Dart 3 Records (Anonymous, immutable, aggregate values with positional & named fields)",
    },
    {
        "category": "Modern Features - Dart 3: Patterns & Pattern Matching",
        "path": "patterns.md",
        "web_url": f"{DART_WEB_BASE}/patterns",
        "title": "Dart 3 Patterns (Destructuring, Pattern matching in switch/if-case, Exhaustiveness)",
    },
    {
        "category": "Modern Features - Dart 3: Class Modifiers",
        "path": "class-modifiers.md",
        "web_url": f"{DART_WEB_BASE}/class-modifiers",
        "title": "Dart 3 Class Modifiers (sealed, final, base, interface, abstract, mixin class)",
    },
    {
        "category": "Modern Features - Dart 3.3: Extension Types",
        "path": "extension-types.md",
        "web_url": f"{DART_WEB_BASE}/extension-types",
        "title": "Dart 3.3 Extension Types (Zero-cost compile-time wrappers with representation type)",
    },
]


def fetch_dart_file(path: str) -> str:
    url = f"{DART_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Dart Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_dart_markdown(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Hapus Jekyll/Liquid tags {% ... %}
    text = re.sub(r'\{%[\s\S]*?%\}', '', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_dart_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
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
        code_blocks = re.findall(r'```(?:dart)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_dart_markdown(text_only)

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
    print(" SCRAPING DOKUMENTASI RESMI DART (DART 3.x - SOUND NULL SAFETY & RECORDS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "dart_docs.pdf"
    csv_file = output_dir / "dart_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_dart_file(target["path"])
        if not raw_md:
            continue

        sections = parse_dart_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode Dart)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"dart_{idx:03d}",
            "language": "Dart",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk Dart ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Dart (Dart 3.x Up-to-Date)",
        language="Dart",
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

    print(f"\n DATASET DART BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk Dart")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode Dart")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

