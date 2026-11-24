"""External data tools (Project 2): one exploratory OpenAlex request per call.

Bulk collection happens in `run_python` with `openalex(...)` / `openalex_many(...)`, which go through the
same harness service (cache, rate limit, budget) via the local proxy.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

from ..harness.openalex import ExternalBudgetExceeded, OpenAlexError
from ..session import Session
from .data_tools import _emit_call, _emit_result
from .python_exec import truncate

API_NOTES = """
OpenAlex REST API notes:
- Paths: entity lists such as `works`, `authors`, `sources`, `institutions`, `topics`, or one record such as
  `works/W2741809807`.
- `filter`: `field:value` pairs joined by commas (AND). Within one field, `|` means OR (at most 100 values per
  field), and a leading `!` negates a value. Examples of fields on works: `cites` (works whose reference list
  contains the given work), `cited_by`, `referenced_works`, `ids.openalex`, `publication_year`,
  `from_publication_date` / `to_publication_date` (YYYY-MM-DD), `authorships.author.id`, `type`.
- `select`: comma-separated top-level fields to return (smaller, faster responses).
- `per_page`: 1-200. `cursor=*` starts cursor paging; continue with `meta.next_cursor`.
- `meta.count` is the number of matching records; with `per_page=1` a request is effectively a count.
- `group_by=<field>` returns counts per value of that field in `group_by`.
- Cost: list requests (anything returning a list, including counts and group_by) are charged against a
  session budget and the key's daily budget; single-record lookups are free; cached responses are free.
"""


def openalex_tools(s: Session, agent: str):
    @tool
    def openalex_query(path: str, params: dict | None = None, max_chars: int = 4000) -> str:
        """Send one GET request to the OpenAlex API through the harness (key, cache, rate limit and budget are
        handled for you) and return the JSON response, trimmed to `max_chars`. Use it to explore the API and
        check filter semantics on small cases; collect data in bulk with `openalex_many` in `run_python`.
        """
        _emit_call(s, agent, "openalex_query", {"path": path, "params": json.dumps(params or {})})
        try:
            data = s.openalex.get(path, params or {})
            text = truncate(json.dumps(data, ensure_ascii=False), max(500, min(max_chars, 20000)))
            ok = True
        except (OpenAlexError, ExternalBudgetExceeded, ValueError) as e:
            text, ok = f"Request failed: {e}", False
        text += "\n" + s.openalex.usage_text()
        _emit_result(s, agent, "openalex_query", ok, text)
        return text

    openalex_query.description += API_NOTES
    return [openalex_query]
