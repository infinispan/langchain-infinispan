"""Integration tests for InfinispanVectorStore.

These tests require a live Infinispan 15+ server, which is started and stopped
automatically by the ``infinispan_server`` fixture in ``conftest.py``.
"""

import uuid

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from langchain_infinispan import InfinispanVectorStore

from .conftest import ServerInfo

# Deterministic embeddings that never produce a zero-magnitude vector (which
# would break cosine similarity on the server).
EMBEDDING_DIM = 3


def make_embeddings() -> DeterministicFakeEmbedding:
    return DeterministicFakeEmbedding(size=EMBEDDING_DIM)


@pytest.fixture
def cache_name() -> str:
    return f"test_langchain_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def store(
    cache_name: str, infinispan_server: ServerInfo
) -> InfinispanVectorStore:
    url, user, password = infinispan_server
    s = InfinispanVectorStore(
        embedding=make_embeddings(),
        cache_name=cache_name,
        ispn_url=url,
        ispn_user=user,
        ispn_password=password,
        dimension=3,
        verify=False,
    )
    yield s  # type: ignore[misc]
    try:
        s._client.delete_cache(cache_name)
    except Exception:
        pass
    s.close()


@pytest.mark.requires("requests")
class TestInfinispanVectorStore:
    def test_add_and_search(self, store: InfinispanVectorStore) -> None:
        ids = store.add_texts(
            ["alpha", "beta", "gamma"],
            metadatas=[{"idx": "0"}, {"idx": "1"}, {"idx": "2"}],
        )
        assert len(ids) == 3

        results = store.similarity_search("alpha", k=2)
        assert len(results) > 0
        assert all(isinstance(r, Document) for r in results)

    def test_add_and_search_with_score(
        self, store: InfinispanVectorStore
    ) -> None:
        store.add_texts(["hello world", "goodbye world"])

        results = store.similarity_search_with_score("hello", k=2)
        assert len(results) > 0
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)

    def test_delete(self, store: InfinispanVectorStore) -> None:
        ids = store.add_texts(["to be deleted"])
        assert store.delete(ids=ids)

    def test_from_texts(
        self, cache_name: str, infinispan_server: ServerInfo
    ) -> None:
        url, user, password = infinispan_server
        store = InfinispanVectorStore.from_texts(
            texts=["doc1", "doc2"],
            embedding=make_embeddings(),
            cache_name=cache_name,
            ispn_url=url,
            ispn_user=user,
            ispn_password=password,
            dimension=3,
            verify=False,
        )
        results = store.similarity_search("doc1", k=1)
        assert len(results) > 0
        try:
            store._client.delete_cache(cache_name)
        except Exception:
            pass
        store.close()

    def test_from_documents(
        self, cache_name: str, infinispan_server: ServerInfo
    ) -> None:
        url, user, password = infinispan_server
        docs = [
            Document(page_content="first", metadata={"source": "a"}),
            Document(page_content="second", metadata={"source": "b"}),
        ]
        store = InfinispanVectorStore.from_documents(
            documents=docs,
            embedding=make_embeddings(),
            cache_name=cache_name,
            ispn_url=url,
            ispn_user=user,
            ispn_password=password,
            dimension=3,
            verify=False,
        )
        results = store.similarity_search("first", k=1)
        assert len(results) > 0
        try:
            store._client.delete_cache(cache_name)
        except Exception:
            pass
        store.close()
