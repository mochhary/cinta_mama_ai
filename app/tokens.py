import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "knowledge-base")

# Konfigurasi budget token default untuk jendela konteks 4096 token (Llama 3.2 3B)
DEFAULT_BUDGET = {
    "total_window": 4096,
    "system_prompt": 250,
    "user_query_and_history": 500,
    "knowledge_context": 2346,
    "reserved_generation": 1000,
}


def count_tokens(text: str) -> int:
    """
    Menghitung estimasi token secara deterministik dan cepat menggunakan
    subword/BPE regex yang selaras dengan model LLaMA dan Nomic.
    Bekerja 100% lokal tanpa dependensi jaringan eksternal.
    """
    if not text:
        return 0

    # Tokenisasi berbasis kata, karakter tanda baca, dan baris baru
    words = re.findall(r"[\w]+|[^\s\w]|\n", text)
    tokens = 0
    for w in words:
        if w == "\n":
            tokens += 1
        elif len(w) <= 4:
            tokens += 1
        else:
            # Kata yang lebih panjang dipecah oleh tokenizer subword BPE
            tokens += math.ceil(len(w) / 3.8)

    return max(1, int(tokens))


def truncate_by_tokens(text: str, max_tokens: int) -> str:
    """
    Memotong teks agar tidak melebihi batas token tertentu, dengan memotong
    pada batas kalimat (. ! ?) atau baris baru terdekat agar struktur kalimat utuh.
    """
    if not text or max_tokens <= 0:
        return ""

    current_tokens = count_tokens(text)
    if current_tokens <= max_tokens:
        return text

    # Estimasi kasar posisi karakter berdasarkan rasio token
    ratio = max_tokens / current_tokens
    estimated_char_limit = int(len(text) * ratio)

    # Cari batas akhir kalimat (. ! ?) atau baris baru sebelum batas estimasi
    candidate = text[:estimated_char_limit]
    break_points = [
        candidate.rfind(".\n"),
        candidate.rfind(". "),
        candidate.rfind("!\n"),
        candidate.rfind("! "),
        candidate.rfind("?\n"),
        candidate.rfind("? "),
        candidate.rfind("\n\n"),
        candidate.rfind("\n"),
    ]
    valid_breaks = [bp for bp in break_points if bp > (estimated_char_limit // 2)]

    if valid_breaks:
        best_break = max(valid_breaks) + 1
        truncated = text[:best_break].strip()
    else:
        # Fallback potong di spasi terdekat
        last_space = candidate.rfind(" ")
        if last_space > 0:
            truncated = text[:last_space].strip() + "..."
        else:
            truncated = candidate.strip() + "..."

    # Validasi ulang agar pasti tidak melebihi max_tokens
    while count_tokens(truncated) > max_tokens and len(truncated) > 10:
        truncated = truncated[:-10].rstrip() + "..."

    return truncated


def fit_context_to_budget(
    chunks: List[Dict[str, Any]],
    max_token_budget: int = DEFAULT_BUDGET["knowledge_context"],
    separator: str = "\n\n---\n\n",
) -> Dict[str, Any]:
    """
    Memilih dan menyusun chunk-chunk hasil pencarian ke dalam konteks prompt,
    memastikan total token akumulatif tidak melebihi batas budget pengetahuan.
    """
    selected_chunks = []
    accumulated_tokens = 0
    separator_tokens = count_tokens(separator)
    formatted_texts = []

    for chunk in chunks:
        content = chunk.get("content", "")
        # Gunakan token_count yang sudah di-cache jika tersedia
        chunk_tok = chunk.get("token_count")
        if chunk_tok is None:
            chunk_tok = count_tokens(content)

        additional_tokens = chunk_tok + (separator_tokens if selected_chunks else 0)

        # Jika masih muat secara utuh
        if accumulated_tokens + additional_tokens <= max_token_budget:
            selected_item = dict(chunk)
            selected_item["used_tokens"] = chunk_tok
            selected_item["is_truncated"] = False
            selected_chunks.append(selected_item)
            formatted_texts.append(content)
            accumulated_tokens += additional_tokens
        else:
            # Jika tidak muat utuh, cek sisa budget
            remaining_budget = max_token_budget - accumulated_tokens - (separator_tokens if selected_chunks else 0)
            if remaining_budget >= 80:
                # Potong bagian akhir chunk ini agar pas dengan sisa budget
                truncated_content = truncate_by_tokens(content, remaining_budget)
                used_tok = count_tokens(truncated_content)
                selected_item = dict(chunk)
                selected_item["content"] = truncated_content
                selected_item["used_tokens"] = used_tok
                selected_item["is_truncated"] = True
                selected_chunks.append(selected_item)
                formatted_texts.append(truncated_content)
                accumulated_tokens += used_tok + (separator_tokens if selected_chunks else 0)
            break

    return {
        "selected_chunks": selected_chunks,
        "total_chunks_selected": len(selected_chunks),
        "total_context_tokens": accumulated_tokens,
        "max_token_budget": max_token_budget,
        "formatted_context": separator.join(formatted_texts),
    }


def estimate_prompt_tokens(
    system_prompt: str,
    user_query: str,
    context: str = "",
    history_messages: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, int]:
    """
    Menghitung rincian alokasi token untuk seluruh komponen prompt RAG.
    """
    sys_tokens = count_tokens(system_prompt)
    query_tokens = count_tokens(user_query)
    context_tokens = count_tokens(context)

    history_tokens = 0
    if history_messages:
        for msg in history_messages:
            history_tokens += count_tokens(msg.get("content", ""))

    total = sys_tokens + query_tokens + context_tokens + history_tokens

    return {
        "system_tokens": sys_tokens,
        "query_tokens": query_tokens,
        "context_tokens": context_tokens,
        "history_tokens": history_tokens,
        "total_prompt_tokens": total,
    }


def annotate_all_chunks(kb_path: str = DEFAULT_KB_PATH) -> Dict[str, Any]:
    """
    Menyisipkan field token_count ke seluruh chunk di knowledge-base/embedded_chunks.json
    dan knowledge-base/ingested_chunks.json, serta memperbarui berkas summary.
    """
    embedded_file = os.path.join(kb_path, "embedded_chunks.json")
    ingested_file = os.path.join(kb_path, "ingested_chunks.json")
    summary_file = os.path.join(kb_path, "embedded_summary.json")

    if not os.path.exists(embedded_file):
        raise FileNotFoundError(f"Berkas {embedded_file} tidak ditemukan.")

    t0 = time.time()
    print(f"[INFO] Membaca data chunk dari {embedded_file}...")
    with open(embedded_file, "r", encoding="utf-8") as f:
        embedded_chunks = json.load(f)

    total_chunks = len(embedded_chunks)
    total_tokens = 0
    token_counts = []
    lang_tokens: Dict[str, Dict[str, Any]] = {}

    for chunk in embedded_chunks:
        tok = count_tokens(chunk["content"])
        chunk["token_count"] = tok
        total_tokens += tok
        token_counts.append(tok)

        lang = chunk.get("language", "Unknown")
        if lang not in lang_tokens:
            lang_tokens[lang] = {"chunks": 0, "tokens": 0, "characters": 0}
        lang_tokens[lang]["chunks"] += 1
        lang_tokens[lang]["tokens"] += tok
        lang_tokens[lang]["characters"] += chunk.get("char_count", len(chunk["content"]))

    # Simpan kembali embedded_chunks.json dengan token_count
    print(f"[INFO] Menyimpan {total_chunks} chunk beranotasi token ke {embedded_file}...")
    with open(embedded_file, "w", encoding="utf-8") as f:
        json.dump(embedded_chunks, f, ensure_ascii=False)

    # Sinkronisasi token_count juga ke ingested_chunks.json
    if os.path.exists(ingested_file):
        print(f"[INFO] Menyinkronkan token_count ke {ingested_file}...")
        with open(ingested_file, "r", encoding="utf-8") as f:
            ingested_chunks = json.load(f)
        for chunk in ingested_chunks:
            chunk["token_count"] = count_tokens(chunk["content"])
        with open(ingested_file, "w", encoding="utf-8") as f:
            json.dump(ingested_chunks, f, ensure_ascii=False, indent=2)

    # Muat summary yang ada atau buat baru
    summary_data = {}
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                summary_data = json.load(f)
        except Exception:
            summary_data = {}

    summary_data.update({
        "total_tokens": total_tokens,
        "average_tokens_per_chunk": round(total_tokens / total_chunks, 1) if total_chunks else 0,
        "min_tokens_per_chunk": min(token_counts) if token_counts else 0,
        "max_tokens_per_chunk": max(token_counts) if token_counts else 0,
        "token_budget_config": DEFAULT_BUDGET,
        "language_token_distribution": {
            lang: {
                "chunks": data["chunks"],
                "total_tokens": data["tokens"],
                "avg_tokens": round(data["tokens"] / data["chunks"], 1) if data["chunks"] else 0,
            }
            for lang, data in sorted(lang_tokens.items())
        },
    })

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    duration = round(time.time() - t0, 2)
    print(f"[OK] Selesai menambahkan anotasi token dalam {duration} detik.")

    return {
        "status": "success",
        "total_chunks": total_chunks,
        "total_tokens": total_tokens,
        "avg_tokens": round(total_tokens / total_chunks, 1) if total_chunks else 0,
        "min_tokens": min(token_counts) if token_counts else 0,
        "max_tokens": max(token_counts) if token_counts else 0,
        "duration_seconds": duration,
        "language_distribution": lang_tokens,
    }


def main():
    print("=" * 65)
    print("MEMULAI PROSES PENANGANAN DAN ANOTASI TOKEN")
    print("=" * 65)

    stats = annotate_all_chunks()

    print("\n" + "=" * 65)
    print("STATISTIK PENANGANAN TOKEN CORPUS")
    print("=" * 65)
    print(f"Total Chunk Diproses     : {stats['total_chunks']:,} chunk")
    print(f"Total Token Terhitung    : {stats['total_tokens']:,} token")
    print(f"Rata-rata Token per Chunk: {stats['avg_tokens']} token")
    print(f"Token Terpendek          : {stats['min_tokens']} token")
    print(f"Token Terpanjang         : {stats['max_tokens']} token")
    print(f"Waktu Eksekusi           : {stats['duration_seconds']} detik")
    print("-" * 65)
    print(f"{'Bahasa':<12} | {'Chunks':<7} | {'Total Token':<13} | {'Rata-rata':<10}")
    print("-" * 65)
    for lang, data in sorted(stats["language_distribution"].items()):
        avg = round(data["tokens"] / data["chunks"], 1) if data["chunks"] else 0
        print(f"{lang:<12} | {data['chunks']:<7} | {data['tokens']:<13,} | {avg:<10}")
    print("=" * 65)
    print("[OK] Seluruh data chunk telah diperkaya dengan atribut token_count.")


if __name__ == "__main__":
    main()

