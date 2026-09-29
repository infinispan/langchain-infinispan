.PHONY: install dev_install test integration_tests lint format

install:
	uv sync

dev_install:
	uv sync --all-groups

test:
	uv run --group test pytest tests/unit_tests

integration_tests:
	uv run --group test --group test_integration pytest tests/integration_tests

lint:
	uv run --group lint ruff check .

format:
	uv run --group lint ruff format .
	uv run --group lint ruff check --fix .
