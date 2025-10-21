.PHONY: test lint run

run:
python -m government.orchestrator

lint:
ruff check .
ruff format --check .

test:
pytest -q
