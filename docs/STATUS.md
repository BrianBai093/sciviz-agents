# Status (handoff snapshot)

_Last updated: 2026-11-23, M1 in progress._

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
- **In progress:** end-to-end runs of the three demo questions through `sciviz ask`.

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
- The first agent runs are under way. Results and issues will be logged in DEVLOG and in `docs/reviews/M1.md`.
- Repo name `sciviz-agents` is still tentative (D17).

## Next steps
1. Run the three demo questions.
2. Fix systemic issues using generic fixes only.
3. Write `docs/reviews/M1.md`.
4. Check in with the user.

## Environment notes
- Secrets: `~/Desktop/fsu/.env` (`OPENALEX_API_KEY`), `OPENAI_API_KEY` in the shell environment. Never commit or print them.
- Raw snapshot: `~/Desktop/fsu/data/openalex_columbia_2026-11-23/` (frozen). Processed DB: `data/columbia.duckdb` (gitignored).
