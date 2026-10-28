"""
Script Scraper Dokumentasi Resmi Go / Golang (go.dev & golang/website - Go 1.22 / 1.23)
Mencakup Getting Started, Go Modules, Control Structures, Functions & Defer, Slices & Maps,
Interfaces & Methods, Concurrency (Goroutines & Channels), Generics, Multi-module Workspaces,
serta Fitur Terbaru Go 1.22 & Go 1.23 (Range over Integer & Function Iterators, Modern http.ServeMux).
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

GO_RAW_BASE = "https://raw.githubusercontent.com/golang/website/master/_content/doc"

DOC_TARGETS = [
    {
        "category": "Getting Started & Tooling",
        "url": f"{GO_RAW_BASE}/tutorial/getting-started.html",
        "web_url": "https://go.dev/doc/tutorial/getting-started",
        "title": "Tutorial: Get Started with Go (Installation & CLI)",
        "type": "html",
    },
    {
        "category": "Go Modules & Dependency",
        "url": f"{GO_RAW_BASE}/tutorial/create-module.html",
        "web_url": "https://go.dev/doc/tutorial/create-module",
        "title": "Tutorial: Create a Go Module (go mod init, packages)",
        "type": "html",
    },
    {
        "category": "Error Handling & Robustness",
        "url": f"{GO_RAW_BASE}/tutorial/handle-errors.html",
        "web_url": "https://go.dev/doc/tutorial/handle-errors",
        "title": "Tutorial: Return and Handle Errors (errors.New, panic/recover)",
        "type": "html",
    },
    {
        "category": "Generics (Type Parameters)",
        "url": f"{GO_RAW_BASE}/tutorial/generics.md",
        "web_url": "https://go.dev/doc/tutorial/generics",
        "title": "Tutorial: Getting Started with Generics (Type constraints, any)",
        "type": "markdown",
    },
    {
        "category": "Multi-Module Workspaces",
        "url": f"{GO_RAW_BASE}/tutorial/workspaces.md",
        "web_url": "https://go.dev/doc/tutorial/workspaces",
        "title": "Tutorial: Multi-Module Workspaces (go work init & go.work)",
        "type": "markdown",
    },
    {
        "category": "Effective Go - Syntax & Idioms",
        "url": f"{GO_RAW_BASE}/effective_go.html",
        "web_url": "https://go.dev/doc/effective_go",
        "title": "Effective Go: Core Syntax, Data, Methods, Concurrency & Web Server",
        "type": "effective_go",
    },
    {
        "category": "Modern Features - Go 1.22",
        "url": "https://go.dev/doc/go1.22",
        "web_url": "https://go.dev/doc/go1.22",
        "title": "Go 1.22 Release Notes (for loop scoping, range-over-integer, http.ServeMux routing)",
        "type": "html",
    },
    {
        "category": "Modern Features - Go 1.23",
        "url": "https://go.dev/doc/go1.23",
        "web_url": "https://go.dev/doc/go1.23",
        "title": "Go 1.23 Release Notes (Range-over-function iterators iter.Seq, Tooling)",
        "type": "html",
    },
]


class HTMLContentExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.code_parts = []
        self.in_code = False
        self.current_code = []

    def handle_starttag(self, tag, attrs):
        if tag in ["pre", "code"]:
            self.in_code = True

    def handle_endtag(self, tag):
        if tag in ["pre", "code"]:
            self.in_code = False
            code_str = "".join(self.current_code).strip()
            if code_str:
                self.code_parts.append(code_str)
            self.current_code = []
        elif tag in ["p", "div", "li", "h1", "h2", "h3", "h4", "br"]:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if self.in_code:
            self.current_code.append(data)
        else:
            self.text_parts.append(data)


def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Golang Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_html_tags(html_str: str) -> str:
    text = re.sub(r'<pre[\s\S]*?</pre>', '', html_str)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_effective_go(html_content: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    """Memecah Effective Go menjadi section terstruktur berdasarkan h2/h3."""
    sections = re.split(r'\n(?=<h[23][^>]*>)', html_content)
    records = []

    for sec in sections:
        header_match = re.search(r'<h[23][^>]*>(.*?)</h[23]>', sec, re.DOTALL)
        if not header_match:
            continue
        sec_title = re.sub(r'<[^>]+>', '', header_match.group(1)).strip()

        # Ekstrak kode dalam <pre>
        codes = re.findall(r'<pre[^>]*>([\s\S]*?)</pre>', sec)
        clean_codes = []
        for c in codes:
            clean_c = re.sub(r'<[^>]+>', '', c).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
            if clean_c:
                clean_codes.append(clean_c)

        text_content = clean_html_tags(sec)
        if len(text_content) < 40 and not clean_codes:
            continue

        records.append({
            "category": target["category"],
            "main_title": target["title"],
            "section_title": sec_title,
            "source_url": target["web_url"],
            "text_content": text_content[:1800],
            "code_snippet": "\n\n// -----------------------------------------\n\n".join(clean_codes[:3]),
        })

    return records


def parse_markdown_go(md_content: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    clean_md = re.sub(r'^---[\s\S]*?---\s*', '', md_content)
    sections = re.split(r'\n(?=##\s+)', clean_md)
    records = []

    for sec in sections:
        header_match = re.match(r'^##\s+(.+)$', sec, re.MULTILINE)
        sec_title = header_match.group(1).strip() if header_match else "Overview"

        codes = re.findall(r'```(?:go|bash|sh)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        clean_codes = [c.strip() for c in codes if c.strip()]

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        text_only = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text_only)
        lines = [l.strip() for l in text_only.splitlines() if l.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) < 30 and not clean_codes:
            continue

        records.append({
            "category": target["category"],
            "main_title": target["title"],
            "section_title": sec_title,
            "source_url": target["web_url"],
            "text_content": clean_text[:1800],
            "code_snippet": "\n\n// -----------------------------------------\n\n".join(clean_codes[:3]),
        })

    return records


def main():
    print("=" * 75)
    print(" SCRAPING DOKUMENTASI RESMI GO (GOLANG 1.22 / 1.23 MODERN LANGUAGE & TOOLS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "golang_docs.pdf"
    csv_file = output_dir / "golang_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_content = fetch_url(target["url"])
        if not raw_content:
            continue

        if target["type"] == "markdown":
            sections = parse_markdown_go(raw_content, target)
        else:
            sections = parse_effective_go(raw_content, target)

        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"        {target['category']}: {len(sections)} section ({code_count} ada contoh kode Go)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"golang_{idx:03d}",
            "language": "Go",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n Mengekspor {len(formatted_records)} chunk Go ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Go (Golang 1.22/1.23 Up-to-Date)",
        language="Go",
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

    print(f"\n DATASET GO BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk Go")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode Go")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

