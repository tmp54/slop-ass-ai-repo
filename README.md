# slop-ass-ai-repo
A bunch of slops...

## Backend

FastAPI + SQLite (SQLAlchemy, Alembic), managed with `uv`. Uses a stub AI by default; see `backend/README.md` to enable the real pipeline.

```bash
cd backend
cp .env.example .env          # edit if needed
uv sync
uv run alembic upgrade head   # create the SQLite schema (required before first run)
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
```

API docs at http://localhost:8000/docs. More in `backend/README.md`.

## Frontend

Vue 3 + Vite + TypeScript, Pinia, Vue Router. Needs the backend on `http://localhost:8000` (override with `VITE_API_BASE_URL`).

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm test         # Vitest (VITE_TEST_BACKEND_URL=http://localhost:8000 also runs a live-backend test)
npm run build
```
