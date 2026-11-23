"""Pluggable datasets (DECISIONS D23): a dataset is a DuckDB file plus a catalog.

Agents learn about data only through the catalog, so another dataset (e.g. SciSciNet)
can be plugged in by pointing SCIVIZ_DB / SCIVIZ_CATALOG at different files.
"""
from __future__ import annotations

from functools import cached_property
from pathlib import Path

import duckdb
import yaml


class Dataset:
    def __init__(self, db_path: Path, catalog_path: Path):
        self.db_path = Path(db_path)
        self.catalog_path = Path(catalog_path)

    @cached_property
    def catalog(self) -> dict:
        return yaml.safe_load(self.catalog_path.read_text())

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Read-only connection; agents can never modify the dataset."""
        return duckdb.connect(str(self.db_path), read_only=True)

    # ---- catalog views used by tools and prompts -------------------------------------------
    def overview(self) -> str:
        ds = self.catalog["dataset"]
        lines = [f"Dataset: {ds.get('title')}", ds.get("description", "").strip(), "", "Tables:"]
        for name, t in self.catalog["tables"].items():
            lines.append(f"- {name} ({t['row_count']:,} rows): {t['description']}")
        return "\n".join(lines)

    def full_notes(self) -> str:
        ds = self.catalog["dataset"]
        parts = [self.overview(), "", "Scope exclusions:"]
        parts += [f"- {x}" for x in ds.get("scope_exclusions", [])]
        parts += ["", "Caveats:"] + [f"- {x}" for x in ds.get("caveats", [])]
        parts += ["", "Counting rules:"] + [f"- {x}" for x in ds.get("counting_rules", [])]
        parts += ["", "Relationships:"] + [f"- {x}" for x in self.catalog.get("relationships", [])]
        return "\n".join(parts)

    def describe_table(self, table: str) -> str:
        t = self.catalog["tables"].get(table)
        if not t:
            return f"Unknown table '{table}'. Known tables: {', '.join(self.catalog['tables'])}"
        lines = [f"Table {table} ({t['row_count']:,} rows): {t['description']}", "Columns:"]
        for c, ci in t["columns"].items():
            extra = []
            if "range" in ci:
                extra.append(f"range {ci['range'][0]}..{ci['range'][1]}")
            if "top_values" in ci:
                tops = ", ".join(f"{k} ({v:,})" for k, v in list(ci["top_values"].items())[:8])
                extra.append(f"top values: {tops}")
            if "examples" in ci:
                extra.append("examples: " + "; ".join(str(e) for e in ci["examples"]))
            lines.append(
                f"- {c} [{ci['type']}, nulls {ci['null_pct']}%, ~{ci['distinct']:,} distinct] {ci['description']}"
                + (f" | {' | '.join(extra)}" if extra else "")
            )
        return "\n".join(lines)

    def search(self, query: str, limit: int = 20) -> str:
        q = query.lower()
        hits = []
        for t, info in self.catalog["tables"].items():
            if q in t.lower() or q in info["description"].lower():
                hits.append(f"table {t}: {info['description']}")
            for c, ci in info["columns"].items():
                text = f"{c} {ci['description']} {' '.join(map(str, ci.get('top_values', {}).keys()))}".lower()
                if q in text:
                    hits.append(f"{t}.{c}: {ci['description']}")
        return "\n".join(hits[:limit]) if hits else f"No catalog entries mention '{query}'."
