"""
Script Scraper Dokumentasi Resmi Rust (rust-lang/book - The Rust Programming Language Book 2021/2024 Edition)
Mencakup Cargo & Toolchain, Ownership & Memory Safety, References & Borrowing, Structs, Enums & Pattern Matching,
Error Handling (Result & ?), Generics & Traits, Lifetimes, Closures & Iterators, Smart Pointers (Box, Rc, Arc), serta Concurrency.
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

RUST_RAW_BASE = "https://raw.githubusercontent.com/rust-lang/book/main/src"
RUST_WEB_BASE = "https://doc.rust-lang.org/book"

DOC_TARGETS = [
    {
        "category": "Installation & Cargo Tooling",
        "path": "ch01-01-installation.md",
        "web_url": f"{RUST_WEB_BASE}/ch01-01-installation.html",
        "title": "Installation and rustup Toolchain Setup",
    },
    {
        "category": "Cargo Build System",
        "path": "ch01-03-hello-cargo.md",
        "web_url": f"{RUST_WEB_BASE}/ch01-03-hello-cargo.html",
        "title": "Hello, Cargo! (Cargo.toml, cargo build, cargo run, cargo check)",
    },
    {
        "category": "Variables, Mutability & Types",
        "path": "ch03-01-variables-and-mutability.md",
        "web_url": f"{RUST_WEB_BASE}/ch03-01-variables-and-mutability.html",
        "title": "Variables, Mutability, Shadowing & Constants",
    },
    {
        "category": "Control Flow & Loops",
        "path": "ch03-05-control-flow.md",
        "web_url": f"{RUST_WEB_BASE}/ch03-05-control-flow.html",
        "title": "Control Flow (if expressions, loop, while, for in ranges)",
    },
    {
        "category": "Ownership & Move Semantics",
        "path": "ch04-01-what-is-ownership.md",
        "web_url": f"{RUST_WEB_BASE}/ch04-01-what-is-ownership.html",
        "title": "What is Ownership? (Stack vs Heap, Memory Allocation, Moves, Clones)",
    },
    {
        "category": "References, Borrowing & Slices",
        "path": "ch04-02-references-and-borrowing.md",
        "web_url": f"{RUST_WEB_BASE}/ch04-02-references-and-borrowing.html",
        "title": "References and Borrowing (Mutable References, Dangling References Rules)",
    },
    {
        "category": "Structs & Method Syntax",
        "path": "ch05-01-defining-structs.md",
        "web_url": f"{RUST_WEB_BASE}/ch05-01-defining-structs.html",
        "title": "Defining and Instantiating Structs (Tuple Structs, impl blocks)",
    },
    {
        "category": "Enums & Pattern Matching",
        "path": "ch06-02-match.md",
        "web_url": f"{RUST_WEB_BASE}/ch06-02-match.html",
        "title": "The match Control Flow Construct (Option<T>, Exhaustive Matching, if-let, let-else)",
    },
    {
        "category": "Error Handling (Result & ? Operator)",
        "path": "ch09-02-recoverable-errors-with-result.md",
        "web_url": f"{RUST_WEB_BASE}/ch09-02-recoverable-errors-with-result.html",
        "title": "Recoverable Errors with Result<T, E> and Propagating Errors with ?",
    },
    {
        "category": "Generics & Traits",
        "path": "ch10-02-traits.md",
        "web_url": f"{RUST_WEB_BASE}/ch10-02-traits.html",
        "title": "Traits: Defining Shared Behavior (impl Trait, Trait Bounds, where clauses)",
    },
    {
        "category": "Lifetimes Validation",
        "path": "ch10-03-lifetime-syntax.md",
        "web_url": f"{RUST_WEB_BASE}/ch10-03-lifetime-syntax.html",
        "title": "Validating References with Lifetimes ('a Lifetime Annotations, Borrow Checker)",
    },
    {
        "category": "Smart Pointers (Box, Rc, Arc)",
        "path": "ch15-01-box.md",
        "web_url": f"{RUST_WEB_BASE}/ch15-01-box.html",
        "title": "Using Box<T> to Point to Data on the Heap (Deref and Drop Traits)",
    },
    {
        "category": "Fearless Concurrency (Threads & Channels)",
        "path": "ch16-01-threads.md",
        "web_url": f"{RUST_WEB_BASE}/ch16-01-threads.html",
        "title": "Fearless Concurrency (spawn threads, move closures, message passing)",
    },
]


def fetch_rust_file(path: str) -> str:
    url = f"{RUST_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Rust Book Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_rust_markdown(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_rust_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    # Pecah per sub-heading (## atau ###)
    sections = re.split(r'\n(?=#{2,3}\s+)', raw_md)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r'^#{2,3}\s+(.+)$', sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        snippets = []
        code_blocks = re.findall(r'```(?:rust|bash|sh|toml)?(?:,[^\n]*)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            # Hapus tanda pagar rustdoc hiding lines: # ...
            clean_lines = [l for l in cb.splitlines() if not l.strip().startswith('# ')]
            cb_clean = "\n".join(clean_lines).strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_rust_markdown(text_only)

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
    print("🦀 SCRAPING DOKUMENTASI RESMI RUST (THE RUST BOOK - 2021/2024 EDITION UP-TO-DATE)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "rust_docs.pdf"
    csv_file = output_dir / "rust_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_rust_file(target["path"])
        if not raw_md:
            continue

        sections = parse_rust_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode Rust)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"rust_{idx:03d}",
            "language": "Rust",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk Rust ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Rust (2021/2024 Edition Up-to-Date)",
        language="Rust",
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

    print(f"\n🎉 DATASET RUST BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk Rust")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode Rust")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
