"""
Script Scraper Dokumentasi Resmi TypeScript (microsoft/TypeScript-Website - TypeScript 5.x Modern Handbook & Release Notes)
Mencakup Basics, Type System, Narrowing, Functions, Object Types, Generics, Classes,
serta Fitur Terbaru TypeScript 5.x (using statements, satisfies operator, inferred type predicates, NoInfer, const type parameters).
"""

import os
import re
import csv
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any

try:
    from scripts.pdf_exporter import export_records_to_pdf
except ImportError:
    from pdf_exporter import export_records_to_pdf

RAW_BASE = "https://raw.githubusercontent.com/microsoft/TypeScript-Website/v2/packages/documentation/copy/en"
WEB_BASE = "https://www.typescriptlang.org/docs/handbook"

DOC_TARGETS = [
    {
        "category": "Basics & Tooling",
        "path": "handbook-v2/Basics.md",
        "web_url": f"{WEB_BASE}/2/basic-types.html",
        "title": "The Basics (Type Checking, Types by Inference, Downleveling)",
    },
    {
        "category": "Everyday Types",
        "path": "handbook-v2/Everyday Types.md",
        "web_url": f"{WEB_BASE}/2/everyday-types.html",
        "title": "Everyday Types (Primitives, Arrays, any, Union Types, Type Aliases, Interfaces)",
    },
    {
        "category": "Narrowing & Type Guards",
        "path": "handbook-v2/Narrowing.md",
        "web_url": f"{WEB_BASE}/2/narrowing.html",
        "title": "Narrowing (typeof, Truthiness, Equality, in operator, Type Predicates)",
    },
    {
        "category": "Functions & Call Signatures",
        "path": "handbook-v2/More on Functions.md",
        "web_url": f"{WEB_BASE}/2/more-on-functions.html",
        "title": "More on Functions (Generic Functions, Optional Parameters, Function Overloads)",
    },
    {
        "category": "Object Types & Interfaces",
        "path": "handbook-v2/Object Types.md",
        "web_url": f"{WEB_BASE}/2/objects.html",
        "title": "Object Types (Property Modifiers, readonly, Index Signatures, Extending Types)",
    },
    {
        "category": "Generics & Type Manipulation",
        "path": "handbook-v2/Type Manipulation/Generics.md",
        "web_url": f"{WEB_BASE}/2/generics.html",
        "title": "Generics (Type Variables, Generic Types, Generic Classes, Constraints)",
    },
    {
        "category": "Classes & Modern OOP",
        "path": "handbook-v2/Classes.md",
        "web_url": f"{WEB_BASE}/2/classes.html",
        "title": "Classes (Members, Getters/Setters, Implements, Extends, Visibility, static)",
    },
    {
        "category": "Modern Modules & ESM",
        "path": "handbook-v2/Modules.md",
        "web_url": f"{WEB_BASE}/2/modules.html",
        "title": "Modules (ESM, CommonJS, TypeScript Specific Syntax, Resolution)",
    },
    {
        "category": "Modern Features - TypeScript 5.2",
        "path": "release-notes/TypeScript 5.2.md",
        "web_url": "https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-2.html",
        "title": "TypeScript 5.2: using Declarations and Explicit Resource Management",
    },
    {
        "category": "Modern Features - TypeScript 5.4",
        "path": "release-notes/TypeScript 5.4.md",
        "web_url": "https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-4.html",
        "title": "TypeScript 5.4: Preserved Narrowing in Closures, NoInfer Utility Type",
    },
    {
        "category": "Modern Features - TypeScript 5.5",
        "path": "release-notes/TypeScript 5.5.md",
        "web_url": "https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html",
        "title": "TypeScript 5.5: Inferred Type Predicates, Regular Expression Syntax Checking",
    },
]


def fetch_doc(rel_path: str) -> str:
    """Mengunduh file markdown dari GitHub repo microsoft/TypeScript-Website."""
    encoded_path = urllib.parse.quote(rel_path)
    url = f"{RAW_BASE}/{encoded_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TypeScript Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_markdown_for_rag(text: str) -> str:
    """Membersihkan markdown dari tag dekoratif dan HTML."""
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_ts_markdown(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    """Memecah markdown TypeScript Handbook menjadi section-section yang terstruktur."""
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    # Hapus frontmatter YAML
    clean_md = re.sub(r'^---[\s\S]*?---\s*', '', raw_md)

    # Pecah per heading level 2 atau level 3 (## atau ###)
    sections = re.split(r'\n(?=##{1,2}\s+)', clean_md)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r'^##{1,2}\s+(.+)$', sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        # Ekstrak kode blok ts, typescript, js, json, bash
        snippets = []
        code_blocks = re.findall(r'```(?:ts|typescript|js|javascript|json|bash|sh)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        # Hapus kode dari narasi teks
        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_markdown_for_rag(text_only)

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
    print("🔷 SCRAPING DOKUMENTASI RESMI TYPESCRIPT (5.x MODERN HANDBOOK & RELEASE NOTES)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "typescript_docs.pdf"
    csv_file = output_dir / "typescript_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_doc(target["path"])
        if not raw_md:
            continue

        sections = parse_ts_markdown(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode/syntax)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"typescript_{idx:03d}",
            "language": "TypeScript",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk TypeScript ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks TypeScript (5.x Up-to-Date)",
        language="TypeScript",
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

    print(f"\n🎉 DATASET TYPESCRIPT BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk TypeScript")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode TypeScript")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

