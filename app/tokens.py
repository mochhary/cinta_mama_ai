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

    ratio = max_tokens / current_tokens
    estimated_char_limit = int(len(text) * ratio)

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
        last_space = candidate.rfind(" ")
        if last_space > 0:
            truncated = text[:last_space].strip() + "..."
        else:
            truncated = candidate.strip() + "..."

    while count_tokens(truncated) > max_tokens and len(truncated) > 10:
        truncated = truncated[:-10].rstrip() + "..."

    return truncated


def fit_context_to_budget(
    documents: List[Dict[str, Any]],
    max_token_budget: int = DEFAULT_BUDGET["knowledge_context"],
    separator: str = "\n\n---\n\n",
) -> Dict[str, Any]:
    """
    Memilih dan menyusun dokumen-dokumen hasil pencarian ke dalam konteks prompt,
    memastikan total token akumulatif tidak melebihi batas budget pengetahuan.
    """
    selected_documents = []
    accumulated_tokens = 0
    separator_tokens = count_tokens(separator)
    formatted_texts = []

    for doc in documents:
        content = doc.get("content", "")
        doc_tok = doc.get("token_count")
        if doc_tok is None:
            doc_tok = count_tokens(content)

        additional_tokens = doc_tok + (separator_tokens if selected_documents else 0)

        # Jika masih muat secara utuh
        if accumulated_tokens + additional_tokens <= max_token_budget:
            selected_item = dict(doc)
            selected_item["used_tokens"] = doc_tok
            selected_item["is_truncated"] = False
            selected_documents.append(selected_item)
            formatted_texts.append(content)
            accumulated_tokens += additional_tokens
        else:
            # Jika tidak muat utuh, cek sisa budget
            remaining_budget = max_token_budget - accumulated_tokens - (separator_tokens if selected_documents else 0)
            if remaining_budget >= 80:
                truncated_content = truncate_by_tokens(content, remaining_budget)
                used_tok = count_tokens(truncated_content)
                selected_item = dict(doc)
                selected_item["content"] = truncated_content
                selected_item["used_tokens"] = used_tok
                selected_item["is_truncated"] = True
                selected_documents.append(selected_item)
                formatted_texts.append(truncated_content)
                accumulated_tokens += used_tok + (separator_tokens if selected_documents else 0)
            break

    return {
        "selected_documents": selected_documents,
        "total_documents_selected": len(selected_documents),
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


def annotate_all_documents(kb_path: str = DEFAULT_KB_PATH) -> Dict[str, Any]:
    """
    Menyisipkan field token_count ke seluruh dokumen di knowledge-base/embedded_documents.json
    dan knowledge-base/ingested_documents.json, serta memperbarui berkas summary.
    """
    embedded_file = os.path.join(kb_path, "embedded_documents.json")
    ingested_file = os.path.join(kb_path, "ingested_documents.json")
    summary_file = os.path.join(kb_path, "embedded_summary.json")

    if not os.path.exists(embedded_file):
        raise FileNotFoundError(f"Berkas {embedded_file} tidak ditemukan.")

    t0 = time.time()
    print(f"[INFO] Membaca data dokumen dari {embedded_file}...")
    with open(embedded_file, "r", encoding="utf-8") as f:
        embedded_docs = json.load(f)

    total_docs = len(embedded_docs)
    total_tokens = 0
    token_counts = []
    lang_tokens: Dict[str, Dict[str, Any]] = {}

    for doc in embedded_docs:
        tok = count_tokens(doc["content"])
        doc["token_count"] = tok
        total_tokens += tok
        token_counts.append(tok)

        lang = doc.get("language", "Unknown")
        if lang not in lang_tokens:
            lang_tokens[lang] = {"documents": 0, "tokens": 0, "characters": 0}
        lang_tokens[lang]["documents"] += 1
        lang_tokens[lang]["tokens"] += tok
        lang_tokens[lang]["characters"] += doc.get("char_count", len(doc["content"]))

    # Simpan kembali embedded_documents.json
    print(f"[INFO] Menyimpan {total_docs} dokumen beranotasi token ke {embedded_file}...")
    with open(embedded_file, "w", encoding="utf-8") as f:
        json.dump(embedded_docs, f, ensure_ascii=False, indent=2)

    # Sinkronisasi token_count juga ke ingested_documents.json
    if os.path.exists(ingested_file):
        print(f"[INFO] Menyinkronkan token_count ke {ingested_file}...")
        with open(ingested_file, "r", encoding="utf-8") as f:
            ingested_docs = json.load(f)
        for doc in ingested_docs:
            doc["token_count"] = count_tokens(doc["content"])
        with open(ingested_file, "w", encoding="utf-8") as f:
            json.dump(ingested_docs, f, ensure_ascii=False, indent=2)

    # Update summary
    summary_data = {}
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                summary_data = json.load(f)
        except Exception:
            summary_data = {}

    summary_data.update({
        "total_tokens": total_tokens,
        "average_tokens_per_document": round(total_tokens / total_docs, 1) if total_docs else 0,
        "min_tokens_per_document": min(token_counts) if token_counts else 0,
        "max_tokens_per_document": max(token_counts) if token_counts else 0,
        "token_budget_config": DEFAULT_BUDGET,
        "language_token_distribution": {
            lang: {
                "documents": data["documents"],
                "total_tokens": data["tokens"],
                "avg_tokens": round(data["tokens"] / data["documents"], 1) if data["documents"] else 0,
            }
            for lang, data in sorted(lang_tokens.items())
        },
    })

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    duration = round(time.time() - t0, 2)
    print(f"[OK] Selesai menghitung token {total_docs} dokumen dalam {duration}s.")
    print(f"[OK] Total token di seluruh basis pengetahuan: {total_tokens:,} token.")
    print(f"[OK] Rata-rata token per dokumen: {summary_data['average_tokens_per_document']} token.")

    return summary_data


def main():
    print("=" * 65)
    print("ANALISIS DAN ANOTASI TOKEN BASIS PENGETAHUAN DOKUMEN")
    print("=" * 65)
    annotate_all_documents()


if __name__ == "__main__":
    main()
