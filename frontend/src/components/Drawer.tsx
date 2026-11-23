import { useEffect, useMemo, useRef, useState } from "react";
import { api, cachedGet } from "../api";
import { AGENT_COLORS, useStore, type DrawerTab, type Ev, type Item } from "../store";

const TABS: { id: DrawerTab; label: string }[] = [
  { id: "details", label: "Details" }, { id: "trace", label: "Trace" }, { id: "artifacts", label: "Artifacts" }, { id: "plan", label: "Plan" },
];

export default function Drawer() {
  const { drawer, setDrawer } = useStore();
  return (
    <div className="flex h-full flex-col">
      <nav className="flex border-b border-stone-200 px-2">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setDrawer(t.id)}
            className={`px-3 py-2 text-sm ${drawer === t.id ? "border-b-2 border-stone-900 font-medium text-stone-900" : "text-stone-500 hover:text-stone-800"}`}>
            {t.label}
          </button>
        ))}
      </nav>
      <div className="scroll-thin min-h-0 flex-1 overflow-y-auto">
        {drawer === "details" && <Details />}
        {drawer === "trace" && <Trace />}
        {drawer === "artifacts" && <Artifacts />}
        {drawer === "plan" && <Plan />}
      </div>
    </div>
  );
}

function Badge({ agent }: { agent: string }) {
  return <span className="rounded px-1.5 py-0.5 text-[10.5px] font-semibold uppercase tracking-wide text-white" style={{ background: AGENT_COLORS[agent] ?? "#78716c" }}>{agent}</span>;
}

// ---------------------------------------------------------------------------------------------------- details
function Details() {
  const { hover, selection, sessionId } = useStore();
  const target = hover?.item ? { viz: hover.viz, items: [hover.item], how: `hovered in ${hover.view_id}` }
    : selection?.items?.length ? { viz: selection.viz, items: selection.items.slice(0, 5), how: `selected in ${selection.view_id}` } : null;
  if (!target) return <p className="p-4 text-sm text-stone-500">Hover over or click a mark in a view to see its details here. Selected items are sent along with your next question.</p>;
  return (
    <div className="space-y-4 p-4">
      <div className="text-xs text-stone-500">{target.how}{selection && selection.items.length > 5 && !hover?.item ? ` (first 5 of ${selection.items.length})` : ""}</div>
      {target.items.map((it, i) => <ItemDetails key={i} item={it} viz={target.viz} sessionId={sessionId!} />)}
    </div>
  );
}

function matches(row: any, it: Item): boolean {
  if (it.id !== undefined && it.id !== null) return Object.values(row).some((v) => String(v) === String(it.id));
  if (it.key && typeof it.key === "object") return Object.entries(it.key as object).every(([k, v]) => String(row[k]) === String(v));
  return false;
}

function rowsOf(data: any): any[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") return Object.values(data).filter(Array.isArray).flat() as any[];
  return [];
}

function ItemDetails({ item, viz, sessionId }: { item: Item; viz: string; sessionId: string }) {
  const [entity, setEntity] = useState<any>(null);
  const [records, setRecords] = useState<any[]>([]);
  useEffect(() => {
    setEntity(null); setRecords([]);
    if (item.id) cachedGet(`/api/entity/${encodeURIComponent(item.id)}`).then(setEntity).catch(() => {});
    cachedGet(`/api/sessions/${sessionId}/artifacts/${viz}/viz.json`).then(async (m) => {
      const out: any[] = [];
      for (const aid of Object.values<string>(m.data ?? {})) {
        const d = await cachedGet(`/api/sessions/${sessionId}/artifacts/${aid}/data`).catch(() => null);
        out.push(...rowsOf(d).filter((r) => r && typeof r === "object" && matches(r, item)).slice(0, 3));
      }
      setRecords(out.slice(0, 4));
    }).catch(() => {});
  }, [item.id, JSON.stringify(item.key), viz]);
  return (
    <div className="rounded-lg border border-stone-200">
      <div className="border-b border-stone-100 px-3 py-2">
        <div className="text-sm font-medium">{item.label ?? entity?.label ?? item.id ?? JSON.stringify(item.key)}</div>
        <div className="font-mono text-[11px] text-stone-500">{item.type} · {item.id ?? JSON.stringify(item.key)}</div>
      </div>
      {entity && <KV title={`dataset record (${entity.type})`} obj={entity.record} />}
      {records.map((r, i) => <KV key={i} title="data shown in the view" obj={r} />)}
    </div>
  );
}

function KV({ title, obj }: { title: string; obj: Record<string, unknown> }) {
  const entries = Object.entries(obj).filter(([, v]) => v !== null && v !== "" && typeof v !== "object").slice(0, 16);
  return (
    <div className="px-3 py-2">
      <div className="mb-1 text-[11px] uppercase tracking-wide text-stone-400">{title}</div>
      <table className="w-full text-xs">
        <tbody>{entries.map(([k, v]) => (
          <tr key={k}><td className="w-2/5 py-0.5 pr-2 align-top text-stone-500">{k}</td><td className="break-words py-0.5 text-stone-800">{String(v)}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------- trace
const HIDDEN = new Set(["cost", "session"]);

function Trace() {
  const events = useStore((s) => s.events);
  const sessionId = useStore((s) => s.sessionId);
  const end = useRef<HTMLDivElement>(null);
  const shown = useMemo(() => events.filter((e) => !HIDDEN.has(e.kind) && !(e.kind === "tool_result" && e.payload.ok)), [events]);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [shown.length]);
  const costs = useMemo(() => {
    const by: Record<string, number> = {};
    for (const e of events) if (e.kind === "cost") by[e.agent] = (by[e.agent] ?? 0) + e.payload.usd;
    return by;
  }, [events]);
  return (
    <div className="space-y-1.5 p-3 text-xs">
      {Object.keys(costs).length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2 rounded-md bg-stone-50 p-2 text-[11px] text-stone-600">
          {Object.entries(costs).map(([a, v]) => <span key={a}><Badge agent={a} /> ${v.toFixed(3)}</span>)}
        </div>
      )}
      {shown.map((e, i) => <TraceRow key={i} e={e} sessionId={sessionId!} />)}
      <div ref={end} />
    </div>
  );
}

function TraceRow({ e, sessionId }: { e: Ev; sessionId: string }) {
  const [open, setOpen] = useState(false);
  const p = e.payload || {};
  let summary: React.ReactNode = null;
  let detail: string | null = null;
  switch (e.kind) {
    case "message": summary = <span className="text-stone-700">{e.agent === "user" ? "User: " : "Answer: "}{String(p.text).slice(0, 140)}</span>; detail = p.text; break;
    case "delegate": summary = <span>→ <b>{p.to}</b>: {String(p.brief).split("\n").find((l: string) => /^GOAL/i.test(l))?.replace(/^GOAL:\s*/i, "") ?? ""}</span>; detail = p.brief; break;
    case "report": summary = <span className="text-stone-600">report: {String(p.text).split("\n")[0].slice(0, 120)}</span>; detail = p.text; break;
    case "tool_call": summary = <span className="font-mono">{p.tool}</span>; detail = Object.entries(p.args || {}).map(([k, v]) => `${k}: ${v}`).join("\n\n"); break;
    case "tool_result": summary = <span className="text-red-600">✗ {p.tool} failed</span>; detail = p.result; break;
    case "artifact": summary = <span>saved <b className="font-mono">{p.id}</b> ({p.artifact_kind}) {p.title}</span>; break;
    case "gate": summary = (
      <span className={p.verdict === "pass" ? "text-emerald-700" : "text-red-700"}>
        review <b className="font-mono">{p.artifact}</b>: {p.verdict} {p.stage === "automated" ? "(automated checks)" : p.scores ? `· ${p.scores}` : ""}
      </span>);
      detail = [p.summary, ...(p.issues || []).map((x: any) => `[${x.severity}] ${x.problem} → ${x.fix}`), ...(p.problems || [])].filter(Boolean).join("\n");
      break;
    case "view": summary = <span>view {p.action} <b>{p.view_id}</b> {p.viz ?? ""} {p.params ? JSON.stringify(p.params) : ""}</span>; break;
    case "select": summary = <span>selected {p.items?.length ?? 0} item(s) in {p.view_id}</span>; break;
    case "plan": summary = p.todos ? <span>plan updated ({p.todos.length} steps)</span> : p.decision ? <span>decided: {String(p.decision).slice(0, 140)}</span> : <span>{p.escalation}</span>; detail = p.decision ?? null; break;
    case "interrupt": summary = <span className="text-amber-700">asks the user: {p.question}</span>; break;
    case "error": summary = <span className="text-red-700">error: {p.message}</span>; break;
    case "done": summary = <span className="text-stone-500">turn finished · {p.seconds}s · ${p.cost}</span>; break;
    default: summary = <span className="text-stone-500">{e.kind}</span>;
  }
  return (
    <div className="rounded border border-transparent px-1 py-0.5 hover:border-stone-200">
      <div className="flex cursor-pointer items-start gap-1.5" onClick={() => detail && setOpen((x) => !x)}>
        <Badge agent={e.agent} />
        <div className="min-w-0 flex-1 break-words leading-5">{summary}</div>
        {detail && <span className="text-stone-400">{open ? "▾" : "▸"}</span>}
      </div>
      {e.kind === "gate" && (
        <img className="ml-12 mt-1 max-h-28 rounded border border-stone-200" alt={`screenshot of ${p.artifact}`}
          src={`/api/sessions/${sessionId}/artifacts/${p.artifact}/shots/default.png`} />
      )}
      {open && detail && <pre className="ml-12 mt-1 max-h-72 overflow-auto whitespace-pre-wrap rounded bg-stone-50 p-2 font-mono text-[11px] text-stone-700">{detail}</pre>}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------- artifacts
function Artifacts() {
  const { artifacts, focusArtifact, focus, sessionId } = useStore();
  const [detail, setDetail] = useState<any>(null);
  useEffect(() => {
    setDetail(null);
    if (focusArtifact) api.get(`/api/sessions/${sessionId}/artifacts/${focusArtifact}`).then(setDetail).catch(() => setDetail({ error: true }));
  }, [focusArtifact, sessionId]);
  const list = Object.values(artifacts);
  return (
    <div className="p-3 text-xs">
      {focusArtifact && (
        <div className="mb-3 rounded-lg border border-stone-200 p-3">
          <div className="mb-1 flex items-center gap-2">
            <b className="font-mono text-sm">{focusArtifact}</b>
            <span className="truncate text-stone-600">{detail?.title}</span>
            <button className="ml-auto text-stone-400 hover:text-stone-700" onClick={() => focus(null)}>✕</button>
          </div>
          {detail && !detail.error && (
            <div className="space-y-2">
              <div className="text-stone-500">{detail.kind} · by {detail.producer}{detail.status ? ` · ${detail.status}` : ""}</div>
              {detail.inputs?.length > 0 && <div>inputs: {detail.inputs.map((i: string) => <span key={i} className="cite" onClick={() => focus(i)}>{i}</span>)}</div>}
              {detail.description && <p className="text-stone-700">{detail.description}</p>}
              {detail.kind === "viz" && <img className="rounded border border-stone-200" alt="screenshot" src={`/api/sessions/${sessionId}/artifacts/${focusArtifact}/shots/default.png`} />}
              {detail.summary_text && <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded bg-stone-50 p-2 font-mono text-[11px]">{detail.summary_text}</pre>}
              {detail.code && <details><summary className="cursor-pointer text-stone-600">code that produced it</summary>
                <pre className="mt-1 max-h-72 overflow-auto whitespace-pre-wrap rounded bg-stone-50 p-2 font-mono text-[11px]">{detail.code}</pre></details>}
              {detail.reviews?.filter((r: any) => r.stage === "critic").map((r: any, i: number) => (
                <div key={i} className="rounded bg-stone-50 p-2"><b>critic: {r.verdict}</b> — {r.summary}</div>
              ))}
            </div>
          )}
        </div>
      )}
      <table className="w-full">
        <tbody>
          {list.map((a) => (
            <tr key={a.id} className={`cursor-pointer hover:bg-stone-50 ${focusArtifact === a.id ? "bg-sky-50" : ""}`} onClick={() => focus(a.id)}>
              <td className="py-1 pr-2 font-mono font-semibold">{a.id}</td>
              <td className="py-1 pr-2 text-stone-500">{a.kind}</td>
              <td className="py-1 pr-2">{a.title}</td>
              <td className="py-1"><Badge agent={a.producer} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      {!list.length && <p className="text-stone-500">No artifacts yet.</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------------------------------- plan
function Plan() {
  const { todos, decisions } = useStore();
  return (
    <div className="space-y-4 p-4 text-sm">
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">Lead's plan</h3>
        {todos.length ? todos.map((t, i) => (
          <div key={i} className="flex gap-2 py-0.5">
            <span>{t.status === "completed" ? "✓" : t.status === "in_progress" ? "◐" : "○"}</span>
            <span className={t.status === "completed" ? "text-stone-400 line-through" : ""}>{t.content}</span>
          </div>
        )) : <p className="text-stone-500">No plan yet.</p>}
      </div>
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">Definitions and assumptions</h3>
        {decisions.length ? decisions.map((d, i) => (
          <div key={i} className="mb-2 flex gap-2"><Badge agent={d.agent} /><span className="text-stone-700">{d.text}</span></div>
        )) : <p className="text-stone-500">None recorded yet.</p>}
      </div>
    </div>
  );
}
