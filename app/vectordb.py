import json
import os
import time
from typing import Any, Dict, List, Optional
import httpx

try:
    from app.embeddings import embed_text
except ImportError:
    from embeddings import embed_text

DEFAULT_OPENSEARCH_URL = os.environ.get("OPENSEARCH_BASE_URL", "http://localhost:9200")
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "knowledge_base")
DEFAULT_KB_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "knowledge-base")


class VectorStore:
    """
    Pengelola Vector Database berbasis OpenSearch dengan dukungan k-NN plugin.
    Menyediakan operasi pembuatan indeks vektor, bulk indexing dokumen utuh,
    dan pencarian kemiripan semantik (k-NN search).
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OPENSEARCH_URL,
        index_name: str = DEFAULT_INDEX_NAME,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.index_name = index_name
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout

    def ensure_index(self) -> bool:
        """Memastikan indeks k-NN sudah terdaftar di OpenSearch dengan mapping 768 dimensi."""
        url = f"{self.base_url}/{self.index_name}"
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(url)
            if res.status_code == 200:
                return True
            if res.status_code != 404:
                res.raise_for_status()

            # Buat indeks baru jika belum ada
            payload = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 100,
                    }
                },
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "doc_id": {"type": "keyword"},
                        "doc_type": {"type": "keyword"},
                        "language": {"type": "keyword"},
                        "category": {"type": "text"},
                        "title": {"type": "text"},
                        "content": {"type": "text"},
                        "token_count": {"type": "integer"},
                        "source": {"type": "keyword"},
                        "source_url": {"type": "keyword"},
                        "embedding": {
                            "type": "knn_vector",
                            "dimension": 768,
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib",
                                "parameters": {"ef_construction": 128, "m": 16},
                            },
                        },
                    }
                },
            }

            create_res = client.put(url, json=payload)
            create_res.raise_for_status()
            return True

    def bulk_index_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """
        Mengunggah kumpulan dokumen embedding ke OpenSearch menggunakan bulk API.
        """
        self.ensure_index()
        total_documents = len(documents)
        start_time = time.time()
        success_count = 0
        error_count = 0

        print(f"[INFO] Memulai bulk index {total_documents} dokumen ke OpenSearch ({self.index_name})...")

        with httpx.Client(timeout=120.0) as client:
            for i in range(0, total_documents, batch_size):
                batch = documents[i : i + batch_size]
                lines = []

                for doc in batch:
                    doc_id = doc.get("id", doc.get("doc_id"))
                    meta_line = json.dumps({"index": {"_index": self.index_name, "_id": doc_id}})
                    data_line = json.dumps(doc)
                    lines.append(meta_line)
                    lines.append(data_line)

                payload = "\n".join(lines) + "\n"

                res = client.post(
                    f"{self.base_url}/_bulk",
                    content=payload,
                    headers={"Content-Type": "application/x-ndjson"},
                )
                res.raise_for_status()
                result = res.json()

                for item in result.get("items", []):
                    action_data = item.get("index", {})
                    if action_data.get("status") in (200, 201):
                        success_count += 1
                    else:
                        error_count += 1

                progress = min(i + batch_size, total_documents)
                rate = progress / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                print(
                    f"[INFO] Progress: {progress}/{total_documents} "
                    f"({(progress / total_documents * 100):.1f}%) | "
                    f"Kecepatan: {rate:.1f} doc/s"
                )

        # Refresh index agar dokumen langsung siap dicari
        with httpx.Client(timeout=30.0) as client:
            client.post(f"{self.base_url}/{self.index_name}/_refresh")

        duration = round(time.time() - start_time, 2)
        print(f"[OK] Bulk indexing selesai: {success_count} berhasil, {error_count} gagal dalam {duration}s.")

        return {
            "status": "success",
            "total_documents": total_documents,
            "indexed_count": success_count,
            "error_count": error_count,
            "duration_seconds": duration,
        }

    def search(
        self,
        query: str,
        k: int = 5,
        language: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian semantik vektor k-NN terhadap query teks.
        Mengembalikan daftar k dokumen paling mirip lengkap dengan skor similarity.
        """
        # Ubah query teks pengguna menjadi vektor 768 dimensi via Ollama
        query_vector = embed_text(query, base_url=self.ollama_url)

        knn_clause: Dict[str, Any] = {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": k,
                }
            }
        }

        filters = []
        if language:
            filters.append({"term": {"language": language}})
        if doc_type:
            filters.append({"term": {"doc_type": doc_type}})

        if filters:
            search_query: Dict[str, Any] = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [knn_clause],
                        "filter": filters,
                    }
                },
            }
        else:
            search_query = {
                "size": k,
                "query": knn_clause,
            }

        with httpx.Client(timeout=self.timeout) as client:
            res = client.post(f"{self.base_url}/{self.index_name}/_search", json=search_query)
            res.raise_for_status()
            data = res.json()

        hits = data.get("hits", {}).get("hits", [])
        results = []
        for hit in hits:
            source = hit.get("_source", {})
            item = {
                "id": source.get("id"),
                "doc_id": source.get("doc_id"),
                "doc_type": source.get("doc_type"),
                "language": source.get("language"),
                "category": source.get("category"),
                "title": source.get("title"),
                "content": source.get("content"),
                "token_count": source.get("token_count"),
                "source": source.get("source"),
                "source_url": source.get("source_url"),
                "similarity_score": round(hit.get("_score", 0.0), 4),
            }
            results.append(item)

        return results


def index_knowledge_base(
    embedded_file: str = None,
    opensearch_url: str = DEFAULT_OPENSEARCH_URL,
    index_name: str = DEFAULT_INDEX_NAME,
) -> Dict[str, Any]:
    """Membaca embedded_documents.json dan memasukkan seluruhnya ke OpenSearch."""
    if embedded_file is None:
        embedded_file = os.path.join(DEFAULT_KB_PATH, "embedded_documents.json")

    if not os.path.exists(embedded_file):
        raise FileNotFoundError(f"Berkas {embedded_file} tidak ditemukan.")

    print(f"[INFO] Memuat berkas dokumen embedding dari: {embedded_file}")
    with open(embedded_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    store = VectorStore(base_url=opensearch_url, index_name=index_name)
    return store.bulk_index_documents(documents)


def main():
    print("=" * 65)
    print("MEMULAI PROSES INDEXING DAN PENGUJIAN VECTOR SEARCH DOKUMEN")
    print("=" * 65)

    result = index_knowledge_base()
    print(f"[OK] Selesai indexing: {result['indexed_count']} dokumen tersimpan.")

    print("\n" + "=" * 65)
    print("PENGUJIAN SEMANTIC VECTOR SEARCH")
    print("=" * 65)

    store = VectorStore()
    test_queries = [
        "bagaimana cara instalasi compiler C di sistem operasi macos?",
        "cara membuat fungsi async dan Promise pada TypeScript",
        "standar konvensi penamaan variabel dan modul di Python",
    ]

    for q in test_queries:
        print(f"\n[QUERY] : \"{q}\"")
        hits = store.search(q, k=2)
        for idx, hit in enumerate(hits, start=1):
            print(f"  Result #{idx} (Score: {hit['similarity_score']}):")
            print(f"    - ID       : {hit['id']}")
            print(f"    - Bahasa   : {hit['language']} | Tipe: {hit['doc_type']}")
            print(f"    - Judul    : {hit['title']}")
            print(f"    - Tokens   : {hit['token_count']}")
            preview = hit['content'][:120].replace('\n', ' ')
            print(f"    - Cuplikan : {preview}...")
    print("\n" + "=" * 65)
    print("[OK] Vector Search berhasil diverifikasi dan siap digunakan.")


if __name__ == "__main__":
    main()
