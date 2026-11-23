#!/usr/bin/env python3
"""Build the analysis database (DuckDB) from a raw OpenAlex snapshot.

Input : a snapshot folder written by fetch_openalex_snapshot.py
        (works/, topics/, authors/, sources/ with *.jsonl.gz, manifest.json)
Output: one DuckDB file with normalized tables + a `snapshot_meta` table.

Usage:
  uv run python data_pipeline/build_duckdb.py --snapshot ../data/openalex_columbia_2026-11-23 \
      --out data/columbia.duckdb
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import duckdb
import pyarrow as pa


def short(oa_id):
    return oa_id.rsplit("/", 1)[-1] if oa_id else None


def records(folder: Path):
    for p in sorted(folder.glob("*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf8") as f:
            for line in f:
                yield json.loads(line)


def rebuild_abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    slots: dict[int, str] = {}
    for word, positions in inv.items():
        for pos in positions:
            slots[pos] = word
    return " ".join(slots[i] for i in sorted(slots)) or None


class Columns:
    """Column-wise accumulator that becomes a pyarrow table."""

    def __init__(self, schema: dict[str, pa.DataType]):
        self.schema = schema
        self.cols = {k: [] for k in schema}

    def add(self, **row):
        for k in self.cols:
            self.cols[k].append(row.get(k))

    def table(self) -> pa.Table:
        return pa.table({k: pa.array(v, type=self.schema[k]) for k, v in self.cols.items()})


S, I, F, B, D = pa.string(), pa.int64(), pa.float64(), pa.bool_(), pa.date32()


def build(snapshot: Path, out: Path) -> None:
    manifest = json.loads((snapshot / "manifest.json").read_text())
    inst = manifest["institution"]

    works = Columns({
        "work_id": S, "doi": S, "title": S, "abstract": S, "publication_year": I, "publication_date": S,
        "type": S, "language": S, "source_id": S, "source_name": S, "cited_by_count": I, "fwci": F,
        "citation_percentile": F, "is_top_1pct_cited": B, "is_top_10pct_cited": B, "is_oa": B,
        "oa_status": S, "referenced_works_count": I, "authors_count": I, "columbia_authors_count": I,
        "countries_distinct_count": I, "institutions_distinct_count": I, "is_retracted": B,
        "is_paratext": B, "primary_topic_id": S, "primary_topic": S, "primary_subfield": S,
        "primary_field": S, "primary_domain": S,
    })
    authorships = Columns({
        "work_id": S, "author_order": I, "author_id": S, "author_name": S, "author_position": S,
        "is_corresponding": B, "is_columbia": B,
    })
    auth_inst = Columns({"work_id": S, "author_order": I, "author_id": S, "institution_id": S})
    work_topics = Columns({"work_id": S, "topic_id": S, "score": F, "is_primary": B, "rank": I})
    citations = Columns({"citing_work_id": S, "cited_work_id": S})
    cby = Columns({"work_id": S, "year": I, "cited_by_count": I})
    keywords = Columns({"work_id": S, "keyword_id": S, "keyword": S, "score": F})
    funders = Columns({"work_id": S, "funder_id": S, "funder_name": S})
    institutions: dict[str, dict] = {}

    n = 0
    for w in records(snapshot / "works"):
        n += 1
        wid = short(w["id"])
        src = (w.get("primary_location") or {}).get("source") or {}
        pt = w.get("primary_topic") or {}
        cnp = w.get("citation_normalized_percentile") or {}
        oa = w.get("open_access") or {}
        col_authors = 0
        for order, a in enumerate(w.get("authorships") or []):
            author = a.get("author") or {}
            aid = short(author.get("id"))
            is_col = False
            for i in a.get("institutions") or []:
                iid = short(i.get("id"))
                if not iid:
                    continue
                lineage = [short(x) for x in (i.get("lineage") or [])]
                if inst in lineage or iid == inst:
                    is_col = True
                if iid not in institutions:
                    institutions[iid] = {
                        "institution_id": iid, "name": i.get("display_name"), "country_code": i.get("country_code"),
                        "type": i.get("type"), "ror": i.get("ror"), "is_columbia": inst in lineage or iid == inst,
                    }
                auth_inst.add(work_id=wid, author_order=order, author_id=aid, institution_id=iid)
            col_authors += is_col
            authorships.add(work_id=wid, author_order=order, author_id=aid,
                            author_name=author.get("display_name"), author_position=a.get("author_position"),
                            is_corresponding=bool(a.get("is_corresponding")), is_columbia=is_col)
        primary_tid = short(pt.get("id"))
        for rank, t in enumerate(w.get("topics") or []):
            tid = short(t.get("id"))
            work_topics.add(work_id=wid, topic_id=tid, score=t.get("score"), is_primary=tid == primary_tid, rank=rank)
        for ref in w.get("referenced_works") or []:
            citations.add(citing_work_id=wid, cited_work_id=short(ref))
        for c in w.get("counts_by_year") or []:
            cby.add(work_id=wid, year=c.get("year"), cited_by_count=c.get("cited_by_count"))
        for k in w.get("keywords") or []:
            keywords.add(work_id=wid, keyword_id=short(k.get("id")), keyword=k.get("display_name"), score=k.get("score"))
        for f in w.get("funders") or []:
            funders.add(work_id=wid, funder_id=short(f.get("id")), funder_name=f.get("display_name"))
        works.add(
            work_id=wid, doi=w.get("doi"), title=w.get("title") or w.get("display_name"),
            abstract=rebuild_abstract(w.get("abstract_inverted_index")),
            publication_year=w.get("publication_year"), publication_date=w.get("publication_date"),
            type=w.get("type"), language=w.get("language"), source_id=short(src.get("id")),
            source_name=src.get("display_name"), cited_by_count=w.get("cited_by_count"), fwci=w.get("fwci"),
            citation_percentile=cnp.get("value"), is_top_1pct_cited=cnp.get("is_in_top_1_percent"),
            is_top_10pct_cited=cnp.get("is_in_top_10_percent"), is_oa=oa.get("is_oa"),
            oa_status=oa.get("oa_status"), referenced_works_count=w.get("referenced_works_count"),
            authors_count=len(w.get("authorships") or []), columbia_authors_count=col_authors,
            countries_distinct_count=w.get("countries_distinct_count"),
            institutions_distinct_count=w.get("institutions_distinct_count"),
            is_retracted=w.get("is_retracted"), is_paratext=w.get("is_paratext"), primary_topic_id=primary_tid,
            primary_topic=pt.get("display_name"), primary_subfield=(pt.get("subfield") or {}).get("display_name"),
            primary_field=(pt.get("field") or {}).get("display_name"),
            primary_domain=(pt.get("domain") or {}).get("display_name"),
        )
    print(f"works parsed: {n}")

    topics = Columns({
        "topic_id": S, "topic": S, "subfield_id": S, "subfield": S, "field_id": S, "field": S,
        "domain_id": S, "domain": S, "description": S, "keywords": S, "works_count": I,
    })
    for t in records(snapshot / "topics"):
        sf, fd, dm = t.get("subfield") or {}, t.get("field") or {}, t.get("domain") or {}
        topics.add(topic_id=short(t["id"]), topic=t.get("display_name"), subfield_id=short(sf.get("id")),
                   subfield=sf.get("display_name"), field_id=short(fd.get("id")), field=fd.get("display_name"),
                   domain_id=short(dm.get("id")), domain=dm.get("display_name"), description=t.get("description"),
                   keywords="; ".join(t.get("keywords") or []), works_count=t.get("works_count"))

    authors = Columns({
        "author_id": S, "name": S, "orcid": S, "works_count": I, "cited_by_count": I, "h_index": I,
        "i10_index": I, "two_year_mean_citedness": F, "last_known_institutions": S,
    })
    for a in records(snapshot / "authors"):
        ss = a.get("summary_stats") or {}
        authors.add(author_id=short(a["id"]), name=a.get("display_name"), orcid=a.get("orcid"),
                    works_count=a.get("works_count"), cited_by_count=a.get("cited_by_count"),
                    h_index=ss.get("h_index"), i10_index=ss.get("i10_index"),
                    two_year_mean_citedness=ss.get("2yr_mean_citedness"),
                    last_known_institutions="; ".join(i.get("display_name") or "" for i in
                                                     (a.get("last_known_institutions") or [])))

    sources = Columns({
        "source_id": S, "name": S, "type": S, "issn_l": S, "publisher": S, "country_code": S, "is_oa": B,
        "works_count": I, "cited_by_count": I, "h_index": I,
    })
    for s in records(snapshot / "sources"):
        ss = s.get("summary_stats") or {}
        sources.add(source_id=short(s["id"]), name=s.get("display_name"), type=s.get("type"),
                    issn_l=s.get("issn_l"), publisher=s.get("host_organization_name"),
                    country_code=s.get("country_code"), is_oa=s.get("is_oa"), works_count=s.get("works_count"),
                    cited_by_count=s.get("cited_by_count"), h_index=ss.get("h_index"))

    inst_tbl = Columns({"institution_id": S, "name": S, "country_code": S, "type": S, "ror": S, "is_columbia": B})
    for row in institutions.values():
        inst_tbl.add(**row)

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    con = duckdb.connect(str(out))
    tables = {
        "works": works, "authorships": authorships, "authorship_institutions": auth_inst,
        "institutions": inst_tbl, "authors": authors, "topics": topics, "work_topics": work_topics,
        "sources": sources, "citations": citations, "work_citations_by_year": cby,
        "work_keywords": keywords, "work_funders": funders,
    }
    for name, cols in tables.items():
        arrow_tbl = cols.table()  # noqa: F841  (referenced by name inside SQL)
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM arrow_tbl")
        print(f"{name}: {con.execute(f'SELECT count(*) FROM {name}').fetchone()[0]:,} rows")

    con.execute("ALTER TABLE works ALTER publication_date TYPE DATE USING TRY_CAST(publication_date AS DATE)")
    # derived convenience flags
    con.execute("ALTER TABLE citations ADD COLUMN cited_in_snapshot BOOLEAN")
    con.execute("UPDATE citations SET cited_in_snapshot = cited_work_id IN (SELECT work_id FROM works)")
    con.execute("ALTER TABLE authors ADD COLUMN works_in_snapshot BIGINT")
    con.execute("""
        UPDATE authors SET works_in_snapshot = c.n FROM (
          SELECT author_id, count(DISTINCT work_id) AS n FROM authorships WHERE is_columbia GROUP BY author_id
        ) c WHERE authors.author_id = c.author_id""")

    meta = {
        "snapshot_date_utc": manifest["snapshot_date_utc"], "institution": inst,
        "works_filter": manifest["works_filter"], "years": manifest["years"],
        "max_authors": str(manifest["max_authors"]), "source": manifest["source"],
    }
    con.execute("CREATE TABLE snapshot_meta (key VARCHAR, value VARCHAR)")
    con.executemany("INSERT INTO snapshot_meta VALUES (?, ?)", list(meta.items()))
    con.execute("CHECKPOINT")
    con.close()
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    build(args.snapshot, args.out)
