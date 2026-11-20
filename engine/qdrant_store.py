import os
from typing import Any, Dict, List, Optional
import numpy as np
from .router import LocalEmbedder

class QdrantVectorStore:
    """
    Persistent Qdrant Vector Store wrapper.
    Uses qdrant-client embedded local disk mode (path='./qdrant_local_db') if installed,
    or falls back seamlessly to an in-memory Qdrant-compatible payload store so notebooks never break.
    """
    def __init__(self, collection_name: str = "sre_runbooks", path: str = "./qdrant_local_db", embedder: Optional[LocalEmbedder] = None):
        self.collection_name = collection_name
        self.path = path
        self.embedder = embedder or LocalEmbedder()
        self.mode = "memory_fallback"
        self._client = None
        self._mem_points: List[Dict[str, Any]] = []

        try:
            from qdrant_client import QdrantClient
            os.makedirs(path, exist_ok=True)
            self._client = QdrantClient(path=path)
            self.mode = f"qdrant_embedded ({path})"
        except Exception:
            self._client = None

    def upsert_documents(self, documents: List[Dict[str, Any]]):
        """Each doc dict expects: {'id': int, 'text': str, 'metadata': dict}"""
        texts = [d["text"] for d in documents]
        vectors = self.embedder.encode(texts)

        if self._client is not None:
            from qdrant_client.models import Distance, VectorParams, PointStruct
            if self._client.collection_exists(self.collection_name):
                self._client.delete_collection(self.collection_name)
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=int(vectors.shape[1]), distance=Distance.COSINE)
            )
            points = [
                PointStruct(
                    id=int(doc["id"]),
                    vector=vectors[i].tolist(),
                    payload={"text": doc["text"], **doc.get("metadata", {})}
                )
                for i, doc in enumerate(documents)
            ]
            self._client.upsert(collection_name=self.collection_name, points=points)
        else:
            self._mem_points = [
                {"id": int(doc["id"]), "vector": vectors[i], "payload": {"text": doc["text"], **doc.get("metadata", {})}}
                for i, doc in enumerate(documents)
            ]

    def search(self, query: str, top_k: int = 3, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        q_vec = self.embedder.encode([query])[0]

        if self._client is not None:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            q_filter = None
            if metadata_filter:
                conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in metadata_filter.items()]
                q_filter = Filter(must=conditions)
            hits = self._client.query_points(
                collection_name=self.collection_name,
                query=q_vec.tolist(),
                query_filter=q_filter,
                limit=top_k
            ).points
            return [
                {
                    "id": h.id,
                    "score": round(float(h.score), 4),
                    "text": h.payload.get("text", ""),
                    "metadata": {k: v for k, v in h.payload.items() if k != "text"},
                    "filter_applied": metadata_filter or {}
                }
                for h in hits
            ]
        else:
            results = []
            for pt in self._mem_points:
                payload = pt["payload"]
                if metadata_filter and not all(payload.get(k) == v for k, v in metadata_filter.items()):
                    continue
                score = float(np.dot(pt["vector"], q_vec))
                results.append({
                    "id": pt["id"],
                    "score": round(score, 4),
                    "text": payload.get("text", ""),
                    "metadata": {k: v for k, v in payload.items() if k != "text"},
                    "filter_applied": metadata_filter or {}
                })
            return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
