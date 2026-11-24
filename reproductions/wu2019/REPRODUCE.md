# Reproducing this run

This folder is the exported reproduction package of `sciviz reproduce` session `r-full-8k`: the agents' attempt to
reproduce Wu, Wang & Evans (2019), "Large teams develop and small teams disrupt science and technology"
(*Nature* 566, 378–382), on the Columbia OpenAlex snapshot. Everything in it except this file was written by
`uv run sciviz export-run --session r-full-8k --out reproductions/wu2019`.

## What is here

| Path | Contents |
|---|---|
| `report.pdf` (`.html`, `.md`) | The report the report gate released (round 2), followed by the harness's run record (time, spend, API requests, gate rounds per turn) and an evidence index of every cited artifact |
| `figures/` | The report's five figures as vector PDF and PNG, numbered as in the report; `figures/other/` holds every other figure that passed the figure gate (for example the stage-1 versions) |
| `data/artifacts/<id>/` | Every artifact of the run (tables, findings, JSON, and every figure version submitted to the figure gate): `meta.json` (title, producer, inputs, the exact code that made it) and the data (Parquet or JSON). Ids match the citations in the report |
| `data/api_responses.sqlite.xz` | The 29,126 OpenAlex API responses the run used, frozen (37 MB compressed, 126 MB unpacked) |
| `scripts/cells/` | Every code cell the agents ran, in order, including background jobs (`NNNN_<agent>[_jobN].py`), with `cells.jsonl` as the index |
| `scripts/files/`, `files.jsonl` | Files the agents wrote with their file tools, with the content after each write |
| `scripts/jobs.jsonl` | Every background job: id, start time, and its script and log under `trace/jobs/` |
| `scripts/run_all.py` | Offline replay of the whole run (below) |
| `trace/` | Inputs (paper brief, constraints), claim plan, decisions, event log, cell log, figure reviews, report reviews, the lead's report of each turn and the released report text |

## 1. Replay the analysis offline (no API keys, no network)

Requirements: the repository environment and the snapshot database (README §1).

```bash
uv sync
mkdir -p data && curl -L -o data/columbia.duckdb https://github.com/BrianBai093/sciviz-agents/releases/download/v1.0.0/columbia.duckdb
uv run python reproductions/wu2019/scripts/run_all.py
```

`run_all.py` unpacks the frozen API responses, then re-executes all 52 code cells in their original order, with the
same helpers the agents had (`sql`, `load`, `save_table`, `openalex`, ...). External API calls are answered from the
frozen responses through the same local proxy the agents used. Before each cell it restores what the harness or the
agents had written by then: background-job scripts and logs, and files written with the file tools. Artifacts get
their original ids, so later cells find them. At the end every artifact is compared with the original. A cell that
fails in the replay but succeeded in the run is reported, and the replay continues with the artifacts that cell made
in the run. The replay writes to `reproductions/wu2019/replay/` (per-cell logs in `_cell_logs/`, a summary in
`replay_summary.json`). It takes about two minutes.

Result of the replay on 2026-11-24:

- All 52 cells ran in 77 s, after the responses were unpacked.
- Of the 109 data artifacts the replay recomputed, 98 are identical to the run's: 95 exactly, and 3 with the same rows
  in a different order. The 11 that differ either record timings, retries or live API usage (J6, J8, T16, T23, T28,
  T31), or are reference-metadata tables made before the agent re-requested 200 responses that had failed during the
  collection (T30, T35–T38). In the replay those requests are answered from the frozen file and never fail. The tables
  made after the re-request (T39, T41, T45) are identical.
- Two cells cannot pass offline, by design. Cell 28 checks the run's live API spend. Cell 52 checks that re-rendered
  figure files are byte-identical to the gated files, which fails offline because PDF files embed their creation time.
  The 5 artifacts these cells made are taken from the run.
- The two stage-1 jobs that the agent stopped had saved 8 artifacts. The replay does not rerun stopped jobs.
- All 10 figures (the newest gated version of each) are rendered again with identical pixels.

## 2. Rerun the agents from scratch

Needs `OPENAI_API_KEY` and `OPENALEX_API_KEY` (with about $3.50 of OpenAlex credit). The original run cost $3.41 of LLM
spend in total (pilot $0.48, stage 1 $1.25, stage 2 $1.68) and $3.00 of OpenAlex requests, and took about 70 minutes of
agent time. The four steps are the same commands with the inputs in [`inputs/wu2019/`](../../inputs/wu2019/):

```bash
Q="How does team size influence the balance between disruptive innovation and developmental research in science and technology?"
# 1. pilot on 100 works (separate session): designs the data collection and measures its cost
uv run sciviz reproduce --session my-pilot --paper inputs/wu2019/paper_brief.md --constraints inputs/wu2019/pilot.md --external-budget 0.2 --question "$Q"
# 2. stage 1: 8,000-work stratified sample, data collection, analysis, gated figures
uv run sciviz reproduce --session my-run --paper inputs/wu2019/paper_brief.md --constraints inputs/wu2019/full_stage1.md --input inputs/wu2019/pilot_report.md --input inputs/wu2019/pilot_decisions.md --external-budget 3.5 --question "$Q"
# 3. stage 2: the user's two corrections, then the report through the report gate
uv run sciviz reproduce --session my-run --paper inputs/wu2019/paper_brief.md --constraints inputs/wu2019/full_stage2.md --external-budget 0.3 --question "$Q"
# 4. stage 3: figure wording and the report rewritten in plain language (no new analysis)
uv run sciviz reproduce --session my-run --paper inputs/wu2019/paper_brief.md --constraints inputs/wu2019/full_stage3.md --external-budget 0 --question "$Q"
uv run sciviz export-run --session my-run --out reproductions/my-run
```

`pilot_report.md` and `pilot_decisions.md` are the pilot's results, which the user passed to stage 1. A new run will not
match this one exactly: the agents are not deterministic, and OpenAlex changes every day (citation counts grow). The
frozen responses in this package are what make this run checkable.

## 3. Checks made outside the agents

- **Disruption counts.** For 7 sampled works the score was recomputed from complete lists of citing works (a different
  method from the agents' grouped counts): 4 in the main window, 3 in the fixed window. All matched exactly.
- **Main result.** The mean disruption percentile and the median citation count by team size were recomputed
  independently from the agents' per-work data (works with at least one citation). They match the report to rounding
  (solo 62.5, ten authors 47.6, 51–100 authors 36.2; medians 4, 15, 39).
- **Report numbers.** Spot checks of the report against the recorded findings (claims C1, C3, C5, C7, C8, C9) found no
  differences.

## 4. Notes on this run

- **Job ids.** In stage 2, background-job ids restarted at `job1` and overwrote the folders of stage-1 jobs 1–3. The
  harness now keeps job ids unique within a workspace and records stopped jobs. The stage-1 job folders were rebuilt
  under `history/turn1/jobs/` in the workspace: the scripts of the two jobs the agent stopped were recovered from
  artifact J3 by undoing the two edits the agent made to them; they match the event log's copy (length, first 500
  and last 1,000 characters). Those jobs' logs were lost; their `log.txt` says so.
- **File-tool writes.** The agents also wrote scripts with their file tools, which the cell log did not record. They
  were recovered from the run's LangGraph checkpoints (`scripts/files.jsonl`, marked "backfilled"); the harness now
  logs such writes as they happen.
