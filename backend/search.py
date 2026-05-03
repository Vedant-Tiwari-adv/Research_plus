import numpy as np
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from logger import get_logger

logger = get_logger("search")

_CACHE: dict[str, list[dict]] = {}
_CACHE_MAX = 500


class SemanticSearch:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.index: faiss.IndexFlatIP | None = None
        self.papers: list[dict] = []
        self.dim = 384

    def build_index(self, df: pd.DataFrame):
        """Full rebuild — used on startup only."""
        logger.info(f"Building FAISS index for {len(df)} papers...")
        texts = (df["title"] + ". " + df["abstract"]).tolist()
        embeddings = self.model.encode(
            texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True
        )
        embeddings = np.array(embeddings, dtype="float32")

        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        self.papers = df.to_dict(orient="records")

        # Clear cache so searches reflect the new index
        _CACHE.clear()
        logger.info("FAISS index built successfully")

    def add_papers(self, new_df: pd.DataFrame):
        """
        Incrementally add new papers to the existing index.
        Much faster than full rebuild — only encodes the new rows.
        """
        if self.index is None:
            # No index yet, do a full build
            self.build_index(new_df)
            return

        logger.info(f"Incrementally adding {len(new_df)} papers to FAISS index...")
        texts = (new_df["title"] + ". " + new_df["abstract"]).tolist()
        embeddings = self.model.encode(
            texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True
        )
        embeddings = np.array(embeddings, dtype="float32")

        self.index.add(embeddings)
        self.papers.extend(new_df.to_dict(orient="records"))

        # Clear cache so new papers show up in searches
        _CACHE.clear()
        logger.info(f"Incremental add done. Total papers in index: {len(self.papers)}")

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        cache_key = f"{query.lower().strip()}|{top_k}"
        if cache_key in _CACHE:
            logger.info(f"Cache HIT for query: '{query}'")
            return _CACHE[cache_key]

        if self.index is None:
            return []

        q_emb = self.model.encode([query], normalize_embeddings=True)
        q_emb = np.array(q_emb, dtype="float32")

        scores, indices = self.index.search(q_emb, min(top_k, len(self.papers)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            paper = dict(self.papers[idx])
            paper["similarity_score"] = round(float(score), 4)
            results.append(paper)

        # Cache management
        if len(_CACHE) >= _CACHE_MAX:
            oldest = next(iter(_CACHE))
            del _CACHE[oldest]
        _CACHE[cache_key] = results

        logger.info(f"Search '{query}' -> {len(results)} results")
        return results

    def precision_at_k(self, query: str, relevant_category: str, k: int = 5) -> float:
        results = self.search(query, top_k=k)
        if not results:
            return 0.0
        hits = sum(1 for r in results[:k] if r.get("category") == relevant_category)
        return round(hits / k, 4)


_search_engine = SemanticSearch()


def get_search_engine() -> SemanticSearch:
    return _search_engine