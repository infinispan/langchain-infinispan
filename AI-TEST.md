# Testing Instructions

## Test Framework

All tests use **pytest**. The test suite is split into two categories:

| Category         | Location                          | External Services | Naming    |
|------------------|-----------------------------------|-------------------|-----------|
| Unit tests       | `tests/unit_tests/`               | None              | `test_*`  |
| Integration tests| `tests/integration_tests/`        | Infinispan server | `test_*`  |

## Running Tests

All commands run from `libs/infinispan/`:

```bash
# Run unit tests (fast, no external dependencies)
make test

# Run integration tests (requires Docker or Podman)
make integration_tests

# Run a single test file
uv run --group test pytest tests/unit_tests/test_filters.py

# Run a single test method
uv run --group test pytest tests/unit_tests/test_filters.py::test_specific_method

# Run with verbose output
uv run --group test pytest tests/unit_tests -v
```

## Writing Unit Tests

Unit tests live in `tests/unit_tests/` and must not require any external services.

### What to Test
- Import correctness (`test_imports.py`)
- Client request building and response parsing (`test_client.py`)
- Filter translation logic (`test_filters.py`)
- Vector store initialization and parameter handling (`test_vectorstores.py`)

### Patterns
- Use `pytest-mock` for mocking HTTP responses from the Infinispan REST API
- Test edge cases: empty inputs, missing parameters, invalid configurations
- Test all `DistanceStrategy` variants where behavior differs

### Example

```python
def test_vector_store_default_distance_strategy():
    """Default distance strategy should be COSINE."""
    store = InfinispanVectorStore(
        embedding=FakeEmbeddings(),
        cache_name="test",
        ispn_url="http://localhost:11222",
    )
    assert store._similarity == DistanceStrategy.COSINE
```

## Writing Integration Tests

Integration tests live in `tests/integration_tests/` and run against a real Infinispan server.

### Container Management

The test suite auto-manages an Infinispan container via the `conftest.py` fixture. You do not need to start a server manually. The fixture:
1. Detects Docker or Podman
2. Starts a fresh Infinispan container with a unique name
3. Waits for the server to be ready
4. Tears down the container after the session

### Configuration

Environment variables (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `INFINISPAN_IMAGE` | `infinispan/server:15.2` | Container image to run |
| `INFINISPAN_CONTAINER_RUNTIME` | auto-detect | Force Docker or Podman |
| `INFINISPAN_USER` | `admin` | Server user |
| `INFINISPAN_PASSWORD` | `password` | Server password |
| `INFINISPAN_EXTERNAL_URL` | _(unset)_ | Skip container management, use this server |

### What to Test
- End-to-end vector add and similarity search
- All distance strategies (`test_distance_strategies.py`)
- Relevance score normalization (`test_relevance_scores.py`)
- Metadata filtering with various operators
- LangChain standard `VectorStoreIntegrationTests` suite (`test_standard.py`)

### LangChain Standard Tests

The `test_standard.py` file implements LangChain's `VectorStoreIntegrationTests` base class. When updating the vector store interface, ensure these standard tests still pass — they validate compatibility with the broader LangChain ecosystem.

Note: async tests are skipped (`has_async = False`) because the REST client is synchronous.

### Patterns
- Each test should create its own cache (or use a unique cache name) to avoid interference
- Clean up caches after tests when possible
- Use the `vector_store` fixture from `conftest.py` for standard setups

## CI Pipeline

The GitHub Actions CI (`.github/workflows/ci.yml`) runs:
- **Lint + type check + unit tests:** on Python 3.10, 3.11, 3.12, 3.13
- **Integration tests:** on Python 3.12 with Docker

All tests must pass before a PR can be merged.
