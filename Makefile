.PHONY: build lint test

build: lint test
	poetry build

lint:
	black --check scru128 tests
	mypy --strict scru128 tests

test:
	python -m unittest -v
