import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, cachedGet } from "../api";
import { useStore, type Item, type ViewState } from "../store";

const lastState = new Map<string, unknown>(); // view_id -> module state (zoom/pan/layout), survives version swaps

export default function ViewsArea() {
  const views = useStore((s) => s.views);
  if (!views.length)
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-sm text-stone-500">
        Views appear here when the agents deliver a visualization that has passed review.
      </div>
    );
  const cols = views.length === 1 ? "grid-cols-1" : "grid-cols-2";
  const rows = views.length <= 2 ? "grid-rows-1" : "grid-rows-2";
  return (
    <div className={`grid h-full gap-3 p-3 ${cols} ${rows}`}>
      {views.slice(-4).map((v) => (
        <div key={v.view_id} className={`min-h-0 ${v.compareWith && views.length > 1 ? "col-span-2" : ""}`}>
          <ViewPanel view={v} />
        </div>
      ))}
    </div>
  );
}

function ViewPanel({ view }: { view: ViewState }) {
  const { sessionId, mode, patchView } = useStore();
  const box = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState<{ w: number; h: number } | null>(null);
  const [manifest, setManifest] = useState<any>(null);
  const [versions, setVersions] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => {
      const w = Math.floor(e.contentRect.width), h = Math.floor(e.contentRect.height);
      setSize((old) => (!old || Math.abs(old.w - w) > 40 || Math.abs(old.h - h) > 40 ? { w, h } : old));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    setError(null);
    cachedGet(`/api/sessions/${sessionId}/artifacts/${view.viz}/viz.json`).then(setManifest).catch(() => setManifest(null));
    api.get<any[]>(`/api/sessions/${sessionId}/artifacts/${view.viz}/versions`).then(setVersions).catch(() => {});
  }, [sessionId, view.viz, view.revision]);

  const setParam = (k: string, v: unknown) => {
    patchView(view.view_id, { params: { ...view.params, [k]: v } });
    if (mode !== "live") return;
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => api.post(`/api/sessions/${sessionId}/views/${view.view_id}`, { params: { [k]: v } }), 300);
  };
  const switchTo = (viz: string) => {
    if (mode === "live") api.post(`/api/sessions/${sessionId}/views/${view.view_id}`, { viz }).catch((e) => setError(e.message));
  };
  const current = versions.find((x) => x.id === view.viz);
  const approved = versions.filter((x) => x.status === "approved" || x.status === "approved_with_issues");

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm">
      <header className="flex items-center gap-2 border-b border-stone-100 px-3 py-2">
        <span className="rounded bg-stone-100 px-1.5 py-0.5 font-mono text-[11px] text-stone-600">{view.view_id}</span>
        <h2 className="min-w-0 flex-1 truncate text-sm font-medium" title={view.title}>{view.title}</h2>
        {approved.length > 1 && (
          <select className="rounded border border-stone-300 px-1 py-0.5 text-xs" value={view.viz} disabled={mode !== "live"}
            onChange={(e) => switchTo(e.target.value)} title="Switch version">
            {approved.map((x) => <option key={x.id} value={x.id}>{x.id} · v{x.version}</option>)}
          </select>
        )}
        {approved.length <= 1 && current && <span className="font-mono text-[11px] text-stone-500">{view.viz} · v{current.version}</span>}
        {view.history.length > 0 && (
          <>
            <button className="rounded px-1.5 py-0.5 text-xs text-stone-600 hover:bg-stone-100" disabled={mode !== "live"}
              onClick={() => switchTo(view.history[view.history.length - 1])} title="Back to the previous version">↶ Undo</button>
            <button className={`rounded px-1.5 py-0.5 text-xs hover:bg-stone-100 ${view.compareWith ? "bg-sky-50 text-sky-700" : "text-stone-600"}`}
              onClick={() => patchView(view.view_id, { compareWith: view.compareWith ? null : view.history[view.history.length - 1] })}
              title="Show the previous version side by side">⇆ Compare</button>
          </>
        )}
      </header>
      <ParamControls schema={manifest?.params} values={view.params} onChange={setParam} />
      {error && <div className="bg-red-50 px-3 py-1 text-xs text-red-700">{error}</div>}
      <div ref={box} className="relative min-h-0 flex-1">
        {size && size.w > 100 && size.h > 100 && (
          view.compareWith ? (
            <div className="absolute inset-0 flex">
              <div className="relative flex-1 border-r border-stone-200">
                <span className="absolute left-2 top-1 z-10 rounded bg-white/90 px-1 text-[10px] text-stone-500">{view.compareWith} (previous)</span>
                <ViewFrame view={view} viz={view.compareWith} w={Math.floor(size.w / 2)} h={size.h} secondary onError={setError} />
              </div>
              <div className="relative flex-1">
                <ViewFrame view={view} viz={view.viz} w={Math.floor(size.w / 2)} h={size.h} onError={setError} />
              </div>
            </div>
          ) : (
            <ViewFrame key={`${view.viz}-${size.w}x${size.h}`} view={view} viz={view.viz} w={size.w} h={size.h} onError={setError} />
          )
        )}
      </div>
    </section>
  );
}

function ViewFrame({ view, viz, w, h, secondary, onError }: {
  view: ViewState; viz: string; w: number; h: number; secondary?: boolean; onError: (e: string | null) => void;
}) {
  const { sessionId, mode, selection, setSelection, setHover } = useStore();
  const ref = useRef<HTMLIFrameElement>(null);
  const ready = useRef(false);
  const post = (msg: object) => ref.current?.contentWindow?.postMessage({ target: "sciviz-view", ...msg }, "*");

  useEffect(() => {
    ready.current = false;
    const onMsg = (e: MessageEvent) => {
      if (e.source !== ref.current?.contentWindow) return;
      const d = e.data;
      if (!d || d.source !== "sciviz-view") return;
      if (d.type === "ready") {
        ready.current = true;
        onError(null);
        const st = useStore.getState();
        const vs = st.views.find((x) => x.view_id === view.view_id);
        if (vs && !secondary && Object.keys(vs.params).length) post({ cmd: "setParams", params: vs.params });
        if (!secondary && lastState.has(view.view_id)) post({ cmd: "setState", state: lastState.get(view.view_id) });
        if (vs?.highlight?.length) post({ cmd: "highlight", items: vs.highlight });
        if (st.selection?.items?.length) post({ cmd: "setSelection", items: st.selection.items });
      } else if (d.type === "select" && d.payload.mode !== "external") {
        const items: Item[] = d.payload.items || [];
        const sel = items.length ? { view_id: view.view_id, viz, items } : null;
        setSelection(sel);
        if (mode === "live") api.post(`/api/sessions/${sessionId}/selection`, sel ?? { view_id: view.view_id, viz, items: [] }).catch(() => {});
      } else if (d.type === "hover") {
        setHover(d.payload.item ? { view_id: view.view_id, viz, item: d.payload.item } : null);
      } else if (d.type === "state" && !secondary) {
        lastState.set(view.view_id, d.payload.state);
      } else if (d.type === "error") {
        onError(`View error: ${String(d.payload.message).slice(0, 300)}`);
      }
    };
    window.addEventListener("message", onMsg);
    const poll = window.setInterval(() => ready.current && !secondary && post({ cmd: "getState" }), 2000);
    return () => { window.removeEventListener("message", onMsg); window.clearInterval(poll); };
  }, [viz, sessionId, mode]);

  const paramsKey = JSON.stringify(view.params);
  useEffect(() => { if (ready.current && !secondary) post({ cmd: "setParams", params: view.params }); }, [paramsKey]);
  const hlKey = JSON.stringify(view.highlight);
  useEffect(() => { if (ready.current) post({ cmd: "highlight", items: view.highlight }); }, [hlKey]);
  const selKey = JSON.stringify(selection?.items ?? []);
  useEffect(() => { if (ready.current) post({ cmd: "setSelection", items: selection?.items ?? [] }); }, [selKey]);

  // Views are designed (and reviewed) at desktop sizes: narrow panels render at a minimum width and scale down.
  const MIN_W = 720;
  const scale = w < MIN_W ? w / MIN_W : 1;
  const rw = Math.round(w / scale), rh = Math.round(h / scale);
  const src = `/runtime/view.html?session=${sessionId}&viz=${viz}&view=${secondary ? "" : view.view_id}&w=${rw}&h=${rh}&fresh=1`;
  return (
    <iframe ref={ref} title={`${view.view_id} ${viz}`} sandbox="allow-scripts" src={src}
      style={{ width: rw, height: rh, transform: `scale(${scale})`, transformOrigin: "0 0" }}
      className="absolute left-0 top-0 border-0" />
  );
}

function ParamControls({ schema, values, onChange }: {
  schema?: { properties?: Record<string, any> }; values: Record<string, unknown>; onChange: (k: string, v: unknown) => void;
}) {
  const props = Object.entries(schema?.properties ?? {});
  if (!props.length) return null;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-stone-100 bg-stone-50/60 px-3 py-1.5 text-xs">
      {props.map(([k, sch]) => {
        const v = values[k] ?? sch.default;
        const label = sch.title || k;
        if (Array.isArray(sch.enum))
          return (
            <label key={k} className="flex items-center gap-1.5 text-stone-600">
              {label}
              <select className="rounded border border-stone-300 bg-white px-1 py-0.5" value={String(v)} onChange={(e) => {
                const raw = e.target.value;
                const found = sch.enum.find((x: unknown) => String(x) === raw);
                onChange(k, found ?? raw);
              }}>
                {sch.enum.map((x: unknown) => <option key={String(x)} value={String(x)}>{String(x)}</option>)}
              </select>
            </label>
          );
        if (sch.type === "boolean")
          return (
            <label key={k} className="flex items-center gap-1.5 text-stone-600">
              <input type="checkbox" checked={Boolean(v)} onChange={(e) => onChange(k, e.target.checked)} />{label}
            </label>
          );
        if ((sch.type === "number" || sch.type === "integer") && sch.minimum !== undefined && sch.maximum !== undefined)
          return (
            <label key={k} className="flex items-center gap-1.5 text-stone-600">
              {label}
              <input type="range" min={sch.minimum} max={sch.maximum} step={sch.type === "integer" ? 1 : (sch.maximum - sch.minimum) / 100}
                value={Number(v)} onChange={(e) => onChange(k, sch.type === "integer" ? parseInt(e.target.value) : parseFloat(e.target.value))} />
              <span className="w-10 font-mono text-stone-800">{sch.type === "integer" ? Number(v) : Number(v).toFixed(2)}</span>
            </label>
          );
        return (
          <label key={k} className="flex items-center gap-1.5 text-stone-600">
            {label}
            <input className="w-24 rounded border border-stone-300 px-1 py-0.5" defaultValue={String(v ?? "")}
              onKeyDown={(e) => { if (e.key === "Enter") { const t = (e.target as HTMLInputElement).value; onChange(k, sch.type === "number" || sch.type === "integer" ? Number(t) : t); } }} />
          </label>
        );
      })}
    </div>
  );
}
