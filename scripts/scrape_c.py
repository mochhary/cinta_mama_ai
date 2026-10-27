"""
Script Scraper Dokumentasi Resmi Bahasa C (MicrosoftDocs/cpp-docs & Modern C17 / C23 Standards)
Mencakup C Standards (/std:c11, /std:c17, -std=c23), Fundamental Types, Pointers & Memory Addressing,
Structures & Designated Initializers, Unions, Functions & Variadic Functions, Control Flow (if, switch, for),
Dynamic Memory Management (malloc, free, realloc), Generic Selection (_Generic C11/C17/C23), serta Fitur Modern C23 (nullptr, auto, constexpr).
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

CPP_DOCS_RAW = "https://raw.githubusercontent.com/MicrosoftDocs/cpp-docs/main/docs"
WEB_BASE = "https://learn.microsoft.com/en-us/cpp/c-language"

DOC_TARGETS = [
    {
        "category": "C Standards & Conformance (C11, C17, C23)",
        "url": f"{CPP_DOCS_RAW}/overview/install-c17-support.md",
        "web_url": "https://learn.microsoft.com/en-us/cpp/overview/install-c17-support",
        "title": "C Language Standards Conformance (C11, C17, and C23 Compiler Flags /std:c11 /std:c17 -std=c23)",
    },
    {
        "category": "Data Types & Type Specifiers",
        "url": f"{CPP_DOCS_RAW}/c-language/c-type-specifiers.md",
        "web_url": f"{WEB_BASE}/c-type-specifiers",
        "title": "C Type Specifiers & Data Types (int, float, double, char, _Bool, <stdint.h> fixed-width integers)",
    },
    {
        "category": "Pointers & Memory Addressing",
        "url": f"{CPP_DOCS_RAW}/c-language/pointer-declarations.md",
        "web_url": f"{WEB_BASE}/pointer-declarations",
        "title": "Pointer Declarations and Indirection (Pointer arithmetic, NULL, void*, double pointers **)",
    },
    {
        "category": "Structures & Designated Initializers",
        "url": f"{CPP_DOCS_RAW}/c-language/structure-declarations.md",
        "web_url": f"{WEB_BASE}/structure-declarations",
        "title": "Structure Declarations (struct, typedef struct, Member access, Designated Initializers .x = 1)",
    },
    {
        "category": "Unions & Bit Fields",
        "url": f"{CPP_DOCS_RAW}/c-language/union-declarations.md",
        "web_url": f"{WEB_BASE}/union-declarations",
        "title": "Union Declarations (Memory sharing, Tagged unions, Bit fields)",
    },
    {
        "category": "Functions & Variadic Arguments",
        "url": f"{CPP_DOCS_RAW}/c-language/c-function-definitions.md",
        "web_url": f"{WEB_BASE}/c-function-definitions",
        "title": "Function Definitions (Parameters, static functions, inline, Variadic arguments va_list)",
    },
    {
        "category": "Control Flow - Selection (if & switch)",
        "url": f"{CPP_DOCS_RAW}/c-language/switch-statement-c.md",
        "web_url": f"{WEB_BASE}/switch-statement-c",
        "title": "Selection Statements (switch, case, break, fallthrough, if-else)",
    },
    {
        "category": "Control Flow - Iteration (for & while)",
        "url": f"{CPP_DOCS_RAW}/c-language/for-statement-c.md",
        "web_url": f"{WEB_BASE}/for-statement-c",
        "title": "Iteration Statements (for loops with C99/C11 loop variable declarations, while, do-while)",
    },
    {
        "category": "Modern Features - C11/C17/C23 Generic Selection",
        "url": f"{CPP_DOCS_RAW}/c-language/generic-selection.md",
        "web_url": f"{WEB_BASE}/generic-selection",
        "title": "Generic Selection (_Generic keyword for type-directed macro dispatch and polymorphism)",
    },
    {
        "category": "Dynamic Memory Allocation (Heap Management)",
        "url": f"{CPP_DOCS_RAW}/c-runtime-library/reference/malloc.md",
        "web_url": "https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/malloc",
        "title": "Dynamic Memory Allocation (malloc, free, calloc, realloc, Heap safety & Memory Leaks)",
    },
]


def fetch_url_content(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (C Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_markdown_for_rag(text: str) -> str:
    text = re.sub(r'<!--[\s\S]*?-->', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_c_sections(raw_md: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
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
        code_blocks = re.findall(r'```(?:c|cpp|cmd|bash|sh)?\s*\n([\s\S]*?)```', sec, re.IGNORECASE)
        for cb in code_blocks:
            cb_clean = cb.strip()
            if cb_clean:
                snippets.append(cb_clean)

        text_only = re.sub(r'```[\s\S]*?```', '', sec)
        cleaned_text = clean_markdown_for_rag(text_only)

        if len(cleaned_text) < 30 and not snippets:
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


def get_c23_modern_features_records() -> List[Dict[str, Any]]:
    """Menambahkan ringkasan resmi fitur modern standar C23 (ISO/IEC 9899:2024)."""
    return [
        {
            "category": "Modern Features - C23 Standard (ISO C23)",
            "main_title": "ISO C23 Modern Language Enhancements (nullptr, auto, constexpr, bool)",
            "section_title": "C23 nullptr, auto Type Inference, and constexpr",
            "source_url": "https://en.cppreference.com/w/c/23",
            "text_content": (
                "C23 adalah revisi standar bahasa C terbaru (ISO/IEC 9899:2024). "
                "Perubahan utama meliputi:\n"
                "1. nullptr: C23 menambahkan konstanta 'nullptr' dari tipe 'nullptr_t' untuk menggantikan makro NULL yang ambigu.\n"
                "2. auto Type Inference: Kata kunci 'auto' kini dapat digunakan untuk inferensi tipe otomatis variabel seperti di C++: auto x = 42;\n"
                "3. constexpr Object Specifier: Mendukung 'constexpr' untuk variabel objek waktu kompilasi sejati.\n"
                "4. bool, true, false menjadi keyword resmi C23 tanpa memerlukan header <stdbool.h>.\n"
                "5. Standard Attributes: Sintaks atribut standar ganda [[nodiscard]], [[deprecated]], [[maybe_unused]], [[fallthrough]].\n"
                "6. #embed Preprocessor: Perintah preprocessor baru untuk menyematkan data biner mentah secara langsung saat kompilasi."
            ),
            "code_snippet": (
                "// Contoh Fitur Modern C23\n"
                "#include <stdio.h>\n\n"
                "// C23 Attributes & bool tanpa stdbool.h\n"
                "[[nodiscard]] bool check_pointer(void* ptr) {\n"
                "    return ptr != nullptr; // C23 nullptr\n"
                "}\n\n"
                "int main(void) {\n"
                "    auto count = 100; // C23 auto type inference\n"
                "    constexpr double PI = 3.1415926535; // C23 constexpr\n\n"
                "    int* p = nullptr;\n"
                "    if (!check_pointer(p)) {\n"
                "        printf(\"Pointer is null\\n\");\n"
                "    }\n"
                "    return 0;\n"
                "}"
            ),
        }
    ]


def main():
    print("=" * 75)
    print("⚡ SCRAPING DOKUMENTASI RESMI BAHASA C (C11, C17 & C23 MODERN STANDARDS)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "c_docs.pdf"
    csv_file = output_dir / "c_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_md = fetch_url_content(target["url"])
        if not raw_md:
            continue

        sections = parse_c_sections(raw_md, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh kode C)")

    # Tambahkan section fitur modern C23
    c23_records = get_c23_modern_features_records()
    all_records.extend(c23_records)
    print(f"       ✓ Modern Features - C23: Ditambahkan ringkasan standar C23 (nullptr, auto, constexpr)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"c_{idx:03d}",
            "language": "C",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk Bahasa C ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Bahasa C (C17 / C23 Up-to-Date)",
        language="C",
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

    print(f"\n🎉 DATASET BAHASA C BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk Bahasa C")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh kode C")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

