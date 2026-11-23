#!/usr/bin/env python3
"""Make a small sample database (committed to the repo) from the full DuckDB file.

Keeps a deterministic hash-based sample of works and every row related to them; the topic
hierarchy is kept in full. Used for quick starts and unit tests (DECISIONS D20).

Usage: uv run python data_pipeline/make_sample.py --db data/columbia.duckdb --out catalog/columbia_sample.duckdb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--percent", type=int, default=3)
    args = ap.parse_args()
    if args.out.exists():
        args.out.unlink()
    con = duckdb.connect(str(args.out))
    con.execute(f"ATTACH '{args.db}' AS src (READ_ONLY)")
    con.execute(f"CREATE TABLE works AS SELECT * FROM src.works WHERE hash(work_id) % 100 < {args.percent}")
    keep = "work_id IN (SELECT work_id FROM works)"
    for t in ("authorships", "authorship_institutions", "work_topics", "work_citations_by_year",
              "work_keywords", "work_funders"):
        con.execute(f"CREATE TABLE {t} AS SELECT * FROM src.{t} WHERE {keep}")
    con.execute("CREATE TABLE citations AS SELECT citing_work_id, cited_work_id, "
                "cited_work_id IN (SELECT work_id FROM works) AS cited_in_snapshot "
                "FROM src.citations WHERE citing_work_id IN (SELECT work_id FROM works)")
    con.execute("CREATE TABLE authors AS SELECT * FROM src.authors WHERE author_id IN "
                "(SELECT author_id FROM authorships WHERE is_columbia)")
    con.execute("CREATE TABLE institutions AS SELECT * FROM src.institutions WHERE institution_id IN "
                "(SELECT institution_id FROM authorship_institutions)")
    con.execute("CREATE TABLE sources AS SELECT * FROM src.sources WHERE source_id IN (SELECT source_id FROM works)")
    con.execute("CREATE TABLE topics AS SELECT * FROM src.topics")
    con.execute("CREATE TABLE snapshot_meta AS SELECT * FROM src.snapshot_meta")
    con.execute(f"INSERT INTO snapshot_meta VALUES ('sample', '{args.percent}% hash sample of works')")
    con.execute("DETACH src")
    con.execute("CHECKPOINT")
    n = con.execute("SELECT count(*) FROM works").fetchone()[0]
    con.close()
    print(f"wrote {args.out}: {n:,} works, {args.out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
