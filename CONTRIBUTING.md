Guidelines for contributing to langchain-infinispan
====

Contributions from the community are essential in keeping langchain-infinispan strong and successful.

This guide focuses on how to contribute back to langchain-infinispan using GitHub pull requests.

## Legal

All original contributions to langchain-infinispan are licensed under the
[ASL - Apache License](https://www.apache.org/licenses/LICENSE-2.0),
version 2.0 or later.

All contributions are subject to the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

## Getting Started

If you are just getting started with Git, GitHub and/or contributing to langchain-infinispan there are a
few prerequisite steps:

* Make sure you have a [GitHub account](https://github.com/signup/free)
* [Fork](https://help.github.com/articles/fork-a-repo/) the
  langchain-infinispan [repository](https://github.com/infinispan/langchain-infinispan).
  As discussed in the linked page, this also includes:
    * [Setting](https://help.github.com/articles/set-up-git) up your local git install
    * Cloning your fork

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

## Create a topic branch

Create a "topic" branch on which you will work. The convention is to name the branch
using a short description of the change. Assuming you will be working from the main branch:

```shell
git checkout -b my-feature origin/main
```

## Code

Code away...

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
Infinispan container before the session and stops it afterwards.

```bash
make integration_tests
```

#### Configuration

All of the following are optional environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `INFINISPAN_IMAGE` | `infinispan/server:15.2` | Container image to run. |
| `INFINISPAN_CONTAINER_RUNTIME` | auto-detect (Docker, then Podman) | Force a specific runtime. |
| `INFINISPAN_USER` | `admin` | Server user. |
| `INFINISPAN_PASSWORD` | `password` | Server password. |
| `INFINISPAN_EXTERNAL_URL` | _(unset)_ | If set, the suite skips container management and runs against this already-running server instead. |

## Linting, formatting, and typing

```bash
make lint     # ruff check .
make format   # ruff format . && ruff check --fix .

# type checking
uv run --group typing mypy langchain_infinispan
```

## Commit

* Make commits of logical units.
* Be sure to write a clear, concise commit message.
* Avoid formatting changes to existing code as much as possible: they make the intent of your patch less clear.
* Make sure you have added the necessary tests for your changes.
* Run _all_ the tests to assure nothing else was accidentally broken.

_Prior to committing, if you want to pull in the latest upstream changes,
please use rebasing rather than merging. Merging creates
"merge commits" that muck up the project timeline._

Add the original repository as a remote repository called upstream:

```shell
git remote add upstream git@github.com:infinispan/langchain-infinispan.git
```

If you want to rebase your branch on top of the main branch:

```shell
git pull --rebase upstream main
```

## Use of Generative AI

Generative AI tools may be used to assist in writing code, tests, or documentation, provided that you fully understand every change you submit. The goal is to keep the codebase consistent and high-quality while respecting reviewers' limited time.

If you use generative AI to assist with your contribution, all the following are required:

* You understand the change. You must be able to explain what your code does and why. Submitting AI-generated code you do not understand is not acceptable.
* You engage with review feedback. You are expected to respond to questions and comments from reviewers. If you use AI to help draft responses, you must edit and proofread them to ensure they are accurate and address the reviewer's point.
* You can revise the code yourself. If a reviewer requests changes, you are responsible for addressing them, even if your AI tool is unable to produce a suitable fix.
* You disclose AI agents usage. Include a note in the PR description indicating the usage of AI agents for generating complete solutions from a prompt (i.e. you do not need to mention a simple AI autocomplete). This helps reviewers calibrate their review.
* You ensure licensing compliance. All generated code must be released under the Apache License, Version 2.0, the same license as this project. You are responsible for verifying that the tools you use do not introduce additional licensing restrictions.

## Submit

* Push your changes to a topic branch in your fork of the repository.
* Initiate a [pull request](http://help.github.com/send-pull-requests/).

## Before opening a PR

Make sure the following pass locally:

```bash
make lint
make test
uv run --group typing mypy langchain_infinispan
```

Running the integration tests as well is appreciated:

```bash
make integration_tests
```

## Contributing

For contributing guidelines please refer to this document. All contributions are subject
to [Developer Certificate of Origin (DCO)](https://developercertificate.org/).

*The Infinispan project team*
