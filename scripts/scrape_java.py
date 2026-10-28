"""
Script Scraper Dokumentasi Resmi Java dari Oracle dev.java, OpenJDK (Project Amber & JEPs), dan Adoptium Temurin.
Mencakup Sintaks Bahasa Pemrograman, Panduan Instalasi JDK (macOS, Windows, Linux), Tooling (javac, java, single-file runner),
dan Fitur Modern Java (Java 17 & 21 LTS: Records, Sealed Classes, Pattern Matching, Virtual Threads, Sequenced Collections).
"""

import csv
import html
import os
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Any

try:
    from scripts.pdf_exporter import export_records_to_pdf
except ImportError:
    from pdf_exporter import export_records_to_pdf

# Target dokumen resmi Java (Sintaks, Tooling, Instalasi JDK, dan Fitur Versi Modern)
DOC_TARGETS = [
    # ========================================================
    # 1. PANDUAN INSTALASI JDK (macOS, Windows, Linux) - Adoptium Eclipse Temurin
    # ========================================================
    {
        "category": "Installation & Setup - macOS",
        "url": "https://raw.githubusercontent.com/adoptium/adoptium.net/main/content/asciidoc-pages/installation/macOS/index.adoc",
        "canonical_url": "https://adoptium.net/installation/macOS/",
        "format": "adoc",
    },
    {
        "category": "Installation & Setup - Windows",
        "url": "https://raw.githubusercontent.com/adoptium/adoptium.net/main/content/asciidoc-pages/installation/windows/index.adoc",
        "canonical_url": "https://adoptium.net/installation/windows/",
        "format": "adoc",
    },
    {
        "category": "Installation & Setup - Linux",
        "url": "https://raw.githubusercontent.com/adoptium/adoptium.net/main/content/asciidoc-pages/installation/linux/index.adoc",
        "canonical_url": "https://adoptium.net/installation/linux/",
        "format": "adoc",
    },
    # ========================================================
    # 2. GETTING STARTED & TOOLING (javac, java, single-file runner) - Oracle dev.java
    # ========================================================
    {
        "category": "Getting Started & Tooling",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/01_your-first-java-app/01_getting-started-with-java.md",
        "canonical_url": "https://dev.java/learn/getting-started/",
        "format": "markdown",
    },
    # ========================================================
    # 3. DASAR BAHASA: VARIABEL, PRIMITIF & ARRAY - Oracle dev.java
    # ========================================================
    {
        "category": "Language Basics - Variables",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/02_basics/01_creating-variables.md",
        "canonical_url": "https://dev.java/learn/variables/",
        "format": "markdown",
    },
    {
        "category": "Language Basics - Primitives",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/02_basics/02_creating-primitive-types.md",
        "canonical_url": "https://dev.java/learn/primitives/",
        "format": "markdown",
    },
    {
        "category": "Language Basics - Arrays",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/02_basics/03_creating-arrays.md",
        "canonical_url": "https://dev.java/learn/arrays/",
        "format": "markdown",
    },
    # ========================================================
    # 4. MODERN SYNTAX: VAR & TEXT BLOCKS - OpenJDK Project Amber
    # ========================================================
    {
        "category": "Modern Features - Type Inference (var)",
        "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/guides/lvti-style-guide.md",
        "canonical_url": "https://openjdk.org/projects/amber/guides/lvti-style-guide",
        "format": "markdown",
    },
    {
        "category": "Modern Features - Text Blocks",
        "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/guides/text-blocks-guide.md",
        "canonical_url": "https://openjdk.org/projects/amber/guides/text-blocks-guide",
        "format": "markdown",
    },
    # ========================================================
    # 5. OBJECT-ORIENTED: ENUMS - Oracle dev.java
    # ========================================================
    {
        "category": "Object-Oriented - Enums",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/04_classes_objects/01_enums.md",
        "canonical_url": "https://dev.java/learn/enums/",
        "format": "markdown",
    },
    # ========================================================
    # 6. MODERN DATA CARRIERS & TYPES (Java 16/17 LTS) - OpenJDK JEPs
    # ========================================================
    {
        "category": "Modern OOP - Records",
        "url": "https://openjdk.org/jeps/395",
        "canonical_url": "https://openjdk.org/jeps/395",
        "format": "jep_html",
    },
    {
        "category": "Modern OOP - Sealed Classes",
        "url": "https://openjdk.org/jeps/409",
        "canonical_url": "https://openjdk.org/jeps/409",
        "format": "jep_html",
    },
    # ========================================================
    # 7. MODERN PATTERN MATCHING (Java 17, 21 LTS, 22) - OpenJDK
    # ========================================================
    {
        "category": "Pattern Matching - Switch Patterns",
        "url": "https://openjdk.org/jeps/441",
        "canonical_url": "https://openjdk.org/jeps/441",
        "format": "jep_html",
    },
    {
        "category": "Pattern Matching - Record Patterns",
        "url": "https://openjdk.org/jeps/440",
        "canonical_url": "https://openjdk.org/jeps/440",
        "format": "jep_html",
    },
    {
        "category": "Pattern Matching - Unnamed Patterns",
        "url": "https://openjdk.org/jeps/456",
        "canonical_url": "https://openjdk.org/jeps/456",
        "format": "jep_html",
    },
    {
        "category": "Pattern Matching - Exhaustiveness",
        "url": "https://raw.githubusercontent.com/openjdk/amber-docs/master/site/guides/exhaustiveness-guide.md",
        "canonical_url": "https://openjdk.org/projects/amber/guides/exhaustiveness-guide",
        "format": "markdown",
    },
    # ========================================================
    # 8. VIRTUAL THREADS & CONCURRENCY (Java 21 LTS) - dev.java & OpenJDK
    # ========================================================
    {
        "category": "Concurrency - Virtual Threads Tutorial",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/02_new-features/00_virtual-threads.md",
        "canonical_url": "https://dev.java/learn/new-features/virtual-threads/",
        "format": "markdown",
    },
    {
        "category": "Concurrency - Virtual Threads Spec",
        "url": "https://openjdk.org/jeps/444",
        "canonical_url": "https://openjdk.org/jeps/444",
        "format": "jep_html",
    },
    # ========================================================
    # 9. FUNCTIONAL PROGRAMMING & STREAMS API - Oracle dev.java
    # ========================================================
    {
        "category": "Functional Programming - Loops to Streams",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/03_refactoring_to_functional_style/01_converting_simple_loops.md",
        "canonical_url": "https://dev.java/learn/functional-loops/",
        "format": "markdown",
    },
    {
        "category": "Functional Programming - Filtering Streams",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/03_refactoring_to_functional_style/03_converting_foreach_with_if.md",
        "canonical_url": "https://dev.java/learn/functional-filtering/",
        "format": "markdown",
    },
    {
        "category": "Functional Programming - Map & Transformations",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/03_refactoring_to_functional_style/04_converting_foreach_with_transformation.md",
        "canonical_url": "https://dev.java/learn/functional-transforming/",
        "format": "markdown",
    },
    {
        "category": "Functional Programming - Stream Pipelines",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/03_getting-to-know-the-language/03_refactoring_to_functional_style/05_converting_to_streams.md",
        "canonical_url": "https://dev.java/learn/thinking-in-streams/",
        "format": "markdown",
    },
    {
        "category": "Collections - Sequenced Collections",
        "url": "https://openjdk.org/jeps/431",
        "canonical_url": "https://openjdk.org/jeps/431",
        "format": "jep_html",
    },
    # ========================================================
    # 10. MODERN I/O (NIO.2) - Oracle dev.java
    # ========================================================
    {
        "category": "Standard Library - Modern I/O",
        "url": "https://raw.githubusercontent.com/java/devjava-content/main/app/pages/learn/01_tutorial/04_mastering-the-api/02_modern_io/01_modern_io.md",
        "canonical_url": "https://dev.java/learn/modern-io/",
        "format": "markdown",
    },
]


def fetch_url_content(url: str) -> str:
    """Mengunduh konten teks dari URL dengan timeout."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (CintaMamaAI Java Scraper/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


# ========================================================
# 1. PARSER UNTUK MARKDOWN (dev.java & Project Amber)
# ========================================================
def parse_markdown_doc(raw_md: str, source_url: str, category: str) -> List[Dict[str, Any]]:
    # Ekstrak judul utama dari YAML frontmatter atau h1
    title_match = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", raw_md, re.MULTILINE)
    if not title_match:
        title_match = re.search(r"^#\s+(.+)$", raw_md, re.MULTILINE)
    main_title = title_match.group(1).strip() if title_match else "Java Documentation"

    # Bersihkan YAML frontmatter
    content = re.sub(r"^---[\s\S]*?---\s*", "", raw_md)

    # Pecah per sub-heading (## )
    sections = re.split(r"\n(?=##\s+)", content)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        h_match = re.match(r"^##\s+(.+)$", sec, re.MULTILINE)
        section_title = h_match.group(1).strip() if h_match else "Overview"

        # Bersihkan anchor HTML dari dev.java seperti <a id="foo">&nbsp;</a>
        sec_clean = re.sub(r"<a[^>]*>&nbsp;</a>", "", sec)
        sec_clean = re.sub(r"<a[^>]*>.*?</a>", "", sec_clean)

        # Ekstrak blok kode (java, bash, sh, text, xml)
        code_blocks = re.findall(
            r"```[a-z]*\s*\n([\s\S]*?)```", sec_clean, re.IGNORECASE
        )
        snippets = [cb.strip() for cb in code_blocks if cb.strip()]
        combined_code = "\n\n// -----------------------------------------\n\n".join(snippets)

        # Hapus blok kode dari teks deskriptif
        text_only = re.sub(r"```[\s\S]*?```", "", sec_clean)
        text_only = re.sub(r"^##\s+.+$", "", text_only, flags=re.MULTILINE)
        text_only = re.sub(r">\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", "", text_only)
        text_only = re.sub(r"^\s*>\s?", "", text_only, flags=re.MULTILINE)
        text_only = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text_only)
        text_clean = "\n".join([line.strip() for line in text_only.splitlines() if line.strip()])

        if len(text_clean) > 30 or combined_code:
            records.append({
                "category": category,
                "main_title": main_title,
                "section_title": section_title,
                "source_url": source_url,
                "text_content": text_clean,
                "code_snippet": combined_code,
            })

    return records


# ========================================================
# 2. PARSER UNTUK ASCIIDOC (Adoptium Temurin Installation)
# ========================================================
def parse_adoc_doc(raw_adoc: str, source_url: str, category: str) -> List[Dict[str, Any]]:
    title_match = re.search(r"^=\s+(.+)$", raw_adoc, re.MULTILINE)
    main_title = title_match.group(1).strip() if title_match else "Eclipse Temurin Installation"

    # Pecah per == atau ===
    chunks = re.split(r"\n(?====?\s+)", raw_adoc)
    records = []

    for c in chunks:
        c = c.strip()
        if not c:
            continue

        h_match = re.match(r"^===?\s+(.+)$", c, re.MULTILINE)
        section_title = h_match.group(1).strip() if h_match else "Overview"

        # Ekstrak kode blok [source, bash] \n ---- \n ... \n ----
        code_blocks = re.findall(r"\[source[^\]]*\]\s*\n----\n([\s\S]*?)----", c)
        if not code_blocks:
            code_blocks = re.findall(r"----\n([\s\S]*?)----", c)

        snippets = [cb.strip() for cb in code_blocks if cb.strip()]
        combined_code = "\n\n# -----------------------------------------\n\n".join(snippets)

        # Bersihkan teks
        text_only = re.sub(r"\[source[^\]]*\]\s*\n----\n[\s\S]*?----", "", c)
        text_only = re.sub(r"----\n[\s\S]*?----", "", text_only)
        text_only = re.sub(r"^===?\s+.+$", "", text_only, flags=re.MULTILINE)
        text_only = re.sub(r"\[(NOTE|IMPORTANT|TIP|WARNING)\]\s*====[\s\S]*?====", "", text_only)
        text_only = re.sub(r"link:[^\[]+\[([^\]]+)\]", r"\1", text_only)
        text_only = re.sub(r":[^:]+:\s*.*$", "", text_only, flags=re.MULTILINE)
        text_clean = "\n".join([line.strip() for line in text_only.splitlines() if line.strip()])

        if len(text_clean) > 25 or combined_code:
            records.append({
                "category": category,
                "main_title": main_title,
                "section_title": section_title,
                "source_url": source_url,
                "text_content": text_clean,
                "code_snippet": combined_code,
            })

    return records


# ========================================================
# 3. PARSER UNTUK OPENJDK JEPS (HTML)
# ========================================================
class OpenJDKJEPParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections: List[Dict[str, Any]] = []
        self.page_title = ""
        self.current_title = "Overview & Metadata"
        self.current_text: List[str] = []
        self.current_code: List[str] = []

        self.in_title = False
        self.in_header = False
        self.header_buf = ""
        self.in_pre = False
        self.pre_buf = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag in ("h2", "h3"):
            self.in_header = True
            self.header_buf = ""
        elif tag == "pre":
            self.in_pre = True
            self.pre_buf = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("h2", "h3"):
            self.in_header = False
            header_clean = self.header_buf.strip()
            self._flush_section()
            if header_clean:
                self.current_title = header_clean
        elif tag == "pre":
            self.in_pre = False
            c = html.unescape(self.pre_buf.strip())
            if c:
                self.current_code.append(c)

    def handle_data(self, data):
        if self.in_title:
            self.page_title += data
        elif self.in_header:
            self.header_buf += data
        elif self.in_pre:
            self.pre_buf += data
        else:
            cleaned = data.strip()
            if cleaned:
                self.current_text.append(cleaned)

    def _flush_section(self):
        t = "\n".join(self.current_text).strip()
        c = "\n\n// -----------------------------------------\n\n".join(self.current_code).strip()
        skip_titles = ("Table of contents", "References", "Navigation")
        if (len(t) > 30 or c) and self.current_title not in skip_titles:
            self.sections.append({
                "section_title": self.current_title,
                "text_content": t,
                "code_snippet": c,
            })
        self.current_text = []
        self.current_code = []

    def finish(self):
        self._flush_section()


def parse_jep_html_doc(raw_html: str, source_url: str, category: str) -> List[Dict[str, Any]]:
    parser = OpenJDKJEPParser()
    parser.feed(raw_html)
    parser.finish()

    main_title = parser.page_title.strip() or f"OpenJDK JEP ({source_url.split('/')[-1]})"
    main_title = html.unescape(main_title)

    results = []
    for s in parser.sections:
        results.append({
            "category": category,
            "main_title": main_title,
            "section_title": s["section_title"],
            "source_url": source_url,
            "text_content": s["text_content"],
            "code_snippet": s["code_snippet"],
        })
    return results


# ========================================================
# 4. MAIN WORKFLOW
# ========================================================
def main():
    print("=" * 75)
    print(" SCRAPING DOKUMENTASI RESMI JAVA (SINTAKS, INSTALASI, TOOLING & JEPs)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "java_docs.pdf"
    csv_file = output_dir / "java_docs.csv"

    all_records: List[Dict[str, Any]] = []
    total_targets = len(DOC_TARGETS)

    for idx, target in enumerate(DOC_TARGETS, 1):
        cat = target["category"]
        url = target["url"]
        fmt = target["format"]
        canonical = target["canonical_url"]

        print(f"[{idx:02d}/{total_targets}] [{fmt.upper()}] Mengunduh: {cat}...")
        raw_content = fetch_url_content(url)
        if not raw_content:
            print(f"       [!] Skip: Gagal mengambil data")
            continue

        if fmt == "markdown":
            parsed = parse_markdown_doc(raw_content, canonical, cat)
        elif fmt == "adoc":
            parsed = parse_adoc_doc(raw_content, canonical, cat)
        elif fmt == "jep_html":
            parsed = parse_jep_html_doc(raw_content, canonical, cat)
        else:
            parsed = []

        all_records.extend(parsed)
        code_count = sum(1 for p in parsed if p["code_snippet"])
        print(f"        {len(parsed)} section/chunk ({code_count} ada kode/CLI)")

    formatted_records = []
    for i, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"java_{i:03d}",
            "language": "Java",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print("\n Menyimpan dataset lengkap Java ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks Java",
        language="Java",
    )

    # Simpan juga backup CSV
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

    print(f"\n DATASET JAVA LENGKAP SELESAI DIBUAT DALAM FORMAT PDF!")
    print(f" Lokasi File PDF : {pdf_file.resolve()}")
    print(f" Total Dokumen   : {len(all_records)} chunk/section Java")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f" Total Kode      : {code_total} section memiliki contoh kode Java / perintah CLI")
    print(f" Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()
