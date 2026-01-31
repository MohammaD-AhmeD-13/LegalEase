import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class RetrievalService:
    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        index_path: Optional[Path] = None,
        metadata_path: Optional[Path] = None,
        embedding_model_id: Optional[str] = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.dataset_path = dataset_path or Path(
            os.getenv("RAG_DATASET_PATH", base_dir / "data" / "legalease_rag_dataset_clean.json")
        )
        self.index_path = index_path or Path(
            os.getenv("RAG_INDEX_PATH", base_dir / "data" / "rag_index.npz")
        )
        self.metadata_path = metadata_path or Path(
            os.getenv("RAG_METADATA_PATH", base_dir / "data" / "rag_metadata.json")
        )
        self.embedding_model_id = embedding_model_id or os.getenv(
            "RAG_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
        )
        self.model: Optional[SentenceTransformer] = None
        self.embeddings: Optional[np.ndarray] = None
        self.metadata: Optional[List[Dict[str, Any]]] = None

        if self.index_path.exists() and self.metadata_path.exists():
            self._load_index()

    def _load_model(self) -> None:
        if self.model is None:
            self.model = SentenceTransformer(self.embedding_model_id)

    def _load_index(self) -> None:
        data = np.load(self.index_path)
        self.embeddings = data["embeddings"].astype(np.float32)
        self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))

    def _format_query(self, query: str) -> str:
        if "e5" in self.embedding_model_id.lower():
            return f"query: {query}"
        return query

    def _format_passage(self, passage: str) -> str:
        if "e5" in self.embedding_model_id.lower():
            return f"passage: {passage}"
        return passage

    def build_index(self, batch_size: int = 32) -> Dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.dataset_path}")

        self._load_model()
        records = json.loads(self.dataset_path.read_text(encoding="utf-8"))

        passages = [self._format_passage(item["text"]) for item in records]
        embeddings = self.model.encode(
            passages,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        embeddings = np.asarray(embeddings, dtype=np.float32)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(self.index_path, embeddings=embeddings)

        minimal_metadata = [
            {
                "chunk_id": item.get("chunk_id"),
                "law_name": item.get("law_name"),
                "domain": item.get("domain"),
                "jurisdiction": item.get("jurisdiction"),
                "section_id": item.get("section_id"),
                "section_title": item.get("section_title"),
                "text": item.get("text"),
            }
            for item in records
        ]
        self.metadata_path.write_text(
            json.dumps(minimal_metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.embeddings = embeddings
        self.metadata = minimal_metadata
        return {
            "indexed_chunks": len(minimal_metadata),
            "embedding_model": self.embedding_model_id,
            "index_path": str(self.index_path),
        }

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.embeddings is None or self.metadata is None:
            raise ValueError("RAG index not built yet. Call build_index first.")

        self._load_model()
        query_text = self._format_query(query)
        query_embedding = self.model.encode(
            [query_text],
            normalize_embeddings=True,
        )[0]

        scores = np.dot(self.embeddings, query_embedding)
        top_k = max(1, min(top_k, len(scores)))
        best_indices = np.argsort(scores)[-top_k:][::-1]

        results = []
        for idx in best_indices:
            item = dict(self.metadata[idx])
            item["score"] = float(scores[idx])
            results.append(item)
        return results


_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
