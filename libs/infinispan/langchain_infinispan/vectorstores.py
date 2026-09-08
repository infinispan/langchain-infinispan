import json
import logging
import uuid
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

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
_DEFAULT_DISTANCE = 3


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
        distance: int = _DEFAULT_DISTANCE,
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
        self._distance = distance
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
            metadata_entries = [
                {"name": k, "value": str(v)} for k, v in meta.items()
            ]
            item = {
                "_type": self.entity_type,
                "id": id_,
                "text": text,
                "embedding": emb,
                "metadata": metadata_entries,
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
            metadata_entries = [
                {"name": k, "value": str(v)} for k, v in meta.items()
            ]
            item = {
                "_type": self.entity_type,
                "id": id_,
                "text": text,
                "embedding": emb,
                "metadata": metadata_entries,
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

    def clear(self) -> None:
        """Clear all entries from the cache."""
        self._client.clear_cache(self._cache_name)

    def _build_vector_query(
        self,
        embedding: List[float],
        k: int = 4,
        filter: Optional[str] = None,
    ) -> str:
        vector_str = "[" + ",".join(str(v) for v in embedding) + "]"
        query = (
            f"select i, score(i) from {self.entity_type} i "
            f"where i.embedding <-> {vector_str}~{self._distance}"
        )
        if filter:
            query += f" filtering({filter})"
        return query

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Return documents most similar to query.

        Args:
            query: Text to search for.
            k: Number of results to return.
            filter: Optional Ickle query filter expression.

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
        filter: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents most similar to query, with scores.

        Args:
            query: Text to search for.
            k: Number of results to return.
            filter: Optional Ickle query filter expression.

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
        filter: Optional[str] = None,
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
        filter: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Tuple[Document, float]]:
        """Return documents most similar to the given embedding, with scores."""
        self._ensure_setup(len(embedding))
        ickle = self._build_vector_query(embedding, k=k, filter=filter)
        hits = self._client.query(self._cache_name, ickle, max_results=k)

        results: List[Tuple[Document, float]] = []
        for hit in hits:
            hit_data = hit.get("hit", hit)
            score = hit.get("score", 0.0) if isinstance(hit, dict) else 0.0

            text = hit_data.get("text", "")
            metadata: Dict[str, Any] = {}

            raw_metadata = hit_data.get("metadata", [])
            if isinstance(raw_metadata, list):
                for entry in raw_metadata:
                    if isinstance(entry, dict):
                        name = entry.get("name", "")
                        value = entry.get("value", "")
                        if name:
                            metadata[name] = value

            doc = Document(page_content=text, metadata=metadata)
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
