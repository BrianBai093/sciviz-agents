# Decision records

Each record states the context, the options considered, the decision, and why. Records are never rewritten. A later change adds a new record that supersedes the old one, and the old record's status says so. All decisions below were made with the user during planning on 2026-11-23.

| ID | Decision | Status |
|---|---|---|
| D1 | Build Project 1 (T1–T3) first; Design figure and Project 2 later | Accepted |
| D2 | GPT-6.2 Sol for every agent | Accepted |
| D3 | Escalation model: GPT-6.2 Astra | Accepted |
| D4 | Data scope: Columbia University only, 2021–2024, ≤100 authors, snapshot 2026-11-23 | Accepted (supersedes earlier 2015–2024 scope) |
| D5 | Paradigm: Lead agent + specialist sub-agents + verification gate | Accepted |
| D6 | Harness base: LangChain Deep Agents on LangGraph | Accepted (supersedes a short-lived "custom harness" proposal) |
| D7 | Result delivery by the Lead, with artifact citations | Accepted |
| D8 | Visualizations are agent-written JS modules in sandboxed iframes | Accepted |
| D9 | Interaction: generic contract + host runtime + automated interaction tests | Accepted |
| D10 | Python runs in local Jupyter kernels; only secrets are stripped | Accepted |
| D11 | Discovery tools: npm search, package docs, OpenAI web search | Accepted |
| D12 | No correctness-verification subsystem, no held-out eval set | Accepted |
| D13 | Evaluation: 4 tasks | Accepted |
| D14 | UI layout: Chat · Views · Drawer | Accepted |
| D15 | Demo video: replay mode + scripted recording + English TTS | Accepted |
| D16 | English for UI, README, video and docs | Accepted |
| D17 | Repo name `sciviz-agents`, public, push only after the user's OK | Tentative (name not yet confirmed) |
| D18 | LLM API budget: $50 total | Accepted |
| D19 | 3 milestones with self-review and user check-in; documentation protocol | Accepted |
| D20 | Full DB as GitHub Release asset, small sample in the repo | Accepted |
| D21 | Pinned JS library versions + local caching proxy | Accepted |
| D22 | Unified visual theme tokens for all generated visualizations | Accepted |
| D23 | Pluggable dataset layer (catalog-driven) | Accepted |
| D24 | Unit tests + GitHub Actions, no LLM calls in CI | Accepted |
| D25 | Exclude works with more than 100 authors | Accepted |

---

## D1. Build Project 1 first
- **Context:** The test has Project 1 (multi-agent data-science framework with a web UI), Project 2 (paper reproduction) and a Design Test.
- **Decision:** Plan and build Project 1, tasks T1–T3, first. The Option A architecture figure is drawn after the system exists, so it matches what was built.

## D2. LLM: GPT-6.2 Sol for every agent
- **Context:** The user prefers cheap models first and moving to expensive ones only when the cheap ones fail.
- **Options:**
  - DeepSeek V4 Pro ($1.32 / $3.96 per M tokens at peak). Cheapest, supports tool calling, but no image input, and the user had no key.
  - GPT-6.2 Sol ($2 / $10). Text and image input, tool calling, and the user's existing key has access (checked with a free models-API call).
  - Claude Opus 5.5 ($4 / $20). Strongest, but pricier and needs a new key.
- **Decision:** GPT-6.2 Sol for all agents.
- **Why:** Zero setup, image input for the Critic, still in the cheap tier. Provider switching remains a configuration change.

## D3. Escalation model: GPT-6.2 Astra
- **Decision:** When a step keeps failing the verification gate, retry it once with GPT-6.2 Astra ($8 / $40).
- **Why:** Same key and provider. Escalation is capped at once per question to protect the budget (D18).

## D4. Data scope
- **Context:** The PDF allows a small, documented OpenAlex subset such as one university's papers. The user is from Columbia.
- **Facts checked on 2026-11-23:**
  - Columbia University (I78577930) has 134,328 works in 2015–2024.
  - Columbia University Irving Medical Center is a separate OpenAlex institution with 51,307 works in that period. 33,602 of them do not carry the Columbia University affiliation.
- **Options:**
  - Columbia University only, or Columbia University + CUIMC (~168k works).
  - Year range: 2015–2024 (initially chosen), then narrowed.
- **Decision:**
  - Columbia University lineage only (CUIMC and affiliated colleges excluded).
  - Publication years 2021–2024.
  - At most 100 authors (D25).
  - Result: 55,371 works, OpenAlex snapshot of 2026-11-23, never refreshed.
- **Why:** The user wants a small dataset and an unambiguous definition. The exclusions are documented in DATA.md.
- **History:** The scope was first 2015–2024 (131,355 works after D25). A download of that scope was started, then stopped at page 129 of 657 when the user narrowed the years. The partial download was set aside and not used.

## D5. Paradigm: Lead + specialists + verification gate
- **Options:**
  - Fixed pipeline: simple, but the order is hard-coded, and it risks reading as a "predefined workflow".
  - Single strong agent loop like Claude Code: flexible, but it does not satisfy the multi-agent requirement, its context fills with data, code and screenshots, and it reviews its own work.
  - Plan-and-execute: the plan is visible, but it is made before the agent has seen the data.
  - Lead + specialists + gate: dynamic, isolated contexts, independent review, multi-agent by construction.
- **Decision:** Lead + specialists + gate.
- **Why:** The Lead decides the steps dynamically, so no workflow is predefined. Specialists keep clean contexts. The Critic is independent. The handoff-loss risk is handled by fixed-schema briefs and the shared workspace.

## D6. Harness base: Deep Agents on LangGraph
- **Options:** custom harness on the OpenAI SDK; LangGraph by hand; LangChain Deep Agents; DeepSeek Harness (dsh); OpenAI Agents SDK.
- **Facts checked (2026-11):**
  - `langgraph-supervisor` is no longer maintained. LangChain recommends a main agent that calls sub-agents as tools, which matches D5.
  - Deep Agents is LangChain's harness on LangGraph. It provides planning, sub-agents with isolated context, filesystem tools, summarization, interrupts and per-sub-agent streaming, and its examples use GPT-6.x Sol.
  - dsh is DeepSeek's TypeScript coding-agent harness from August 2026. It is a developer preview with announced breaking changes.
- **Decision:** Deep Agents. If the day-0 spike fails, fall back to LangChain `create_agent` + a custom `StateGraph`.
- **Why:** The user was concerned that custom harnesses often perform poorly. The risky plumbing (state, interrupts, streaming, retries, context compression) is already solved there. Our own work goes into tools, the catalog, the viz runtime, the gate and escalation. dsh does not fit a Python data stack with a custom web UI. It may suit Project 2.
- **History:** A custom harness was briefly recommended, then withdrawn after this review.

## D7. Result delivery by the Lead
- **Decision:** No separate Reporter agent. The Lead writes the final answer, and the harness requires each claim to cite an existing artifact.
- **Why:** The Lead has the full picture, and one fewer handoff means less information loss.

## D8. Visualization representation
- **Options:** agent-written JS modules with any library; Vega-Lite specs only.
- **Decision:** JS modules, rendered in sandboxed iframes, following the contract in PLAN §4.1.
- **Why:** Vega-Lite cannot express algorithmic network layouts such as edge bundling. A module contract keeps any library usable while giving the host a uniform interface.

## D9. Interaction guarantees
- **Decision:** Interactivity is guaranteed by three things rather than left to the model:
  - the generic contract (data-bound marks, `update`, `highlight`, `setSelection`, `getState`/`setState`);
  - a host runtime written once (selection, details-on-demand, linked views, selection passed into the chat);
  - automated interaction tests inside the gate.
- AI modifications take one of three paths: parameters, highlight/filter, or code edit with hot reload.
- **Why:** This is the user's core scenario (click → details → select → ask the AI → the chart updates). The contract says nothing about chart types, so it is not hardcoding.

## D10. Execution sandbox
- **Decision:** One local Jupyter kernel per sub-task. Kernels start with an environment from which all API keys are removed. No Docker, no further hardening.
- **Why:** The user wants a demo ("just run a demo"). Removing secrets costs nothing and protects the user's key.

## D11. Discovery tools
- **Decision:** npm registry search, package README and type definitions via jsDelivr, and OpenAI's hosted web search.
- **Why:** The PDF requires that agents can select or discover algorithms and libraries.

## D12. No correctness subsystem, no held-out set
- **Context:** Proposed were data invariants, independent re-checks, ground-truth eval answers, and a dev/held-out split of eval prompts.
- **Decision:** Not built.
- **Why:** The user's call; this is a demo.

## D13. Evaluation size
- **Decision:** 4 tasks: trend chart, force-directed network, HEB, and one technique not seen before. A single-agent comparison runs on the same tasks only if the budget allows.
- **Why:** The budget is $50 and this is a demo. 12 tasks were proposed and reduced.

## D14. UI layout
- **Decision:**
  - Chat on the left.
  - 1–4 linked views in the centre, with parameter controls, versions, compare and undo.
  - A drawer on the right with Details, Trace, Artifacts and Plan.
  - A top bar with session, model and cost.

## D15. Demo video
- **Decision:** Record a scripted Playwright run over replay mode, add English TTS narration and subtitles with ffmpeg, keep it to 5 minutes or less.
- **Why:** The user prefers replay + TTS over recording live.

## D16. Language
- **Decision:** English for the UI, README, video and repo docs. Chat with the user stays in Chinese.

## D17. Repository
- **Decision:** `sciviz-agents`, public on the user's GitHub. It is pushed only after the user's explicit OK.
- **Status:** Tentative. The user has not confirmed the name yet.

## D18. Budget
- **Decision:** $50 total LLM API spend. The spend ledger warns at $35 and hard-stops at $50.

## D19. Process and documentation
- **Decision:**
  - 3 milestones: M1 data + agent core, M2 web app + interaction, M3 evaluation + docs + delivery.
  - Each ends with a self-review (`docs/reviews/M<n>.md`) and a check-in with the user.
  - DEVLOG, DECISIONS and STATUS are kept current so that another agent can take over or review at any time.
  - Local git commits after each meaningful step.
- **Why:** The user asked for checkpoints and for records good enough to hand off to another agent for review.

## D20. Data distribution
- **Decision:** Publish the full DuckDB file as a GitHub Release asset and commit a small sample database plus the rebuild scripts.
- **Why:** The full file is too large for git. Reviewers can still run the system quickly.

## D21. JS library versions
- **Decision:** Pin every imported library to an exact version at submission, and serve libraries through a local caching proxy.
- **Why:** Saved visualizations keep working later and offline.

## D22. Unified theme
- **Decision:** The runtime passes theme tokens (fonts, palettes, light/dark) to every module.
- **Why:** Generated charts otherwise look inconsistent. The theme covers style only, not chart choice.

## D23. Pluggable datasets
- **Decision:** A dataset is a DuckDB connection plus a catalog, and agents learn about data only through catalog tools.
- **Why:** Project 2 (SciSciNet) can reuse the agents without code changes.

## D24. Tests and CI
- **Decision:** Unit tests for harness components, plus the no-hardcoding lint test, run in GitHub Actions. CI makes no LLM calls.

## D25. Exclude works with more than 100 authors
- **Facts:**
  - 2,973 Columbia works in 2015–2024 have more than 100 authors, and 1,023 have more than 1,000.
  - OpenAlex list endpoints return only the first 100 authorships per work.
- **Decision:** Drop these works from the dataset entirely (filter `authors_count:<101`).
- **Why:** Their author lists are truncated, and they would add millions of edges to co-authorship networks. User's decision.

---

## Decisions made during M1

| ID | Decision | Status |
|---|---|---|
| D26 | One persistent Python kernel per (session, agent) instead of per sub-task | Accepted (refines PLAN §3.2) |
| D27 | Reasoning effort: Lead medium, Data/Analyst medium, Viz high, Critic high | Accepted (PLAN said Lead high) |
| D28 | Host runtime handles clicks/hovers and default selection styling | Accepted |
| D29 | Generic interaction tests in the gate | Accepted |
| D30 | Sample DB is a 3% hash sample (11 MB) | Accepted |
| D31 | Remove shell `execute` and the generic sub-agent; Lead's file tools are read-only | Accepted |
| D32 | `highlight()` and `setSelection()` take items, not bare ids | Accepted (refines PLAN §4.1) |
| D33 | The Critic knows the host renders parameter controls | Accepted |
| D34 | Viz agent at medium reasoning effort (user decision after M1) | Accepted (supersedes part of D27) |
| D35 | Browser views load pinned CDN URLs directly; the disk cache serves the headless gate | Accepted (narrows D21) |
| D36 | UI state is derived from the event stream; user actions are logged as events | Accepted |
| D37 | View iframes start from manifest defaults; the UI pushes parameters derived from events | Accepted |
| D38 | Gate adds a multi-item selection/highlight and state round-trip test | Accepted |
| D39 | Narrow panels render views at ≥720 px and scale down; a compared view spans the full width | Accepted |
| D40 | Single-agent ablation mode with the same tools and gate | Accepted |
| D41 | Process-safe ledger; cost events are the source of truth | Accepted |
| D42 | The Critic reviews each view in isolation, against checkable criteria | Accepted |
| D43 | Atomic, locked view-state updates; tool exceptions are returned to the model | Accepted |
| D44 | Retry a failed turn by forking from the last good checkpoint | Accepted |

## D26. Kernel lifetime
- **Decision:** One persistent kernel per (session, agent).
- **Why:** Simpler, and an agent keeps its working state across calls in a session. Artifacts remain the only official handoff between agents, and every artifact records the code that produced it.

## D27. Reasoning effort per role
- **Decision:** Lead medium (PLAN said high), Data/Analyst medium, Viz high, Critic high.
- **Why:** The Lead mostly coordinates and is called often, so medium effort saves budget. Quality-critical work (writing view code, reviewing views) keeps high effort. To be revisited if the Lead's planning quality is poor.

## D28. Runtime-owned interaction handling
- **Decision:** The host runtime turns clicks and hovers on data-bound marks into selections and details through event delegation. Modules only tag their marks. When a module does not implement `setSelection`/`highlight`, the runtime applies default CSS feedback (`sv-selected`, `sv-dimmed`, `sv-highlight`).
- **Why:** Interactivity is guaranteed by the runtime rather than by each generated module (D9).

## D29. Interaction tests
- **Decision:** Every submitted view must pass these generic checks:
  - hovering a mark emits a hover event;
  - clicking emits a selection whose ids appear in the bound data;
  - selection and highlight each change at least 0.05% of pixels;
  - each declared parameter re-renders without errors and with a visible change.

## D30. Sample DB size
- **Decision:** A 3% hash sample (1,661 works, 11 MB) instead of "a few MB".
- **Why:** The full topic table and the citation rows dominate the size. 11 MB is still fine for git.

## D31. Tool surface
- **Decision:** A harness profile removes the shell `execute` tool (no sandbox backend) and Deep Agents' generic `general-purpose` sub-agent, so all work goes to the specialists. The Lead's filesystem tools are restricted to `ls` and `read_file`.

## D32. Item-based selection API
- **Decision:** `highlight(items)` and `setSelection(items)` take items (`{type, id}` or `{type, key}`) rather than bare ids.
- **Why:** Aggregated marks are identified by grouping keys, not ids.

## D33. The Critic knows about host-rendered parameter controls
- **Context:** In Q3, the Critic rejected V2 because the declared filters had no visible in-view widgets. The Viz prompt, meanwhile, tells modules not to build such widgets, because the host app renders controls for declared parameters.
- **Decision:** The Critic prompt says host controls exist outside the screenshots, and the review message lists the declared parameters (name, title, default). The Critic judges whether the parameters are meaningful, not whether they have widgets inside the view.
- **Status:** Accepted.

## D34. Viz agent reasoning effort: medium
- **Context:** M1 review issue 1. Questions took 6.5–11.5 min, and the Viz agent accounted for about 70% of model calls and cost at high effort.
- **Decision:** The user chose to run Viz at medium effort from M2 on. The Critic stays at high effort, and escalation to GPT-6.2 Astra stays on as the safety net. Supersedes the Viz part of D27.
- **Status:** Accepted (user decision, 2026-11-23).

## D35. Browser views load pinned CDN URLs directly
- **Context:** PLAN §4.2 / D21 planned a local caching proxy for every JS library load. In the browser, esm.sh modules import further root-relative paths, so routing them through a same-origin proxy would mean rewriting module bodies plus an import map.
- **Decision:** Views in the browser load their pinned, exact-version CDN URLs directly. The disk cache is still used by the headless gate. Pinning keeps results reproducible, because pinned CDN builds are immutable.
- **Limitation:** viewing views in the UI needs internet access for the libraries.
- **Status:** Accepted (narrows D21).

## D36. The UI state is derived from the event stream
- **Decision:** The React store is a pure function of the session's events: messages, views, parameters, highlights, selections, artifacts, plan, costs. User actions in the UI are posted to the API and logged as events (`user` / `view` / `select`): parameter changes, version switches and selections.
- **Why:** Replay mode is then just a re-stream of `events.jsonl` with time scaling. It reproduces both the agents' work and the user's interactions, needs no API key, and makes no LLM calls.
- **Status:** Accepted.

## D37. View iframes start from manifest defaults
- **Decision:** `view.html?fresh=1` starts a view from its manifest defaults, and the UI pushes the parameter values derived from events once the view reports `ready`. During a replay, a view therefore shows the parameters of the moment being replayed, not the final ones.
- **Status:** Accepted.

## D38. Gate: multi-item and state round-trip interaction test
- **Context:** A view passed the gate but failed in the UI. Highlighting several items, or restoring zoom state after a version swap, called d3 transition methods that were never imported.
- **Decision:** A new generic test, `multi_item_and_state`. It selects and highlights up to 3 items at once and, if the module implements `getState`, does a `getState` → `setState` round trip. Any error fails the gate.
- **Status:** Accepted.

## D39. View sizing in the UI
- **Decision:** Panels narrower than 720 px render the view at 720 px wide and scale it down with a CSS transform. The browser maps pointer events correctly, so interaction still works. A view in compare mode spans the full grid width.
- **Why:** Generated views are designed and reviewed at desktop size (1200×800). Squeezing them into 400 px broke their layouts.
- **Status:** Accepted.

## D40. Single-agent ablation mode
- **Decision:** `build_single_agent` is one Deep Agent with all of the multi-agent system's tools, the same verification gate, and a prompt assembled from the same role prompts. It runs at medium effort. Only the architecture differs: no delegation, no context isolation, no Lead/worker split.
- **Why:** To answer "why multi-agent?" with measurements (D13).
- **Status:** Accepted.

## D41. Process-safe spend ledger; events are the source of truth
- **Context:** Two processes running in parallel corrupted `_ledger.json` through a shared temp file name (see DEVLOG M3).
- **Decision:**
  - An exclusive `fcntl` file lock around every read-modify-write, with unique temp files and an atomic replace.
  - Each model call's `cost` event is written to the session's `events.jsonl` before the ledger is updated, and a damaged ledger is rebuilt from those events.
  - Ledger failures can no longer break an agent run.
- **Status:** Accepted.

## D42. Each view is reviewed in isolation, against checkable criteria
- **Context:** In the demo session, the Viz agent passed acceptance criteria such as "side by side with V1" and "a 420×625 layout" to the gate. The Critic rejected an edge-bundling view twice (answers_question 3/5) for missing evidence of things one view's screenshots cannot show, and asked for "verification" of exact routing. The view was only approved on the next turn.
- **Decision:**
  - The Critic reviews one view in isolation. Cross-view placement and linking, and other viewport sizes, are the host's job.
  - The Critic must not reject a view for evidence the gate cannot provide, and ignores criteria that cannot be checked from a single view.
  - The Viz prompt says to pass only criteria checkable from the view itself.
- **Status:** Accepted.

## D43. Atomic view-state updates; tool failures go back to the model
- **Context:** In the demo session the Lead called `highlight_view` for two views as parallel tool calls. One read `views.json` while the other was rewriting it, got an empty file, raised `JSONDecodeError`, and the exception aborted the whole agent run.
- **Decision:**
  - `views.json` is written atomically (temp file + replace), and every read-modify-write runs under a lock (`Workspace.update_views`, also used by `show_view` and the API).
  - Every agent has LangChain's `ToolErrorMiddleware`, so any tool exception becomes an error `ToolMessage` the model can react to instead of halting the run.
- **Status:** Accepted.

## D44. Retry a failed turn from the last good checkpoint
- **Decision:** `run_turn(..., from_checkpoint=<id>)` forks the conversation from an earlier LangGraph checkpoint, so a crashed turn can be retried without the failed attempt in the agents' context. It was used once to repair the demo session (`demo/continue_demo.py`). The event log is truncated to match.
- **Status:** Accepted.
