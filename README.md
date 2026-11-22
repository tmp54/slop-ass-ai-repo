# slop-ass-ai-repo
A bunch of slops...

## Frontend

Vue 3 + Vite + TypeScript, Pinia, Vue Router. Needs the backend on `http://localhost:8000` (override with `VITE_API_BASE_URL`).

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm test         # Vitest (VITE_TEST_BACKEND_URL=http://localhost:8000 also runs a live-backend test)
npm run build
```
