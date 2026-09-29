"""Standard LangChain VectorStore integration tests.

Subclasses ``langchain_tests`` ``VectorStoreIntegrationTests`` so the
integration is validated against LangChain's conformance suite. Requires a
live Infinispan server, which is provided by the session-scoped
``infinispan_server`` fixture in ``conftest.py``.
"""

import uuid
from typing import Generator

import pytest
from langchain_core.vectorstores import VectorStore
from langchain_tests.integration_tests.vectorstores import (
    VectorStoreIntegrationTests,
)

from langchain_infinispan import InfinispanVectorStore

from .conftest import ServerInfo


class TestInfinispanStandard(VectorStoreIntegrationTests):
    @pytest.fixture()
    def vectorstore(
        self, infinispan_server: ServerInfo
    ) -> Generator[VectorStore, None, None]:
        """Yield an empty InfinispanVectorStore backed by a fresh cache."""
        url, user, password = infinispan_server
        embedding = self.get_embeddings()
        dimension = len(embedding.embed_query("dimension probe"))
        cache_name = f"test_standard_{uuid.uuid4().hex[:8]}"
        store = InfinispanVectorStore(
            embedding=embedding,
            cache_name=cache_name,
            ispn_url=url,
            ispn_user=user,
            ispn_password=password,
            dimension=dimension,
            verify=False,
        )
        try:
            yield store
        finally:
            try:
                store._client.delete_cache(cache_name)
            except Exception:
                pass
            store.close()

    @property
    def has_get_by_ids(self) -> bool:
        # get_by_ids implemented in PR #7 (merged).
        return True

    @property
    def has_async(self) -> bool:
        # The REST client is synchronous (requests); async methods would only
        # exercise the base thread-pool fallback, so they are not claimed here.
        return False
