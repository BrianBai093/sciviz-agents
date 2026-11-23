import { useEffect, useMemo, useRef, useState } from "react";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { api } from "../api";
import { useStore, type Msg, type Selection } from "../store";
import { DIRECTOR } from "../App";

const EXAMPLES = [
  "How has Columbia's publication output in each research field changed from 2021 to 2024?",
  "Show the collaboration network among Columbia's 80 most prolific researchers as a force-directed node-link diagram.",
  "Which countries does Columbia collaborate with most, and in which fields?",
];

function renderMarkdown(text: string): string {
  // artifact citations like [T3] or [V1, T2] become clickable chips
  const withCites = text.replace(/\[((?:[A-Z]\d+)(?:\s*,\s*[A-Z]\d+)*)\]/g, (_, ids: string) =>
    ids.split(/\s*,\s*/).map((id) => `<span class="cite" data-artifact="${id}">${id}</span>`).join(""));
  return DOMPurify.sanitize(marked.parse(withCites, { async: false }) as string, { ADD_ATTR: ["data-artifact"] });
}

function SelectionChip({ sel, onClear }: { sel: Selection; onClear?: () => void }) {
  const names = sel.items.slice(0, 3).map((i) => i.label ?? i.id ?? JSON.stringify(i.key)).join(", ");
  return (
    <div className="inline-flex max-w-full items-center gap-1.5 rounded-md bg-sky-50 px-2 py-1 text-xs text-sky-800">
      <span className="font-medium">{sel.items.length} selected</span>
      <span className="truncate">in {sel.view_id}: {names}{sel.items.length > 3 ? "…" : ""}</span>
      {onClear && <button className="ml-1 text-sky-600 hover:text-sky-900" onClick={onClear} aria-label="Clear selection">✕</button>}
    </div>
  );
}

function Message({ m }: { m: Msg }) {
  const focus = useStore((s) => s.focus);
  const html = useMemo(() => (m.role === "assistant" ? renderMarkdown(m.text) : ""), [m.text, m.role]);
  if (m.role === "user")
    return (
      <div className="ml-6 flex flex-col items-end gap-1">
        {m.selection?.items?.length ? <SelectionChip sel={m.selection} /> : null}
        <div className="rounded-lg rounded-br-sm bg-stone-800 px-3 py-2 text-sm text-white">{m.text}</div>
      </div>
    );
  if (m.role === "system")
    return <div className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-700">{m.text}</div>;
  return (
    <div
      className="md text-[13.5px] leading-relaxed text-stone-800"
      dangerouslySetInnerHTML={{ __html: html }}
      onClick={(e) => {
        const id = (e.target as HTMLElement).dataset?.artifact;
        if (id) focus(id);
      }}
    />
  );
}

export default function Chat() {
  const { sessionId, messages, busy, activity, question, selection, setSelection, mode } = useStore();
  const [text, setText] = useState("");
  const [answer, setAnswer] = useState("");
  const [err, setErr] = useState("");
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages.length, busy, question]);

  const send = async (t?: string) => {
    const body = (t ?? text).trim();
    if (!body || !sessionId) return;
    if (DIRECTOR) { setText(""); return; }  // recording a replay: typing is only shown, never sent
    setErr("");
    try {
      await api.post(`/api/sessions/${sessionId}/messages`, { text: body, selection });
      setText("");
    } catch (e) {
      setErr((e as Error).message);
    }
  };
  const resume = async () => {
    if (!answer.trim() || !sessionId) return;
    await api.post(`/api/sessions/${sessionId}/resume`, { answer });
    setAnswer("");
  };

  return (
    <div className="flex h-full flex-col">
      <div className="scroll-thin flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {!messages.length && (
          <div className="space-y-2 pt-6 text-sm text-stone-500">
            <p>Ask a question about Columbia's 2021–2024 publications. Try:</p>
            {EXAMPLES.map((q) => (
              <button key={q} className="block w-full rounded-md border border-stone-200 px-3 py-2 text-left hover:bg-stone-50" onClick={() => send(q)} disabled={mode === "replay"}>
                {q}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => <Message key={i} m={m} />)}
        {busy && (
          <div className="flex items-center gap-2 text-xs text-stone-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
            <span className="truncate">{activity || "Working…"}</span>
          </div>
        )}
        {question && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
            <div className="mb-2 font-medium text-amber-900">The lead asks: {question}</div>
            <div className="flex gap-2">
              <input className="flex-1 rounded border border-amber-300 px-2 py-1" value={answer} onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && resume()} placeholder="Your answer" />
              <button className="rounded bg-amber-600 px-3 py-1 text-white" onClick={resume}>Answer</button>
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
      <div className="space-y-2 border-t border-stone-200 p-3">
        {selection?.items?.length ? <SelectionChip sel={selection} onClear={() => setSelection(null)} /> : null}
        {err && <div className="text-xs text-red-600">{err}</div>}
        <div className="flex gap-2">
          <textarea
            className="min-h-[44px] flex-1 resize-none rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none"
            rows={2}
            placeholder={mode === "replay" && !DIRECTOR ? "Replaying a recorded session" : selection ? "Ask about the selection…" : "Ask a question…"}
            value={text}
            disabled={(busy || mode === "replay") && !DIRECTOR}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          />
          <button className="self-end rounded-md bg-stone-900 px-3 py-2 text-sm text-white disabled:opacity-40" disabled={busy || !text.trim() || mode === "replay"} onClick={() => send()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
