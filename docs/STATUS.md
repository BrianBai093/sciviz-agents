# Status (handoff snapshot)

_Last updated: 2026-11-23, M2 complete and waiting for the user's check-in._

## Where we are
- **M1 (data and agent core)** and **M2 (web app and interaction)** are done. Reviews: `docs/reviews/M1.md`, `docs/reviews/M2.md`.
- **Next: M3.**
  1. Regenerate the demo sessions with the current gate and prompts.
  2. Run the 4-task evaluation (plus a single-agent comparison if the budget allows).
  3. Write the README and ARCHITECTURE.
  4. Make the replay + TTS video.
  5. Push to GitHub after the user's OK.

## How to run
```bash
uv sync && uv run playwright install chromium
(cd frontend && npm install)
uv run sciviz serve --port 8000          # API (+ the built UI at / if frontend/dist exists)
(cd frontend && npx vite --port 5173)     # dev UI at http://localhost:5173 (proxies /api and /runtime to :8000)
# replay-only server without an API key (serves the built UI):
env -u OPENAI_API_KEY uv run sciviz serve --port 8001   # http://localhost:8001/?session=<id>&replay=1&speed=8
uv run sciviz ask "<question>" [--session <id>]           # CLI
uv run pytest -q                                          # unit tests (no LLM calls)
uv run python tests/ui/ui_smoke.py <session>              # headless UI smoke test (needs the dev stack)
uv run python demo/record_replay.py <session> <out_dir> --speed 16   # record a replay video
```
The Claude desktop browser pane blocks iframes, so use a regular browser.

## What works
- Data pipeline; agents; verification gate (render checks, interaction tests including multi-item selection and state round trip, Critic, escalation).
- Web UI:
  - chat with grounded answers;
  - linked views;
  - parameter controls;
  - versions, undo and compare;
  - details-on-demand;
  - trace, artifacts and plan panels;
  - interrupt questions.
- The AI's three modification paths: parameters, highlight, code edit.
- Replay without an API key.

## Known issues
See `docs/reviews/M2.md`. The main points:
- the legacy M1 views have bugs (fixed going forward by D33/D38);
- new full questions have not yet been timed at medium Viz effort.

## Sessions worth knowing

| Session | Contents |
|---|---|
| `s20261123-125430` | Q1 (field trends) |
| `s20261123-125649` | Q2 network, Q3 edge bundling, plus the M2 highlight, parameter and code-edit tests |
| `s20261123-135456` | interrupt test |

## Environment notes
- Secrets: `~/Desktop/fsu/.env` (`OPENALEX_API_KEY`); `OPENAI_API_KEY` in the shell environment. Never commit or print them.
- Raw snapshot: `~/Desktop/fsu/data/openalex_columbia_2026-11-23/` (frozen). Processed DB: `data/columbia.duckdb` (gitignored).
- Ledger: `workspaces/_ledger.json` ($2.09 of $50 at the end of M2).
