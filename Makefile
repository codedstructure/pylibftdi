# Basic development functions for pylibftdi.

# Example:
#   make container && make lint && make test && make build

.PHONY: all
all: container test lint build

.PHONY: container
container:
	docker build -t pylibftdi-dev:latest .

.PHONY: build
build:
	docker run --rm -t -v $$PWD:/app -w /app pylibftdi-dev:latest uv build

.PHONY: test
test:
	docker run --rm -t -v $$PWD:/app -w /app pylibftdi-dev:latest uv run pytest

.PHONY: lint
lint:
	docker run --rm -t -v $$PWD:/app -w /app pylibftdi-dev:latest bash -c 'uv run ruff format --check . && uv run ruff check src tests && uv run mypy src'

.PHONY: format
format:
	docker run --rm -t -v $$PWD:/app -w /app pylibftdi-dev:latest bash -c 'uv run ruff format . && uv run ruff check --fix src tests'

.PHONY: shell
shell:
	# Drop into a shell where e.g. `uv run python -m pylibftdi.examples.list_devices` etc can be run
	docker run --rm -it -v $$PWD:/app -w /app pylibftdi-dev:latest bash

.PHONY: docs
docs:
	uv run --group docs sphinx-build -b html docs docout/html
	uv run python -m webbrowser "file://$(abspath docout/html/index.html)"

.PHONY: clean
clean:
	# Ideally this would remove all relevant dev containers too...
	rm -rf dist/ .venv/ docout/
