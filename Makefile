.PHONY: help db-up db-down install init-db seed run demo serve test clean reset

PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

help:
	@echo "Targets:"
	@echo "  make install   - create .venv and install the package + deps"
	@echo "  make db-up      - start Postgres (docker compose)"
	@echo "  make db-down    - stop Postgres"
	@echo "  make init-db    - apply database migrations"
	@echo "  make seed       - generate + ingest synthetic e-commerce data"
	@echo "  make run        - run the full decisioning pipeline once"
	@echo "  make demo       - db-up + init-db + seed + run (one command)"
	@echo "  make serve      - start the API + dashboard at http://localhost:8000"
	@echo "  make test       - run the test suite"
	@echo "  make reset      - drop + recreate schema, then reseed"

.venv:
	python3 -m venv .venv

install: .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

db-up:
	docker compose up -d
	@echo "Waiting for Postgres to be healthy..."
	@until docker compose exec -T db pg_isready -U cac -d cac >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres is ready on localhost:55432"

db-down:
	docker compose down

init-db:
	$(PY) -m app.cli init-db

seed:
	$(PY) -m app.cli seed

run:
	$(PY) -m app.cli run

demo: db-up init-db seed run
	@echo ""
	@echo "Demo data is ready. Now run:  make serve"

serve:
	$(PY) -m app.cli serve

test:
	$(PY) -m pytest

reset:
	$(PY) -m app.cli init-db --reset
	$(PY) -m app.cli seed

clean:
	rm -rf .venv .pytest_cache **/__pycache__ *.egg-info
