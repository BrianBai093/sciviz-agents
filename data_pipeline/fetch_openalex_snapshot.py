#!/usr/bin/env python3
"""Download a frozen OpenAlex snapshot of one institution's works.

Stages (run in order, each resumable):
  works    - all works matching the institution/year/author-count filter
  topics   - the full OpenAlex topic hierarchy (domain > field > subfield > topic)
  authors  - author records for every author affiliated with the institution
  sources  - venue records for every primary source referenced by the works

Output: gzipped JSON Lines files under --out, plus manifest.json.
The API key is read from the OPENALEX_API_KEY environment variable and is
never written to disk or logs.

Example:
  OPENALEX_API_KEY=... python3 -I fetch_openalex_snapshot.py --out data/snap
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.openalex.org/"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


class Client:
    def __init__(self, key: str) -> None:
        self.key = key
        self.calls = 0

    def get(self, path: str, params: dict, retries: int = 8) -> dict:
        params = {**params, "api_key": self.key}
        url = API + path + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url, headers={"Accept-Encoding": "gzip", "User-Agent": "openalex-snapshot-script/1.0"}
        )
        delay = 2.0
        for _ in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                    self.calls += 1
                    return json.loads(raw)
            except urllib.error.HTTPError as e:
                body = e.read()[:300].decode("utf8", "replace")
                if e.code in (429, 500, 502, 503, 504):
                    log(f"HTTP {e.code}; retrying in {delay:.0f}s ({body[:100]})")
                    time.sleep(delay)
                    delay = min(delay * 2, 120)
                    continue
                raise RuntimeError(f"HTTP {e.code}: {body}") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                log(f"network error {e!r}; retrying in {delay:.0f}s")
                time.sleep(delay)
                delay = min(delay * 2, 120)
        raise RuntimeError(f"giving up on {path} after {retries} attempts")


def write_json_atomic(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2))
    os.replace(tmp, path)


def write_jsonl_gz(path: Path, records: list[dict]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def iter_records(folder: Path):
    for p in sorted(folder.glob("*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf8") as f:
            for line in f:
                yield json.loads(line)


def short_id(oa_id: str | None) -> str | None:
    return oa_id.rsplit("/", 1)[-1] if oa_id else None


def fetch_cursor_list(client: Client, entity: str, flt: str | None, outdir: Path,
                      per_page: int = 200, max_pages: int | None = None) -> dict:
    """Cursor-page through a list endpoint, one gz file per page, resumable."""
    outdir.mkdir(parents=True, exist_ok=True)
    state_path = outdir / "_state.json"
    state = (json.loads(state_path.read_text()) if state_path.exists()
             else {"cursor": "*", "page": 0, "records": 0, "done": False, "per_page": per_page})
    if state["done"]:
        log(f"{entity}: already complete ({state['records']} records)")
        return state
    started = time.time()
    while True:
        params = {"per_page": state["per_page"], "cursor": state["cursor"]}
        if flt:
            params["filter"] = flt
        try:
            data = client.get(entity, params)
        except RuntimeError as e:
            if "HTTP 400" in str(e) and state["per_page"] > 100:
                log(f"{entity}: per_page={state['per_page']} rejected, falling back to 100")
                state["per_page"] = 100
                continue
            raise
        if state["page"] == 0 and "expected" not in state:
            state["expected"] = data["meta"].get("count")
            log(f"{entity}: {state['expected']} records expected (per_page={state['per_page']})")
        results = data.get("results", [])
        if results:
            state["page"] += 1
            write_jsonl_gz(outdir / f"page_{state['page']:05d}.jsonl.gz", results)
            state["records"] += len(results)
        nxt = data.get("meta", {}).get("next_cursor")
        state["done"] = not results or not nxt
        state["cursor"] = nxt
        write_json_atomic(state_path, state)
        if state["page"] % 20 == 0 or state["done"]:
            rate = state["records"] / max(time.time() - started, 1e-6)
            log(f"{entity}: page {state['page']}, {state['records']}/{state.get('expected')} records ({rate:.0f}/s)")
        if state["done"] or (max_pages and state["page"] >= max_pages):
            return state


def fetch_by_ids(client: Client, entity: str, ids: list[str], outdir: Path, batch: int = 100) -> dict:
    """Fetch records by OpenAlex ID in OR-batches of up to 100, resumable."""
    outdir.mkdir(parents=True, exist_ok=True)
    state_path = outdir / "_state.json"
    state = (json.loads(state_path.read_text()) if state_path.exists()
             else {"next_batch": 0, "records": 0, "requested": len(ids), "filter_key": "openalex", "done": False})
    if state["done"]:
        log(f"{entity}: already complete ({state['records']} records)")
        return state
    chunks = [ids[i:i + batch] for i in range(0, len(ids), batch)]
    log(f"{entity}: {len(ids)} ids in {len(chunks)} batches (resuming at {state['next_batch']})")
    k = state["next_batch"]
    while k < len(chunks):
        flt = f"{state['filter_key']}:" + "|".join(chunks[k])
        try:
            data = client.get(entity, {"filter": flt, "per_page": batch})
        except RuntimeError as e:
            if "HTTP 400" in str(e) and state["filter_key"] == "openalex":
                log(f"{entity}: 'openalex' filter rejected, trying 'ids.openalex'")
                state["filter_key"] = "ids.openalex"
                continue
            raise
        write_jsonl_gz(outdir / f"batch_{k:05d}.jsonl.gz", data.get("results", []))
        state["records"] += len(data.get("results", []))
        k += 1
        state["next_batch"] = k
        write_json_atomic(state_path, state)
        if k % 50 == 0:
            log(f"{entity}: batch {k}/{len(chunks)}, {state['records']} records")
    state["done"] = True
    write_json_atomic(state_path, state)
    log(f"{entity}: done, {state['records']} records")
    return state


def affiliated_author_ids(works_dir: Path, inst: str) -> list[str]:
    ids: set[str] = set()
    for w in iter_records(works_dir):
        for a in w.get("authorships") or []:
            for i in a.get("institutions") or []:
                lineage = [short_id(x) for x in (i.get("lineage") or [])] + [short_id(i.get("id"))]
                if inst in lineage:
                    aid = short_id((a.get("author") or {}).get("id"))
                    if aid:
                        ids.add(aid)
                    break
    return sorted(ids)


def primary_source_ids(works_dir: Path) -> list[str]:
    ids: set[str] = set()
    for w in iter_records(works_dir):
        src = ((w.get("primary_location") or {}).get("source") or {}).get("id")
        if src:
            ids.add(short_id(src))
    return sorted(ids)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--institution", default="I78577930", help="OpenAlex institution id (default: Columbia University)")
    ap.add_argument("--years", default="2015-2024")
    ap.add_argument("--max-authors", type=int, default=100, help="drop works with more authors than this")
    ap.add_argument("--stages", default="works,topics,authors,sources")
    ap.add_argument("--max-pages", type=int, default=None, help="testing only: stop works stage after N pages")
    args = ap.parse_args()

    key = os.environ.get("OPENALEX_API_KEY")
    if not key:
        raise SystemExit("OPENALEX_API_KEY is not set")
    client = Client(key)
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "source": "OpenAlex API (https://api.openalex.org)",
        "snapshot_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "institution": args.institution,
        "years": args.years,
        "max_authors": args.max_authors,
        "works_filter": (f"authorships.institutions.lineage:{args.institution},"
                         f"publication_year:{args.years},authors_count:<{args.max_authors + 1}"),
        "stages": {},
    }
    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    works_dir = out / "works"

    if "works" in stages:
        st = fetch_cursor_list(client, "works", manifest["works_filter"], works_dir, max_pages=args.max_pages)
        manifest["stages"]["works"] = {k: st.get(k) for k in ("records", "expected", "page", "done")}
        write_json_atomic(manifest_path, manifest)
        if not st["done"]:
            log("works stage stopped early (--max-pages); skipping dependent stages")
            return
    if "topics" in stages:
        st = fetch_cursor_list(client, "topics", None, out / "topics")
        manifest["stages"]["topics"] = {k: st.get(k) for k in ("records", "expected", "done")}
        write_json_atomic(manifest_path, manifest)
    if "authors" in stages:
        ids = affiliated_author_ids(works_dir, args.institution)
        st = fetch_by_ids(client, "authors", ids, out / "authors")
        manifest["stages"]["authors"] = {k: st.get(k) for k in ("records", "requested", "done")}
        write_json_atomic(manifest_path, manifest)
    if "sources" in stages:
        ids = primary_source_ids(works_dir)
        st = fetch_by_ids(client, "sources", ids, out / "sources")
        manifest["stages"]["sources"] = {k: st.get(k) for k in ("records", "requested", "done")}
        write_json_atomic(manifest_path, manifest)

    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["api_calls_this_run"] = client.calls
    write_json_atomic(manifest_path, manifest)
    log(f"all requested stages finished ({client.calls} API calls this run)")


if __name__ == "__main__":
    main()
