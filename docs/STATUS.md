# Status (handoff snapshot)

_Last updated: 2026-11-23. M3 complete and published._

## Where we are
- **All three milestones are done.** Reviews: `docs/reviews/M1.md`, `M2.md`, `M3.md`.
- **Published (D45):** public repo https://github.com/BrianBai093/sciviz-agents. The full database is the asset of release [v1.0.0](https://github.com/BrianBai093/sciviz-agents/releases/tag/v1.0.0); README §1 gives the download command and checksum. GitHub Actions runs lint and the unit tests on every push.
- **Open (user decision):** where to host the video. For now it is in the repo (`demo/video/sciviz_demo.mp4`).
- **Design Test (Option A):** done. The architecture figure is `docs/figures/sciviz_architecture.{pdf,png,svg}`, built by `docs/figures/build_architecture_figure.py` (D46), and it opens README §3.
- **Next:** Project 2.

## How to run
See README §1. In short:
```bash
uv sync && uv run playwright install chromium && (cd frontend && npm install && npm run build)
SCIVIZ_WORKSPACES=recordings uv run sciviz serve --port 8001      # replay the recordings, no API key
uv run sciviz serve --port 8000                                    # live mode (needs OPENAI_API_KEY)
uv run pytest -q                                                   # unit tests (no LLM calls)
uv run python evals/run_eval.py --mode multi                       # evaluation (live)
uv run python demo/build_video.py demo/storyboard.yaml             # rebuild the narrated video from recordings
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
- Full live workspaces (with LangGraph checkpoints) are in `workspaces/` (gitignored). Curated copies are in `recordings/`.
