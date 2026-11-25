# Project 2 build plan: agent-driven reproduction of Wu, Wang & Evans (2019)

| | |
|---|---|
| Status | Approved 2026-11-23, with a 100-work pilot first (D47). P2-M1 and P2-M2 done; P2-M3: report, plain-language rewrite, export, design-test figure and demo video done (2026-11-25) |
| Last updated | 2026-11-24 |
| Paper | L. Wu, D. Wang, J. A. Evans, "Large teams develop and small teams disrupt science and technology", *Nature* 566, 378–382 (2019) |
| Related docs | [PLAN.md](PLAN.md) (Project 1), [DECISIONS.md](DECISIONS.md), [DEVLOG.md](DEVLOG.md), [STATUS.md](STATUS.md) |

## 0. Summary

**Goal.** Use the sciviz-agents multi-agent system, extended with a backend-only "report" mode, to reproduce the paper's main findings on the frozen Columbia OpenAlex snapshot. The run produces:
- a PDF report with written analysis and figures;
- the scripts;
- the intermediate data;
- reproduction instructions.

**Agreed choices** (with the user, 2026-11-23):

| Topic | Choice |
|---|---|
| Data | OpenAlex Columbia snapshot only (55,371 works, 2021–2024). No SciSciNet. |
| Scope | Papers only. The full set of paper-level figures: Fig 2, Fig 3, Fig 4, and the within-author regression. |
| System | Extend sciviz-agents with a report mode. No new repo. |
| Data fetching | Done by the agents, through a generic OpenAlex tool in the harness. The API key stays in the harness. |
| Citation window | Main analysis: all citations up to the snapshot, with percentiles taken within each publication year. Check: a fixed 2-year window. |
| What we can't reproduce | An explicit table: each claim of the paper, its status, why, and our number next to theirs. |
| Output, budget | PDF report. LLM spend capped at $30, cheap models first (GPT-6.2 Sol). |

## 1. Requirements traceability

| Requirement (test PDF, Project 2 T1) | Addressed in |
|---|---|
| An LLM agent system reproduces the main findings | §3 (agents do the data design, fetching, analysis, figures and writing) |
| Input is a question such as "How does team size influence the balance between disruptive and developmental research?" | §3.1 CLI |
| Output is a PDF or Word report with the findings, analysis and figures | §5 |
| Scripts, intermediate data artifacts, reproduction instructions | §6 |
| Harness engineering (recommended) | §3.2–§3.4 |
| Backend-only is acceptable | No UI work; the existing trace viewer is optional |
| Demo video of 5 minutes or less | §8, P2-M3 |

## 2. Data and what has to be fetched

**Already in `data/columbia.duckdb`:**
- `works`, with year, type, `cited_by_count`, `referenced_works_count`, `authors_count` (= team size), field and topic;
- `authorships`, which gives the authors for the within-author analysis;
- `citations`: the focal work's references, 2.32M edges to 1.47M distinct works.

**Missing, fetched by the agents through the harness tool:**
- **Forward citation counts for D.** For a focal paper *f* with reference set *R*:
  - *nᵢ* = works that cite *f* but nothing in *R*;
  - *nⱼ* = works that cite *f* and something in *R*;
  - *nₖ* = works that cite something in *R* but not *f*.

  With OpenAlex filters this is three count queries per paper: `cites:f`, `cites:f` + `cites:R…`, and `cites:R…`. The `cites:R…` filter is one OR list of at most 100 values.
  - Eligible works: at least 1 citation and 1–100 references, **36,626 works**, about **110k requests**.
  - The 4,065 works with more than 100 references are excluded and reported (mostly reviews).
  - The same queries with `publication_year ≤ y+2` give the 2-year-window check: about 110k more requests, or a 10k-paper stratified sample if the quota is tight.
- **Metadata for references (Fig 4).** Publication year and `cited_by_count` for the 1.47M distinct referenced works: about 15k batched requests of 100 IDs each.

The agent derives the query design above from the paper's definition of D; it is **not** written into prompts or code (§4). This section records the expected design so a reviewer can check the agent's choice.

## 3. Agent system (extension of Project 1)

### 3.1 Entry point
```bash
uv run sciviz reproduce --paper inputs/wu2019/paper_brief.md \
  --question "How does team size influence the balance between disruptive innovation and developmental research?"
```
- `paper_brief.md` is our own paraphrase of the public parts of the paper: the abstract, the claims, the definition of D, and what each figure shows. Nature's text is not copied.
- The run writes to `workspaces/<session>/` as in Project 1 and finishes with a `report/` folder (§5).

### 3.2 Roles

Lead, Data, Analyst and Critic are reused unchanged. Two new roles:

| Agent | Responsibility | New tools |
|---|---|---|
| **Lead** | Reads the paper brief, turns it into a list of claims to test (the "claim plan"), and delegates the work | `write_claim_plan` |
| **Data** | Designs and runs the fetch: pilot first, then the full batch job; checks coverage | `openalex_query`, `start_job` / `job_status` |
| **Analyst** | Computes the metrics, percentiles, CIs and regressions; draws the figures (matplotlib, vector PDF) | `submit_figure` (gate) |
| **Writer** (new) | Writes the report sections. Every number cites an artifact. | `write_section`, `build_report` |
| **Reviewer** (new; Critic used for text) | Checks each section against the claim plan and the artifacts: unsupported claims, numbers that don't match, overclaiming | none (structured verdict) |

### 3.3 New harness parts (all generic)

1. **`openalex_query` tool and kernel proxy.**
   - A generic GET on any OpenAlex entity with `filter`, `select`, `group_by`, `per_page`, and a count-only mode.
   - The harness holds the key. Python kernels reach OpenAlex only through a local proxy on `127.0.0.1` that adds the key, so kernels still start without secrets.
   - The proxy adds an on-disk cache (SQLite, keyed by the normalized URL), a rate limit, retries with backoff, and a request budget (default 300k).
2. **Background jobs** (`start_job`, `job_status`).
   - A job is a long-running Python script the agent writes; for example, 110k requests take about 3–4 hours.
   - Jobs run detached, write progress to the workspace, and resume after a crash, which the cache makes cheap.
   - Agents poll the status; the harness wakes the Lead when the job ends.
3. **Figure gate (`submit_figure`).**
   - Checks that the file exists and is a vector PDF plus a PNG, and that it is not blank.
   - Then the Critic does a vision review of the PNG against the claim the figure supports: readable, labelled, honest axes.
   - Up to 3 revision rounds, as in Project 1.
4. **Report builder (`build_report`).**
   - Assembles the Markdown sections, the figures and the claim table into HTML, then renders a PDF with Playwright, as for the Design Test figure.
   - Refuses the report if a number or claim lacks an artifact reference.
5. **Script export.** At the end, the code of every artifact on the lineage of a figure or table is written to `report/scripts/` in dependency order, with a `run_all.py`.

### 3.4 Flow
1. **Claim plan.** The Lead lists about 8 claims from the brief, each with the evidence needed. Expected claims: D falls with team size; citations rise with team size; the pattern holds across impact levels; it holds across fields; larger teams cite newer references; larger teams cite more popular references; the pattern holds within author; the 2-year window check.
2. **Data pilot.** The Data agent designs the fetch and pilots it on 100 papers (D47). The output is a coverage report.
   - It checks a few cases by hand: it pulls the full citer lists for 5 small papers and confirms *nᵢ*, *nⱼ*, *nₖ* against the counts.
3. **Full job.** The fetch runs as a background job, followed by a coverage report.
4. **Analysis.** The Analyst computes D, the within-year D percentile, the figures and the regressions. Each figure goes through `submit_figure`.
5. **Writing.** The Writer drafts the sections, the Reviewer checks them, and the Writer revises (up to 2 rounds).
6. **Delivery.** `build_report` produces the PDF, and the scripts are exported.

## 4. Generalizability safeguards

Project 1's rule carries over.
- **No paper-specific code or prompts.** Prompts and harness code never mention disruption, team size, D, or this paper.
- **Single source of paper knowledge.** Everything specific to the paper reaches the agents only through `paper_brief.md` and the question.
- **Lint denylist.** The existing lint test gets new denylist terms (e.g. `disrupt`, `team size`, `n_i`) for `backend/` prompts and tools.
- **Other papers.** The README shows how the same command would take another paper brief.

## 5. Report (PDF, about 8–12 pages)

1. Summary: question, data, headline answer.
2. Data and methods: the Columbia snapshot, the definition of D and how it was fetched, the citation windows, the exclusions with counts.
3. Results, one subsection per claim, with figures:
   - **R1 (≈ Fig 2):** mean D percentile and median citations vs. team size 1–10+, with bootstrap 95% CIs.
   - **R2 (≈ Fig 3):** the same curves split by impact level (citation tiers) and by OpenAlex field.
   - **R3 (≈ Fig 4):** reference age and reference popularity vs. team size.
   - **R4:** regression of D on team size with year, field and author fixed effects (within-author).
   - **R5:** robustness to the 2-year window.
4. **Comparison table:** each main claim of the paper, the status (reproduced / partly / not reproduced / out of scope), the paper's number, our number, and the reason. Patents, software, the 1954–2014 trends, and the funding and Nobel panels are marked out of scope.
5. Limitations:
   - short windows (2021–2024 works);
   - a single institution;
   - OpenAlex coverage;
   - the cap at 100 references;
   - LLM-agent caveats.
6. Reproduction: commands, run cost, number of requests, runtime.
7. Appendix: the agent trace summary (who did what, revision rounds, spend).

## 6. Deliverables in the repo

`reproductions/wu2019/` contains:
- `report.pdf`;
- `figures/` (PDF + PNG);
- `scripts/` (exported, with `run_all.py`);
- `data/` (small intermediate parquet: per-work D inputs and reference metadata aggregates; large files go into a release asset if they exceed about 50 MB);
- `REPRODUCE.md`;
- `trace/` (curated workspace: plan, claim plan, decisions, events).

The README gets a Project 2 section.

## 7. Milestones (each ends with a self-review and a check-in with the user)

**P2-M1 Harness and pilot.**
- Build: the OpenAlex tool and proxy (cache, rate limit, budget), background jobs, `submit_figure`, `build_report`, script export, the `reproduce` CLI, the paper brief, and the lint terms.
- Tests without LLM calls.
- An agent pilot run on 100 papers, done first (D47), ending with a check-in on the pilot's D numbers and the time and quota estimate.

**P2-M2 Full run.**
- The full fetch job, the analysis, and the gated figures.
- Check-in on the results before writing.

**P2-M3 Report and delivery.**
- Writing and review loop, PDF, script export, `REPRODUCE.md`, README, DEVLOG, DECISIONS, STATUS, review `docs/reviews/P2-M3.md`.
- A narrated demo video (5 minutes or less): the terminal trace and the report.
- Push only after the user's OK.

## 8. Budget and time
- **LLM:** a $30 cap on the ledger, separate from Project 1's spend. The run warns at $20.
  - Expected spend for one full run: $5–10.
  - Revision loops and reruns account for the rest.
- **OpenAlex:** about 140k–250k requests with the API key. The free key's budget is **$1 per day**: list and filter requests cost $0.0001 each (about 10k per day), and single-record lookups are free (D48). At that rate the full design takes about 1–2 weeks of daily quota. The pilot measures the real cost per work; the options (a sample, several days, or prepaid credit bought by the user) are decided at the M1 check-in.
- **Wall clock:** the fetch job takes hours and runs in the background; everything else takes minutes.

## 9. Risks and fallbacks

| Risk | Fallback |
|---|---|
| The OpenAlex daily quota is too small for 110k+ requests | A stratified sample by year × team size (for example 12k papers); the reduced N is stated in the report |
| Short citation windows make D noisy or near zero | Percentiles within year plus bootstrap CIs; the 2-year check; a weak effect is reported honestly, not tuned |
| The agent designs the D queries wrongly | The pilot's hand-checked cases; the check-in at the end of M1 |
| The Writer overclaims | The Reviewer gate, plus `build_report` refusing claims that lack an artifact |
| 4,065 works with >100 references are excluded | Reported; a sensitivity check on the D2-style subset (popular references only) if time allows |

## 10. Out of scope
- Patents and software (no team-size or citation data in our snapshot).
- Trends over 1954–2014.
- The funding, NSF and Nobel panels; novelty (Extended Data figures).
- A web UI for report mode.
