"""
Script konverter untuk mengubah file dataset CSV ke PDF.
Dapat dijalankan langsung dengan:
    python scripts/convert_csv_to_pdf.py
"""

import sys
from pathlib import Path

try:
    from scripts.pdf_exporter import convert_csv_to_pdf
except ImportError:
    from pdf_exporter import convert_csv_to_pdf


def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    print("=" * 65)
    print("📄 KONVERSI DATASET CSV KE PDF UNTUK RAG KNOWLEDGE BASE")
    print("=" * 65)

    files_to_convert = [
        ("csharp_docs.csv", "csharp_docs.pdf", "C#"),
        ("java_docs.csv", "java_docs.pdf", "Java"),
    ]

    for csv_name, pdf_name, lang in files_to_convert:
        csv_path = data_dir / csv_name
        pdf_path = data_dir / pdf_name

        if not csv_path.exists():
            print(f"[!] Lewati: {csv_path.name} tidak ditemukan")
            continue

        print(f"\n🔄 Mengonversi {csv_path.name} -> {pdf_path.name} ({lang})...")
        count, out_file = convert_csv_to_pdf(csv_path, pdf_path, default_language=lang)
        size_kb = out_file.stat().st_size / 1024
        print(f"   ✓ Selesai: {count} dokumen/chunk berhasil diekspor!")
        print(f"   📁 Output : {out_file}")
        print(f"   📦 Ukuran : {size_kb:.2f} KB")

    print("\n🎉 Semua dataset CSV berhasil dikonversi ke PDF!")


if __name__ == "__main__":
    main()

