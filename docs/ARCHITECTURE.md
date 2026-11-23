# Architecture (developer guide)

How the code is organized and how one question flows through the system. For the reasons behind each choice see
[DECISIONS.md](DECISIONS.md); for the plan see [PLAN.md](PLAN.md).

## Code map

| Path | What it does |
|---|---|
| `backend/sciviz/config.py` | Settings from env vars; model price table |
| `backend/sciviz/datasets.py` | Pluggable dataset = DuckDB file + catalog. All of the agents' knowledge about data comes from here. |
| `backend/sciviz/session.py` | `Session`: workspace, dataset, event log, spend ledger, kernels, gate state, escalation flags |
| `backend/sciviz/harness/workspace.py` | Artifact store (tables, graphs, trees, json, findings, viz) with lineage, decision log, view state |
| `backend/sciviz/harness/events.py` | Append-only JSONL event log with live subscribers (CLI now, SSE/UI and replay later) |
| `backend/sciviz/harness/budget.py` | Spend ledger with a hard stop, and a LangChain callback that prices every model call per agent |
| `backend/sciviz/tools/python_exec.py` | Jupyter kernel per (session, agent), with secrets removed from its environment and a helper prelude |
| `backend/sciviz/tools/data_tools.py` | Catalog tools, read-only SQL, Python, artifact inspection, decisions |
| `backend/sciviz/tools/discovery_tools.py` | npm search and package docs, so agents can discover libraries and algorithms |
| `backend/sciviz/tools/viz_tools.py` | `render_preview` and `submit_viz` (the verification gate, including escalation) |
| `backend/sciviz/tools/lead_tools.py` | Show views, set view parameters, highlight items, ask the user (interrupt) |
| `backend/sciviz/agents/critic.py` | Independent Critic: structured verdict from screenshots, automated checks and data summary |
| `backend/sciviz/agents/models.py` | Model per role (reasoning effort), escalation middleware, trace callback |
| `backend/sciviz/agents/build.py` | Assembles Lead + sub-agents on Deep Agents |
| `backend/sciviz/prompts/*.md` | Role prompts. They contain no technique-specific content; `tests/test_no_hardcoding.py` enforces this. |
| `backend/sciviz/runtime/static/host.{html,js}` | The generic visualization runtime used by the gate (headless) and, in M2, the UI (iframe) |
| `backend/sciviz/runtime/cdn.py` | Import pinning to exact npm versions; disk cache for CDN responses |
| `backend/sciviz/runtime/renderer.py` | Headless rendering (Playwright), layout metrics, screenshots, interaction tests |
| `backend/sciviz/cli.py` | `sciviz ask`, `sciviz cost` |
| `data_pipeline/` | Snapshot download, DuckDB build, catalog/DATA.md generation, sample DB |

## One question, end to end

1. **CLI / UI** creates or loads a `Session` and builds the agent graph. The Lead's system prompt contains the
   session's artifact index, decisions and views. The user message is sent, together with the current selection
   if there is one.
2. **Lead** (Deep Agents main agent; tools: `write_todos`, `task`, artifact inspection, view tools, `ask_user`):
   - plans;
   - records definitions;
   - delegates with a fixed-schema brief (USER QUESTION, GOAL, INPUTS, DEFINITIONS, ACCEPTANCE CRITERIA, OUTPUT).
3. **Sub-agents** (`data`, `analyst`, `viz`) run their own tool loops in isolated contexts:
   - they read data only through catalog tools, SQL and Python;
   - they save results as artifacts with lineage;
   - they return a structured report to the Lead.
4. **Viz** writes `/viz/<slug>/module.js` and `viz.json` into the session workspace, iterates with
   `render_preview` (it can look at the screenshots), and then calls `submit_viz`.
5. **Gate** (`submit_viz`), run as code and not left to the model:
   1. Validate the manifest and data bindings, and enforce the data size limit.
   2. Syntax-check the module with Node and pin its imports.
   3. Register a new viz artifact version.
   4. Render headlessly and run the interaction tests.
   5. If any of this fails, reply REVISE without calling the Critic.
   6. Otherwise call the Critic. Its verdict marks the artifact `approved` or `rejected`.
   7. After 3 failed rounds, the Viz agent is escalated to the stronger model once. After that the best renderable version is delivered as `approved_with_issues`.
6. **Lead** shows approved views (`show_view`) and answers. Every claim cites an artifact id.
7. **Everything is an event** in `workspaces/<session>/events.jsonl`: delegations, reports, tool calls and results, artifacts, gate verdicts, views, costs. This file drives the CLI output now and the UI trace and replay mode later.

## Visualization contract (summary)
- A module exports `render(el, ctx)` and returns `update`, `setSelection`, `highlight` and, optionally, `getState`/`setState`/`destroy`/`pick`.
- Data-bound marks carry either `data-id` + `data-type` (one entity) or `data-key` (an aggregated group).
- The runtime turns clicks into selections and hovers into details. It also applies default selection styling when a module does not implement its own.
- Full text: the Viz prompt (`backend/sciviz/prompts/viz.md`) and the header comment of `host.js`.

## Where state lives

| State | Location |
|---|---|
| Conversation and agent state | `workspaces/<session>/checkpoints.sqlite` (LangGraph checkpointer) |
| Artifacts | `workspaces/<session>/artifacts/<id>/` (`meta.json` + data/module/screenshots) |
| Agent-authored view sources | `workspaces/<session>/viz/<slug>/` |
| Spend | `workspaces/_ledger.json` |
| CDN cache | `.cdn_cache/` |
