#!/usr/bin/env python3
"""Profile a DuckDB dataset and merge the profile with hand-written semantics.

Outputs
  - <catalog>.yaml : machine-readable catalog read by the agents' catalog tools
  - DATA.md        : human-readable data documentation

Usage:
  uv run python data_pipeline/build_catalog.py --db data/columbia.duckdb \
      --semantics catalog/columbia_semantics.yaml --out catalog/columbia.yaml --doc docs/DATA.md
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import yaml

LOW_CARDINALITY = 30
NUMERIC_PREFIXES = ("BIGINT", "INTEGER", "DOUBLE", "FLOAT", "DECIMAL", "HUGEINT", "SMALLINT", "TINYINT")


def plain(v):
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, float):
        return round(v, 4)
    if isinstance(v, str) and len(v) > 80:
        return v[:77] + "..."
    return v


def profile(con: duckdb.DuckDBPyConnection) -> dict:
    out = {}
    for (table,) in con.execute("SELECT table_name FROM information_schema.tables ORDER BY table_name").fetchall():
        n = con.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
        cols = {}
        for name, typ in con.execute(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position",
            [table],
        ).fetchall():
            q = f'"{name}"'
            nulls, distinct = con.execute(
                f'SELECT count(*) - count({q}), approx_count_distinct({q}) FROM "{table}"'
            ).fetchone()
            info = {"type": typ, "null_pct": round(100 * nulls / n, 1) if n else 0.0, "distinct": int(distinct)}
            if typ.startswith(NUMERIC_PREFIXES) or typ in ("DATE", "TIMESTAMP"):
                lo, hi = con.execute(f'SELECT min({q}), max({q}) FROM "{table}"').fetchone()
                info["range"] = [plain(lo), plain(hi)]
            if typ == "BOOLEAN" or (typ == "VARCHAR" and distinct <= LOW_CARDINALITY):
                rows = con.execute(
                    f'SELECT {q}, count(*) c FROM "{table}" WHERE {q} IS NOT NULL GROUP BY 1 ORDER BY c DESC LIMIT 12'
                ).fetchall()
                info["top_values"] = {str(plain(v)): c for v, c in rows}
            elif typ == "VARCHAR":
                rows = con.execute(f'SELECT DISTINCT {q} FROM "{table}" WHERE {q} IS NOT NULL LIMIT 3').fetchall()
                info["examples"] = [plain(r[0]) for r in rows]
            cols[name] = info
        out[table] = {"row_count": n, "columns": cols}
    return out


def merge(prof: dict, sem: dict) -> dict:
    tables = {}
    for t, p in prof.items():
        st = sem.get("tables", {}).get(t, {})
        cols = {}
        for c, info in p["columns"].items():
            cols[c] = {"description": st.get("columns", {}).get(c, ""), **info}
        tables[t] = {"description": st.get("description", ""), "row_count": p["row_count"], "columns": cols}
    return {
        "dataset": sem.get("dataset", {}),
        "tables": tables,
        "relationships": sem.get("relationships", []),
        "entities": sem.get("entities", {}),
    }


def render_md(cat: dict, db_path: str) -> str:
    ds = cat["dataset"]
    lines = [f"# Data: {ds.get('title', '')}", "", ds.get("description", "").strip(), ""]
    lines += ["## Scope exclusions", ""] + [f"- {x}" for x in ds.get("scope_exclusions", [])] + [""]
    lines += ["## Caveats", ""] + [f"- {x}" for x in ds.get("caveats", [])] + [""]
    lines += ["## Counting rules", ""] + [f"- {x}" for x in ds.get("counting_rules", [])] + [""]
    lines += ["## Tables", "", "| Table | Rows | Description |", "|---|---:|---|"]
    for t, info in cat["tables"].items():
        lines.append(f"| `{t}` | {info['row_count']:,} | {info['description']} |")
    lines.append("")
    for t, info in cat["tables"].items():
        lines += [f"### `{t}`", "", info["description"], "", "| Column | Type | Nulls | Distinct | Description |",
                  "|---|---|---:|---:|---|"]
        for c, ci in info["columns"].items():
            lines.append(f"| `{c}` | {ci['type']} | {ci['null_pct']}% | {ci['distinct']:,} | {ci['description']} |")
        lines.append("")
    lines += ["## Relationships", ""] + [f"- `{r}`" for r in cat["relationships"]] + [""]
    lines += ["## Rebuild", "", "```bash",
              "# 1. download the raw snapshot (needs OPENALEX_API_KEY); the published snapshot date is 2026-11-23",
              "python3 -I data_pipeline/fetch_openalex_snapshot.py --out <snapshot_dir> --years 2021-2024",
              "# 2. build the database and this document",
              f"uv run python data_pipeline/build_duckdb.py --snapshot <snapshot_dir> --out {db_path}",
              f"uv run python data_pipeline/build_catalog.py --db {db_path} --semantics catalog/columbia_semantics.yaml "
              "--out catalog/columbia.yaml --doc docs/DATA.md", "```", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--semantics", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--doc", type=Path)
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    cat = merge(profile(con), yaml.safe_load(args.semantics.read_text()))
    args.out.write_text(yaml.safe_dump(cat, sort_keys=False, allow_unicode=True, width=120))
    print(f"wrote {args.out}")
    if args.doc:
        args.doc.write_text(render_md(cat, "data/columbia.duckdb"))
        print(f"wrote {args.doc}")


if __name__ == "__main__":
    main()
