# Project 1 build plan: `sciviz-agents`

| | |
|---|---|
| Status | Draft, waiting for the user's approval |
| Last updated | 2026-11-23 |
| Related docs | [DECISIONS.md](DECISIONS.md) (why each choice was made), [DEVLOG.md](DEVLOG.md) (what was done, step by step), [STATUS.md](STATUS.md) (current state, for handoff) |

## 0. Summary

**Goal.** A harness-based multi-agent LLM system that answers natural-language analytical questions about Columbia University's publications and returns interactive visualizations in a web app. Users can hover for details, select marks, ask follow-up questions about the selection, and have the AI modify the chart. This is Project 1 (tasks T1–T3) of the WHALES Lab Round-1 coding test.

**Key choices** (details and rationale in [DECISIONS.md](DECISIONS.md)):
- A **Lead agent** plans and delegates to **specialist sub-agents** (Data, Analyst, Viz). A **verification gate** enforced by the harness (render checks → interaction tests → Critic review) decides whether a visualization can be delivered.
- Built on **LangChain Deep Agents** (LangGraph runtime). Our own code covers the parts that decide quality: tools, data catalog, visualization runtime, interaction contract, gate, model escalation.
- **GPT-6.2 Sol** for every agent. A step that keeps failing the gate escalates once to **GPT-6.2 Astra**.
- A visualization is an **agent-written JavaScript module** that follows a generic interaction contract and renders in a sandboxed iframe. Nothing in the code or prompts is specific to a chart type.
- **Replay mode** re-plays recorded sessions without an API key. It is used for the demo video and for reviewers.
- **Data:** an OpenAlex snapshot taken 2026-11-23 and never refreshed. Columbia University, 2021–2024, works with at most 100 authors: **55,371 works**.
- **Budget:** $50 of LLM API spend in total. **3 milestones**, each ending with a self-review and a check-in with the user.

## 1. Requirements traceability

| Requirement (from the test PDF) | Addressed in |
|---|---|
| T1: multi-agent architecture for data understanding, filtering/preprocessing, analysis/code execution, visualization generation, result delivery | §3.1 |
| T1: harness for the execution environment, orchestration, intermediate artifacts, error handling, retry/revision loops | §3.2–§3.6 |
| T2: web UI where a natural-language question produces an interactive visualization, with follow-ups and modifications | §4.3, §5 |
| T3: statistical chart; network with an algorithmic layout; advanced layout that is more readable than the conventional one | §6 eval tasks, §8 demo |
| Generalizability: no hardcoded prompts, workflows or visualization-specific logic; agents interpret requirements, select or discover algorithms and libraries, generate and execute code, refine | §6 |
| Explain how agents collaborate, how computation runs, and how visualizations are represented and rendered | README (M3), docs/ARCHITECTURE.md |
| Encouraged: interactive filtering, hovering, linked views, layout adjustments | §4 |
| Submission: repo with source, setup, dependencies and README; demo video of 5 minutes or less with narration | §7, M3 |
| Dataset: a small, well-documented subset of SciSciNet or OpenAlex | §2 |

## 2. Data

**Scope** (decision D4):
- OpenAlex institution lineage `I78577930`. This is Columbia University plus its OpenAlex children: GISS, Lamont-Doherty, ICAP, CZ Biohub NY.
- `publication_year` 2021–2024 and `authors_count ≤ 100`.
- **Deliberately excluded:**
  - The separate OpenAlex record for Columbia University Irving Medical Center (I2799503643). Many of its papers do not also carry the Columbia University affiliation.
  - Affiliated colleges such as Barnard.
  - Hyper-authored works with more than 100 authors. OpenAlex list endpoints truncate their author lists, and they would distort co-authorship networks.

**Snapshot.** Fetched on 2026-11-23 with `data_pipeline/fetch_openalex_snapshot.py` (currently `../scripts/` until the repo is scaffolded):
- works (full records),
- the complete topic hierarchy,
- every author with a Columbia affiliation on at least one of these works,
- the primary sources (venues).

The raw gzipped JSON Lines files live outside the repo (`~/Desktop/fsu/data/openalex_columbia_2026-11-23/`) and are never refreshed.

**Processed store.** One DuckDB file. These tables are the planned shape; final columns are recorded in DATA.md:

| Table | Grain | Notes |
|---|---|---|
| `works` | one row per work | title, abstract (rebuilt from the inverted index), year, date, type, language, source, citation count, FWCI, open-access status, reference count, author count, retraction flag, primary topic |
| `authorships` | work × author | position, corresponding flag, `is_columbia` (Columbia affiliation on *this* work) |
| `authorship_institutions` | work × author × institution | links authorships to institutions |
| `institutions` | institution | name, country, type, ROR, taken from authorship records |
| `authors` | Columbia-affiliated author | name, ORCID, works count, citation count, h-index, i10-index |
| `topics` | topic | full hierarchy: topic → subfield → field → domain |
| `work_topics` | work × topic | score, primary flag |
| `sources` | venue | name, type, ISSN-L, publisher |
| `citations` | citing work × cited work | `cited_in_snapshot` flag for internal citations |
| `work_citations_by_year` | work × year | citations received per year |
| `work_funders`, `work_keywords` | work × item | only if present and cheap to build |

**Catalog.** A generated `catalog/columbia.yaml`, rendered into `docs/DATA.md`. It holds:
- for each table and column: a description, the type, the null rate, the distinct count, and examples or a value range;
- join keys;
- snapshot row counts;
- caveats:
  - the scope exclusions;
  - author IDs come from algorithmic disambiguation;
  - topics are assigned by a machine-learning classifier;
  - cited works outside the snapshot have no metadata;
  - all counts are as of the snapshot date.

The semantic notes are dataset documentation. They contain no task logic.

**Pluggable datasets** (D23). A dataset is a DuckDB connection plus a catalog. Agents learn about data only through the catalog tools, so a second dataset (for example SciSciNet for Project 2) plugs in without code changes.

**Distribution** (D20). The full DuckDB file is published as a GitHub Release asset. A small sample database (a few MB) is committed for quick start and tests. The rebuild script is documented.

## 3. Agent system

### 3.1 Roles

| Agent | Responsibility | Tools | Produces |
|---|---|---|---|
| **Lead** | Interpret the question (ask when it is genuinely ambiguous), keep the plan, delegate, integrate results, write the final answer. **Runs no code itself.** | `write_todos`, `task` (delegate), `inspect_artifact`, view tools (`show_view`, `set_view_params`, `highlight_view`, `filter_view`), `ask_user` (interrupt) | Plan; final answer where every claim cites an artifact |
| **Data** | Know the dataset: map the question to tables and fields, then filter, clean, and build analysis-ready tables | catalog tools (`list_tables`, `describe_table`, `search_catalog`), `run_sql` (read-only), `run_python`, `save_artifact` | Clean tables, plus notes on filters applied, rows kept, and caveats |
| **Analyst** | Know the methods: statistics, network construction, communities, hierarchies, layout precomputation | `run_python` (pandas, numpy, scipy, networkx, scikit-learn and statsmodels preinstalled), `run_sql`, `save_artifact` | Derived artifacts (aggregates, graphs, trees, metrics) and findings with numbers |
| **Viz** | Choose the visualization technique, discover libraries and read their docs, write the rendering module, declare parameters and interactions | `inspect_artifact`, `run_python` (reshape data), `search_npm`, `read_package_docs`, `web_search` (OpenAI hosted), workspace file tools (write and edit the module), `render_preview`, `submit_viz` (runs the gate) | Visualization artifact: module, manifest, data bindings, screenshots |
| **Critic** | Review independently: does the visualization answer the question, is it readable, is it misleading, do the numbers match | none | Structured verdict: pass, or revise with issues and suggestions |

Result delivery belongs to the Lead (D7). The harness rejects final answers whose claims do not reference existing artifacts.

### 3.2 Harness base: Deep Agents on LangGraph (D6)

| Design element | Implementation |
|---|---|
| Lead loop and plan | Deep Agents main agent with the todo middleware |
| Specialists | Declarative sub-agents, each with its own prompt, tools and model. Isolated context; each returns one report. |
| Shared workspace | A per-session directory, mounted as the agent filesystem |
| SQL and Python | Custom tools: read-only DuckDB; one Jupyter kernel per sub-task, started with an environment that has all API keys removed |
| Verification gate | Runs inside `submit_viz`. `show_view` refuses artifacts that are not approved. |
| Asking the user | LangGraph `interrupt()`, then resume with `Command(resume=…)` |
| Budgets, retries, escalation | LangChain call-limit and retry middleware where available; a custom middleware switches to Astra after repeated gate failure |
| Trace in the UI | Per-sub-agent event streams forwarded to the browser over SSE |

**Day-0 spike** (start of M1). Verify four things:
1. GPT-6.2 Sol works through langchain-openai with a reasoning-effort setting.
2. Images (screenshots) reach the model.
3. Sub-agent events stream.
4. Interrupt and resume work.

**Fallback.** If any of these fails, use LangChain `create_agent` plus a custom LangGraph `StateGraph`. The design stays the same.

### 3.3 Communication

- **Lead ↔ specialists** communicate only through a **brief** and a **report**.
  - Brief (fixed schema): the user's question verbatim, the Lead's interpretation, the goal, input artifact IDs, constraints, acceptance criteria, expected outputs.
  - Report: status, summary, output artifact IDs, decisions and assumptions made, open issues.
  - Specialists never talk to each other. Missing inputs go back to the Lead.
- **Parallel delegation** is allowed, for example preparing data for two linked views.
- **Viz ↔ Critic** happens inside the gate. The Lead is not involved.
- **Every agent ↔ the shared workspace** (artifacts, decision log).

### 3.4 Artifacts and the shared workspace

Each session gets `workspaces/<session_id>/` containing:
- `artifacts/<id>/` with the data (`.parquet` or `.json`) or `module.js`, plus `meta.json`, the generating code, and screenshots;
- `plan.json`, `decisions.jsonl`, `views.json`, `events.jsonl`.

**Artifact meta:**
- `id`, `kind` (table | graph | tree | json | finding | viz), `title`;
- `producer` (agent, step), `inputs` (artifact IDs, giving the lineage), `code`;
- `summary` (schema, row count, stats, sample), `created_at`;
- for visualizations only: `version`, `parent_version`, `status` (draft | approved | approved_with_issues | rejected), and the review history.

**Visibility:**

| Role | Sees | Does not see |
|---|---|---|
| Lead | Conversation, plan, artifact index (one-line summaries), decision log, view state, catalog overview | Raw data, code |
| Specialists | Brief, summaries of relevant artifacts (can load full data), their own knowledge (catalog for Data/Analyst, runtime contract for Viz) | Full conversation history |
| Critic | User question, acceptance criteria, screenshots, metrics, data summary | The Viz agent's reasoning |

**Decision log.** Definitions and assumptions made during a session, for example "prolific = top 50 Columbia authors by works 2021–2024", go into the log. They are injected into later briefs and cited in answers.

### 3.5 Verification gate (inside `submit_viz`)

1. **Static checks.** The module parses and exports `render`. Imports are pinned: unpinned imports are resolved and pinned automatically, and the versions are recorded.
2. **Render** in headless Chromium (Playwright) at the standard size. It must have:
   - no uncaught errors or console errors;
   - a non-blank canvas (pixel variance);
   - at least one data-bound mark;
   - text-overlap ratio and out-of-bounds marks measured;
   - render time measured.
3. **Interaction tests** (§4.4).
4. **Critic review** using the screenshots.

**Loop.**
1. Up to 3 revision rounds.
2. Then one round on GPT-6.2 Astra.
3. Then deliver the best version as `approved_with_issues`, and the Lead must mention the issues.

### 3.6 Models, budgets, errors, context

- **Models.** GPT-6.2 Sol for all agents. Reasoning effort is high for Lead, Viz and Critic, and medium for Data and Analyst. Escalation to GPT-6.2 Astra happens at most once per question.
- **Budgets.**
  - Per question: a soft cap of $1.50 and a cap on model calls per sub-agent.
  - Global: a spend ledger warns at $35 and hard-stops at $50; at the hard stop the system pauses and asks the user.
  - When a cap is exceeded, the run stops gracefully and returns partial results.
- **Errors.**
  - API calls retry with backoff.
  - Tool errors go back to the model, with tracebacks trimmed.
  - The same error three times triggers escalation or a stop.
- **Cost and context.**
  - Prompt prefixes stay stable (no timestamps; tools in a fixed order) so OpenAI's prompt cache hits.
  - Tool outputs are summarized: a table becomes its schema, head and counts.
  - Long sessions are summarized.

## 4. Visualization runtime and interaction

### 4.1 Module contract (written by the Viz agent)

```js
// module.js: an ES module
export default function render(el, ctx) {
  // ctx = { data, params, width, height, theme, host }
  // host = { select(items, { mode }), hover(item | null), emit(type, payload) }
  return { update(params), highlight(ids), setSelection(selection), getState(), setState(state), destroy() };
}
```

- **Data-bound marks.**
  - Marks for single entities carry `data-id` and `data-type`.
  - Aggregated marks carry `data-key`: a JSON grouping predicate such as `{"year": 2022, "field": "Medicine"}`. Selecting the mark selects that subset.
  - Canvas or WebGL renderers implement `pick(x, y)` instead.
- **Manifest `viz.json`.** Title, description, data bindings, parameters as JSON Schema (the UI generates controls from it), entity types, libraries with pinned versions, supported interactions.
- **Theme tokens** come in through `ctx.theme`: fonts, a categorical palette, sequential and diverging ramps, light and dark modes (D22). The theme covers style only.

### 4.2 Host runtime (written once, used by every visualization)

- **Isolation.** A sandboxed iframe (`allow-scripts` only) with a `postMessage` bridge.
- **Events.** Event delegation on data-bound marks. Click selects, Shift-click adds to the selection, hover shows details.
- **Selection state.** The host owns it and pushes it to every view through `setSelection`. Views that share an entity type link automatically.
- **Details panel.** A backend lookup by type and ID, or a summary of the selected predicate.
- **Selection in chat.**
  - A chip above the input shows the current selection.
  - The selection (type, IDs, labels or predicate) is sent with the next message as structured context.
  - Agents can use the IDs directly in SQL.
- **JS libraries** load through a local caching proxy (`/cdn/*`) with pinned versions. This works offline and is reproducible (D21).

### 4.3 How the AI modifies a chart

| Path | Example | Mechanism | Target latency |
|---|---|---|---|
| Parameters | "only 2023+", "size nodes by citations" | Lead → `set_view_params` → `update(params)` | seconds |
| Highlight / filter | "highlight her co-authors" | Lead → Data (IDs via SQL) → `highlight_view` / `filter_view` | ~10 s |
| Code change | "add a timeline brush linked to the network" | Lead → Viz edits the existing module → fast gate → hot reload preserving state via `getState`/`setState` | 30–60 s |

Every change creates a new view version, which supports compare and undo.

### 4.4 Interaction tests (part of the gate, generic)

Each check must hold:
1. Hovering sample marks fires `host.hover` with IDs that exist in the bound data.
2. Clicking fires `host.select` with valid IDs.
3. `setSelection` produces a visible change (pixel diff).
4. `highlight` produces a visible change.
5. For each parameter, setting an alternative value raises no error and produces a visible change.

## 5. Web application

- **Layout** (D14):
  - left: Chat;
  - centre: Views, 1–4 linked panels with parameter controls, version switch, compare and undo;
  - right: a drawer with Details, Trace, Artifacts (with lineage) and Plan tabs;
  - top bar: session, model, cumulative cost;
  - light and dark themes.
- **Backend:** FastAPI.
  - `POST /sessions`
  - `POST /sessions/{id}/messages` (SSE event stream)
  - `POST /sessions/{id}/resume` (interrupt answers)
  - `GET /artifacts/{id}/…`
  - `GET /entity/{type}/{id}`
  - `GET /cdn/*` (caching proxy)
  - `GET /replay/{session}` (SSE)
- **Frontend:** React, TypeScript, Vite, Tailwind, Zustand.
- **Event schema** (shared by live mode and replay): `{ts, session, agent, kind, payload}`. `kind` is one of `plan | delegate | tool_call | tool_result | artifact | gate | message | cost | error`.

## 6. Generalizability safeguards

- **No technique-specific prompts, code or workflows.** Prompts contain roles, contracts, process and general visualization-design principles only.
- **"No hardcoding" lint test** (runs in CI). It fails if prompts or harness code contain technique or layout names from a denylist, for example force, bundl, sankey, chord, treemap, sunburst, streamgraph, voronoi.
- **Runtime discovery.** npm search, package README and type definitions, and web search.
- **Small evaluation** (D13): 4 tasks.
  1. Publication trend by field (open-ended).
  2. Collaboration network of prolific authors (force-directed requested).
  3. The same network reorganized by the field hierarchy with bundled edges (HEB requested).
  4. One technique not seen before, for example citation flows between fields as a Sankey or chord diagram.

  Each task records pass or fail, revision rounds, time, cost and screenshots. A single-agent comparison on the same tasks runs if the budget allows.

## 7. Replay mode and demo video

- **Replay.** All events and artifacts are persisted per session. The replay endpoint re-streams the events with time scaling (for example 4×), so the UI looks identical without any API key.
- **Video** (D15):
  1. A scripted Playwright run drives a replayed demo session (clicks, hovers, selections) and records the screen.
  2. English narration is generated with TTS (OpenAI TTS, with macOS `say` as fallback).
  3. ffmpeg merges video and audio and adds subtitles.
  4. Total length is 5 minutes or less.

## 8. Demo scenario (draft; exact questions tuned in M3)

| Time | Content | Shows |
|---|---|---|
| 0:00–0:20 | One-line intro and the architecture figure | — |
| 0:20–1:10 | Publication trend by field → line chart. Hover, legend filter. Follow-up "only the top 6 fields" changes a parameter in seconds. | T2, statistical chart |
| 1:10–2:10 | Collaboration network of prolific authors → force-directed. Click a person for details. Ask "who are their cross-field collaborators?" with the selection → the AI highlights them. | Network, selection → AI → modify |
| 2:10–3:10 | "Too tangled: group by field hierarchy and bundle the edges" → HEB, shown side by side with the previous version, with linked highlighting and the bundling-strength slider | Advanced layout, readability comparison |
| 3:10–3:50 | A technique not shown before (for example a Sankey of citation flows between fields). The trace shows the Viz agent searching for a library. | Generalizability |
| 3:50–4:40 | Under the hood: plan, delegation, a Critic rejection and the fix, artifact lineage, evaluation table | Harness |
| 4:40–5:00 | What works and what is incomplete | — |

## 9. Milestones

Every milestone ends with a self-review against the checklist below.
1. The review is written to `docs/reviews/M<n>.md`.
2. Then a check-in message goes to the user, with screenshots or links.
3. Work resumes only after the user's OK.

### M1: data and agent core, no UI

**Tasks**
1. Repo scaffold (uv, ruff, pytest), `AGENTS.md`, docs. Move the fetch script into `data_pipeline/`.
2. Build DuckDB from the snapshot; write the catalog generator; write `DATA.md`; build the sample database.
3. Day-0 spike (§3.2).
4. Tools: catalog, `run_sql`, Python kernel runner (keys removed from its environment), artifact store, workspace.
5. Lead, Data and Analyst prompts; brief and report schemas.
6. Headless viz runner, module contract, Viz agent with discovery tools, the gate (render checks, interaction tests, Critic), escalation middleware, spend ledger.
7. CLI: `sciviz ask "…"` produces artifacts, screenshots and a trace.

**Exit criteria**
- The three demo questions run end-to-end from the CLI and produce approved visualizations.
- The trace shows delegation and at least one gate round.
- Spend so far is $15 or less.

**Check-in:** the three outputs as screenshots, trace excerpts, cost.

### M2: web application and interaction

**Tasks**
- FastAPI with SSE; the React app; the iframe host runtime; the details panel.
- Selection → chat; linked views; parameter controls; versions, compare and undo.
- The three modification paths.
- Event log and replay mode; the CDN caching proxy with pinning.

**Exit criteria**
- In the browser: ask a question → see the visualization → hover, select, and ask with the selection.
- Each modification path works once.
- Two views stay linked.
- A recorded session replays without an API key.
- Cumulative spend is $30 or less.

**Check-in:** a local URL for the user to try, plus a short screen recording.

### M3: evaluation, documentation, delivery

**Tasks**
- Tune the demo.
- Run the 4-task evaluation, plus the single-agent comparison if the budget allows.
- Lint test, unit tests, GitHub Actions.
- README covering: architecture, agent collaboration, how computation runs, how visualizations are represented and rendered, what works and what is incomplete, decisions, results, cost.
- Final DATA.md.
- Demo video (replay + TTS).
- Release asset.
- Push to GitHub after the user's OK.

**Exit criteria:** §10 is met; total spend is $50 or less.

**Check-in:** final review before pushing.

### Self-review checklist (every milestone)

- [ ] Exit criteria met, with evidence
- [ ] Tests and the no-hardcoding check pass
- [ ] Prompts and code reviewed for technique-specific logic
- [ ] DEVLOG, DECISIONS and STATUS updated
- [ ] Spend compared with the budget
- [ ] Known issues listed with severity

## 10. Acceptance criteria

1. One command installs, one command starts. `.env.example` lists the required keys.
2. Data: the 2026-11-23 snapshot is loaded into DuckDB, with the generated catalog and `DATA.md` (source, scope, exclusions, fields).
3. The three required cases run end-to-end in the UI without manual intervention.
4. Interaction works:
   - hover for details;
   - click and multi-select;
   - a selection carries into a follow-up question;
   - each of the three modification paths is shown once;
   - two linked views;
   - version compare and undo.
5. The gate and escalation demonstrably work: the trace shows at least one reject → revise → pass cycle.
6. The 4-task evaluation runs with one command and produces a results table. The no-hardcoding check passes.
7. Replay mode opens recorded sessions without an API key.
8. Unit tests run in GitHub Actions.
9. The README covers architecture, collaboration, computation, visualization representation and rendering, what works and what is incomplete, decisions, results, and cost.
10. A demo video (5 minutes or less, English TTS narration) and its script.

**Targets, not hard limits:** a simple chart in about 1 minute or less, a complex one in about 3 minutes or less, about $1 or less per question.

## 11. Documentation and handoff protocol (D19)

- `docs/DEVLOG.md`: append-only. For each step: time, milestone/step, what was done, what was chosen (linked to a decision), result and evidence, issues, spend.
- `docs/DECISIONS.md`: numbered decision records with context, options, decision, rationale, consequences, date and status. A later change adds a new record that supersedes the old one; old records are never rewritten.
- `docs/STATUS.md`: always-current handoff snapshot. It covers phase, what works, what is broken, how to run, next steps and open questions. It is updated before any work session ends.
- `docs/reviews/M1.md` … `M3.md`: milestone self-reviews.
- `AGENTS.md`: how any agent, builder or reviewer, should work in this repo.
- **Local git commits** after each meaningful step, with descriptive messages. Nothing is pushed without the user's OK.

## 12. Repository layout (planned)

```
sciviz-agents/
  AGENTS.md  README.md  Makefile  .env.example
  docs/            PLAN, DECISIONS, DEVLOG, STATUS, DATA, ARCHITECTURE, reviews/
  data_pipeline/   fetch_openalex_snapshot.py, build_duckdb.py, build_catalog.py, make_sample.py
  backend/sciviz/  agents/, prompts/, tools/, harness/ (gate, budget, escalation, events, replay),
                   runtime/ (headless viz runner), api/ (FastAPI), datasets/
  frontend/        React app + iframe host runtime
  evals/           tasks.yaml, run_eval.py, results/
  demo/            recorded sessions, video script, TTS, build_video.py
  tests/
```

## 13. Budget ($50 hard cap on LLM API spend)

| Item | Estimate |
|---|---|
| M1 development runs | ~$15 |
| M2 development runs | ~$10–15 |
| M3 tuning, 4-task evaluation (both modes if affordable), rehearsal | ~$15 |
| TTS narration | under $1 |
| Buffer | ~$5 |

OpenAlex usage stays within the free daily allowance.

## 14. Risks and fallbacks

| Risk | Fallback |
|---|---|
| Deep Agents does not fully support GPT-6.2 Sol features | LangChain `create_agent` + custom `StateGraph`, same design |
| The model cannot produce a working advanced layout | Escalate to Astra; otherwise document it as incomplete |
| Budget overrun | Ledger stops at $50 and the builder asks the user |
| Browser performance on large networks | Data-size limits in the harness; agents choose filtering, aggregation or canvas rendering |
| CDN outage or version drift | Pinned versions and the local caching proxy |
| Deep Agents prompt overhead raises cost | Prompt caching, trimmed tool lists |

## 15. Out of scope (by decision)

- Multi-user use, authentication, deployment.
- Sandbox hardening beyond removing secrets from kernels (D10).
- A dedicated correctness-verification subsystem and a held-out evaluation set (D12).
- Columbia University Irving Medical Center and affiliated colleges (D4).
- Refreshing the data.
- The Design Test figure and Project 2. These are separate follow-ups; the pluggable dataset layer keeps Project 2 cheap.
