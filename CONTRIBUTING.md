# Contributing to langchain-infinispan

Thanks for your interest in contributing! This guide explains how to set up your
environment so you can run the test suites and iterate reliably. It follows the
current [LangChain contributing conventions](https://docs.langchain.com/oss/python/contributing/code),
which use [`uv`](https://docs.astral.sh/uv/) for dependency management.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (Python package/dependency manager)
- [`make`](https://www.gnu.org/software/make/)
- [`git`](https://git-scm.com/)
- A container runtime — [Docker](https://docs.docker.com/get-docker/) or
  [Podman](https://podman.io/) — **only required for the integration tests**,
  which start a throwaway Infinispan server in a container. Unit tests do not
  need it.

Install `uv` (any one of these):

```bash
# Standalone installer (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via pipx
pipx install uv

# or via Homebrew
brew install uv
```

`uv` manages the Python interpreter for you. If you don't have a compatible
Python (the project requires `>=3.10,<4.0`), let `uv` install one:

```bash
uv python install 3.12
```

## Setup

All package sources live under `libs/infinispan/`. Work from there:

```bash
cd libs/infinispan
```

Create the virtual environment and install every dependency group
(runtime + test + lint + typing) from the pinned lockfile:

```bash
make dev_install
# equivalent to: uv sync --all-groups
```

`uv sync` reads `uv.lock`, so every contributor gets the exact same, reproducible
set of dependencies. The lockfile **is committed** — do not delete it.

## Running the test suites

### Unit tests

Unit tests are fast, hermetic, and run without any external services. Run them on
every change:

```bash
make test
# equivalent to: uv run --group test pytest tests/unit_tests
```

### Integration tests

Integration tests exercise the client and query layer against a real
**Infinispan 15+** server with vector search support. Run them when you touch
the client, query, or serialization code.

You do **not** need to start a server yourself. The test suite starts a fresh
Infinispan container before the session and stops it afterwards, using a
dedicated container so it never depends on — or interferes with — any server
already running on your machine. This requires a container runtime (Docker or
Podman); see [Prerequisites](#prerequisites).

```bash
make integration_tests
# equivalent to:
#   uv run --group test --group test_integration pytest tests/integration_tests
```

This runs both LangChain's standard `VectorStoreIntegrationTests` suite and the
package's own integration tests. The suite's async tests are skipped
(`has_async=False`) because the REST client is synchronous.

#### Configuration

All of the following are optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `INFINISPAN_IMAGE` | `infinispan/server:15.2` | Container image to run. |
| `INFINISPAN_CONTAINER_RUNTIME` | auto-detect (Docker, then Podman) | Force a specific runtime. |
| `INFINISPAN_USER` | `admin` | Server user. |
| `INFINISPAN_PASSWORD` | `password` | Server password. |
| `INFINISPAN_EXTERNAL_URL` | _(unset)_ | If set, the suite skips container management and runs against this already-running server instead (e.g. a CI service container). |

Examples:

```bash
# Use a different Infinispan image
INFINISPAN_IMAGE=infinispan/server:16.2 make integration_tests

# Force Podman
INFINISPAN_CONTAINER_RUNTIME=podman make integration_tests

# Run against an already-running server, don't manage a container
INFINISPAN_EXTERNAL_URL=http://localhost:11222 make integration_tests
```

## Linting, formatting, and typing

```bash
make lint     # ruff check .
make format   # ruff format . && ruff check --fix .

# type checking
uv run --group typing mypy langchain_infinispan
```

## Managing dependencies

- **Add a runtime dependency:** `uv add <package>` (updates `pyproject.toml` and
  `uv.lock`).
- **Add a dev/test dependency:** `uv add --group test <package>` (or `lint` /
  `typing`).
- **Refresh the lockfile after editing `pyproject.toml` by hand:** `uv lock`.

Always commit the resulting `uv.lock` change alongside your `pyproject.toml`
change so the environment stays reproducible for everyone.

## Before opening a PR

Make sure the following pass locally:

```bash
make lint
make test
uv run --group typing mypy langchain_infinispan
```

Running the integration tests as well is appreciated — they only require a
container runtime (Docker or Podman) and manage the Infinispan server for you:

```bash
make integration_tests
```
