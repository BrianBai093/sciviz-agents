# Working in this repository (for any agent: builder or reviewer)

`sciviz-agents` is a multi-agent LLM system that answers natural-language questions about an OpenAlex snapshot of Columbia University's publications (2021–2024) with interactive, AI-modifiable visualizations. It is Project 1 of the WHALES Lab coding test.

## Read first
1. `docs/STATUS.md`: where things stand right now.
2. `docs/PLAN.md`: what is being built and the milestones.
3. `docs/DECISIONS.md`: why things are the way they are. Do not re-open an accepted decision silently; add a new record that supersedes it.
4. `docs/DEVLOG.md`: what has been done, in order.

## Rules
- **Generalizability is a graded requirement.** Never add chart-, layout- or technique-specific prompts, templates, workflows or code paths. Examples of forbidden content: special handling for force layouts, edge bundling, or Sankey diagrams. Prompts describe roles, contracts, process and general design principles only. The lint test in `tests/` enforces a denylist.
- **Secrets:** never print, log or commit API keys. `.env` stays untracked, and Python kernels start with keys removed from their environment.
- **Budget:** LLM spend is capped at $50 in total (see the spend ledger). Do not run large batches without checking the ledger.
- **Data:** the snapshot is frozen (2026-11-23). Do not re-download or refresh it.
- **Documentation protocol:** after each meaningful step:
  1. Append to `docs/DEVLOG.md` (what, choice, result, issues, spend).
  2. Add a record to `docs/DECISIONS.md` for any non-trivial choice.
  3. Update `docs/STATUS.md`.
  4. Make a local git commit.
  Never push without the user's explicit OK.
- **Milestones:** each ends with `docs/reviews/M<n>.md`, a self-review against the checklist in PLAN §9.

## Review guidance (for reviewer agents)
Check that:
- the code matches PLAN.md and DECISIONS.md;
- no technique-specific logic exists;
- the gate and interaction tests actually run;
- the docs reflect reality.
Report mismatches in a new file under `docs/reviews/`.
