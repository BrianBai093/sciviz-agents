# P2 pilot review (100 works)

Checked against PLAN_P2 §3.4 steps 1–3 and the run constraints in `inputs/wu2019/pilot.md`.

| Check | Result |
|---|---|
| Claim plan covers every claim in the brief, with testability and reasons | Yes: 12 entries (C1–C8, C9a–d) |
| The collection follows the definition of D (later works only; set algebra, never summed overlapping counts) | Yes. Three counts per work; disjoint chunk counts for more than 99 references |
| Independent validation by the agent | 3 of 3 match (full citing records) |
| Independent validation by the reviewer, outside the agent run | 4 of 4 match: W3154161236, W4317568260, W4311732840, W3199769837 |
| Within budget | OpenAlex $0.0825 of $0.20; LLM $0.48 of $30 |
| No study-specific code or prompts | `STUDY_DENYLIST` lint passes |
| Stopped where the constraints said | Yes: no figures, no report |

**Observations**
- D sits near 0 for most works (median −0.00025), because n_k, the number of works citing the references, is large. The full analysis should use percentiles, as the study does, plus the raw D.
- The Data agent spent many requests on preflight and audit work: about 6.2 requests per work in production, and 8.3 per work including preflight, validation and the metadata audit. A full run should reuse the tested design without the audit overhead.
- 19 works have fewer live citations in the date window than the snapshot's later-year counts. The two are different measurements (live graph vs. snapshot); this is recorded, not fixed.

**Open decision for the user:** the scale of the full run, given the $1 per day OpenAlex quota (STATUS).
