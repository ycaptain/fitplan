.PHONY: setup setup-backend setup-frontend backend frontend dev test eval lint clean

setup: setup-backend setup-frontend

setup-backend:
	cd backend && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev]"

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
	cd backend && .venv/bin/ruff check app tests
	cd frontend && pnpm lint

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf backend/.venv frontend/node_modules frontend/.next
