import httpx


class VectorStore:
    def __init__(self, base_url: str, dimension: int = 768):
        self.base_url = base_url.rstrip("/")
        self.dimension = dimension

    def ensure_index(self, index_name: str) -> None:
        with httpx.Client() as client:
            existing = client.head(f"{self.base_url}/{index_name}", timeout=30.0)
            if existing.status_code == 200:
                return
            response = client.put(
                f"{self.base_url}/{index_name}",
                json={
                    "settings": {"index": {"knn": True}},
                    "mappings": {
                        "properties": {
                            "text": {"type": "text"},
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": self.dimension,
                                "method": {
                                    "engine": "nmslib",
                                    "space_type": "cosinesimil",
                                    "name": "hnsw",
                                },
                            },
                            "metadata": {"type": "object"},
                        }
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()

    def index_document(
        self,
        index_name: str,
        doc_id: str,
        text: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        with httpx.Client() as client:
            response = client.put(
                f"{self.base_url}/{index_name}/_doc/{doc_id}",
                params={"refresh": "true"},
                json={"text": text, "embedding": embedding, "metadata": metadata},
                timeout=30.0,
            )
            response.raise_for_status()

    def search(
        self, index_name: str, query_embedding: list[float], k: int = 3
    ) -> list[dict]:
        with httpx.Client() as client:
            response = client.post(
                f"{self.base_url}/{index_name}/_search",
                json={
                    "size": k,
                    "query": {"knn": {"embedding": {"vector": query_embedding, "k": k}}},
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["hits"]["hits"]
