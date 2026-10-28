import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

DEFAULT_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
DEFAULT_KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "knowledge-base")


def embed_text(text: str, base_url: str = DEFAULT_BASE_URL, model: str = DEFAULT_MODEL) -> List[float]:
    """Mendapatkan vektor embedding untuk satu teks menggunakan Ollama."""
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{base_url}/api/embed",
            json={"model": model, "input": text},
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]


def embed_batch(
    texts: List[str],
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> List[List[float]]:
    """Mendapatkan vektor embedding untuk batch kumpulan teks menggunakan Ollama."""
    last_err = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    f"{base_url}/api/embed",
                    json={"model": model, "input": texts},
                )
                response.raise_for_status()
                return response.json()["embeddings"]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Gagal melakukan embedding setelah {max_retries} percobaan: {last_err}")


def embed_all_chunks(
    input_file: str = None,
    output_file: str = None,
    summary_file: str = None,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    batch_size: int = 15,
) -> Dict[str, Any]:
    """
    Melakukan embedding seluruh chunk dari knowledge-base/ingested_chunks.json
    dengan dukungan checkpointing agar dapat dilanjutkan jika terputus.
    """
    if input_file is None:
        input_file = os.path.join(DEFAULT_KB_PATH, "ingested_chunks.json")
    if output_file is None:
        output_file = os.path.join(DEFAULT_KB_PATH, "embedded_chunks.json")
    if summary_file is None:
        summary_file = os.path.join(DEFAULT_KB_PATH, "embedded_summary.json")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Berkas chunk {input_file} tidak ditemukan. Jalankan ingest terlebih dahulu.")

    with open(input_file, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)

    total_chunks = len(chunks)
    print(f"[INFO] Memuat {total_chunks} chunk dari {input_file}")
    print(f"[INFO] Model embedding: {model} melalui {base_url}")
    print(f"[INFO] Ukuran batch: {batch_size}")

    # Memeriksa checkpoint jika output_file sudah ada sebelumnya
    embedded_data: List[Dict[str, Any]] = []
    processed_ids = set()

    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                embedded_data = json.load(f)
            processed_ids = {item["id"] for item in embedded_data if "embedding" in item}
            if processed_ids:
                print(f"[INFO] Ditemukan checkpoint: {len(processed_ids)}/{total_chunks} chunk sudah di-embed.")
        except Exception:
            embedded_data = []
            processed_ids = set()

    # Filter chunk yang belum di-embed
    chunks_to_process = [c for c in chunks if c["id"] not in processed_ids]
    if not chunks_to_process:
        print("[INFO] Seluruh chunk sudah memiliki embedding.")
        return {
            "status": "success",
            "message": "All chunks already embedded",
            "total_chunks": total_chunks,
            "output_file": output_file,
        }

    start_time = time.time()
    total_to_process = len(chunks_to_process)
    print(f"[INFO] Memulai proses embedding untuk {total_to_process} chunk tersisa...")

    batch_texts = []
    batch_chunks = []
    processed_count = len(processed_ids)

    for idx, chunk in enumerate(chunks_to_process, start=1):
        batch_texts.append(chunk["content"])
        batch_chunks.append(chunk)

        # Proses batch saat mencapai batch_size atau chunk terakhir
        if len(batch_texts) >= batch_size or idx == total_to_process:
            embeddings = embed_batch(batch_texts, base_url=base_url, model=model)

            for c, emb in zip(batch_chunks, embeddings):
                item = dict(c)
                item["embedding"] = emb
                item["embedding_dim"] = len(emb)
                item["embedding_model"] = model
                embedded_data.append(item)

            processed_count += len(batch_chunks)
            elapsed = time.time() - start_time
            rate = (idx / elapsed) if elapsed > 0 else 0
            eta_seconds = (total_to_process - idx) / rate if rate > 0 else 0

            print(
                f"[INFO] Progress: {processed_count}/{total_chunks} "
                f"({(processed_count / total_chunks * 100):.1f}%) | "
                f"Rate: {rate:.1f} chunk/s | "
                f"ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
            )

            # Simpan checkpoint sementara setiap 100 chunk atau pada batch terakhir
            if processed_count % 100 == 0 or idx == total_to_process:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(embedded_data, f, ensure_ascii=False)

            batch_texts = []
            batch_chunks = []

    total_duration = round(time.time() - start_time, 2)
    embedding_dim = embedded_data[0]["embedding_dim"] if embedded_data else 0

    summary = {
        "status": "success",
        "model": model,
        "base_url": base_url,
        "embedding_dimension": embedding_dim,
        "total_chunks_embedded": len(embedded_data),
        "total_duration_seconds": total_duration,
        "average_speed_chunks_per_sec": round(len(chunks_to_process) / total_duration, 2) if total_duration > 0 else 0,
        "output_file": os.path.abspath(output_file),
    }

    # Simpan ringkasan embedding
    Path(summary_file).parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Proses embedding selesai dalam {total_duration} detik.")
    print(f"[OK] Total chunk tersimpan: {len(embedded_data)} ke {output_file}")
    print(f"[OK] Dimensi vektor: {embedding_dim}")
    print(f"[OK] Ringkasan disimpan ke: {summary_file}")

    return summary


def main():
    print("=" * 60)
    print("MEMULAI PROSES EMBEDDING CHUNK (NOMIC-EMBED-TEXT)")
    print("=" * 60)
    embed_all_chunks()


if __name__ == "__main__":
    main()


def embed_batch(
    texts: List[str],
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> List[List[float]]:
    """Mendapatkan vektor embedding untuk batch kumpulan teks menggunakan Ollama."""
    last_err = None
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    f"{base_url}/api/embed",
                    json={"model": model, "input": texts},
                )
                response.raise_for_status()
                return response.json()["embeddings"]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"Gagal melakukan embedding setelah {max_retries} percobaan: {last_err}")


def embed_all_chunks(
    input_file: str = None,
    output_file: str = None,
    summary_file: str = None,
    base_url: str = DEFAULT_BASE_URL,
    model: str = DEFAULT_MODEL,
    batch_size: int = 15,
) -> Dict[str, Any]:
    """
    Melakukan embedding seluruh chunk dari knowledge-base/ingested_chunks.json
    dengan dukungan checkpointing agar dapat dilanjutkan jika terputus.
    """
    if input_file is None:
        input_file = os.path.join(DEFAULT_KB_PATH, "ingested_chunks.json")
    if output_file is None:
        output_file = os.path.join(DEFAULT_KB_PATH, "embedded_chunks.json")
    if summary_file is None:
        summary_file = os.path.join(DEFAULT_KB_PATH, "embedded_summary.json")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Berkas chunk {input_file} tidak ditemukan. Jalankan ingest terlebih dahulu.")

    with open(input_file, "r", encoding="utf-8") as f:
        chunks: List[Dict[str, Any]] = json.load(f)

    total_chunks = len(chunks)
    print(f"[INFO] Memuat {total_chunks} chunk dari {input_file}")
    print(f"[INFO] Model embedding: {model} melalui {base_url}")
    print(f"[INFO] Ukuran batch: {batch_size}")

    # Memeriksa checkpoint jika output_file sudah ada sebelumnya
    embedded_data: List[Dict[str, Any]] = []
    processed_ids = set()

    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                embedded_data = json.load(f)
            processed_ids = {item["id"] for item in embedded_data if "embedding" in item}
            if processed_ids:
                print(f"[INFO] Ditemukan checkpoint: {len(processed_ids)}/{total_chunks} chunk sudah di-embed.")
        except Exception:
            embedded_data = []
            processed_ids = set()

    # Filter chunk yang belum di-embed
    chunks_to_process = [c for c in chunks if c["id"] not in processed_ids]
    if not chunks_to_process:
        print("[INFO] Seluruh chunk sudah memiliki embedding.")
        return {
            "status": "success",
            "message": "All chunks already embedded",
            "total_chunks": total_chunks,
            "output_file": output_file,
        }

    start_time = time.time()
    total_to_process = len(chunks_to_process)
    print(f"[INFO] Memulai proses embedding untuk {total_to_process} chunk tersisa...")

    batch_texts = []
    batch_chunks = []
    processed_count = len(processed_ids)

    for idx, chunk in enumerate(chunks_to_process, start=1):
        batch_texts.append(chunk["content"])
        batch_chunks.append(chunk)

        # Proses batch saat mencapai batch_size atau chunk terakhir
        if len(batch_texts) >= batch_size or idx == total_to_process:
            embeddings = embed_batch(batch_texts, base_url=base_url, model=model)

            for c, emb in zip(batch_chunks, embeddings):
                item = dict(c)
                item["embedding"] = emb
                item["embedding_dim"] = len(emb)
                item["embedding_model"] = model
                embedded_data.append(item)

            processed_count += len(batch_chunks)
            elapsed = time.time() - start_time
            rate = (idx / elapsed) if elapsed > 0 else 0
            eta_seconds = (total_to_process - idx) / rate if rate > 0 else 0

            print(
                f"[INFO] Progress: {processed_count}/{total_chunks} "
                f"({(processed_count / total_chunks * 100):.1f}%) | "
                f"Rate: {rate:.1f} chunk/s | "
                f"ETA: {int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
            )

            # Simpan checkpoint sementara setiap 100 chunk atau pada batch terakhir
            if processed_count % 100 == 0 or idx == total_to_process:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(embedded_data, f, ensure_ascii=False)

            batch_texts = []
            batch_chunks = []

    total_duration = round(time.time() - start_time, 2)
    embedding_dim = embedded_data[0]["embedding_dim"] if embedded_data else 0

    summary = {
        "status": "success",
        "model": model,
        "base_url": base_url,
        "embedding_dimension": embedding_dim,
        "total_chunks_embedded": len(embedded_data),
        "total_duration_seconds": total_duration,
        "average_speed_chunks_per_sec": round(len(chunks_to_process) / total_duration, 2) if total_duration > 0 else 0,
        "output_file": os.path.abspath(output_file),
    }

    # Simpan ringkasan embedding
    Path(summary_file).parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Proses embedding selesai dalam {total_duration} detik.")
    print(f"[OK] Total chunk tersimpan: {len(embedded_data)} ke {output_file}")
    print(f"[OK] Dimensi vektor: {embedding_dim}")
    print(f"[OK] Ringkasan disimpan ke: {summary_file}")

    return summary


def main():
    print("=" * 60)
    print("MEMULAI PROSES EMBEDDING CHUNK (NOMIC-EMBED-TEXT)")
    print("=" * 60)
    embed_all_chunks()


if __name__ == "__main__":
    main()

