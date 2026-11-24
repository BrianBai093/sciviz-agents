"""Harness-side access to the OpenAlex REST API (Project 2, PLAN_P2 §3.3).

Agents may need data the local snapshot lacks (for example, who cites a work). The harness owns that access:
- the API key stays in this process; Python kernels have no secrets and reach the API only through a local
  proxy (`OpenAlexProxy`, bound to 127.0.0.1) that adds the key;
- every successful response is cached on disk (SQLite, keyed by path + sorted params), so reruns and retries
  are free and the collected data stays fixed once fetched;
- requests are rate limited, retried with backoff, and charged against a per-session budget in USD using the
  cost the API reports in its response headers; the remaining daily budget of the key is tracked as well.

Nothing here knows what the data is used for.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import httpx

API = "https://api.openalex.org/"
# Entity endpoints only (list or single record); account endpoints such as /rate-limit are not reachable.
ALLOWED_PATH = re.compile(
    r"^(works|authors|sources|institutions|topics|subfields|fields|domains|publishers|funders|keywords|concepts)"
    r"(/[A-Za-z0-9:._%-]+)?$"
)
STRIPPED_PARAMS = {"api_key", "mailto"}


class OpenAlexError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status, self.message = status, message


class ExternalBudgetExceeded(RuntimeError):
    pass


def cache_key(path: str, params: dict) -> str:
    items = sorted((str(k), str(v)) for k, v in params.items() if str(k).lower() not in STRIPPED_PARAMS)
    return path.strip("/") + "?" + "&".join(f"{k}={v}" for k, v in items)


class ResponseCache:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, body BLOB, fetched_at REAL)")
        self._db.commit()
        self._lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT body FROM responses WHERE key = ?", (key,)).fetchone()
        return json.loads(zlib.decompress(row[0])) if row else None

    def put(self, key: str, data: dict) -> None:
        blob = zlib.compress(json.dumps(data, separators=(",", ":")).encode())
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO responses VALUES (?, ?, ?)", (key, blob, time.time()))
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()


class RateLimiter:
    """At most `rate` request starts per second across all threads."""

    def __init__(self, rate: float):
        self.interval = 1.0 / rate
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.interval
        if start > now:
            time.sleep(start - now)


class OpenAlexService:
    def __init__(self, key: str, cache_path: Path, budget_usd: float, rate_per_s: float = 10.0,
                 daily_reserve_usd: float = 0.02, usage_path: Path | None = None, events=None,
                 transport: httpx.BaseTransport | None = None, offline: bool = False):
        """`offline=True`: serve only cached responses (replay of a finished run); a miss is an error."""
        if not key and not offline:
            raise RuntimeError("OPENALEX_API_KEY is not set; external data access is unavailable.")
        self.offline = offline
        self._key = key
        self.cache = ResponseCache(cache_path)
        self.limiter = RateLimiter(rate_per_s)
        self.daily_reserve_usd = daily_reserve_usd
        self.usage_path = usage_path
        self.events = events
        self._http = httpx.Client(base_url=API, timeout=120, transport=transport,
                                  headers={"User-Agent": "sciviz-agents (research reproduction)"})
        self._lock = threading.Lock()
        self.usage = {"requests": 0, "cache_hits": 0, "errors": 0, "usd": 0.0, "budget_usd": budget_usd,
                      "daily_remaining_usd": None, "daily_limit_usd": None, "prepaid_remaining_usd": None,
                      "started_at": time.time()}
        if offline:  # replay: every response comes from the frozen cache at no cost, so no budget can run out
            self.usage.update(budget_usd=1e6, daily_remaining_usd=1e6, daily_limit_usd=1e6,
                              prepaid_remaining_usd=0.0, offline=True)
        self.served_keys: set[str] = set()  # cache keys this session used (for exporting a frozen subset)
        self._proxy: OpenAlexProxy | None = None

    # ---- public ---------------------------------------------------------------------------
    def get(self, path: str, params: dict | None = None) -> dict:
        path = path.strip("/")
        if not ALLOWED_PATH.match(path):
            raise ValueError(f"Path {path!r} is not an OpenAlex entity endpoint (e.g. 'works', 'works/W123').")
        params = {k: v for k, v in (params or {}).items() if str(k).lower() not in STRIPPED_PARAMS}
        key = cache_key(path, params)
        cached = self.cache.get(key)
        if cached is not None:
            with self._lock:
                self.usage["cache_hits"] += 1
                self.served_keys.add(key)
            return cached
        if self.offline:
            raise OpenAlexError(404, f"not in the frozen response cache: {key[:200]}")
        self._check_budget()
        delay = 1.0
        for _ in range(7):
            self.limiter.wait()
            try:
                r = self._http.get(path, params={**params, "api_key": self._key})
            except httpx.TransportError as e:
                last = f"network error: {type(e).__name__}"
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            self._account(r)
            if r.status_code == 429 or r.status_code >= 500:
                last = f"HTTP {r.status_code}: {self._scrub(r.text[:300])}"
                if r.status_code == 429 and self._key_exhausted():
                    raise ExternalBudgetExceeded("The API key's daily budget and prepaid credit are used up.")
                retry_after = float(r.headers.get("retry-after", 0) or 0)
                time.sleep(max(delay, retry_after))
                delay = min(delay * 2, 60)
                continue
            if r.status_code >= 400:
                with self._lock:
                    self.usage["errors"] += 1
                raise OpenAlexError(r.status_code, self._scrub(r.text[:600]))
            data = r.json()
            self.cache.put(key, data)
            with self._lock:
                self.served_keys.add(key)
            return data
        with self._lock:
            self.usage["errors"] += 1
        raise OpenAlexError(503, f"gave up after retries ({last})")

    def usage_snapshot(self) -> dict:
        with self._lock:
            u = dict(self.usage)
        u["usd"] = round(u["usd"], 6)
        u["remaining_session_budget_usd"] = round(u["budget_usd"] - u["usd"], 6)
        return u

    def usage_text(self) -> str:
        u = self.usage_snapshot()
        daily = "unknown" if u["daily_remaining_usd"] is None else (
            f"${u['daily_remaining_usd']:.4f} daily + ${u['prepaid_remaining_usd'] or 0:.4f} prepaid")
        return (f"[external API this session: {u['requests']} paid-path requests, {u['cache_hits']} cache hits, "
                f"${u['usd']:.4f} of ${u['budget_usd']:.2f} session budget; key's remaining daily budget {daily}]")

    def start_proxy(self) -> str:
        if self._proxy is None:
            self._proxy = OpenAlexProxy(self)
        return self._proxy.url

    def close(self) -> None:
        if self._proxy is not None:
            self._proxy.stop()
            self._proxy = None
        self._save_usage()
        if self.usage_path is not None:  # which cached responses this run used, for exporting a frozen subset
            keys_file = self.usage_path.with_name("external_keys.json")
            old = set(json.loads(keys_file.read_text())) if keys_file.exists() else set()
            keys_file.write_text(json.dumps(sorted(old | self.served_keys)))
        self._http.close()
        self.cache.close()

    # ---- internals ------------------------------------------------------------------------
    def _scrub(self, text: str) -> str:
        return text.replace(self._key, "***") if self._key else text

    def _check_budget(self) -> None:
        with self._lock:
            u = self.usage
            if u["usd"] >= u["budget_usd"]:
                raise ExternalBudgetExceeded(
                    f"External API session budget reached (${u['usd']:.4f} of ${u['budget_usd']:.2f}). "
                    "Cached requests still work; ask for a larger budget to fetch more.")
        if self._key_exhausted():
            raise ExternalBudgetExceeded("The API key's daily budget and prepaid credit are nearly used up.")

    def _key_exhausted(self) -> bool:
        """Daily allowance plus prepaid credit, as reported by the API in its last response."""
        with self._lock:
            daily, prepaid = self.usage["daily_remaining_usd"], self.usage["prepaid_remaining_usd"]
        return daily is not None and daily + (prepaid or 0.0) <= self.daily_reserve_usd

    def _account(self, r: httpx.Response) -> None:
        h = r.headers
        cost = float(h.get("x-ratelimit-cost-usd", 0) or 0) if r.status_code < 400 else 0.0
        with self._lock:
            self.usage["requests"] += 1
            self.usage["usd"] += cost
            if h.get("x-ratelimit-remaining-usd") is not None:
                self.usage["daily_remaining_usd"] = float(h["x-ratelimit-remaining-usd"])
            if h.get("x-ratelimit-limit-usd") is not None:
                self.usage["daily_limit_usd"] = float(h["x-ratelimit-limit-usd"])
            if h.get("x-ratelimit-prepaid-remaining-usd") is not None:
                self.usage["prepaid_remaining_usd"] = float(h["x-ratelimit-prepaid-remaining-usd"])
            n = self.usage["requests"]
        if n % 200 == 0:
            self._save_usage()
            if self.events is not None:
                self.events.emit("system", "external_usage", **self.usage_snapshot())

    def _save_usage(self) -> None:
        if self.usage_path is not None:
            tmp = self.usage_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.usage_snapshot(), indent=2))
            tmp.replace(self.usage_path)


class OpenAlexProxy:
    """Local HTTP front for the service: GET http://127.0.0.1:<port>/<path>?<params> -> JSON.
    `/__usage` returns the session's usage. Errors come back as JSON {"error": ...} with an HTTP status."""

    def __init__(self, service: OpenAlexService):
        svc = service

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                u = urlsplit(self.path)
                try:
                    if u.path == "/__usage":
                        code, data = 200, svc.usage_snapshot()
                    else:
                        code, data = 200, svc.get(u.path, dict(parse_qsl(u.query, keep_blank_values=True)))
                except ExternalBudgetExceeded as e:
                    code, data = 402, {"error": str(e)}
                except OpenAlexError as e:
                    code, data = e.status, {"error": e.message}
                except ValueError as e:
                    code, data = 400, {"error": str(e)}
                except Exception as e:  # never leak a traceback (or anything else) to the kernel
                    code, data = 500, {"error": f"{type(e).__name__}: {svc._scrub(str(e))[:300]}"}
                body = json.dumps(data, separators=(",", ":")).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):  # silence per-request logging
                pass

        class Server(ThreadingHTTPServer):
            request_queue_size = 256  # many concurrent kernel/job workers; the default backlog (5) resets connections

        self._server = Server(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="openalex-proxy")
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


def export_cache_subset(src: Path, dst: Path, keys: set[str]) -> int:
    """Copy the cached responses for `keys` into a new SQLite file (a frozen, shareable subset)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    out = sqlite3.connect(str(dst))
    out.execute("CREATE TABLE responses (key TEXT PRIMARY KEY, body BLOB, fetched_at REAL)")
    src_db = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    n = 0
    keys = sorted(keys)
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        rows = src_db.execute(f"SELECT key, body, fetched_at FROM responses WHERE key IN ({','.join('?' * len(chunk))})",
                              chunk).fetchall()
        out.executemany("INSERT OR REPLACE INTO responses VALUES (?, ?, ?)", rows)
        n += len(rows)
    out.commit()
    out.close()
    src_db.close()
    return n
