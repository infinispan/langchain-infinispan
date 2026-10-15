# Configuration Change Instructions

Adding or modifying configuration options in langchain-infinispan requires changes across multiple files. Missing a step will cause broken initialization, missing documentation, or silent loss of user-specified settings.

## Architecture Overview

Configuration flows through constructor parameters into the client and vector store:

```
User kwargs  →  InfinispanVectorStore.__init__()  →  InfinispanClient
                                                  →  DistanceStrategy
                                                  →  Cache/Schema configuration
```

Key files:
- `langchain_infinispan/vectorstores.py` — vector store constructor and configuration
- `langchain_infinispan/client.py` — REST client constructor and connection settings
- `langchain_infinispan/_utilities.py` — DistanceStrategy enum, Protobuf schema builder, cache config template

## Checklist: Adding a New Configuration Parameter

### 1. Add the Constructor Parameter

**File:** `vectorstores.py` (for vector store config) or `client.py` (for client/connection config)

Add the parameter to `__init__()` with a type hint and default value. Store it as an instance attribute.

### 2. Wire It Through

If the parameter affects client behavior, ensure it is passed from `InfinispanVectorStore` to `InfinispanClient` when the store creates its own client internally.

### 3. Update the Protobuf Schema or Cache Config (if applicable)

**File:** `_utilities.py`

- If the parameter affects how vectors are stored (dimension, distance, etc.), update `_build_proto_schema()`.
- If the parameter affects cache configuration (indexing, storage, etc.), update the cache config template.

### 4. Add Unit Tests

**File:** `tests/unit_tests/test_vectorstores.py` or `tests/unit_tests/test_client.py`

Test that the parameter is accepted, stored, and has the correct default value.

### 5. Add Integration Tests (if applicable)

**File:** `tests/integration_tests/test_vectorstores.py`

If the parameter changes runtime behavior, add an integration test that exercises it against a real Infinispan server.

### 6. Update Documentation

- Update the package `README.md` (`libs/infinispan/README.md`) with usage examples.
- Update AsciiDoc docs in `documentation/asciidoc/` if the parameter is user-facing.

### 7. Update `__init__.py` Exports (if adding a new public type)

**File:** `langchain_infinispan/__init__.py`

If the parameter introduces a new enum or configuration class, add it to `__all__` and the module exports.

## Common Mistakes

- **Forgetting to pass the parameter to the client** — the vector store accepts it but nothing changes
- **Not providing a default value** — breaks existing users who don't pass the new parameter
- **Not updating the cache config template** — Infinispan creates a cache without the intended setting
- **Not testing with both auth modes** — Digest and Bearer token authentication may behave differently
- **Changing DistanceStrategy values** — these map to Infinispan index configuration; renaming breaks existing caches
