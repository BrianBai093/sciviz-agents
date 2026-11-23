# Development log

Append-only. Each entry records what was done, what was chosen (with a link to [DECISIONS.md](DECISIONS.md)), the result, any issues, and spend. Times are local.

---

## 2026-11-23: Planning (with the user)

**Done**
- Read the test PDF (`../../Coding_Design_Test_20261122.pdf`). Scope set to Project 1, T1–T3 (D1).
- Checked the environment:
  - macOS, Apple M5, 16 GB RAM;
  - Python 3.13, uv, Node 25, Docker installed (daemon not running), ffmpeg, `gh` logged in;
  - `OPENAI_API_KEY` present, no Anthropic or DeepSeek key.
- Checked model options on the web (2026-11-23):
  - DeepSeek V4 Pro: no image input.
  - GPT-6.2 Sol: text and image input. A free models-API call confirmed the user's key can access it.
  - Chose GPT-6.2 Sol (D2), with GPT-6.2 Astra for escalation (D3).
- OpenAlex has required a free API key since 2026-02. The user supplied one; it is stored in `~/Desktop/fsu/.env`, outside any repo.
- Sized the data with real API queries (D4, D25):
  - Columbia University (I78577930) has 134,328 works in 2015–2024.
  - The separate CUIMC record has 51,307 works, 33,602 of them without the Columbia University affiliation.
  - 2,973 works have more than 100 authors.
  - OpenAlex list endpoints truncate author lists at 100.
- Ran three planning rounds:
  - Round 1: architecture paradigm (D5).
  - Round 2: harness base, after the user's challenge and a web check of LangGraph, Deep Agents and dsh (D6). Interaction guarantees (D9).
  - Round 3: UI (D14), video (D15), budget (D18), process (D19).
  - Blind-spot review: D10, D12, D20–D24.
- Wrote [PLAN.md](PLAN.md), this log, [DECISIONS.md](DECISIONS.md) and [STATUS.md](STATUS.md).

**Issues and notes**
- I first proposed a fixed agent pipeline, then a custom harness. Both were superseded; see D5 and D6.

**Spend:** LLM $0. OpenAlex: a few dozen requests, within the free tier.

---

## 2026-11-23 12:20–: OpenAlex snapshot download

**Done**
- Wrote `~/Desktop/fsu/scripts/fetch_openalex_snapshot.py`. It moves into `data_pipeline/` in M1.
  - Stages: works → topics → Columbia-affiliated authors → primary sources.
  - Each stage writes gzipped JSONL, is resumable, and retries with backoff.
  - The API key is read from the environment and never logged.
- Test run of one page:
  - `per_page=200` accepted;
  - full records include `abstract_inverted_index`, `authorships`, `topics`, `referenced_works`, `counts_by_year`, `awards`, `funders`, `keywords`;
  - about 1.4 MB gzipped per 200 works.
- First full run (2015–2024, 131,355 works expected): stopped at page 129 when the user narrowed the scope to 2021–2024. The partial data was moved to the session scratchpad and is not used.
- Second run started in the background: 2021–2024 and `authors_count:<101`, **55,371 works expected**. Output goes to `~/Desktop/fsu/data/openalex_columbia_2026-11-23/`, log to `~/Desktop/fsu/data/openalex_columbia_2026-11-23.log`.

**Result:** in progress. The outcome will be appended here.

**Spend:** LLM $0. OpenAlex: about 300–700 list requests, roughly $0.03–0.07 of the free $1/day.

---

## 2026-11-23 12:35–: M1 build (data + agent core)

**Scaffold**
- `git init`; uv project (`pyproject.toml`, package `backend/sciviz`).
- Installed versions: deepagents 0.7.41, langchain 1.5.2, langchain-openai 1.8.5, langgraph 1.2.24, openai 3.57.0, duckdb 2.0.1, playwright 1.65.2 (Chromium headless shell).
- Commits use the user's global git identity, local only.

**Day-0 spike** (`tests/spikes/spike_m1_harness.py`, cost ≈ $0.015). All four checks passed:
- (a) GPT-6.2 Sol tool calling with a reasoning-effort setting (3.0 s);
- (b) image input ("A red circle sits to the left of a blue square");
- (c) a declarative sub-agent via `task`, streamed under the `tools` namespace;
- (d) `interrupt()` in a tool, then `Command(resume=…)`.

→ D6 (Deep Agents) confirmed, no fallback needed.

**Snapshot.** Finished at 12:43 after 691 API calls:
- works 55,371/55,371;
- topics 4,516;
- Columbia-affiliated authors 29,518 of 29,520 requested;
- sources 9,465.

**DuckDB** (`data_pipeline/build_duckdb.py`, 173 MB):

| Table | Rows |
|---|---:|
| works | 55,371 |
| authorships | 438,156 |
| authorship_institutions | 619,528 |
| institutions | 15,410 |
| authors | 29,518 |
| topics | 4,516 |
| work_topics | 165,198 |
| sources | 9,465 |
| citations | 2,322,878 (39,134 internal) |
| work_citations_by_year | 155,356 |
| work_keywords | 468,258 |
| work_funders | 120,254 |

- Works per year: 14,175 / 13,636 / 13,616 / 13,944.
- Top fields: Medicine 15,750; Social Sciences 6,439; Computer Science 3,369.
- 26% of works have no abstract.
- Fix along the way: topic `keywords` are objects in the current API, not strings.

**Catalog**
- `data_pipeline/build_catalog.py` profiles every column (type, nulls, distinct, range, top values or examples) and merges the profile with the hand-written `catalog/columbia_semantics.yaml`.
- Outputs: `catalog/columbia.yaml` (read by agents) and `docs/DATA.md`.

**Sample DB.** `catalog/columbia_sample.duckdb`, a 3% hash sample of works: 1,661 works, 11 MB (D30).

**Harness core** (`backend/sciviz/`):
- `config.py`: settings and the price table.
- `datasets.py`: pluggable dataset (D23).
- `harness/events.py`: JSONL event log with subscribers.
- `harness/budget.py`: spend ledger with warn/hard-stop, plus a LangChain usage callback.
- `harness/workspace.py`: artifact store with lineage, decisions, views.
- `tools/python_exec.py`: one Jupyter kernel per agent, secrets stripped (D10, D26).
- `tools/data_tools.py`: catalog, read-only SQL with timeout and save-as-artifact, Python, artifacts, decisions.
- Smoke test passed: lineage `T2 <- T1` recorded, secrets not visible inside the kernel.

**Visualization runtime**
- `runtime/static/host.{html,js}` + `theme.json`: the generic interaction layer.
  - Clicks and hovers on data-bound marks are handled by delegation.
  - Default selection/highlight styling applies when a module does not implement it (D28).
  - Parent ↔ iframe commands for M2.
- `runtime/cdn.py`: pins imports to exact versions via the npm registry; disk cache for CDN responses (D21).
- `runtime/renderer.py`: Playwright render, metrics (marks, text overlap, out-of-bounds, blank), screenshots, and the generic interaction tests (D29).
- Fixture test `tests/fixtures/bar_module.js`: `d3` pinned to 7.9.2; all 5 interaction tests pass (hover, click-select, selection visible, highlight visible, parameter change).

**Agents**
- `prompts/{lead,data,analyst,viz}.md`.
- `agents/critic.py`: structured verdict from screenshots, automated checks and data summary.
- `tools/viz_tools.py`: `render_preview` and `submit_viz`, the gate with escalation.
- `tools/discovery_tools.py`: npm search and package docs.
- `tools/lead_tools.py`: show/params/highlight views, `ask_user`.
- `agents/build.py`: Deep Agents assembly with a harness profile that removes `execute` and the generic sub-agent (D31).
- `cli.py`: `sciviz ask`, `sciviz cost`.

**Demo runs (CLI)**

| Question | Session | Result | Time | Cost |
|---|---|---|---:|---:|
| Q1 "How has Columbia's publication output in each research field changed from 2021 to 2024?" | `s20261123-125430` | V1 approved in one gate round | 387 s | $0.37 |
| Q2 "Show the collaboration network among Columbia's 80 most prolific researchers in 2021-2024 as a force-directed node-link diagram." | `s20261123-125649` | V1 approved in one gate round | 464 s | $0.47 |

- **Q1 flow:** lead (decisions) → data (T1 field × year counts, T2 totals, T3 reconciliation checks) → viz (several `render_preview` rounds) → gate.
  - Critic: 5/5/4/4. The view is a diverging bar chart of the 2024−2021 change with the yearly counts alongside.
  - Parameters: measure, domain, order. All interaction tests pass.
  - The answer cites [T1, T2, T3, V1].
  - Finding: total −1.6%; CS +178; Earth & Planetary −211.
- **Q2 flow:** lead → data (author ranking, work-author incidence) → analyst (G1 graph: 80 nodes, 208 ties, components 57 / 8 / 15 isolates) → viz → gate.
  - Critic: 5/5/4/4. The view is a force-directed network with components separated, top authors labelled, a legend, and filters.
  - The answer cites G1 and T1–T6.
- **Prompt fix (generic):** the Viz prompt now says the host renders controls for declared parameters, so modules should not duplicate them inside the view. Q1 had built in-view widgets.
- Kernel process output (a transport warning) is now discarded, so it no longer clutters agent output.
