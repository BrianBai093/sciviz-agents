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

## D45. Publishing
- **Decision:** a public GitHub repository, https://github.com/BrianBai093/sciviz-agents. The full database (173 MB) is a release asset (v1.0.0), not a repository file. The 3% sample (for a quick look), the recordings (replay mode) and the demo video stay in the repository.
- **Status:** Accepted.

## D46. Architecture figure (Design Test, Option A)
- **Decision:** the figure is an SVG drawn by a Python script (`docs/figures/build_architecture_figure.py`) and rendered to PDF and PNG with Playwright, not made in a drawing tool. This makes it reproducible and diffable, and it uses the same colors as the app. The layout and the level of detail were chosen with the user: three stages plus a feedback loop, concept names plus a few code names, and abstract icons.
- **Status:** Accepted.

## D47. Project 2 scope (agreed with the user)
- **Decision:**
  - Reproduce Wu, Wang & Evans (2019) on the Columbia OpenAlex snapshot only, covering the paper-level claims.
  - Build it as a report mode of sciviz-agents.
  - The agents fetch the missing citation data themselves through a harness tool.
  - D uses all citations to date, with a fixed 2-year window as a check.
  - The report has an explicit table of what could not be reproduced.
  - The deliverable is a PDF; LLM spend is capped at $30, with its own ledger.
  - The user asked for a **100-work pilot first**, before the rest of M1 (figure gate, report builder, background jobs).
- **Why:** checks the data-collection design and its cost before building the parts that only the full run needs. Plan: `docs/PLAN_P2.md`.
- **Status:** Accepted.

## D48. External API access lives in the harness
- **Decision:** `harness/openalex.py`.
  - The key stays in the harness process.
  - Kernels call a local proxy on 127.0.0.1 and have no secrets (D10 still holds).
  - Every response is cached in SQLite, keyed by path plus sorted params, without the key (`data/openalex_cache.sqlite`). Fetched data is therefore frozen on first fetch, and reruns are free.
  - Requests are rate-limited (10/s) and retried with backoff.
  - Cost is charged to a per-session USD budget, using the `x-ratelimit-cost-usd` header that OpenAlex returns.
  - Only entity paths are allowed; account endpoints are not.
- **Why:** OpenAlex now meters usage per key. The free key has a **$1 daily budget**: list and filter requests cost $0.0001 each (about 10,000 per day), and single-record lookups are free. A runaway agent loop could burn the day's quota, so the harness must enforce the budget, not the prompt.
- **Status:** Accepted.

## D49. Study knowledge enters only through the paper brief
- **Decision:**
  - `inputs/wu2019/paper_brief.md` is our own summary of the study's public abstract and captions, not copied text.
  - It is the only place that names the measure or the claims.
  - Prompts and harness code stay generic. A second lint list (`STUDY_DENYLIST` in `tests/test_no_hardcoding.py`) enforces this.
  - Run limits, such as the pilot, come from a constraints file the user passes to `sciviz reproduce`.
- **Status:** Accepted.

## D50. Full-run scale: an 8,000-work sample stratified by team size
- **Decision (user, after the pilot):**
  - About 8,000 eligible works, stratified by team size (1, 2, …, 10, 11–20, 21–50, 51–100 authors), allocated as equally as possible across strata, seed 42.
  - Inclusion probabilities are kept; population-level estimates use sampling weights.
  - The user bought $3 of OpenAlex prepaid credit. The run's external budget is $3.50.
- **Why:** the full population (40,541 works) needs about 130k–189k paid requests ($13–19). The equal allocation also gives each team size enough works for confidence intervals, which a proportional sample would not give the rare large teams.
- **Status:** Accepted.

## D51. Remaining report-mode harness: jobs, figure gate, report gate, export with offline replay
- **Background jobs** (`harness/jobs.py`): agent-written scripts run in their own process with the kernel's helpers. Artifacts they create are tagged with their code.
- **Figure gate** (`submit_figure`):
  - automated file checks (a vector PDF, a PNG that is not blank);
  - then an independent vision review that scores support for the claims, truthfulness, readability and the caption;
  - at most 3 rounds, then the figure is accepted with its issues flagged.
- **Report gate** (`submit_report`):
  - mechanical checks: cited ids exist, figures are approved, and every paragraph or table with a statistic cites an artifact;
  - then an independent reviewer that scores support, coverage of the claim plan, honesty and clarity;
  - at most 3 rounds; after that, the open issues are appended to the report;
  - finally, HTML and a PDF rendered with Playwright, with an evidence index.
- **Cell log and export** (`sciviz export-run`):
  - Every code cell, including failed ones and background jobs, is logged in order with the artifacts it created.
  - The export package holds the report, figures, all data artifacts, the frozen subset of API responses, the cells, and `run_all.py`.
  - `run_all.py` replays every cell offline (with the same helpers, the original artifact ids, and API responses served from the frozen file) and compares the results with the original artifacts. A test covers this.
- **Why:** PLAN_P2 asks for scripts, intermediate data and reproduction instructions. Replaying the agents' own cells is more faithful than a rewritten script, and the frozen API responses make it runnable without a key or network.
- **Status:** Accepted.

## D52. Stage-2 corrections before the report (user, 2026-11-24)
- **Decision:**
  - Main analysis population: works with at least one citing work in the window, in each window separately, as in the study. The stage-1 population (every work with a defined score, including 64 with no citing work) is kept as a robustness column next to every headline estimate.
  - Intervals: a bootstrap that resamples works within every team-size stratum, the fully sampled 51–100 stratum included, without a finite-population correction. The intervals describe uncertainty about the pattern, not only about this finite set of works.
  - For the claim on reference age and popularity, the empirical layout (P12) replaces P9; stage 2 redrew it as P17.
- **Why:** the stage-1 design-based intervals were near zero for the census stratum, and the stage-1 main estimates mixed in works the study would exclude. Both were found in the M2 review (`docs/reviews/P2-M2.md`).
- **Status:** Accepted.

## D53. Faithful offline replay: everything a cell can read is restored in time order
- **Problem:** the first replay of the full run failed from cell 10 on. The agents' cells read files that no cell had written: background-job scripts and logs, the harness's cell log, figure files registered by the figure gate, and scripts the agents had written with their file tools (`write_file`, `edit_file`). In addition, a continued session restarted job ids at `job1` and overwrote the stage-1 job folders.
- **Decision:**
  - Job ids are unique within a workspace, also across turns. At shutdown, jobs that still run are stopped and every unrecorded job goes to the cell log, marked `stopped` when a signal ended it; the replay restores its files but does not run it.
  - Files written with the agents' file tools are logged with their full content (`file_log.jsonl`, `harness/file_log.py`).
  - The export includes job folders, the file log and the figure artifacts. `run_all.py` restores them, and the cell log, at the time they appeared, interleaved with the cells.
  - A cell that fails in the replay but succeeded in the run (for example a check against the live API's usage counter) is reported, and the replay continues with the artifacts that cell made in the run.
  - Tables count as identical when only their row order differs (parallel requests return rows in any order). The offline API service reports an unlimited budget, since it spends nothing.
- **For session `r-full-8k`, recorded before these fixes:**
  - The scripts of the two stage-1 jobs the agent had stopped were rebuilt from artifact J3 by undoing the agent's two edits. They match the event log's truncated copy: the length, the first 500 and the last 1,000 characters.
  - The file-tool writes were rebuilt from the LangGraph checkpoints (`backfill_from_checkpoints`). The rebuilt final contents match the files on disk.
- **Why:** a replay that diverges for bookkeeping reasons hides whether the analysis itself reproduces. With these fixes every remaining difference has a reason that can be read from the artifact titles.
- **Status:** Accepted.

## D54. The harness writes the run record; continued sessions keep each turn's record
- **Decision:**
  - `sciviz export-run` appends a run record to the released report: one row per turn (start, wall time, LLM calls and spend, API requests and spend, background jobs, figure and report reviews), LLM spend by agent, and counts of cells, artifacts and figure versions. It is computed from the event log, the usage files, the cell log and the artifact store. The report is then rendered again, with its figures inside the package.
  - The Writer was told not to estimate times or costs.
  - When a session continues, the CLI first moves the previous turn's constraints, lead report and API usage to `history/turnN/`.
- **Why:** the agents cannot know the run's cost or wall time, and a model would guess them. The harness has the exact numbers. Before this, the second turn overwrote the first turn's lead report and usage file.
- **Status:** Accepted.

## D55. The reproduction package keeps the frozen API responses in the repository, compressed
- **Decision:** `reproductions/wu2019/data/api_responses.sqlite.xz` (37 MB; 126 MB unpacked) is committed with the package, and `run_all.py` unpacks it on first use. The data artifacts add 36 MB.
- **Alternatives:** a GitHub release asset (one more publishing step, and the package is no longer self-contained); leaving the responses out (the replay then reuses the recorded artifacts of the collection cells instead of recomputing them).
- **Why:** both files stay well under GitHub's 100 MB file limit, and the package runs offline right after a clone.
- **Status:** Accepted.

## D56. Reader-facing text must be plain; the report gate adds a reader who sees only the report
- **Problem:** the user found the released Project 2 report hard to read. It used the team's working labels ("strict domain", "comparator", "proxy frame", "Stage 2", "F>0"), symbols in running text and long qualified sentences; the figure titles and captions did too. The report reviewer had passed it with clarity 4 of 5: it reads the claim plan and the evidence, which use the same labels, so they did not look like jargon to it.
- **Decision:**
  - One set of plain-language rules (`prompts/plain_language.md`) for everything a reader sees: everyday words and short sentences; no names the team made up (labels for samples, groups, checks, stages, versions; variable, code or file names); standard terms explained at first use; no symbols in running text, and at most one formula per measure, explained in words with a worked example; numbers rounded to what a reader needs; the final analysis, not the history of the work; plain figure titles and captions. The writer and the analyst get the rules; the figure gate checks titles, captions and labels against them.
  - The report gate has a second, independent check: a reader who gets only the report, with each figure's title and caption in place (`rep.reader_text`), and lists every word, label or sentence a researcher from a neighbouring field could not follow, with plain wording. A report passes only when both the reviewer and the reader pass it. The gate allows 4 rounds (was 3), since it is stricter.
  - The writer no longer writes a how-to-reproduce section or an account of the team's process. The export adds a plain "How to reproduce this report" section, written by the harness, which knows the package, next to the run record.
  - The writer's file tools are read-only (`ls`, `read_file`, `glob`, `grep`); sections change only through `write_section` and the new `remove_section`. In stage 2 the writer had edited sections with `edit_file`, outside the section checks.
  - When a session continues, the released report and its gate reviews are also archived under `history/turnN/report/`.
  - The evidence index in the PDF lists each cited artifact under the title the agents gave it while working, and says so; the long working descriptions are left to the package.
- **Why:** the user's instruction ("write it for people, in plain language, with no made-up terms"). A reviewer that shares the authors' vocabulary cannot judge readability; a reader without that context can. The rules are generic: they name no study, measure or technique.
- **Status:** Accepted.

## D57. Review criteria that converge: figures are judged on testing a claim; the reader is bounded
- **Problem (seen in stage 3, D56's first run):**
  - The figure review marked figures down when the study's claim did not hold in our data ("revise the claim, not the plot"). No caption can fix that, so two figures for claims that reproduced only in part ran into the round limit and were accepted with open issues, after several futile resubmissions.
  - The new reader check did not converge. It reviewed the whole report, appendix and figure captions included, listed every problem it found (about 50, then 63), and called most of them major. The writer answered each point by adding explanation, so the draft grew from 7,100 to 8,300 words and the reader found more to question. The user's instruction was a plainer, less dense report; the run was stopped in round 2.
  - The reviewer passed "Lu Wu" for the brief's "L. Wu" (a first name the writer guessed).
- **Decision:**
  - Figure review: `supports_claims` scores whether the figure tests the listed claims, not whether they hold; a figure showing that a claim held only in part serves the report as well, if its caption says so. The claims' wording is not part of the review.
  - Reader check: it judges the main text; sections titled "Appendix" are checked only for made-up labels; figure captions are context, since the figure gate reviews them under the same rules. At most 12 problems, most important first. "Major" means a reader cannot follow a main method or result, or a made-up label. It passes when no major problem remains, and it prefers fixes that shorten or simplify.
  - Writer: fix readability by rewriting more simply, cutting or moving detail to the appendix, not by adding explanation. Add nothing about the study that the brief does not say. The reviewer checks statements about the study against the brief.
  - A stopped turn (constraints but no lead report) is archived like a finished one when the session continues.
- **Why:** a gate that cannot be satisfied by the work under review produces loops and longer text instead of better text. These rules keep each check on what its author can fix.
- **Status:** Accepted.

## D58. The report reviewer sees all cited evidence; only evidence problems are appended to a released report
- **Problem:**
  - The reviewer's evidence was cut at 60,000 characters, in artifact order. With 170 artifacts (26 new figure versions with long captions among them) it received 60k of 161k characters, and cited tables such as T75–T77 and T87 were not in it, so it could not check numbers taken from them. Earlier reviews of this run were also partly blind to late tables; the reviewer's own spot checks of the main numbers (and mine) had covered the findings.
  - A report released after the last round carried every open point, including the reader's wording suggestions, as an "Open review issues" section.
- **Decision:**
  - `evidence_text` puts every finding first, then every artifact the report cites (title, description, summary, and the rows of small tables or the data of JSON artifacts), then one line for each artifact it does not cite. The budget is 150,000 characters; for this report everything fits (134k).
  - After the last round, the reviewer's unresolved issues are appended to the report (a reader must know about unresolved evidence problems). The reader's unresolved points go to `status.json` and the review log, and the run record mentions them.
- **Status:** Accepted.
