# Handoff backend

```bash
cd backend
cp .env.example .env          # edit if needed
uv sync
uv run alembic upgrade head   # create the SQLite schema
uv run uvicorn app.main:app --reload --port 8000
uv run pytest                 # tests
```

Docs: `docs/state-machine.md`, `docs/api-contract.md`. OpenAPI UI at http://localhost:8000/docs.
Schema diagram: tables `handoffs`, `brief_versions`, `transitions`, `restatements`, `questions`, `confirmations` (see `app/models.py`).

## Enabling the real AI pipeline

The default is a canned stub (`app.ai.stub:StubPipeline`). To use the Anthropic-backed pipeline, set in `.env`:

```
AI_PIPELINE=app.ai.pipeline:Pipeline
ANTHROPIC_API_KEY=<your key>
GITHUB_TOKEN=<read-only token, optional but avoids rate limits and allows private repos>
# optional: ANTHROPIC_MODEL, ANTHROPIC_TIMEOUT_SECONDS, ANTHROPIC_MAX_TOKENS
```

Then restart the server. Behaviour:

- `draft_brief` fetches GitHub PR/issue title, description, comments and changed file names (diffs truncated) with the token.
  Failed fetches (private, deleted, rate-limited, non-GitHub links) become a gap `content not fetched: <url>`.
  Fetched text is passed to the model as fenced, untrusted data.
- Model output is requested as a forced tool call and validated with Pydantic; malformed output is retried once.
  Timeouts, API errors, a missing `ANTHROPIC_API_KEY`, or output still malformed after the retry raise `AIPipelineError` (HTTP 502).
- Prompts live in `app/ai/prompts/` as versioned files (`draft_brief_v1.md`, `compare_restatement_v1.md`).
  Items the model infers rather than reads are prefixed `(inferred)`.
- Tests mock the LLM and GitHub: `uv run pytest tests/ai`. Evaluation samples with expected brief fields are in `tests/ai/samples.json`.
