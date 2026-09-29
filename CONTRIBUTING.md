# Contributing to langchain-infinispan

Thanks for your interest in contributing! This guide explains how to set up your
environment so you can run the test suites and iterate reliably. It follows the
current [LangChain contributing conventions](https://docs.langchain.com/oss/python/contributing/code),
which use [`uv`](https://docs.astral.sh/uv/) for dependency management.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) (Python package/dependency manager)
- [`make`](https://www.gnu.org/software/make/)
- [`git`](https://git-scm.com/)

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

Integration tests require a running **Infinispan 15+** server with vector search
support. They are not run in the default loop; run them when you touch the
client or query layer.

Start a server (Docker):

```bash
docker run -it --rm -p 11222:11222 \
  -e USER=admin -e PASS=password \
  infinispan/server:latest
```

Then point the tests at it and run:

```bash
export INFINISPAN_URL=http://localhost:11222
export INFINISPAN_USER=admin
export INFINISPAN_PASSWORD=password

make integration_tests
# equivalent to:
#   uv run --group test --group test_integration pytest tests/integration_tests
```

Defaults if the env vars are unset: `http://localhost:11222`, `admin`,
`password`.

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

Integration tests are appreciated when you have an Infinispan server available.
