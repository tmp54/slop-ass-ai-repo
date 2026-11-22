# Decisions Log

## 2026-09-21 — Initial code steward
**What:** tmp54 is the initial code steward for the team.
**Why:** try try see

## 2026-11-22 — Prototype software stack
**What:** Vue 3 (Vite, TypeScript, Pinia, Vue Router) frontend; Python FastAPI backend with Pydantic; SQLite via SQLAlchemy and Alembic; Anthropic SDK for the AI pipeline; `uv`, pytest and Vitest for tooling and tests.
**Why:** Python suits the LLM work, FastAPI generates an OpenAPI spec that keeps the frontend and backend contract in sync, and SQLite needs no separate server. The frontend never accesses the database directly; it only calls the backend API.
**AI involvement:** Claude suggested this stack and the gaps it did not cover. The team reviewed and accepted it.

## 2026-11-22 — Prototype scope: identity, notification, files, config, deployment
**What:**
- Identity: users pick a role (sender or receiver). No real authentication.
- Notification: the frontend polls for handoff status. No websockets.
- File uploads: skipped. The prototype is text-first.
- Secrets and config: `.env`, never committed.
- Evaluation data: log timestamps and clarification-question counts from the start.
- Deployment: deferred. Local app first.
**Why:** Keeps the prototype small while still supporting the evaluation metrics (time to understand, number of clarification questions) in the Week 11-13 plan.
**AI involvement:** Claude proposed the options; the team chose them.

## 2026-11-22 — GitHub integration: fetch PR/issue content
**What:** The backend fetches PR and issue title, description and comments through the GitHub REST API using a read-only token in `.env`, and feeds that text to the AI pipeline. Diffs are truncated or limited to file names. If a fetch fails, the link is stored as a plain reference and listed as a gap ("content not fetched"). Fetched text is treated as data to summarize, never as instructions to the AI.
**Why:** The AI drafts a more accurate brief from the real PR/issue content and the sender has less to explain, at the cost of one extra backend function. Storing links only would leave the AI with less context; reading full diffs is more work than the prototype needs.
**AI involvement:** Claude explained the options and recommended this one; the team accepted it.
