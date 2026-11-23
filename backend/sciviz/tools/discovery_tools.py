"""Library/algorithm discovery tools for the Viz agent (DECISIONS D11).

These let agents find and learn JavaScript libraries at runtime instead of relying on templates.
"""
from __future__ import annotations

import httpx
from langchain_core.tools import tool

from ..runtime.cdn import resolve_version
from ..session import Session
from .data_tools import _emit_call, _emit_result
from .python_exec import truncate


def discovery_tools(s: Session, agent: str):
    @tool
    def search_npm(query: str, size: int = 8) -> str:
        """Search the npm registry for JavaScript packages (e.g. libraries implementing an algorithm or
        a kind of visualization). Returns name, latest version, description and keywords."""
        _emit_call(s, agent, "search_npm", {"query": query})
        try:
            r = httpx.get("https://registry.npmjs.org/-/v1/search", params={"text": query, "size": min(size, 20)},
                          timeout=20)
            r.raise_for_status()
            rows = []
            for o in r.json().get("objects", []):
                p = o["package"]
                kw = ", ".join((p.get("keywords") or [])[:8])
                rows.append(f"- {p['name']}@{p.get('version')} ({p.get('date', '')[:10]}): "
                            f"{(p.get('description') or '')[:200]}" + (f" [keywords: {kw}]" if kw else ""))
            text = "\n".join(rows) or "no results"
        except httpx.HTTPError as e:
            text = f"npm search failed: {e}"
        _emit_result(s, agent, "search_npm", True, text)
        return text

    @tool
    def read_package_docs(package: str, version: str = "", path: str = "") -> str:
        """Read documentation of an npm package (from the jsDelivr CDN): its README by default, or a
        specific file such as type definitions when `path` is given (e.g. 'dist/index.d.ts'). Also lists
        the package's files so you can find entry points and type definitions."""
        _emit_call(s, agent, "read_package_docs", {"package": package, "version": version, "path": path})
        try:
            ver = resolve_version(package, version or None)
            out = [f"{package}@{ver}"]
            listing = httpx.get(f"https://data.jsdelivr.com/v1/packages/npm/{package}@{ver}",
                                params={"structure": "flat"}, timeout=20)
            files = [f["name"] for f in listing.json().get("files", [])] if listing.status_code == 200 else []
            if path:
                r = httpx.get(f"https://cdn.jsdelivr.net/npm/{package}@{ver}/{path.lstrip('/')}", timeout=20)
                out.append(f"--- {path} ---\n" + (r.text if r.status_code == 200 else f"HTTP {r.status_code}"))
            else:
                readme = next((f for f in files if f.lower() in ("/readme.md", "/readme.markdown", "/readme")), None)
                if readme:
                    r = httpx.get(f"https://cdn.jsdelivr.net/npm/{package}@{ver}{readme}", timeout=20)
                    out.append(r.text)
                else:
                    out.append("(no README found)")
            interesting = [f for f in files if f.endswith((".d.ts", "package.json")) or "/src/" in f][:40]
            out.append("files (selection): " + ", ".join(interesting or files[:40]))
            text = truncate("\n".join(out), 14000)
        except Exception as e:
            text = f"could not read docs for {package}: {e}"
        _emit_result(s, agent, "read_package_docs", True, text)
        return text

    return [search_npm, read_package_docs]
