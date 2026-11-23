"""Copy selected sessions into recordings/ (committed) so reviewers can replay them without an API key.

Keeps events, views, decisions, artifact metadata/data/modules and the gate screenshots the UI shows
(default + selected); drops LangGraph checkpoints, preview renders and other screenshots.
Usage: uv run python demo/package_recordings.py <session> [<session> ...]
Serve:  SCIVIZ_WORKSPACES=recordings uv run sciviz serve --port 8001
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, DST = ROOT / "workspaces", ROOT / "recordings"
KEEP_SHOTS = {"default.png", "selected.png"}


def package(sid: str) -> int:
    src, dst = SRC / sid, DST / sid
    shutil.rmtree(dst, ignore_errors=True)
    total = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(src)
        parts = rel.parts
        if f.name.startswith("checkpoints.sqlite") or "preview" in parts or f.name.endswith(".tmp"):
            continue
        if "shots" in parts and f.name not in KEEP_SHOTS:
            continue
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        total += f.stat().st_size
    return total


if __name__ == "__main__":
    DST.mkdir(exist_ok=True)
    for sid in sys.argv[1:]:
        print(f"{sid}: {package(sid) / 1e6:.1f} MB")
