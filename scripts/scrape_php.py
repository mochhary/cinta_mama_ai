"""
Script Scraper Dokumentasi Resmi PHP (php/doc-en - PHP 8.2 / 8.3 / 8.4 Modern OOP & Features)
Mencakup Sintaks Dasar, Type System (DNF Types), Match Expressions, Enums, Modern OOP (Readonly Classes, Property Hooks,
Asymmetric Visibility), Attributes, serta Fitur Rilis Terbaru PHP 8.2, 8.3, dan 8.4.
"""

import os
import re
import csv
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Any

try:
    from scripts.pdf_exporter import export_records_to_pdf
except ImportError:
    from pdf_exporter import export_records_to_pdf

PHP_RAW_BASE = "https://raw.githubusercontent.com/php/doc-en/master"
PHP_WEB_BASE = "https://www.php.net/manual/en"

DOC_TARGETS = [
    {
        "category": "Basic Syntax & Types",
        "path": "language/basic-syntax.xml",
        "web_url": f"{PHP_WEB_BASE}/language.basic-syntax.php",
        "title": "PHP Basic Syntax (Tags, Escaping, Comments)",
    },
    {
        "category": "Type Declarations & DNF Types",
        "path": "language/types/declarations.xml",
        "web_url": f"{PHP_WEB_BASE}/language.types.declarations.php",
        "title": "Type Declarations (Return Types, Union Types, Intersection Types, DNF Types)",
    },
    {
        "category": "Control Structures - match Expression",
        "path": "language/control-structures/match.xml",
        "web_url": f"{PHP_WEB_BASE}/control-structures.match.php",
        "title": "The match Expression (Pattern comparison, Exhaustive evaluation)",
    },
    {
        "category": "Modern OOP - Classes & Objects",
        "path": "language/oop5/basic.xml",
        "web_url": f"{PHP_WEB_BASE}/language.oop5.basic.php",
        "title": "Classes and Objects Basics (class, new, extends, readonly classes)",
    },
    {
        "category": "Modern OOP - Visibility & Properties",
        "path": "language/oop5/visibility.xml",
        "web_url": f"{PHP_WEB_BASE}/language.oop5.visibility.php",
        "title": "Property and Method Visibility (public, private, protected, readonly, asymmetric)",
    },
    {
        "category": "Modern OOP - Enumerations (Enums)",
        "path": "language/types/enumerations.xml",
        "web_url": f"{PHP_WEB_BASE}/language.types.enumerations.php",
        "title": "Enumerations (Pure enums, Backed enums, Methods in enums)",
    },
    {
        "category": "Modern OOP - Interfaces & Traits",
        "path": "language/oop5/interfaces.xml",
        "web_url": f"{PHP_WEB_BASE}/language.oop5.interfaces.php",
        "title": "Object Interfaces (implements, Multiple interfaces, Constants)",
    },
    {
        "category": "Modern Attributes Syntax",
        "path": "language/attributes.xml",
        "web_url": f"{PHP_WEB_BASE}/language.attributes.php",
        "title": "Attributes (Metadata reflection, #[Attribute] syntax)",
    },
    {
        "category": "Modern Features - PHP 8.2",
        "path": "appendices/migration82/new-features.xml",
        "web_url": f"{PHP_WEB_BASE}/migration82.new-features.php",
        "title": "PHP 8.2 New Features (Readonly classes, null/false as standalone types, DNF types)",
    },
    {
        "category": "Modern Features - PHP 8.3",
        "path": "appendices/migration83/new-features.xml",
        "web_url": f"{PHP_WEB_BASE}/migration83.new-features.php",
        "title": "PHP 8.3 New Features (Typed class constants, json_validate(), #[\\Override])",
    },
    {
        "category": "Modern Features - PHP 8.4",
        "path": "appendices/migration84/new-features.xml",
        "web_url": f"{PHP_WEB_BASE}/migration84.new-features.php",
        "title": "PHP 8.4 New Features (Property Hooks, Asymmetric Visibility, new without parentheses)",
    },
]


def fetch_php_xml(rel_path: str) -> str:
    url = f"{PHP_RAW_BASE}/{rel_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PHP Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_xml_text(xml_chunk: str) -> str:
    text = re.sub(r'<programlisting[\s\S]*?</programlisting>', '', xml_chunk)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_docbook_sections(raw_xml: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    # Cari section berdasarkan tag <sect1>, <sect2>, atau <section>
    sections = re.split(r'(?=<sect[123]|<section)', raw_xml)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        title_match = re.search(r'<title>(.*?)</title>', sec, re.DOTALL)
        sec_title = clean_xml_text(title_match.group(1)) if title_match else "Overview"

        # Ekstrak kode programlisting
        code_blocks = re.findall(r'<programlisting[^>]*>([\s\S]*?)</programlisting>', sec)
        clean_codes = []
        for cb in code_blocks:
            c_clean = re.sub(r'<[^>]+>', '', cb).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
            # Hapus <?php CDATA tag jika ada
            c_clean = re.sub(r'<!\[CDATA\[|\]\]>', '', c_clean).strip()
            if c_clean:
                clean_codes.append(c_clean)

        text_content = clean_xml_text(sec)
        if len(text_content) < 35 and not clean_codes:
            continue

        records.append({
            "category": category,
            "main_title": main_title,
            "section_title": sec_title,
            "source_url": learn_url,
            "text_content": text_content[:1800],
            "code_snippet": "\n\n// -----------------------------------------\n\n".join(clean_codes[:3]),
        })

    return records


def main():
    print("=" * 75)
    print(" SCRAPING DOKUMENTASI RESMI PHP (PHP 8.2 / 8.3 / 8.4 MODERN OOP & SYNTAX)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "php_docs.pdf"
    csv_file = output_dir / "php_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_xml = fetch_php_xml(target["path"])
        if not raw_xml:
            continue

        sections = parse_docbook_sections(raw_xml, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode PHP)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"php_{idx:03d}",
            "language": "PHP",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk PHP ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks PHP (8.2/8.3/8.4 Up-to-Date)",
        language="PHP",
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

    print(f"\n DATASET PHP BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk PHP")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode PHP")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
