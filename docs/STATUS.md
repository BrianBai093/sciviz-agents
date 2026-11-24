# Status (handoff snapshot)

_Last updated: 2026-11-24. Project 1 complete and published. Project 2: report done and exported; not pushed._

## Where we are
- **Project 1: all three milestones are done.** Reviews: `docs/reviews/M1.md`, `M2.md`, `M3.md`.
- **Published (D45):** public repo https://github.com/BrianBai093/sciviz-agents. The full database is the asset of release [v1.0.0](https://github.com/BrianBai093/sciviz-agents/releases/tag/v1.0.0); README §1 gives the download command and checksum. GitHub Actions runs lint and the unit tests on every push.
- **Open (user decision):** where to host the video. For now it is in the repo (`demo/video/sciviz_demo.mp4`).
- **Design Test (Option A):** done for Project 1. The architecture figure is `docs/figures/sciviz_architecture.{pdf,png,svg}`, built by `docs/figures/build_architecture_figure.py` (D46), and it opens README §3.
- **Project 2** (reproduce Wu, Wang & Evans 2019; plan `docs/PLAN_P2.md`, D47–D55; README §9):
  - **Done:**
    - the pilot;
    - stage 1 (evidence and figures);
    - stage 2 (the user's two corrections, D52, then the report through the report gate);
    - the export to `reproductions/wu2019/`, which replays offline.
    - Reviews: `docs/reviews/P2-pilot.md`, `P2-M2.md`, `P2-M3.md`.
  - **Headline:** the D percentile falls with team size (solo 62.5 → 10 authors 47.6 → 51–100 authors 36.2; −3.48 per doubling, CI −4.27 to −2.70) while citations rise. The stronger decline at high impact does not reproduce. Statuses: C2 reproduced; C1 and C4–C8 partly; C3 not reproduced; C9 not testable.
  - **Spend:** LLM $3.41 of $30 (Project 2 ledger); OpenAlex $3.00.
  - **Still to do:**
    - the narrated demo video (≤ 5 min);
    - the Design Test figure for Project 2;
    - push, after the user's OK. Local commits only so far.
  - **Workspace notes:** `workspaces/reproduce/r-full-8k/history/turn1/` holds the stage-1 constraints, lead report and API usage, and the rebuilt stage-1 job folders (D53). `file_log.jsonl` there was rebuilt from the checkpoints.

## How to run
See README §1. In short:
```bash
uv sync && uv run playwright install chromium && (cd frontend && npm install && npm run build)
SCIVIZ_WORKSPACES=recordings uv run sciviz serve --port 8001      # replay the recordings, no API key
uv run sciviz serve --port 8000                                    # live mode (needs OPENAI_API_KEY)
uv run pytest -q                                                   # unit tests (no LLM calls)
uv run python evals/run_eval.py --mode multi                       # evaluation (live)
uv run python demo/build_video.py demo/storyboard.yaml             # rebuild the narrated video from recordings
# Project 2: replay the exported run offline (no keys), or rerun it (see reproductions/wu2019/REPRODUCE.md)
uv run python reproductions/wu2019/scripts/run_all.py
uv run sciviz export-run --session r-full-8k --out reproductions/wu2019     # re-export from the workspace
```

## Key results
- **Evaluation** (`evals/results/summary.md`): multi-agent 4/4 (335 s average, $1.23); single agent 4/4 (165 s average, $0.61). All views passed the gate on the first round.
- **Demo session** `recordings/demo-network-2`: force-directed network → edge bundling → highlight (10 s) → parameter change (15 s) → code edit (232 s).
- **Video:** `demo/video/sciviz_demo.mp4` (3:28).
- **Spend:** ledger $6.90 of $50, plus about $1–2 untracked (D41).

## Known issues
See README §6 and `docs/reviews/M3.md`:
- latency;
- escalation never triggered live;
- a small evaluation;
- no independent recomputation of numbers;
- demo-grade sandboxing;
- views need internet access for CDN libraries.

## Environment notes
- Secrets: `~/Desktop/fsu/.env` (`OPENALEX_API_KEY`); `OPENAI_API_KEY` in the shell environment. Never commit or print them.
- Raw snapshot: `~/Desktop/fsu/data/openalex_columbia_2026-11-23/` (frozen). Processed DB: `data/columbia.duckdb` (gitignored; published as the release v1.0.0 asset).
- Full live workspaces (with LangGraph checkpoints) are in `workspaces/` (gitignored). Curated copies are in `recordings/`. Project 2 sessions are under `workspaces/reproduce/`; their own ledger is `workspaces/reproduce/_ledger.json`.
- OpenAlex response cache (Project 2): `data/openalex_cache.sqlite` (gitignored). Fetched data is frozen once it is cached.
