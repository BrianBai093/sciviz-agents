# Status (handoff snapshot)

_Last updated: 2026-11-23, end of planning._

## Where we are
- **Phase:** planning finished. [PLAN.md](PLAN.md) is waiting for the user's approval. M1 has not started.
- **Running:** the background download of the OpenAlex snapshot for Columbia University, 2021–2024, ≤100 authors (55,371 works).
  - Output: `~/Desktop/fsu/data/openalex_columbia_2026-11-23/`.
  - Log: `~/Desktop/fsu/data/openalex_columbia_2026-11-23.log`.
  - The download is resumable. Re-running the same command continues from `_state.json`:
    ```bash
    cd ~/Desktop/fsu && set -a && . ./.env && set +a && python3 -I scripts/fetch_openalex_snapshot.py --out data/openalex_columbia_2026-11-23 --years 2021-2024
    ```

## What exists
- `docs/PLAN.md`: the build plan.
- `docs/DECISIONS.md`: D1–D25.
- `docs/DEVLOG.md`: the work log.
- `~/Desktop/fsu/scripts/fetch_openalex_snapshot.py`: the snapshot downloader.
- No application code yet.

## What works / what's broken
- Nothing is built yet, so nothing is broken.

## Next steps (after approval)
- M1, task 1: scaffold the repo and move the fetch script into `data_pipeline/`.
- See PLAN §9.

## Open questions for the user
- The repo name `sciviz-agents` is tentative (D17).

## Environment notes
- Secrets live in `~/Desktop/fsu/.env` (`OPENALEX_API_KEY`) and in the shell environment (`OPENAI_API_KEY`). Never commit or print them.
- The test PDF is at `~/Desktop/fsu/Coding_Design_Test_20261122.pdf`.
