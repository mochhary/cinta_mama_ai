"""
Script Scraper Dokumentasi Resmi C# dari Microsoft (dotnet/docs)
Mencakup Sintaks Bahasa Pemrograman, Panduan Instalasi SDK, Konfigurasi Versi, dan CLI Setup.
"""

import csv
import re
import os
import urllib.request
from pathlib import Path
from typing import Dict

# URL dasar repositori resmi Microsoft dotnet/docs di GitHub Raw
RAW_BASE_URL = "https://raw.githubusercontent.com/dotnet/docs/main/docs"
LEARN_BASE_URL = "https://learn.microsoft.com/en-us/dotnet"

# Cache memori untuk file .cs snippet agar tidak perlu download berulang
SNIPPET_CACHE: Dict[str, str] = {}

# Daftar lengkap modul & artikel resmi C# (Sintaks, Instalasi, dan Konfigurasi)
DOC_TARGETS = [
    # ========================================================
    # 1. PANDUAN INSTALASI .NET SDK (C# Compiler & Runtime)
    # ========================================================
    {
        "category": "Installation & Setup",
        "path": "core/install/macos.md",
        "learn_path": "core/install/macos",
    },
    {
        "category": "Installation & Setup",
        "path": "core/install/windows.md",
        "learn_path": "core/install/windows",
    },
    {
        "category": "Installation & Setup",
        "path": "core/install/linux.md",
        "learn_path": "core/install/linux",
    },
    # ========================================================
    # 2. KONFIGURASI PROYEK & VERSI BAHASA C# (.csproj & CLI)
    # ========================================================
    {
        "category": "Configuration - Language Version",
        "path": "csharp/language-reference/configure-language-version.md",
        "learn_path": "csharp/language-reference/configure-language-version",
    },
    {
        "category": "Configuration - Compiler Options",
        "path": "csharp/language-reference/compiler-options/language.md",
        "learn_path": "csharp/language-reference/compiler-options/language",
    },
    {
        "category": "Configuration - CLI Tools",
        "path": "core/tools/dotnet-new.md",
        "learn_path": "core/tools/dotnet-new",
    },
    # ========================================================
    # 3. OVERVIEW & STRUKTUR PROGRAM C#
    # ========================================================
    {
        "category": "Language Overview",
        "path": "csharp/tour-of-csharp/overview.md",
        "learn_path": "csharp/tour-of-csharp/overview",
    },
    {
        "category": "Program Structure",
        "path": "csharp/fundamentals/program-structure/top-level-statements.md",
        "learn_path": "csharp/fundamentals/program-structure/top-level-statements",
    },
    # ========================================================
    # 4. SISTEM TIPE DATA, CLASS & RECORDS
    # ========================================================
    {
        "category": "Type System",
        "path": "csharp/fundamentals/types/index.md",
        "learn_path": "csharp/fundamentals/types/",
    },
    {
        "category": "Classes & Records",
        "path": "csharp/fundamentals/types/records.md",
        "learn_path": "csharp/fundamentals/types/records",
    },
    # ========================================================
    # 5. PATTERN MATCHING & FITUR FUNGSIONAL MODERN
    # ========================================================
    {
        "category": "Pattern Matching",
        "path": "csharp/fundamentals/patterns/pattern-matching.md",
        "learn_path": "csharp/fundamentals/patterns/pattern-matching",
    },
    {
        "category": "Pattern Matching",
        "path": "csharp/fundamentals/patterns/list-patterns.md",
        "learn_path": "csharp/fundamentals/patterns/list-patterns",
    },
    # ========================================================
    # 6. OBJECT-ORIENTED & EXCEPTION HANDLING
    # ========================================================
    {
        "category": "Object-Oriented",
        "path": "csharp/fundamentals/object-oriented/index.md",
        "learn_path": "csharp/fundamentals/object-oriented/",
    },
    {
        "category": "Exception Handling",
        "path": "csharp/fundamentals/exceptions/index.md",
        "learn_path": "csharp/fundamentals/exceptions/",
    },
    # ========================================================
    # 7. ASYNCHRONOUS PROGRAMMING (KONKURENSI BAWAAN)
    # ========================================================
    {
        "category": "Asynchronous Programming",
        "path": "csharp/asynchronous-programming/async-return-types.md",
        "learn_path": "csharp/asynchronous-programming/async-return-types",
    },
    {
        "category": "Asynchronous Programming",
        "path": "csharp/asynchronous-programming/task-asynchronous-programming-model.md",
        "learn_path": "csharp/asynchronous-programming/task-asynchronous-programming-model",
    },
    # ========================================================
    # 8. LINQ (LANGUAGE INTEGRATED QUERY)
    # ========================================================
    {
        "category": "LINQ",
        "path": "csharp/linq/get-started/introduction-to-linq-queries.md",
        "learn_path": "csharp/linq/get-started/introduction-to-linq-queries",
    },
    # ========================================================
    # 9. KEYWORDS & OPERATORS BAWAAN
    # ========================================================
    {
        "category": "Language Reference - Statements",
        "path": "csharp/language-reference/keywords/statement-keywords.md",
        "learn_path": "csharp/language-reference/keywords/statement-keywords",
    },
    {
        "category": "Language Reference - Parameters",
        "path": "csharp/language-reference/keywords/method-parameters.md",
        "learn_path": "csharp/language-reference/keywords/method-parameters",
    },
    {
        "category": "Language Reference - Operators",
        "path": "csharp/language-reference/operators/null-coalescing-operator.md",
        "learn_path": "csharp/language-reference/operators/null-coalescing-operator",
    },
    # ========================================================
    # 10. FITUR VERSI TERKINI C# (C# 12 & C# 13)
    # ========================================================
    {
        "category": "Whats New in C#",
        "path": "csharp/whats-new/csharp-12.md",
        "learn_path": "csharp/whats-new/csharp-12",
    },
    {
        "category": "Whats New in C#",
        "path": "csharp/whats-new/csharp-13.md",
        "learn_path": "csharp/whats-new/csharp-13",
    },
]


def fetch_file(rel_path: str) -> str:
    """Mengunduh konten teks dari GitHub raw Microsoft dotnet/docs."""
    clean_path = rel_path.lstrip("./").replace("//", "/")
    url = f"{RAW_BASE_URL}/{clean_path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (C# Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        return ""


def get_snippet_code(doc_dir: str, source_rel: str, tag_id: str) -> str:
    """Mengambil potongan kode C# spesifik dari file snippet .cs eksternal."""
    if source_rel.startswith("/"):
        full_rel_path = source_rel.lstrip("/")
    else:
        full_rel_path = f"{doc_dir}/{source_rel}" if doc_dir else source_rel

    full_rel_path = os.path.normpath(full_rel_path).replace("\\", "/")

    if full_rel_path not in SNIPPET_CACHE:
        SNIPPET_CACHE[full_rel_path] = fetch_file(full_rel_path)

    file_content = SNIPPET_CACHE[full_rel_path]
    if not file_content:
        return ""

    if tag_id:
        pattern = rf"//\s*<{re.escape(tag_id)}>(.*?)(?://\s*</{re.escape(tag_id)}>|$)"
        match = re.search(pattern, file_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    lines = file_content.splitlines()
    if len(lines) <= 40:
        return file_content.strip()

    return ""


def clean_markdown_text(text: str) -> str:
    """Membersihkan tag markdown non-tekstual agar optimal untuk RAG."""
    text = re.sub(r":::code\s+[\s\S]*?:::", "", text)
    text = re.sub(r":::zone\s+[\s\S]*?:::", "", text)
    text = re.sub(r">\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", "", text)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text.strip()


def parse_doc_sections(raw_md: str, category: str, doc_rel_path: str, learn_url: str):
    """
    Memecah artikel Markdown menjadi beberapa section/chunk yang rapi
    sekaligus mengekstrak kode C# dan CLI.
    """
    doc_dir = str(Path(doc_rel_path).parent).replace("\\", "/")
    if doc_dir == ".":
        doc_dir = ""

    title_match = re.search(r"^title:\s*(.+)$", raw_md, re.MULTILINE)
    main_title = title_match.group(1).strip() if title_match else "C# Documentation"

    # Hapus YAML frontmatter
    content = re.sub(r"^---[\s\S]*?---\s*", "", raw_md)

    # Pecah per sub-heading (## )
    sections = re.split(r"\n(?=##\s+)", content)
    records = []

    for idx, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue

        header_match = re.match(r"^##\s+(.+)$", sec, re.MULTILINE)
        section_name = header_match.group(1).strip() if header_match else "Overview"

        snippets = []

        # 1. Ekstrak kode blok (csharp, dotnetcli, xml/csproj, bash, dll.)
        inline_code_blocks = re.findall(
            r"```(?:csharp|cs|dotnetcli|xml|bash|sh)?\s*\n([\s\S]*?)```",
            sec,
            re.IGNORECASE,
        )
        for cb in inline_code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        # 2. Ekstrak kode dari direktif Microsoft :::code :::
        code_directives = re.findall(
            r':::code\s+[^:]*source="([^"]+)"(?:\s+id="([^"]+)")?[^:]*:::',
            sec,
            re.IGNORECASE,
        )
        for source_rel, tag_id in code_directives:
            resolved_code = get_snippet_code(doc_dir, source_rel, tag_id)
            if resolved_code:
                snippets.append(resolved_code)

        combined_code = "\n\n// -----------------------------------------\n\n".join(snippets)

        text_only = re.sub(r"```[\s\S]*?```", "", sec)
        cleaned_text = clean_markdown_text(text_only)

        if len(cleaned_text) < 35 and not combined_code:
            continue

        records.append({
            "category": category,
            "main_title": main_title,
            "section_title": section_name,
            "source_url": learn_url,
            "text_content": cleaned_text,
            "code_snippet": combined_code,
        })

    return records


def main():
    print("=" * 70)
    print("🚀 SCRAPING DOKUMENTASI RESMI C# (SINTAKS, INSTALASI & KONFIGURASI)")
    print("=" * 70)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    csv_file = output_dir / "csharp_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Memproses: {target['path']}...")
        raw_md = fetch_file(target["path"])
        if not raw_md:
            print(f"       [!] Skip: File tidak ditemukan")
            continue

        learn_url = f"{LEARN_BASE_URL}/{target['learn_path']}"
        sections = parse_doc_sections(raw_md, target["category"], target["path"], learn_url)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode/CLI)")

    print("\n💾 Menyimpan dataset lengkap ke CSV...")
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

        for idx, rec in enumerate(all_records, 1):
            writer.writerow({
                "doc_id": f"csharp_{idx:03d}",
                "language": "C#",
                "category": rec["category"],
                "main_title": rec["main_title"],
                "section_title": rec["section_title"],
                "source_url": rec["source_url"],
                "text_content": rec["text_content"],
                "code_snippet": rec["code_snippet"],
            })

    print(f"\n🎉 DATASET C# LENGKAP SELESAI DIBUAT!")
    print(f"📁 Lokasi File : {csv_file.resolve()}")
    print(f"📊 Total Baris : {len(all_records)} dokumen/chunk C#")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode  : {code_total} section memiliki snippet kode C# / perintah CLI")
    print(f"📦 Ukuran File : {os.path.getsize(csv_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
