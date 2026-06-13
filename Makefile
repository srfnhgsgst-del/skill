.PHONY: install test lint clean build publish

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache/ __pycache__ src/**/__pycache__ tests/__pycache__

build: clean
	python -m build

publish: build
	twine upload dist/*

check: lint test