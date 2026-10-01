import logging
import uuid
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.structured_query import FilterDirective
from langchain_core.vectorstores import VectorStore

from langchain_infinispan._filters import translate_filter
from langchain_infinispan._utilities import (
    DEFAULT_CACHE_CONFIG_TEMPLATE,
    DistanceStrategy,
    _proto_file_content,
)
from langchain_infinispan.client import InfinispanClient

logger = logging.getLogger(__name__)

_DEFAULT_PACKAGE = "langchain"
_DEFAULT_ITEM_NAME = "LangChainItem"
_DEFAULT_METADATA_NAME = "LangChainMetadata"
_DEFAULT_CACHE_NAME = "langchain_vectors"


def _serialize_metadata_entry(key: str, value: Any) -> Dict[str, Any]:
    """Serialize a metadata key-value pair with type-aware fields.

    Stores the value in the appropriate typed field so that Infinispan
    can filter on it using the correct column (value, value_int, value_float).
    """
    entry: Dict[str, Any] = {"name": key, "value": str(value)}
    if isinstance(value, int) and not isinstance(value, bool):
        entry["value_int"] = value
    elif isinstance(value, float):
        entry["value_float"] = value
    return entry


def _deserialize_metadata(raw_metadata: Any) -> Dict[str, Any]:
    """Deserialize metadata entries back to a dict, recovering typed values."""
    metadata: Dict[str, Any] = {}
    if not isinstance(raw_metadata, list):
        return metadata
    for entry in raw_metadata:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "")
        if not name:
            continue
        if "value_int" in entry and entry["value_int"] is not None:
            metadata[name] = int(entry["value_int"])
        elif "value_float" in entry and entry["value_float"] is not None:
            metadata[name] = float(entry["value_float"])
        else:
            metadata[name] = entry.get("value", "")
    return metadata


class InfinispanVectorStore(VectorStore):
    """Infinispan vector store.

    Setup:
        Install ``langchain-infinispan`` and have an Infinispan 15+ server running.

        .. code-block:: bash

            pip install -qU langchain-infinispan

    Instantiate:
        .. code-block:: python

            from langchain_infinispan import InfinispanVectorStore
            from langchain_openai import OpenAIEmbeddings

            vector_store = InfinispanVectorStore(
                embedding=OpenAIEmbeddings(),
                cache_name="my_vectors",
                ispn_url="http://localhost:11222",
                ispn_user="admin",
                ispn_password="password",
            )

    Instantiate with Bearer token:
        .. code-block:: python

            vector_store = InfinispanVectorStore(
                embedding=OpenAIEmbeddings(),
                cache_name="my_vectors",
                ispn_url="http://localhost:11222",
                ispn_bearer_token="my-token",
            )

    Instantiate with existing client:
        .. code-block:: python

            from langchain_infinispan import InfinispanVectorStore, InfinispanClient

            client = InfinispanClient(
                url="http://localhost:11222",
                username="admin",
                password="password",
            )
            vector_store = InfinispanVectorStore(
                embedding=OpenAIEmbeddings(),
                cache_name="my_vectors",
                client=client,
            )
    """

    def __init__(
        self,
        embedding: Embeddings,
        *,
        cache_name: str = _DEFAULT_CACHE_NAME,
        client: Optional[InfinispanClient] = None,
        ispn_url: str = "http://localhost:11222",
        ispn_user: Optional[str] = None,
        ispn_password: Optional[str] = None,
        ispn_bearer_token: Optional[str] = None,
        verify: bool = True,
        dimension: Optional[int] = None,
        similarity: DistanceStrategy = DistanceStrategy.COSINE,
        cache_config: Optional[str] = None,
        package_name: str = _DEFAULT_PACKAGE,
        item_name: str = _DEFAULT_ITEM_NAME,
        metadata_name: str = _DEFAULT_METADATA_NAME,
        create_cache: bool = True,
        register_schema: bool = True,
    ):
        self._embedding = embedding
        self._cache_name = cache_name
        self._similarity = similarity
        self._package_name = package_name
        self._dimension = dimension
        self._create_cache = create_cache
        self._register_schema = register_schema
        self._cache_config = cache_config
        self._schema_registered = False

        if dimension is not None:
            self._item_name = f"{item_name}{dimension}"
            self._metadata_name = f"{metadata_name}{dimension}"
        else:
            self._item_name = item_name
            self._metadata_name = metadata_name

        if client is not None:
            self._client = client
        else:
            self._client = InfinispanClient(
                url=ispn_url,
                username=ispn_user,
                password=ispn_password,
                bearer_token=ispn_bearer_token,
                verify=verify,
            )

    @property
    def embeddings(self) -> Optional[Embeddings]:
        return self._embedding

    def _select_relevance_score_fn(self) -> Callable[[float], float]:
        """Map the native Infinispan score to a ``[0, 1]`` relevance score.

        Infinispan returns a Lucene similarity score where higher means more
        similar:

        - ``COSINE``, ``INNER_PRODUCT`` and ``L2`` already fall in ``[0, 1]``,
          so relevance is the identity. ``INNER_PRODUCT`` requires unit-length
          (normalized) vectors; the server rejects non-normalized vectors at
          write time.
        - ``MAX_INNER_PRODUCT`` is unbounded in ``(0, inf)``; it is squashed
          into ``(0, 1)`` with ``s / (1 + s)``, which is monotonic and
          preserves ranking.
        """
        if self._similarity == DistanceStrategy.MAX_INNER_PRODUCT:
            return lambda s: s / (1.0 + s)
        return lambda s: s

    @property
    def entity_type(self) -> str:
        return f"{self._package_name}.{self._item_name}"

    @property
    def metadata_type(self) -> str:
        return f"{self._package_name}.{self._metadata_name}"

    @property
    def schema_name(self) -> str:
        dim_part = f".dimension.{self._dimension}" if self._dimension else ""
        return f"{self._package_name}{dim_part}.proto"

    def _ensure_setup(self, dimension: int) -> None:
        if self._schema_registered:
            return

        if self._dimension is None:
            self._dimension = dimension
            self._item_name = f"{_DEFAULT_ITEM_NAME}{dimension}"
            self._metadata_name = f"{_DEFAULT_METADATA_NAME}{dimension}"

        if self._register_schema:
            proto = _proto_file_content(
                package_name=self._package_name,
                item_name=self._item_name,
                metadata_name=self._metadata_name,
                dimension=self._dimension,
                similarity=self._similarity.value,
            )
            self._client.register_schema(self.schema_name, proto)

        if self._create_cache:
            config = self._cache_config or DEFAULT_CACHE_CONFIG_TEMPLATE.format(
                cache_name=self._cache_name,
                entity_type=self.entity_type,
            )
            self._client.get_or_create_cache(self._cache_name, config)

        self._schema_registered = True

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add texts with embeddings to the vector store.

        Args:
            texts: Texts to add.
            metadatas: Optional metadata dicts for each text.
            ids: Optional IDs for each text.

        Returns:
            List of IDs of the added texts.
        """
        texts_list = list(texts)
        embeddings = self._embedding.embed_documents(texts_list)
        self._ensure_setup(len(embeddings[0]))

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts_list]
        if metadatas is None:
            metadatas = [{} for _ in texts_list]

        for id_, text, emb, meta in zip(ids, texts_list, embeddings, metadatas):
            item = {
                "_type": self.entity_type,
                "id": id_,
                "text": text,
                "embedding": emb,
                "metadata": [_serialize_metadata_entry(k, v) for k, v in meta.items()],
            }
            self._client.put(self._cache_name, id_, item)

        return ids

    def add_embeddings(
        self,
        text_embeddings: Iterable[Tuple[str, List[float]]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[str]:
        """Add pre-computed embeddings with texts to the vector store."""
        pairs = list(text_embeddings)
        texts = [t for t, _ in pairs]
        embeddings = [e for _, e in pairs]
        self._ensure_setup(len(embeddings[0]))

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{} for _ in texts]

        for id_, text, emb, meta in zip(ids, texts, embeddings, metadatas):
            item = {
                "_type": self.entity_type,
                "id": id_,
                "text": text,
                "embedding": emb,
                "metadata": [_serialize_metadata_entry(k, v) for k, v in meta.items()],
            }
            self._client.put(self._cache_name, id_, item)

        return ids

    def delete(
        self,
        ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Optional[bool]:
        """Delete entries by IDs."""
        if ids is None:
            raise ValueError("Please specify IDs to delete.")
        for id_ in ids:
            self._client.delete(self._cache_name, id_)
        return True

    def get_by_ids(self, ids: Sequence[str]) -> List[Document]:
        """Get documents by their IDs.

        Documents are returned in the same order as the requested ``ids``.
        IDs that are not found are skipped, so the result may be shorter than
        ``ids`` (and empty if none are found).

        Args:
            ids: IDs of the documents to retrieve.

        Returns:
            List of Documents for the IDs that were found.
        """
        docs: List[Document] = []
        for id_ in ids:
            raw = self._client.get(self._cache_name, id_)
            if raw is None:
                continue
            docs.append(
                Document(
                    id=id_,
                    page_content=raw.get("text", ""),
                    metadata=_deserialize_metadata(raw.get("metadata", [])),
                )
            )
        return docs

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._client.clear_cache(self._cache_name)

    def _build_vector_query(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], FilterDirective]] = None,
    ) -> str:
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"

        filter_result = translate_filter(filter)
        join_part = ""
        filtering_part = ""
        if filter_result is not None:
            join_part = " " + filter_result.join if filter_result.join else ""
            filtering_part = f" filtering({filter_result.query})"

        return (
            f"select i, score(i) from {self.entity_type} i"
            f"{join_part}"
            f" where i.embedding <-> {vector_str}~{k}"
            f"{filtering_part}"
        )

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], FilterDirective]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to query.

        Args:
            query: Text to search for.
            k: Number of results to return.
            filter: Optional filter — either a dict for simple equality
                matching (e.g. ``{"source": "web"}``) or a langchain-core
                ``FilterDirective`` for complex expressions.

        Returns:
            List of Documents most similar to the query.
        """
        docs_and_scores = self.similarity_search_with_score(
            query, k=k, filter=filter, **kwargs
        )
        return [doc for doc, _ in docs_and_scores]

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], FilterDirective]] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents most similar to query, with scores.

        Args:
            query: Text to search for.
            k: Number of results to return.
            filter: Optional filter — dict or ``FilterDirective``.

        Returns:
            List of (Document, score) tuples.
        """
        embedding = self._embedding.embed_query(query)
        return self.similarity_search_by_vector_with_relevance_scores(
            embedding, k=k, filter=filter, **kwargs
        )

    def similarity_search_by_vector(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], FilterDirective]] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to the given embedding vector."""
        docs_and_scores = self.similarity_search_by_vector_with_relevance_scores(
            embedding, k=k, filter=filter, **kwargs
        )
        return [doc for doc, _ in docs_and_scores]

    def similarity_search_by_vector_with_relevance_scores(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], FilterDirective]] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents most similar to the given embedding, with scores."""
        self._ensure_setup(len(embedding))
        ickle = self._build_vector_query(embedding, k=k, filter=filter)
        hits = self._client.query(self._cache_name, ickle, max_results=k)

        results: List[Tuple[Document, float]] = []
        for hit in hits:
            inner = hit.get("hit", hit) if isinstance(hit, dict) else {}
            # The query projects the whole entity together with score(i), so
            # Infinispan nests the entity under the "*" key and the score under
            # "score()". Fall back to treating `inner` as the entity itself for
            # non-projected responses.
            entity = inner.get("*", inner) if isinstance(inner, dict) else {}
            score = inner.get("score()", 0.0) if isinstance(inner, dict) else 0.0

            text = entity.get("text", "")
            metadata = _deserialize_metadata(entity.get("metadata", []))

            doc = Document(id=entity.get("id"), page_content=text, metadata=metadata)
            results.append((doc, float(score)))

        return results

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> "InfinispanVectorStore":
        """Create an InfinispanVectorStore from a list of texts.

        Args:
            texts: Texts to add.
            embedding: Embedding function.
            metadatas: Optional metadata for each text.
            **kwargs: Additional arguments passed to the constructor.

        Returns:
            A new InfinispanVectorStore instance.
        """
        store = cls(embedding=embedding, **kwargs)
        store.add_texts(texts, metadatas=metadatas)
        return store

    @classmethod
    def from_documents(
        cls,
        documents: List[Document],
        embedding: Embeddings,
        **kwargs: Any,
    ) -> "InfinispanVectorStore":
        """Create an InfinispanVectorStore from a list of Documents.

        Args:
            documents: Documents to add.
            embedding: Embedding function.
            **kwargs: Additional arguments passed to the constructor.

        Returns:
            A new InfinispanVectorStore instance.
        """
        store = cls(embedding=embedding, **kwargs)
        store.add_documents(documents)
        return store

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._client.close()
