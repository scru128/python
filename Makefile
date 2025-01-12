.PHONY: build lint test

build: lint test
	poetry build

lint:
	poetry run black --check scru128 tests
	poetry run mypy --strict scru128 tests

test:
	poetry run python -m unittest -v
