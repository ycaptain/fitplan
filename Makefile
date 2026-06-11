.PHONY: setup setup-backend setup-frontend backend frontend dev test eval lint clean

# Override with: make setup-backend PYTHON=/path/to/python3.11
# If unset, auto-detect the first available Python >= 3.11.
PYTHON ?= $(shell \
	for p in python3.13 python3.12 python3.11; do \
		command -v $$p >/dev/null 2>&1 && { echo $$p; exit 0; }; \
	done; \
	command -v python3 >/dev/null 2>&1 && \
		python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' \
		2>/dev/null && echo python3 || echo MISSING)

setup: setup-backend setup-frontend

setup-backend:
	@if [ "$(PYTHON)" = "MISSING" ]; then \
		echo "Error: Python >= 3.11 not found on PATH."; \
		echo "  macOS:  brew install python@3.12"; \
		echo "  pyenv:  pyenv install 3.12.7 && pyenv shell 3.12.7"; \
		echo "  Or:     make setup-backend PYTHON=/path/to/python3.11"; \
		exit 1; \
	fi
	@echo "Using $$($(PYTHON) -V) at $$(command -v $(PYTHON))"
	cd backend && $(PYTHON) -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev]"

setup-frontend:
	cd frontend && pnpm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && pnpm dev

dev:
	@echo "Open two terminals:"
	@echo "  Terminal 1:  make backend"
	@echo "  Terminal 2:  make frontend"

test:
	cd backend && .venv/bin/pytest -v

eval:
	cd backend && .venv/bin/python ../scripts/eval/run_eval.py

lint:
	cd backend && .venv/bin/ruff check app tests ../scripts
	cd frontend && pnpm lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf backend/.venv frontend/node_modules frontend/.next
