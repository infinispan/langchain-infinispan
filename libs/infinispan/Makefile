.PHONY: install dev_install test integration_tests lint format

install:
	poetry install

dev_install:
	poetry install --with test,lint,typing

test:
	poetry run pytest tests/unit_tests

integration_tests:
	poetry run pytest tests/integration_tests

lint:
	poetry run ruff check .

format:
	poetry run ruff format .
	poetry run ruff check --fix .
