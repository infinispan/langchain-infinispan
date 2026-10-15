# Coding Instructions

## Tech Stack
* **Python Version:** >=3.10, <4.0
* **Build Tool:** Hatchling
* **Dependency Manager:** uv (with pinned lockfile)
* **Key Frameworks:** LangChain Core, Requests, pytest

## Project Architecture

```
langchain-infinispan/
├── libs/infinispan/                 # The Python package
│   ├── pyproject.toml               # Package metadata, dependencies, tool config
│   ├── Makefile                     # Dev commands (install, test, lint, format)
│   ├── langchain_infinispan/        # Package source
│   │   ├── __init__.py              # Public exports: InfinispanVectorStore, InfinispanClient, DistanceStrategy, __version__
│   │   ├── vectorstores.py          # InfinispanVectorStore(VectorStore) — add_texts, similarity_search, filtering, scoring
│   │   ├── client.py                # InfinispanClient — REST client (Digest/Bearer auth, cache/schema CRUD, query)
│   │   ├── _utilities.py            # DistanceStrategy enum, proto schema builder, cache config template, user_agent()
│   │   └── _filters.py             # Ickle query filter translator (dict & FilterDirective → Ickle WHERE/JOIN)
│   └── tests/
│       ├── unit_tests/              # Fast, hermetic tests (no external services)
│       └── integration_tests/       # Tests against a real Infinispan server (auto-managed container)
├── documentation/asciidoc/          # AsciiDoc user documentation
├── .github/workflows/ci.yml        # CI: lint/type/unit on py3.10-3.13, integration on py3.12
├── CONTRIBUTING.md                  # Contributing guide
└── README.md                        # Repository overview
```

## Public API

The package exports four symbols from `langchain_infinispan/__init__.py`:
- **`InfinispanVectorStore`** — the LangChain VectorStore implementation
- **`InfinispanClient`** — low-level REST client for Infinispan
- **`DistanceStrategy`** — enum for vector similarity functions (COSINE, L2, INNER_PRODUCT, MAX_INNER_PRODUCT)
- **`__version__`** — package version string

Any change to these exports is a public API change and must be handled with care.

## Common Build Commands

All commands run from `libs/infinispan/`:

* **Install all dependencies:** `make dev_install` (equivalent to `uv sync --all-groups`)
* **Run unit tests:** `make test`
* **Run integration tests:** `make integration_tests` (requires Docker or Podman)
* **Lint:** `make lint` (ruff check)
* **Format:** `make format` (ruff format + ruff check --fix)
* **Type check:** `uv run --group typing mypy langchain_infinispan`

## Development Standards

* **Style:** Follow ruff rules (pycodestyle, pyflakes, isort). Run `make format` before committing.
* **Type hints:** Required for all function signatures (`disallow_untyped_defs = True` in mypy config).
* **Docstrings:** Required for public API classes and methods. Optional for internal/private code.
* **Testing:** Unit tests for all new logic. Integration tests for anything touching the Infinispan REST API.
* **Private modules:** Prefix with underscore (`_utilities.py`, `_filters.py`) for internal-only modules.
* **Dependencies:** Keep minimal. Only `langchain-core` and `requests` at runtime.
* **Lockfile:** Always commit `uv.lock` changes alongside `pyproject.toml` changes.

## Infinispan REST API Patterns

The client communicates with Infinispan via its REST API (typically at port 11222). Key patterns:
- **Authentication:** Digest (username/password) or Bearer token
- **Cache management:** Create/delete caches, check existence
- **Schema management:** Register/update Protobuf schemas for vector storage
- **Vector queries:** Ickle query language for similarity search with optional metadata filtering
- **Server requirement:** Infinispan 15+ with vector search support

## Related Projects

* **Infinispan:** The Infinispan server source code is in ../infinispan
* **Infinispan Console:** The web console source code is in ../infinispan-console
* **Simple Tutorials:** Infinispan tutorials at ../infinispan-simple-tutorials
