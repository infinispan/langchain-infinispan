"""Integration tests for normalized relevance scores.

``similarity_search_with_relevance_scores`` must return scores in ``[0, 1]``
(0 = dissimilar, 1 = most similar) for every supported distance strategy. These
tests insert controlled unit vectors and assert both the bounds and the ranking
against a real server.
"""

import uuid
from typing import Dict, List

import pytest
from langchain_core.embeddings import Embeddings

from langchain_infinispan import DistanceStrategy, InfinispanVectorStore

from .conftest import ServerInfo

# Unit vectors relative to the query direction [1, 0, 0]:
#   same     -> identical            (most similar)
#   ortho    -> orthogonal           (middle)
#   opposite -> opposite direction   (least similar)
_VECTORS: Dict[str, List[float]] = {
    "query": [1.0, 0.0, 0.0],
    "same": [1.0, 0.0, 0.0],
    "ortho": [0.0, 1.0, 0.0],
    "opposite": [-1.0, 0.0, 0.0],
}


class _MappedEmbeddings(Embeddings):
    """Embeddings that map known texts to fixed unit vectors."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [_VECTORS[t] for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return _VECTORS[text]


@pytest.mark.parametrize("strategy", list(DistanceStrategy), ids=lambda s: s.name)
def test_relevance_scores_bounded_and_ordered(
    strategy: DistanceStrategy, infinispan_server: ServerInfo
) -> None:
    url, user, password = infinispan_server
    cache_name = f"test_relevance_{strategy.name.lower()}_{uuid.uuid4().hex[:8]}"
    store = InfinispanVectorStore(
        embedding=_MappedEmbeddings(),
        cache_name=cache_name,
        similarity=strategy,
        dimension=3,
        ispn_url=url,
        ispn_user=user,
        ispn_password=password,
        verify=False,
        package_name=f"relevance_{strategy.name.lower()}",
    )
    try:
        labels = ["same", "ortho", "opposite"]
        store.add_texts(labels, ids=labels)

        results = store.similarity_search_with_relevance_scores("query", k=3)
        scores = {doc.id: score for doc, score in results}

        # Contract: every relevance score is in [0, 1].
        assert all(0.0 <= s <= 1.0 for s in scores.values()), scores
        # Ranking: identical > orthogonal > opposite.
        assert scores["same"] > scores["ortho"] > scores["opposite"], scores
    finally:
        try:
            store._client.delete_cache(cache_name)
        except Exception:
            pass
        store.close()
