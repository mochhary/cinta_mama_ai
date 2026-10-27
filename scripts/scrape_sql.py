"""
Script Scraper Dokumentasi Resmi SQL (postgres/postgres SGML docs - PostgreSQL 16 / 17 Up-to-Date)
Mencakup DDL (Tables, Constraints, Partitioning), DML (Insert, Update, Delete, MERGE syntax),
Queries (Joins, Aggregations, Window Functions, CTE WITH Queries), Modern JSON & JSONB (JSON_TABLE), serta Indexes (B-tree, GIN, BRIN).
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

POSTGRES_RAW_BASE = "https://raw.githubusercontent.com/postgres/postgres/master/doc/src/sgml"
POSTGRES_WEB_BASE = "https://www.postgresql.org/docs/current"

DOC_TARGETS = [
    {
        "category": "Data Definition (DDL) & Constraints",
        "path": "ddl.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/ddl.html",
        "title": "Data Definition Language (CREATE TABLE, Primary/Foreign Keys, Check, Partitioning)",
    },
    {
        "category": "Data Manipulation (DML) & MERGE",
        "path": "dml.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/dml.html",
        "title": "Data Manipulation Language (INSERT, UPDATE, DELETE, MERGE, Returning Data)",
    },
    {
        "category": "Queries (SELECT, Joins, Aggregation)",
        "path": "queries.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/queries.html",
        "title": "Queries (Table Expressions, INNER/LEFT/FULL JOINs, GROUP BY, HAVING, ORDER BY, LIMIT)",
    },
    {
        "category": "Advanced Queries - CTEs & Window Functions",
        "path": "queries.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/queries-with.html",
        "title": "Advanced SQL Queries (WITH Queries / Common Table Expressions, WINDOW OVER Functions)",
    },
    {
        "category": "Modern Data Types - JSON & JSONB",
        "path": "json.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/datatype-json.html",
        "title": "JSON Types and JSONB Operators (JSON indexing, JSONPath, JSON_TABLE in PG 16/17)",
    },
    {
        "category": "Indexes & Performance Optimization",
        "path": "indices.sgml",
        "web_url": f"{POSTGRES_WEB_BASE}/indexes.html",
        "title": "Indexes and Performance (B-tree, Hash, GiST, SP-GiST, GIN, BRIN, Partial Indexes)",
    },
]


def fetch_pg_sgml(path: str) -> str:
    url = f"{POSTGRES_RAW_BASE}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (PostgreSQL Docs Scraper)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.read().decode("utf-8")
    except Exception as e:
        print(f"       [!] Gagal mengunduh {url}: {e}")
        return ""


def clean_sgml_text(sgml_chunk: str) -> str:
    text = re.sub(r'<programlisting[\s\S]*?</programlisting>', '', sgml_chunk)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)


def parse_pg_sections(raw_sgml: str, target: Dict[str, str]) -> List[Dict[str, Any]]:
    main_title = target["title"]
    category = target["category"]
    learn_url = target["web_url"]

    sections = re.split(r'(?=<sect[123]|<section)', raw_sgml)
    records = []

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        title_match = re.search(r'<title>(.*?)</title>', sec, re.DOTALL)
        sec_title = clean_sgml_text(title_match.group(1)) if title_match else "Overview"

        # Ekstrak query SQL dalam programlisting
        code_blocks = re.findall(r'<programlisting[^>]*>([\s\S]*?)</programlisting>', sec)
        clean_codes = []
        for cb in code_blocks:
            c_clean = re.sub(r'<[^>]+>', '', cb).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').strip()
            if c_clean:
                clean_codes.append(c_clean)

        text_content = clean_sgml_text(sec)
        if len(text_content) < 35 and not clean_codes:
            continue

        records.append({
            "category": category,
            "main_title": main_title,
            "section_title": sec_title,
            "source_url": learn_url,
            "text_content": text_content[:1800],
            "code_snippet": "\n\n-- -----------------------------------------\n\n".join(clean_codes[:3]),
        })

    return records


def main():
    print("=" * 75)
    print("🐘 SCRAPING DOKUMENTASI RESMI SQL (POSTGRESQL 16 / 17 MODERN SQL & JSON)")
    print("=" * 75)

    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    pdf_file = output_dir / "sql_docs.pdf"
    csv_file = output_dir / "sql_docs.csv"

    all_records = []
    total_targets = len(DOC_TARGETS)

    for i, target in enumerate(DOC_TARGETS, 1):
        print(f"[{i:02d}/{total_targets}] Mengunduh: {target['title']}...")
        raw_sgml = fetch_pg_sgml(target["path"])
        if not raw_sgml:
            continue

        sections = parse_pg_sections(raw_sgml, target)
        all_records.extend(sections)
        code_count = sum(1 for s in sections if s["code_snippet"])
        print(f"       ✓ {target['category']}: {len(sections)} section ({code_count} ada contoh query SQL)")

    formatted_records = []
    for idx, rec in enumerate(all_records, 1):
        formatted_records.append({
            "doc_id": f"sql_{idx:03d}",
            "language": "SQL",
            "category": rec["category"],
            "main_title": rec["main_title"],
            "section_title": rec["section_title"],
            "source_url": rec["source_url"],
            "text_content": rec["text_content"],
            "code_snippet": rec["code_snippet"],
        })

    print(f"\n📄 Mengekspor {len(formatted_records)} chunk SQL ke PDF...")
    export_records_to_pdf(
        formatted_records,
        pdf_file,
        title="Dokumentasi Resmi & Sintaks SQL (PostgreSQL 16/17 Up-to-Date)",
        language="SQL",
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

    print(f"\n🎉 DATASET SQL BERHASIL DIBUAT DALAM FORMAT PDF!")
    print(f"📁 Lokasi File PDF : {pdf_file.resolve()}")
    print(f"📊 Total Dokumen   : {len(all_records)} chunk SQL")
    code_total = sum(1 for r in all_records if r["code_snippet"])
    print(f"💻 Total Kode      : {code_total} section memiliki contoh query SQL")
    print(f"📦 Ukuran File PDF : {os.path.getsize(pdf_file) / 1024:.2f} KB")


if __name__ == "__main__":
    main()

