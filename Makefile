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
	docker run -t -v $$PWD:/app -w /app pylibftdi-dev:latest poetry build

.PHONY: test
test:
	docker run -t -v $$PWD:/app -w /app pylibftdi-dev:latest bash -c 'poetry install && poetry run pytest'

.PHONY: lint
lint:
	docker run -t -v $$PWD:/app -w /app pylibftdi-dev:latest bash -c 'poetry install && (poetry run black --check .; poetry run ruff src tests; poetry run mypy src)'

.PHONY: shell
shell:
	# Drop into a poetry shell where e.g. `python3 -m pylibftdi.examples.list_devices` etc can be run
	docker run -it -v $$PWD:/app -w /app pylibftdi-dev:latest bash -ic 'poetry install && poetry shell'

.PHONY: clean
clean:
	# Ideally this would remove all relevant dev containers too...
	rm -rf dist/ .venv/
