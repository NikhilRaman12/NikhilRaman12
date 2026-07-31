from dataclasses import dataclass
from pathlib import Path
from .config import Settings

@dataclass(frozen=True)
class Evidence:
    chunk_id: str; text: str; title: str; filename: str; page: int; score: float

class RetrievalUnavailable(RuntimeError): pass

class HybridRetriever:
    """Honest adapter boundary: configured stores are never silently substituted."""
    def __init__(self, settings: Settings): self.settings = settings
    def configured(self) -> bool:
        s = self.settings
        required = [bool(s.pgvector_url)] if s.vector_backend == "pgvector" else [bool(s.milvus_uri)]
        if s.vector_backend == "hybrid": required = [bool(s.pgvector_url), bool(s.milvus_uri)]
        return all(required)
    def retrieve(self, query: str, limit: int = 8) -> list[Evidence]:
        if not self.configured():
            raise RetrievalUnavailable(f"{self.settings.vector_backend} is not configured")
        # Database-specific implementations intentionally fail closed until reachable clients are wired.
        raise RetrievalUnavailable(f"{self.settings.vector_backend} connection unavailable")

def reciprocal_rank_fusion(rankings: list[list[Evidence]], k: int = 60) -> list[Evidence]:
    scores: dict[str, float] = {}; values = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item.chunk_id] = scores.get(item.chunk_id, 0) + 1 / (k + rank); values[item.chunk_id] = item
    return [values[i] for i in sorted(scores, key=scores.get, reverse=True)]
