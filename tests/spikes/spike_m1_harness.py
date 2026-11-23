"""Day-0 spike (PLAN §3.2): can Deep Agents + GPT-6.2 Sol do what the design needs?

Checks
  a) basic call + tool calling with a reasoning-effort setting
  b) image input reaches the model (Critic needs screenshots)
  c) a declarative sub-agent runs via `task` and its events are visible when streaming
  d) interrupt() inside a tool pauses the graph and Command(resume=...) continues it

Run: uv run python tests/spikes/spike_m1_harness.py
"""
from __future__ import annotations

import base64
import io
import json
import time

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from PIL import Image, ImageDraw

MODEL = "openai:gpt-6.2-sol"
usage_total = {"input_tokens": 0, "output_tokens": 0}


def add_usage(msg) -> None:
    u = getattr(msg, "usage_metadata", None) or {}
    usage_total["input_tokens"] += u.get("input_tokens", 0)
    usage_total["output_tokens"] += u.get("output_tokens", 0)


def model(effort: str = "low"):
    return init_chat_model(MODEL, reasoning={"effort": effort})


def check_a() -> None:
    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    llm = model().bind_tools([add])
    t = time.time()
    msg = llm.invoke("Use the add tool to compute 2+40. Call the tool, do not answer directly.")
    add_usage(msg)
    print(f"[a] tool_calls={msg.tool_calls} ({time.time() - t:.1f}s) usage={msg.usage_metadata}")


def check_b() -> None:
    img = Image.new("RGB", (240, 160), "white")
    d = ImageDraw.Draw(img)
    d.ellipse((20, 30, 110, 120), fill="red")
    d.rectangle((140, 40, 220, 120), fill="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    msg = model().invoke([HumanMessage(content=[
        {"type": "text", "text": "Describe the shapes and colors in this image in one short sentence."},
        {"type": "image", "base64": b64, "mime_type": "image/png"},
    ])])
    add_usage(msg)
    print(f"[b] {msg.text!r}")


def check_c_d() -> None:
    @tool
    def count_rows(table: str) -> str:
        """Return the number of rows in a table (fake data for the spike)."""
        return json.dumps({"table": table, "rows": 55371})

    @tool
    def ask_user(question: str) -> str:
        """Ask the human user a clarifying question and wait for the answer."""
        return str(interrupt({"question": question}))

    data_agent = {
        "name": "data",
        "description": "Answers questions about table sizes using count_rows.",
        "system_prompt": "You answer questions about tables. Use count_rows. Reply with one sentence.",
        "tools": [count_rows],
        "model": model(),
    }
    agent = create_deep_agent(
        model=model(),
        tools=[ask_user],
        system_prompt=(
            "You coordinate work. First call ask_user to ask which table the user means. "
            "Then delegate to the 'data' subagent via the task tool to get its row count. "
            "Then reply with one sentence."
        ),
        subagents=[data_agent],
        checkpointer=InMemorySaver(),
    )
    cfg = {"configurable": {"thread_id": "spike-1"}}
    seen_namespaces, interrupted = set(), None
    for ns, mode, chunk in agent.stream(
        {"messages": [{"role": "user", "content": "How big is the works table?"}]},
        cfg, stream_mode=["updates"], subgraphs=True,
    ):
        seen_namespaces.add(ns[0].split(":")[0] if ns else "<root>")
        if isinstance(chunk, dict) and "__interrupt__" in chunk:
            interrupted = chunk["__interrupt__"]
    print(f"[d] interrupted with: {interrupted[0].value if interrupted else None}")
    for ns, mode, chunk in agent.stream(
        Command(resume="the works table"), cfg, stream_mode=["updates"], subgraphs=True,
    ):
        seen_namespaces.add(ns[0].split(":")[0] if ns else "<root>")
    state = agent.get_state(cfg)
    for m in state.values["messages"]:
        add_usage(m)
    print(f"[c] namespaces seen while streaming: {sorted(seen_namespaces)}")
    print(f"[c] final answer: {state.values['messages'][-1].text!r}")
    tool_names = [tc["name"] for m in state.values["messages"] for tc in (getattr(m, "tool_calls", None) or [])]
    print(f"[c] lead tool calls: {tool_names}")


if __name__ == "__main__":
    check_a()
    check_b()
    check_c_d()
    cost = usage_total["input_tokens"] * 2 / 1e6 + usage_total["output_tokens"] * 10 / 1e6
    print(f"[usage] {usage_total} ≈ ${cost:.4f} (upper bound; ignores cache discounts, excludes sub-agent calls)")
