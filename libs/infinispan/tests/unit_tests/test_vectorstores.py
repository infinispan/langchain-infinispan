from typing import List
from unittest.mock import MagicMock

import pytest
from langchain_core.embeddings import Embeddings

from langchain_infinispan import InfinispanVectorStore
from langchain_infinispan._utilities import DistanceStrategy


class FakeEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[1.0, 2.0, 3.0] for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return [1.0, 2.0, 3.0]


@pytest.fixture
def fake_embeddings() -> FakeEmbeddings:
    return FakeEmbeddings()


def test_constructor_defaults(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        create_cache=False,
        register_schema=False,
    )
    assert store.embeddings is fake_embeddings
    assert store._cache_name == "langchain_vectors"
    assert store._similarity == DistanceStrategy.COSINE


def test_constructor_with_client(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        cache_name="test_cache",
        create_cache=False,
        register_schema=False,
    )
    assert store._client is client
    assert store._cache_name == "test_cache"


def test_entity_type_without_dimension(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        create_cache=False,
        register_schema=False,
    )
    assert store.entity_type == "langchain.LangChainItem"


def test_entity_type_with_dimension(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=1536,
        create_cache=False,
        register_schema=False,
    )
    assert store.entity_type == "langchain.LangChainItem1536"
    assert store.metadata_type == "langchain.LangChainMetadata1536"


def test_schema_name(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=384,
        create_cache=False,
        register_schema=False,
    )
    assert store.schema_name == "langchain.dimension.384.proto"


def test_build_vector_query(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    query = store._build_vector_query([1.0, 2.0, 3.0], k=4)
    assert "select i, score(i) from langchain.LangChainItem3 i" in query
    assert "i.embedding <-> [1.0,2.0,3.0]~4" in query


def test_build_vector_query_k_drives_knn_count(
    fake_embeddings: FakeEmbeddings,
) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    query = store._build_vector_query([1.0, 2.0, 3.0], k=10)
    assert "i.embedding <-> [1.0,2.0,3.0]~10" in query


def test_build_vector_query_with_dict_filter(fake_embeddings: FakeEmbeddings) -> None:
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    query = store._build_vector_query(
        [1.0, 2.0, 3.0], k=4, filter={"source": "web"}
    )
    assert "join i.metadata m0" in query
    assert "filtering(m0.name='source' and m0.value = 'web')" in query


def test_build_vector_query_with_structured_filter(
    fake_embeddings: FakeEmbeddings,
) -> None:
    from langchain_core.structured_query import Comparator, Comparison

    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    f = Comparison(comparator=Comparator.GT, attribute="price", value=10.0)
    query = store._build_vector_query([1.0, 2.0, 3.0], k=4, filter=f)
    assert "join i.metadata m0" in query
    assert "filtering(m0.name='price' and m0.value_float > 10.0)" in query


def test_add_texts_generates_ids(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    client.cache_exists.return_value = True
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        create_cache=False,
        register_schema=False,
    )
    store._schema_registered = True

    ids = store.add_texts(["hello", "world"])
    assert len(ids) == 2
    assert client.put.call_count == 2


def test_add_texts_with_string_metadata(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        create_cache=False,
        register_schema=False,
    )
    store._schema_registered = True

    ids = store.add_texts(
        ["hello"],
        metadatas=[{"source": "test"}],
        ids=["id1"],
    )
    assert ids == ["id1"]
    call_args = client.put.call_args
    item = call_args[0][2]
    assert item["text"] == "hello"
    assert item["metadata"] == [{"name": "source", "value": "test"}]


def test_add_texts_with_typed_metadata(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        create_cache=False,
        register_schema=False,
    )
    store._schema_registered = True

    store.add_texts(
        ["hello"],
        metadatas=[{"source": "test", "page": 42, "score": 0.95}],
        ids=["id1"],
    )
    call_args = client.put.call_args
    item = call_args[0][2]
    meta = item["metadata"]
    source_entry = next(e for e in meta if e["name"] == "source")
    page_entry = next(e for e in meta if e["name"] == "page")
    score_entry = next(e for e in meta if e["name"] == "score")
    assert source_entry == {"name": "source", "value": "test"}
    assert page_entry == {"name": "page", "value": "42", "value_int": 42}
    assert score_entry == {"name": "score", "value": "0.95", "value_float": 0.95}


def test_delete(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        create_cache=False,
        register_schema=False,
    )
    result = store.delete(ids=["id1", "id2"])
    assert result is True
    assert client.delete.call_count == 2


def test_delete_no_ids_raises(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        create_cache=False,
        register_schema=False,
    )
    with pytest.raises(ValueError, match="specify IDs"):
        store.delete()


def test_similarity_search_by_vector(fake_embeddings: FakeEmbeddings) -> None:
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    client.query.return_value = [
        {
            "hit": {
                "text": "hello world",
                "metadata": [{"name": "source", "value": "test"}],
            },
            "score": 0.95,
        }
    ]
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    store._schema_registered = True

    results = store.similarity_search_by_vector_with_relevance_scores(
        [1.0, 2.0, 3.0], k=1
    )
    assert len(results) == 1
    doc, score = results[0]
    assert doc.page_content == "hello world"
    assert doc.metadata == {"source": "test"}
    assert score == 0.95


def test_similarity_search_propagates_k_to_query(
    fake_embeddings: FakeEmbeddings,
) -> None:
    """End-to-end: k must reach both the Ickle kNN count and max_results."""
    from langchain_infinispan.client import InfinispanClient

    client = MagicMock(spec=InfinispanClient)
    client.query.return_value = []
    store = InfinispanVectorStore(
        embedding=fake_embeddings,
        client=client,
        dimension=3,
        create_cache=False,
        register_schema=False,
    )
    store._schema_registered = True

    store.similarity_search_by_vector_with_relevance_scores([1.0, 2.0, 3.0], k=7)

    args, kwargs = client.query.call_args
    ickle = args[1]
    assert "~7" in ickle
    assert kwargs["max_results"] == 7
