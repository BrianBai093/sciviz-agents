"""Log of the files agents write with their file tools (write_file, edit_file), for script export and replay.

Code cells and background jobs are logged in kernel_log.jsonl. Files written through the file tools are not
cells, but later cells may run or read them, so every successful write is logged with the file's full content
after the write. Script export replays these writes in time order with the cells.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from deepagents.backends.filesystem import FilesystemBackend

LOG = "file_log.jsonl"
_lock = threading.Lock()


def log_file(root: Path, ts: float, path: str, op: str, content: str | None, source: str | None = None) -> None:
    rec = {"ts": round(ts, 3), "path": path, "op": op, "content": content}
    if source:
        rec["source"] = source
    with _lock, (Path(root) / LOG).open("a", encoding="utf8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class LoggedFilesystemBackend(FilesystemBackend):
    """The agents' file backend (rooted at the workspace); successful writes and edits go to file_log.jsonl."""

    def __init__(self, root_dir, virtual_mode: bool = True, **kw):
        super().__init__(root_dir=root_dir, virtual_mode=virtual_mode, **kw)
        self._log_root = Path(root_dir)

    def write(self, file_path: str, content: str):
        t0 = time.time()
        res = super().write(file_path, content)
        if not getattr(res, "error", None):
            log_file(self._log_root, t0, file_path, "write", content)
        return res

    def edit(self, file_path: str, old_string: str, new_string: str, replace_all: bool = False):
        t0 = time.time()
        res = super().edit(file_path, old_string, new_string, replace_all)
        if not getattr(res, "error", None):
            try:
                log_file(self._log_root, t0, file_path, "edit",
                         self._resolve_path(file_path).read_text(encoding="utf8"))
            except OSError:
                pass
        return res


def _uuid6_time(checkpoint_id: str) -> float:
    u = uuid.UUID(checkpoint_id).int
    ticks = ((u >> 96) & 0xFFFFFFFF) << 28 | ((u >> 80) & 0xFFFF) << 12 | ((u >> 64) & 0x0FFF)
    return (ticks - 0x01B21DD213814000) / 1e7


def backfill_from_checkpoints(root: Path) -> int:
    """For sessions recorded before file writes were logged: rebuild file_log.jsonl from the file-tool calls
    stored in the session's LangGraph checkpoints. The time of each write is that of the checkpoint the call
    ran from (just before the write). Edits are applied in order to get each file's full content."""
    import sqlite3

    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    root = Path(root)
    if (root / LOG).exists():
        raise FileExistsError(f"{root / LOG} exists; it is the record of this session's file writes")
    ser, calls, done = JsonPlusSerializer(), {}, {}
    con = sqlite3.connect(root / "checkpoints.sqlite")
    rows = con.execute("select checkpoint_id, value, type from writes where channel='messages' order by rowid")
    for cid, value, typ in rows:
        try:
            msgs = ser.loads_typed((typ, value))
        except Exception:  # noqa: BLE001, S112 (unreadable entries carry no file writes)
            continue
        for m in msgs if isinstance(msgs, list) else [msgs]:
            for tc in getattr(m, "tool_calls", None) or []:
                if tc["name"] in ("write_file", "edit_file") and tc["id"] not in calls:
                    calls[tc["id"]] = (_uuid6_time(cid), tc["name"], tc["args"])
            if getattr(m, "type", "") == "tool" and m.tool_call_id in calls:
                done[m.tool_call_id] = str(m.content)
    con.close()
    content: dict[str, str] = {}
    n = 0
    for call_id, (ts, name, args) in sorted(calls.items(), key=lambda kv: kv[1][0]):
        result = done.get(call_id, "")
        if not (result.startswith("Updated file") or result.startswith("Successfully replaced")):
            continue  # the call failed or never returned: the file did not change
        path = args["file_path"]
        if name == "write_file":
            content[path] = args["content"]
        elif path in content:
            old, new = args["old_string"], args["new_string"]
            content[path] = content[path].replace(old, new, -1 if args.get("replace_all") else 1)
        else:  # an edit of a file that a cell wrote: its content before the edit is not in the checkpoints
            log_file(root, ts, path, "edit", None, source="backfilled from checkpoints; content unknown")
            n += 1
            continue
        log_file(root, ts, path, "write" if name == "write_file" else "edit", content[path],
                 source="backfilled from checkpoints")
        n += 1
    return n
