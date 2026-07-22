.PHONY: backend frontend seed

backend:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

seed:
	cd backend && source .venv/bin/activate && python -m app.seed
