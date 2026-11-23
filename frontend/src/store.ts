// Client state, derived entirely from the session's event stream (live or replayed), so that a replay
// reproduces exactly what the user saw: messages, views, parameter changes, selections, highlights, trace.
import { create } from "zustand";

export type Item = { type: string; id?: string; key?: unknown; label?: string };
export type Ev = { ts: number; session: string; agent: string; kind: string; payload: any; replay?: boolean };
export type Selection = { view_id: string; viz: string; items: Item[] };
export type ViewState = {
  view_id: string; viz: string; title: string; params: Record<string, unknown>; highlight: Item[];
  history: string[]; compareWith: string | null; revision: number;
};
export type Msg = { role: "user" | "assistant" | "system"; text: string; ts: number; selection?: Selection | null; error?: boolean };
export type Todo = { content: string; status: string };
export type DrawerTab = "details" | "trace" | "artifacts" | "plan";

type State = {
  sessionId: string | null;
  mode: "live" | "replay";
  replayNonce: number;
  events: Ev[];
  messages: Msg[];
  views: ViewState[];
  artifacts: Record<string, { id: string; kind: string; title: string; producer: string; version?: number }>;
  todos: Todo[];
  decisions: { agent: string; text: string }[];
  selection: Selection | null;
  hover: { view_id: string; viz: string; item: Item | null } | null;
  busy: boolean;
  question: string | null;
  cost: number;
  activity: string;
  drawer: DrawerTab;
  focusArtifact: string | null;
  open(sessionId: string, mode?: "live" | "replay"): void;
  replay(): void;
  apply(ev: Ev): void;
  setSelection(sel: Selection | null): void;
  setHover(h: State["hover"]): void;
  setDrawer(t: DrawerTab): void;
  focus(id: string | null): void;
  setBusy(b: boolean, question?: string | null): void;
  patchView(view_id: string, patch: Partial<ViewState>): void;
};

const fresh = {
  events: [], messages: [], views: [], artifacts: {}, todos: [], decisions: [], selection: null, hover: null,
  busy: false, question: null, cost: 0, activity: "", focusArtifact: null,
};

function first(text: unknown, n = 120): string {
  const line = String(text ?? "").split("\n").find((l) => l.trim()) ?? "";
  return line.length > n ? line.slice(0, n) + "…" : line;
}

function activityOf(ev: Ev): string | null {
  const p = ev.payload || {};
  switch (ev.kind) {
    case "delegate": {
      const goal = String(p.brief ?? "").split("\n").find((l: string) => l.toUpperCase().startsWith("GOAL")) ?? "";
      return `Lead → ${p.to}: ${first(goal.replace(/^GOAL:\s*/i, ""), 110)}`;
    }
    case "tool_call": return `${ev.agent} · ${p.tool}`;
    case "gate": return `review ${p.artifact}: ${p.verdict}`;
    case "report": return "Lead is reviewing a report";
    case "artifact": return `${ev.agent} saved ${p.id}`;
    default: return null;
  }
}

export const useStore = create<State>((set, get) => ({
  sessionId: null, mode: "live", replayNonce: 0, drawer: "trace", ...fresh,

  open: (sessionId, mode = "live") => set({ sessionId, mode, ...fresh, replayNonce: get().replayNonce + 1 }),
  replay: () => set({ mode: "replay", ...fresh, replayNonce: get().replayNonce + 1 }),

  apply: (ev) => set((s) => {
    const p = ev.payload || {};
    const next: Partial<State> = { events: [...s.events, ev] };
    const act = activityOf(ev);
    if (act) next.activity = act;
    switch (ev.kind) {
      case "message":
        if (ev.agent === "user") {
          next.messages = [...s.messages, { role: "user", text: p.text, ts: ev.ts, selection: p.selection ?? null }];
          if (p.answer_to) next.question = null; else { next.busy = true; next.activity = "Lead is planning"; }
        } else {
          next.messages = [...s.messages, { role: "assistant", text: p.text, ts: ev.ts }];
        }
        break;
      case "interrupt": next.question = p.question; break;
      case "error":
        next.messages = [...s.messages, { role: "system", text: p.message, ts: ev.ts, error: true }];
        break;
      case "done": next.busy = false; next.activity = ""; break;
      case "cost": next.cost = s.cost + (p.usd || 0); break;
      case "artifact":
        next.artifacts = { ...s.artifacts, [p.id]: { id: p.id, kind: p.artifact_kind, title: p.title, producer: ev.agent, version: p.version } };
        break;
      case "plan":
        if (p.todos) next.todos = p.todos;
        if (p.decision) next.decisions = [...s.decisions, { agent: ev.agent, text: p.decision }];
        break;
      case "select":
        next.selection = p.items?.length ? { view_id: p.view_id, viz: p.viz, items: p.items } : null;
        break;
      case "view": {
        const views = s.views.map((v) => ({ ...v }));
        const v = views.find((x) => x.view_id === p.view_id);
        if (p.action === "show" && !v) {
          views.push({ view_id: p.view_id, viz: p.viz, title: p.title, params: {}, highlight: [], history: [], compareWith: null, revision: 0 });
        } else if (v && p.action === "replace" && p.viz !== v.viz) {
          v.history = [...v.history, v.viz]; v.viz = p.viz; v.title = p.title ?? v.title; v.highlight = []; v.revision++;
        } else if (v && p.action === "params") {
          v.params = { ...v.params, ...p.params };
        } else if (v && p.action === "highlight") {
          v.highlight = p.items || [];
        }
        next.views = views;
        break;
      }
    }
    return next;
  }),

  setSelection: (selection) => set({ selection }),
  setHover: (hover) => set({ hover }),
  setDrawer: (drawer) => set({ drawer }),
  focus: (focusArtifact) => set({ focusArtifact, drawer: focusArtifact ? "artifacts" : get().drawer }),
  setBusy: (busy, question = null) => set({ busy, question }),
  patchView: (view_id, patch) => set((s) => ({ views: s.views.map((v) => (v.view_id === view_id ? { ...v, ...patch } : v)) })),
}));

export const AGENT_COLORS: Record<string, string> = {
  lead: "#7c4dcc", data: "#0f8fa8", analyst: "#2e8b43", viz: "#c27a00", critic: "#c4382b", gate: "#c4382b",
  user: "#57534e", system: "#78716c",
};
