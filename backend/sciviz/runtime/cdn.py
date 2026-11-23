"""JS library handling for agent-written modules (DECISIONS D21).

- pin_imports(): rewrites every import in a module to an exact, pinned CDN URL (esm.sh by default)
  and reports the libraries used. Unpinned or range versions are resolved via the npm registry.
- cached_fetch(): disk cache for CDN responses, so pinned modules keep working offline and in replay.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from ..config import settings

ALLOWED_HOSTS = ("esm.sh", "cdn.jsdelivr.net", "unpkg.com")
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/131.0 Safari/537.36")
IMPORT_RE = re.compile(r"""(?P<pre>\bfrom\s*|\bimport\s*\(\s*|\bimport\s+)(?P<q>["'])(?P<spec>[^"'\s]+)(?P=q)""")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class ImportError_(ValueError):
    pass


@dataclass
class Library:
    name: str
    version: str
    url: str


@lru_cache(maxsize=256)
def _npm_versions(name: str) -> tuple[list[str], str]:
    r = httpx.get(f"https://registry.npmjs.org/{name}", timeout=20,
                  headers={"Accept": "application/vnd.npm.install-v1+json"})
    if r.status_code == 404:
        raise ImportError_(f"npm package '{name}' does not exist")
    r.raise_for_status()
    d = r.json()
    versions = [v for v in d.get("versions", {}) if SEMVER.match(v)]
    return versions, d.get("dist-tags", {}).get("latest", "")


def _key(v: str):
    return tuple(int(x) for x in v.split("."))


def resolve_version(name: str, spec: str | None) -> str:
    versions, latest = _npm_versions(name)
    spec = (spec or "").strip()
    if spec in ("", "latest", "*"):
        return latest or max(versions, key=_key)
    if SEMVER.match(spec):
        if spec in versions:
            return spec
        raise ImportError_(f"{name}@{spec} does not exist on npm")
    caret, tilde = spec.startswith("^"), spec.startswith("~")
    base = spec.lstrip("^~=v")
    parts = base.split(".")
    if not all(p.isdigit() for p in parts if p not in ("x", "*")):
        return latest
    nums = [int(p) for p in parts if p.isdigit()]
    def ok(v):
        k = _key(v)
        if caret and len(nums) >= 1:
            return k[0] == nums[0] and (nums[0] != 0 or len(nums) < 2 or k[1] == nums[1]) and k >= tuple(nums + [0] * (3 - len(nums)))
        if tilde and len(nums) >= 2:
            return k[:2] == tuple(nums[:2]) and k >= tuple(nums + [0] * (3 - len(nums)))
        return k[: len(nums)] == tuple(nums)
    matching = [v for v in versions if ok(v)]
    if not matching:
        raise ImportError_(f"no version of {name} matches '{spec}'")
    return max(matching, key=_key)


def _split_pkg(path: str) -> tuple[str, str | None, str]:
    """'@scope/pkg@1.2/sub/x.js' -> ('@scope/pkg', '1.2', '/sub/x.js')"""
    path = path.lstrip("/")
    segs = path.split("/")
    n = 2 if segs[0].startswith("@") else 1
    head, rest = "/".join(segs[:n]), "/".join(segs[n:])
    if head.startswith("@"):
        scope, _, pv = head.partition("/")
        name_part, _, ver = pv.partition("@")
        name = f"{scope}/{name_part}"
    else:
        name, _, ver = head.partition("@")
    return name, (ver or None), (f"/{rest}" if rest else "")


def pin_spec(spec: str) -> tuple[str, Library | None]:
    if spec.startswith((".", "/")):
        raise ImportError_(f"relative import '{spec}' is not supported: modules are single files; import libraries from a CDN")
    if spec.startswith(("http://", "https://")):
        u = urlsplit(spec)
        if u.hostname not in ALLOWED_HOSTS:
            raise ImportError_(f"import host '{u.hostname}' is not allowed; use one of {', '.join(ALLOWED_HOSTS)}")
        path = u.path
        prefix = ""
        if u.hostname == "cdn.jsdelivr.net":
            if not path.startswith("/npm/"):
                raise ImportError_("only cdn.jsdelivr.net/npm/... URLs are supported")
            path, prefix = path[len("/npm"):], "/npm"
        name, ver, sub = _split_pkg(path)
        exact = resolve_version(name, ver)
        query = f"?{u.query}" if u.query else ""
        url = f"https://{u.hostname}{prefix}/{name}@{exact}{sub}{query}"
        return url, Library(name, exact, url)
    if spec.startswith(("node:", "data:", "blob:")):
        raise ImportError_(f"import '{spec}' is not available in the browser")
    name, ver, sub = _split_pkg(spec)
    exact = resolve_version(name, ver)
    url = f"https://esm.sh/{name}@{exact}{sub}"
    return url, Library(name, exact, url)


def pin_imports(code: str) -> tuple[str, list[Library]]:
    libs: dict[str, Library] = {}
    errors: list[str] = []

    def sub(m: re.Match) -> str:
        try:
            url, lib = pin_spec(m.group("spec"))
        except (ImportError_, httpx.HTTPError) as e:
            errors.append(str(e))
            return m.group(0)
        if lib:
            libs[f"{lib.name}@{lib.version}"] = lib
        return f"{m.group('pre')}{m.group('q')}{url}{m.group('q')}"

    pinned = IMPORT_RE.sub(sub, code)
    if errors:
        raise ImportError_("; ".join(errors))
    return pinned, list(libs.values())


def cached_fetch(url: str) -> tuple[int, str, bytes]:
    """Fetch an allowed CDN URL through the on-disk cache. Returns (status, content_type, body)."""
    host = urlsplit(url).hostname
    if host not in ALLOWED_HOSTS:
        return 403, "text/plain", b"blocked host"
    cache: Path = settings.cdn_cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(url.encode()).hexdigest()
    body_p, meta_p = cache / f"{h}.bin", cache / f"{h}.json"
    if body_p.exists() and meta_p.exists():
        meta = json.loads(meta_p.read_text())
        return 200, meta["content_type"], body_p.read_bytes()
    r = httpx.get(url, timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    ctype = r.headers.get("content-type", "application/javascript")
    if r.status_code == 200:
        body_p.write_bytes(r.content)
        meta_p.write_text(json.dumps({"url": url, "content_type": ctype}))
    return r.status_code, ctype, r.content
