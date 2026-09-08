"""Integration tests for InfinispanVectorStore.

These tests require a running Infinispan 15+ server.
Set environment variables:
  - INFINISPAN_URL (default: http://localhost:11222)
  - INFINISPAN_USER (default: admin)
  - INFINISPAN_PASSWORD (default: password)
"""

import os
import uuid
from typing import List

import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from langchain_infinispan import InfinispanVectorStore

ISPN_URL = os.getenv("INFINISPAN_URL", "http://localhost:11222")
ISPN_USER = os.getenv("INFINISPAN_USER", "admin")
ISPN_PASSWORD = os.getenv("INFINISPAN_PASSWORD", "password")


class FakeEmbeddings(Embeddings):
    """Deterministic fake embeddings for testing."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        h = hash(text) % 1000
        return [float(h % 10) / 10.0 for _ in range(3)]


@pytest.fixture
def cache_name() -> str:
    return f"test_langchain_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def store(cache_name: str) -> InfinispanVectorStore:
    s = InfinispanVectorStore(
        embedding=FakeEmbeddings(),
        cache_name=cache_name,
        ispn_url=ISPN_URL,
        ispn_user=ISPN_USER,
        ispn_password=ISPN_PASSWORD,
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

    def test_from_texts(self, cache_name: str) -> None:
        store = InfinispanVectorStore.from_texts(
            texts=["doc1", "doc2"],
            embedding=FakeEmbeddings(),
            cache_name=cache_name,
            ispn_url=ISPN_URL,
            ispn_user=ISPN_USER,
            ispn_password=ISPN_PASSWORD,
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

    def test_from_documents(self, cache_name: str) -> None:
        docs = [
            Document(page_content="first", metadata={"source": "a"}),
            Document(page_content="second", metadata={"source": "b"}),
        ]
        store = InfinispanVectorStore.from_documents(
            documents=docs,
            embedding=FakeEmbeddings(),
            cache_name=cache_name,
            ispn_url=ISPN_URL,
            ispn_user=ISPN_USER,
            ispn_password=ISPN_PASSWORD,
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
