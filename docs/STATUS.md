# Status (handoff snapshot)

_Last updated: 2026-11-23. Project 1 complete and published. Project 2: pilot done._

## Where we are
- **All three milestones are done.** Reviews: `docs/reviews/M1.md`, `M2.md`, `M3.md`.
- **Published (D45):** public repo https://github.com/BrianBai093/sciviz-agents. The full database is the asset of release [v1.0.0](https://github.com/BrianBai093/sciviz-agents/releases/tag/v1.0.0); README §1 gives the download command and checksum. GitHub Actions runs lint and the unit tests on every push.
- **Open (user decision):** where to host the video. For now it is in the repo (`demo/video/sciviz_demo.mp4`).
- **Design Test (Option A):** done. The architecture figure is `docs/figures/sciviz_architecture.{pdf,png,svg}`, built by `docs/figures/build_architecture_figure.py` (D46), and it opens README §3.
- **Project 2** (reproduce Wu, Wang & Evans 2019; plan `docs/PLAN_P2.md`, D47–D51):
  - M1 done: report-mode harness, pilot, background jobs, figure gate, report gate, export with replay.
  - **Stage 1 of the full run done** (`workspaces/reproduce/r-full-8k`, review `docs/reviews/P2-M2.md`):
    - an 8,000-work stratified sample; findings F1–F9 for claims C1–C9; 5 gated figures;
    - LLM $1.25; OpenAlex $2.91.
    - Headline: the D percentile falls with team size (62.9 for solo → 36.4 for 51–100) while citations rise. This reproduces the main result. The high-impact claim does not reproduce.
  - **Waiting on the user:** check-in on the results, and on two settings for stage 2 (interval method; the at-least-one-citation restriction).
  - Then: stage 2 (writer + report gate → PDF), `sciviz export-run`, README, video.

## How to run
See README §1. In short:
```bash
uv sync && uv run playwright install chromium && (cd frontend && npm install && npm run build)
SCIVIZ_WORKSPACES=recordings uv run sciviz serve --port 8001      # replay the recordings, no API key
uv run sciviz serve --port 8000                                    # live mode (needs OPENAI_API_KEY)
uv run pytest -q                                                   # unit tests (no LLM calls)
uv run python evals/run_eval.py --mode multi                       # evaluation (live)
uv run python demo/build_video.py demo/storyboard.yaml             # rebuild the narrated video from recordings
# Project 2 pilot (needs OPENAI_API_KEY and OPENALEX_API_KEY):
uv run sciviz reproduce --paper inputs/wu2019/paper_brief.md --constraints inputs/wu2019/pilot.md --external-budget 0.2 \
  --question "How does team size influence the balance between disruptive innovation and developmental research in science and technology?"
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
