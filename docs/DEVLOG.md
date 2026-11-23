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
