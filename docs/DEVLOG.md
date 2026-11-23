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
- **Q3** (follow-up in `s20261123-125649`): "…redraw the same collaboration network with hierarchical edge bundling, grouping the researchers by their field and subfield…"
  - Flow: lead → data (field/subfield assignment for the same 80 researchers) → analyst (hierarchy + cross-field measures; finding F7: 94 of 208 ties cross fields) → viz.
  - Gate: V2 was **rejected** by the Critic. Its major issue was that the declared filters are not visible in the screenshots. V3 was **approved** (5/5/4/5).
  - 690 s, $1.24. V1 stays available as view1 for comparison; V3 is view2.
- **Harness fix (D33):** the Critic now gets the declared parameters and is told the host renders their controls. The V2 rejection showed that the Viz prompt and the Critic disagreed on this.
- **M1 self-review:** written to `docs/reviews/M1.md`. Evidence (screenshots, CLI logs) is in `docs/reviews/m1/`. All exit criteria are met; ledger total $1.62.

---

## 2026-11-23: M2 build (web application and interaction)

**User decision after M1:** Viz reasoning effort set to medium (D34).

**Backend** (`backend/sciviz/runner.py`, `backend/sciviz/api/app.py`; start with `sciviz serve`)
- `runner.run_turn`: one shared turn loop for the CLI and the API.
  - Selections are turned into text the Lead can act on (dataset ids, labels, the source view and its entity types).
  - Interrupts are answered through a callback.
  - Emits `message`, `done` and `error` events.
- FastAPI endpoints:
  - sessions: list, create, state;
  - messages (agent run in a thread, one turn at a time per session) and resume for interrupts;
  - `GET /events`: SSE, either a live tail of `events.jsonl` or an accelerated replay;
  - artifacts: meta, data, pinned module, manifest, screenshots, versions;
  - user view updates (params, version switch) and selection, both logged as events;
  - `/api/entity/{id}`: details-on-demand, resolved through catalog entity patterns (D23);
  - `/runtime/view.html`: the host page with injected config;
  - serves the built UI from `frontend/dist`.
- CORS `*`: views run in sandboxed, opaque-origin iframes.
- Without `OPENAI_API_KEY`, live questions return a clear 503 while replay still works (tested on port 8001).
- Lead tools: `show_view(..., replace_view=...)` puts a new version in place of an existing view and keeps the old one for undo. The Lead's prompt lists each view's entity types, declared parameters and current values.

**Frontend** (`frontend/`: React 19, Vite 8, TypeScript 7, Tailwind 4, zustand)
- The store is derived only from events (D36), so live mode and replay share all code.
- Layout follows D14:
  - chat with Markdown answers and clickable artifact citations, a selection chip above the input, and interrupt question cards;
  - up to 4 view panels with parameter controls generated from each manifest's JSON Schema, a version switcher, undo and compare (two versions side by side);
  - a drawer with Details (entity record plus the view's own data rows), Trace (per-agent cost summary, expandable briefs, tool calls, gate verdicts with screenshots), Artifacts (summary, code, lineage, critic reviews) and Plan (todos, decisions).
- Views run in `sandbox="allow-scripts"` iframes and talk to the host through `postMessage` (`setParams`, `setSelection`, `highlight`, `getState`/`setState`).
  - Selections are linked across views by dataset id.
  - Module state is polled and restored after version swaps.

**Testing notes**
- The Claude desktop browser pane blocks iframes (`net::ERR_BLOCKED_BY_CLIENT`), so UI tests run in our own headless Chromium: `tests/ui/ui_smoke.py`.
- Smoke test on the recorded Q2/Q3 session: both views ready with no errors. Clicking "Jason Dennis Wright" (A5057686070) in view1 selected him in both views and showed the chat chip. A parameter change in view2 re-rendered the view.
- Fixed: effects returned the promise from `scrollIntoView` in the current Chromium, which crashed React.
- Replay on the no-key server (`?replay=1&speed=16`) rebuilt the Q1 session (view, answer, trace) in 24 s.

**Live tests of the AI modification paths** (`tests/ui/ask.py`, through the API like the UI; session `s20261123-125649`)

| Path | Message | Result | Time | Cost |
|---|---|---|---:|---:|
| Highlight | Selection = A5057686070 in view1, "Highlight this researcher's coauthors in both views." | Lead → analyst (neighbour ids, T9) → `highlight_view` on view1 and view2 with 5 coauthors. The answer also noted that view2 was filtered to cross-field ties. | 38.5 s | $0.065 |
| Parameters | "In view2, show all ties again, but only for the largest connected group, and hide ties with fewer than 3 shared works." | `set_view_params(view2, {tieScope: "All ties", componentScope: "Largest component", minSharedWorks: 3})`, no delegation needed | 4.7 s | $0.032 |
| Code change | "In view1, color the researchers by their field (same assignment as view2) … add a field legend. Keep everything else the same." | Lead → viz edits the existing module → V4 approved (5/5/4/4) → `show_view(V4, replace_view=view1)`. V1 is kept in history; the Lead re-applied the coauthor highlight. | 264 s | $0.34 |
| Interrupt | New session, "Before doing anything else, ask me which publication years…" | `ask_user` fired after 3 s; resumed with "Only 2023 and 2024." Answer: 27,560 works (13,616 + 13,944) [T1]. | 27 s | $0.03 |
| Typed in the UI | "Set the minimum shared works filter in view2 back to 1." (Playwright typing into the chat) | Parameter path; the iframe's params updated live | 8 s | ~$0.03 |

**Bug found by UI testing.** V1 (built in M1) throws `TypeError: u.interrupt is not a function` in `setState`/highlight paths: it calls d3 transition methods without importing d3-transition. The gate's interaction tests had only highlighted one item and never round-tripped state. Generic hardening (D38): the gate now also highlights and selects several items and does a `getState`/`setState` round trip. Re-checking V1 with the new tests fails exactly this, so such views will now be sent back to the Viz agent.

**UI layout** (D39). Narrow panels render the view at a minimum width of 720 px and scale it down, so the layout matches what the gate reviewed. A view in compare mode spans the full width.

**Tests**
- `tests/test_gate_escalation.py`: retry → escalate → stop and clearing of the escalation flag, deterministic, no browser or LLM. 9 unit tests pass.
- Video: `demo/record_replay.py` recorded the UI replaying session `s20261123-125649` at 16× on the no-key server, then clicked a node. Output `docs/reviews/m2/m2_replay_demo.mp4` (97 s, 4 MB). Stills are in `docs/reviews/m2/`.

**Spend:** ledger total $2.09 of $50 (M2 so far ≈ $0.47).

---

## 2026-11-23: M3 (evaluation, documentation, delivery)

**Single-agent mode (D40)** for the ablation: `build_single_agent`.
- Same tools (catalog, SQL, Python, artifacts, discovery, viz, view tools) and the same verification gate. No sub-agents.
- Its prompt is assembled from the same role prompts (data, analyst, viz, lead process), with the sub-agent report formats removed.
- Reasoning effort is medium, the same as the multi-agent workers.

**Evaluation runner**
- `evals/tasks.yaml` has 4 tasks:
  - t1: open-ended trend;
  - t2: force-directed network;
  - t3: hierarchical edge bundling (standalone);
  - t4: citation flows between fields as a Sankey diagram, a technique used nowhere else in the project.
- `evals/run_eval.py --mode multi|single` runs the tasks in parallel threads and records: success, gate rounds, escalation, time, cost, model calls per agent, critic scores, libraries, screenshot.

**Demo session script.** `demo/make_demo_session.py` runs 5 turns: network → edge-bundling follow-up → (select the most prolific researcher) highlight coauthors → show only cross-field ties → recolour the first view by field.

**Incident: corrupted spend ledger (D41).** The eval and the demo script ran in parallel as separate processes and both wrote `_ledger.json` through the same temp file name. The file was corrupted (`JSONDecodeError: Extra data`), and the demo script crashed on its first read. The eval kept running, but its cost callback failed on every call, so no cost events were written.
- Both runs were stopped and their workspaces renamed to `_aborted-*` (hidden in the UI, still counted).
- Fix: an exclusive `fcntl` lock around every read-modify-write, unique temp files with an atomic replace, automatic rebuild from the per-call `cost` events when the file is damaged, and the cost event emitted before the ledger update.
- New tests `tests/test_ledger.py`: 4 processes × 25 writes, and rebuild from events. 11 unit tests pass.
- Ledger rebuilt from events: $2.16.
- **Untracked spend:** the aborted eval ran about 10 minutes with failing callbacks. Estimated $1–2 is not in the ledger.
- The eval and the demo session were restarted.

**Evaluation results** (`evals/results/summary.md`, `evals/results/{multi,single}.json`, screenshots in `evals/results/shots/`)

| Mode | Solved | First-round passes | Average time | Total cost |
|---|---|---|---:|---:|
| Multi-agent | 4/4 | 4/4 | 335 s | $1.23 |
| Single agent | 4/4 | 4/4 | 165 s | $0.61 |

- Critic scores were similar in both modes.
- On the Sankey task both modes discovered `d3-sankey@0.12.3`.
- Largest prompt per call: Lead 9.6k, Data 11.4k, Analyst 8.1k, Viz 20.9k tokens, against the single agent's 23.6k average and 32.5k maximum.
- Honest reading: on short single-question tasks a single agent with the same harness is as good, cheaper and faster. Multi-agent pays off in context isolation for long sessions, which this evaluation does not measure.
- n = 1 run per task.

**Demo session issues and fixes**
- `demo-network` (first attempt), turn 2: the Critic rejected the edge-bundling view twice (V2, V3; answers_question 3/5). The Viz agent's acceptance criteria demanded things a single view's screenshots cannot show ("side by side with V1", a 420×625 layout), and the Critic asked for "verification" of exact routing.
  - The Lead reported the failure honestly. In turn 3, while serving the highlight request, it fixed the view (V4 approved) and showed it.
  - Generic fix D42: the Critic reviews each view in isolation and ignores uncheckable criteria; the Viz prompt asks only for criteria checkable from the view itself.
- Turn 5 ("color … using the same field colors as the edge-bundling view"): the edge-bundling view had no per-field palette, so the Lead asked for clarification instead of guessing. That is sensible behaviour, but not the planned demo. The step was rephrased to stand on its own.
- `demo-network` is set aside as `_superseded-demo-network`. `demo-network-2` was regenerated with D42.

**Recordings.** `demo/package_recordings.py` copies selected sessions to `recordings/` without LangGraph checkpoints and preview renders, about 0.4–1 MB each. The 8 eval sessions are packaged.

**`demo-network-2`** (regenerated with D42)
- Turns 1–2 were clean: V1 force-directed and V2 edge-bundling, both approved on the first submission.
- Turn 3 crashed: parallel `highlight_view` calls raced on `views.json`.
- Fixes: D43 (atomic, locked view state; `ToolErrorMiddleware`) and D44 (fork from a checkpoint). A stress test with 6 threads × 200 concurrent updates gave no errors.
- `demo/continue_demo.py` rolled the session back to the end of turn 2 (event log truncated, view state restored, conversation forked from the turn-2 checkpoint) and re-ran turns 3–5.
- Also fixed: `show_view(replace_view=…)` with the version already shown is now a no-op. Before, it added a self-referencing undo entry, and the UI ignores such events.

**Demo video.** `demo/build_video.py` + `demo/storyboard.yaml`.
- Pipeline: 18 narrated steps; OpenAI `gpt-4o-mini-tts` (voice "marin"), cached in `demo/tts_cache/`; Playwright drives the UI in director mode over the no-key replay server (`SCIVIZ_WORKSPACES=recordings`); captions are overlaid in the page; ffmpeg places each clip at its step's start time.
- Fixes during building: captions were shown only after a step's actions; `-shortest` cut the video to the audio length; one click hit a link instead of a node, so it now targets A5057686070.
- Result: `demo/video/sciviz_demo.mp4`, 3:28, 12.7 MB.

**M3 wrap-up**
- Self-review in `docs/reviews/M3.md`.
- 11 unit tests pass and lint is clean. CI lint now also covers `evals/` and `demo/`.
- Ledger total: **$6.90**, plus about $1–2 untracked (D41) and about $0.10 of TTS.
- Push to GitHub and the release asset are waiting for the user's OK.

## 2026-11-23: Publishing

- Pre-push scan: no secret values (from `.env` or the shell environment) and no key-like strings in the tracked tree or in git history; `.env` is untracked; the largest file is the 12.7 MB video.
- Public repo https://github.com/BrianBai093/sciviz-agents (D45).
- Release v1.0.0 carries `columbia.duckdb` (173 MB, SHA-256 `e7e28777…f45b49`). README §1 now has the clone and download commands, the checksum and a CI badge.
- CI (GitHub Actions: ruff + pytest) runs on every push.

## 2026-11-23: Design Test, Option A (architecture figure)

- Agreed with the user:
  - three stages (input → multi-agent harness → interactive web app);
  - a feedback loop from the app back to the harness;
  - the shared harness services as a band along the bottom;
  - concept names plus a few real code names;
  - abstract icons for the views, not screenshots.
- Layout references from the top-conference figure gallery:
  - MASPOB (ICML 2026): colored phase panels read left to right;
  - MegaAgent (ACL 2025 Findings): a shared-module band along the bottom;
  - OSDA Agent (ICLR 2025): a ×N generate, evaluate, revise loop.
- `docs/figures/build_architecture_figure.py` writes the SVG, then uses Playwright to render:
  - a vector PDF, 7 × 3.22 in (the width of a two-column figure), with fonts embedded;
  - a 300 dpi PNG.
- Colors follow the app: the agent colors, and accent blue for user input and selection.
- README §3 now opens with the figure and a caption. The Mermaid diagram stays as a collapsible text version.
