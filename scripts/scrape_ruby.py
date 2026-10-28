"""
Script Scraper Dokumentasi Resmi Ruby (ruby/ruby doc/syntax & NEWS.md - Ruby 3.2 / 3.3 Modern Features)
Mencakup Literals, Assignment, Control Expressions, Methods (Endless Methods & Kwargs), Classes & Modules (Data.define),
Pattern Matching in Ruby, Calling Methods, Exceptions Handling, serta Fitur Rilis Modern Ruby 3.2 / 3.3 (YJIT, Prism).
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

RUBY_RAW_BASE = "https://raw.githubusercontent.com/ruby/ruby/master"
RUBY_WEB_BASE = "https://docs.ruby-lang.org/en/master/syntax"

DOC_TARGETS = [
    {
        "category": "Literals & Basic Types",
        "path": "doc/syntax/literals.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/literals_rdoc.html",
        "title": "Literals (Numbers, Strings, Arrays, Hashes, Symbols, Ranges, Regexp)",
    },
    {
        "category": "Assignment & Variables",
        "path": "doc/syntax/assignment.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/assignment_rdoc.html",
        "title": "Assignment (Local, Instance @, Class @@, Global $, Multiple assignment)",
    },
    {
        "category": "Control Expressions",
        "path": "doc/syntax/control_expressions.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/control_expressions_rdoc.html",
        "title": "Control Expressions (if/unless, case/when, while/until, break/next/redo)",
    },
    {
        "category": "Methods & Modern Syntax",
        "path": "doc/syntax/methods.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/methods_rdoc.html",
        "title": "Methods (Default args, Keyword args **, Endless methods def foo() = expr, Blocks)",
    },
    {
        "category": "Modern Features - Pattern Matching",
        "path": "doc/syntax/pattern_matching.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/pattern_matching_rdoc.html",
        "title": "Pattern Matching (case in, Variable pinning ^, Hash/Array patterns, Alternative patterns |)",
    },
    {
        "category": "Classes, Modules & Data",
        "path": "doc/syntax/modules_and_classes.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/modules_and_classes_rdoc.html",
        "title": "Classes and Modules (Inheritance, self, include/prepend/extend, Data.define)",
    },
    {
        "category": "Calling Methods & Blocks",
        "path": "doc/syntax/calling_methods.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/calling_methods_rdoc.html",
        "title": "Calling Methods (Positional/Keyword args, Block arguments &, Safe navigation &.)",
    },
    {
        "category": "Exception Handling",
        "path": "doc/syntax/exceptions.rdoc",
        "web_url": f"{RUBY_WEB_BASE}/exceptions_rdoc.html",
        "title": "Exceptions (raise, rescue, ensure, else, retry, StandardError)",
    },
    {
        "category": "Modern Features - Ruby 3.2 / 3.3",
        "path": "NEWS.md",
        "web_url": "https://www.ruby-lang.org/en/news/",
        "title": "Ruby 3.2 & 3.3 Modern Release Features (YJIT Performance, Data class, Prism Parser)",
    },
]


def fetch_ruby_file(path: str) -> str:
    url = f"{RUBY_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Ruby Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_rdoc_text(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # RDoc formatting: +code+ -> code, *bold* -> bold
    text = re.sub(r'\+([^\+]+)\+', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_ruby_sections(raw_content: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    # RDoc headings use == Heading or === Subheading. Markdown uses ## or ###
    pattern = r'\n(?=(?:={2,3}\s+|#{2,3}\s+))'
    sections = re.split(pattern, raw_content)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r'^(?:={2,3}|#{2,3})\s+(.+)$', sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        snippets = []
        # Kode berindentasi atau ```ruby
        code_blocks = re.findall(r'```(?:ruby)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        # RDoc indented code blocks (4+ spaces)
        indented_code = re.findall(r'\n\n((?:(?:\s{4,}[^\n]*|\s*)\n)+)', sec)
        for ic in indented_code:
            lines = [l.strip() for l in ic.splitlines() if l.strip()]
            code_candidate = "\n".join(lines)
            if any(k in code_candidate for k in ["def ", "class ", "=>", "puts", "rescue", "case ", "in ", "do |"]):
                snippets.append(code_candidate)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_rdoc_text(text_only)

        if len(cleaned_text) < 35 and not snippets:
            continue

        combined_code = "\n\n# -----------------------------------------\n\n".join(snippets[:3])

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
    print(" SCRAPING DOKUMENTASI RESMI RUBY (RUBY 3.2 / 3.3 MODERN SYNTAX & YJIT)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "ruby_docs.pdf"
    csv_file = output_dir / "ruby_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_content = fetch_ruby_file(target["path"])
        if not raw_content:
            continue

        sections = parse_ruby_sections(raw_content, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode Ruby)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"ruby_{idx:03d}",
            "language": "Ruby",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk Ruby ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Ruby (Ruby 3.2/3.3 Up-to-Date)",
        language="Ruby",
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

    print(f"\n DATASET RUBY BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk Ruby")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode Ruby")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

