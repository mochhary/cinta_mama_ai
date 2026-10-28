"""
Script Scraper Dokumentasi Resmi JavaScript (MDN Web Docs - Modern ES2023 / ES2024 & Node.js)
Mencakup Grammar & Types, Control Flow, Functions, Classes, Promises/Async-Await, Modules (ESM),
serta Fitur Terbaru ES2023/ES2024 (Object.groupBy, Promise.withResolvers, Array toSorted/with).
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

MDN_RAW_BASE = "https://raw.githubusercontent.com/mdn/content/main/files/en-us/web/javascript"
MDN_WEB_BASE = "https://developer.mozilla.org/en-US/docs/Web/JavaScript"

DOC_TARGETS = [
    {
        "category": "JavaScript Introduction",
        "path": "guide/introduction/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Introduction",
        "title": "JavaScript Overview & Runtime Introduction",
    },
    {
        "category": "Grammar, Variables & Types",
        "path": "guide/grammar_and_types/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Grammar_and_types",
        "title": "Grammar and Types (let, const, Data Types, Type Coercion, Literals)",
    },
    {
        "category": "Control Flow & Error Handling",
        "path": "guide/control_flow_and_error_handling/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Control_flow_and_error_handling",
        "title": "Control Flow and Error Handling (if, switch, try-catch-finally, Error Types)",
    },
    {
        "category": "Functions & Arrow Syntax",
        "path": "guide/functions/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Functions",
        "title": "Functions (Arrow Functions, Default Parameters, Rest/Spread, Closures)",
    },
    {
        "category": "Classes & Modern OOP",
        "path": "guide/using_classes/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Using_classes",
        "title": "Using Classes (Constructors, Private Fields #, Static Properties, Inheritance)",
    },
    {
        "category": "Asynchronous JavaScript (Promises & Async/Await)",
        "path": "guide/using_promises/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Using_promises",
        "title": "Using Promises and Async/Await (Chaining, Promise.all, Error Handling)",
    },
    {
        "category": "Iterators and Generators",
        "path": "guide/iterators_and_generators/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Iterators_and_generators",
        "title": "Iterators and Generators (yield, Iterables, for...of loops)",
    },
    {
        "category": "JavaScript Modules (ESM)",
        "path": "guide/modules/index.md",
        "web_url": f"{MDN_WEB_BASE}/Guide/Modules",
        "title": "JavaScript Modules (import, export, dynamic import, Top-level await)",
    },
    {
        "category": "Modern Features - ES2023/ES2024: Object.groupBy",
        "path": "reference/global_objects/object/groupby/index.md",
        "web_url": f"{MDN_WEB_BASE}/Reference/Global_Objects/Object/groupBy",
        "title": "Object.groupBy() (Grouping array elements into object keys)",
    },
    {
        "category": "Modern Features - ES2024: Promise.withResolvers",
        "path": "reference/global_objects/promise/withresolvers/index.md",
        "web_url": f"{MDN_WEB_BASE}/Reference/Global_Objects/Promise/withResolvers",
        "title": "Promise.withResolvers() (Modern Promise resolution without manual callback wiring)",
    },
    {
        "category": "Modern Features - ES2023: Non-mutating Array Methods",
        "path": "reference/global_objects/array/tosorted/index.md",
        "web_url": f"{MDN_WEB_BASE}/Reference/Global_Objects/Array/toSorted",
        "title": "Array.prototype.toSorted() & Change Array by Copy (toReversed, toSpliced, with)",
    },
]


def fetch_mdn(rel_path: str) -> str:
    """Mengunduh file markdown dari GitHub repository mdn/content."""
    url = f"{MDN_RAW_BASE}/{rel_path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MDN JavaScript Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_mdn_markdown(text: str) -> str:
    """Membersihkan markdown MDN dari macros {{jsxref(...)}} dan frontmatter."""
    # Hapus makro MDN {{ ... }}
    text = re.sub(r'\{\{[a-zA-Z0-9_\(\)\s,"\'\.\-]+\}\}', '', text)
    # Hapus HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Ubah [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_mdn_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    """Memecah markdown MDN menjadi section terstruktur."""
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    # Hapus frontmatter YAML
    clean_md = re.sub(r'^---[\s\S]*?---\s*', '', raw_md)

    # Pecah per heading level 2 (## )
    sections = re.split(r'\n(?=##\s+)', clean_md)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r'^##\s+(.+)$', sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        # Lewati heading navigasi seperti "See also" atau "Specifications"
        if section_name.lower() in ["see also", "specifications", "browser compatibility"]:
            continue

        snippets = []
        code_blocks = re.findall(r'```(?:js|javascript|html)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_mdn_markdown(text_only)

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
    print(" SCRAPING DOKUMENTASI RESMI JAVASCRIPT (MDN - MODERN ES2023/ES2024 & NODE.JS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "javascript_docs.pdf"
    csv_file = output_dir / "javascript_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_mdn(target["path"])
        if not raw_md:
            continue

        sections = parse_mdn_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"javascript_{idx:03d}",
            "language": "JavaScript",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk JavaScript ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks JavaScript (ES2023/ES2024 Up-to-Date)",
        language="JavaScript",
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

    print(f"\n DATASET JAVASCRIPT BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk JavaScript")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode JavaScript")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

