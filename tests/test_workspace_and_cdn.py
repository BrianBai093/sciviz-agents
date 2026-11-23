
import pandas as pd
import pytest

from sciviz.harness.workspace import Workspace
from sciviz.runtime import cdn


def test_artifacts_and_lineage(tmp_path):
    ws = Workspace(tmp_path / "s1")
    t = ws.save_table(pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}), "small", producer="data")
    g = ws.save_json({"nodes": [{"id": "n1"}], "edges": []}, "graph", "g", producer="analyst", inputs=[t["id"]])
    assert t["id"] == "T1" and g["id"] == "G1"
    assert ws.get("G1")["inputs"] == ["T1"]
    assert list(ws.load_data("T1").columns) == ["a", "b"]
    assert ws.data_for_browser("T1") == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    assert "G1 (graph) g" in ws.index_text() and "<- T1" in ws.index_text()


@pytest.mark.parametrize("spec,expected", [
    ("d3", ("d3", None, "")), ("d3@7", ("d3", "7", "")), ("@scope/pkg@1.2.3/sub/x.js", ("@scope/pkg", "1.2.3", "/sub/x.js")),
    ("pkg/sub", ("pkg", None, "/sub")),
])
def test_split_pkg(spec, expected):
    assert cdn._split_pkg(spec) == expected


def test_pin_imports_rewrites_to_exact_versions(monkeypatch):
    monkeypatch.setattr(cdn, "_npm_versions", lambda name: (["7.8.0", "7.9.2", "6.7.0"], "7.9.2"))
    code = 'import * as d3 from "d3@7";\nimport x from "https://esm.sh/foo";\nconst m = import("bar@^6");'
    pinned, libs = cdn.pin_imports(code)
    assert '"https://esm.sh/d3@7.9.2"' in pinned
    assert '"https://esm.sh/foo@7.9.2"' in pinned
    assert '"https://esm.sh/bar@6.7.0"' in pinned
    assert {lib.name for lib in libs} == {"d3", "foo", "bar"}


def test_relative_and_foreign_imports_rejected():
    with pytest.raises(cdn.ImportError_):
        cdn.pin_spec("./local.js")
    with pytest.raises(cdn.ImportError_):
        cdn.pin_spec("https://example.com/x.js")
