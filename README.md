# AI Real Estate Showing Assistant

A starter codebase for an AI assistant that helps real estate agents analyze properties, save reports, and ask follow-up questions against a verified property profile.

## What is included
- FastAPI backend
- Multi-source property engine scaffold
- Verified profile normalizer
- Chat, report, document, and auth endpoints
- Next.js frontend
- Responsive property dashboard
- Local demo mode that runs without third-party API keys
- Docker Compose
- Project docs folder

## MVP goals
- Accept property input by address or listing URL
- Produce a verified property profile
- Show AI-generated analysis clearly labeled as analysis
- Save property history and reports
- Support follow-up chat tied to property context

## Local setup

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Open
- Frontend: http://localhost:3000
- Backend: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

## Notes
- This starter uses local deterministic demo engines so it works out of the box.
- External APIs can be added later by swapping connector implementations.
- Verified facts and AI analysis are separated by design.
