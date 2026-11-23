# Status (handoff snapshot)

_Last updated: 2026-11-23, M1 complete and waiting for the user's check-in._

## Where we are
- **Phase:** M1 (data and agent core, no UI). The plan was approved by the user.
- **Done:**
  - repo scaffold;
  - day-0 spike;
  - frozen snapshot and DuckDB;
  - catalog and `DATA.md`;
  - harness core (events, ledger, workspace, kernels, data tools);
  - visualization runtime (host, pinning, CDN cache, headless renderer, interaction tests);
  - gate with Critic and escalation;
  - agents and prompts;
  - CLI;
  - unit tests including the no-hardcoding lint;
  - CI workflow.
- **M1 result:** all three demo questions ran end to end with approved views, at a total spend of $1.62. See `docs/reviews/M1.md`.

## How to run
```bash
uv sync && uv run playwright install chromium
# data (already built locally; see docs/DATA.md "Rebuild")
uv run sciviz ask "How has Columbia's publication output in each research field changed from 2021 to 2024?"
uv run sciviz ask "<follow-up>" --session <session id printed by the first run>
uv run sciviz cost      # spend ledger
uv run pytest -q        # unit tests (no LLM calls)
```

Outputs per session are in `workspaces/<session>/`: artifacts with screenshots, `events.jsonl`, `views.json`, `decisions.jsonl`. The spend ledger is `workspaces/_ledger.json`.

## What works
- The data pipeline end to end.
- The tools (SQL, Python, catalog), checked by smoke tests.
- The runtime and interaction tests, checked with a fixture chart.
- The agent graph builds.

## Known issues / open questions
- See `docs/reviews/M1.md` → Known issues. The main one is latency (6.5–11.5 min per question).
- Repo name `sciviz-agents` is still tentative (D17).

## Next steps
1. User check-in for M1, including the latency decision (review issue 1).
2. Then M2: FastAPI with SSE, the React UI, the iframe host, selection → chat, linked views, the three modification paths, replay mode.

## Environment notes
- Secrets: `~/Desktop/fsu/.env` (`OPENALEX_API_KEY`), `OPENAI_API_KEY` in the shell environment. Never commit or print them.
- Raw snapshot: `~/Desktop/fsu/data/openalex_columbia_2026-11-23/` (frozen). Processed DB: `data/columbia.duckdb` (gitignored).
