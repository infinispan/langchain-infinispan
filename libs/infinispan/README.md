# langchain-infinispan

An integration package connecting [Infinispan](https://infinispan.org/) and [LangChain](https://www.langchain.com/).

## Installation

```bash
pip install langchain-infinispan
```

## Usage

```python
from langchain_infinispan import InfinispanVectorStore
from langchain_openai import OpenAIEmbeddings

vector_store = InfinispanVectorStore(
    embedding=OpenAIEmbeddings(),
    cache_name="my_vectors",
    ispn_url="http://localhost:11222",
    ispn_user="admin",
    ispn_password="password",
)

# Add documents
vector_store.add_texts(
    ["Hello world", "Infinispan is fast"],
    metadatas=[{"source": "greeting"}, {"source": "fact"}],
)

# Search
results = vector_store.similarity_search("hello", k=2)
```

### With Bearer token authentication

```python
vector_store = InfinispanVectorStore(
    embedding=OpenAIEmbeddings(),
    cache_name="my_vectors",
    ispn_url="http://localhost:11222",
    ispn_bearer_token="my-token",
)
```

### With pre-built client

```python
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
```

### Distance strategies

Pass `similarity=DistanceStrategy.<X>` to choose the vector similarity function
(default `COSINE`):

| `DistanceStrategy` | Notes |
|---|---|
| `COSINE` | Default. |
| `L2` | Euclidean (squared L2) distance. |
| `INNER_PRODUCT` | **Requires unit-length (normalized) vectors** — the server rejects non-normalized vectors at write time. |
| `MAX_INNER_PRODUCT` | Allows non-normalized vectors. |

Relevance scores from `similarity_search_with_relevance_scores` are normalized
to `[0, 1]` for all strategies.

## Requirements

- Infinispan 15+ with vector search support
- Python 3.10+

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management.

```bash
cd libs/infinispan
make dev_install        # uv sync --all-groups
make test               # unit tests
make integration_tests  # requires a running Infinispan 15+ server
```

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for full setup, prerequisites, and
how to run each test suite.
