import { useEffect, useState } from "react";
import { api } from "../api";
import { useStore } from "../store";

type SessionInfo = { id: string; first_question: string; cost: number; views: number };

export default function TopBar({ drawerOpen, toggleDrawer }: { drawerOpen: boolean; toggleDrawer: () => void }) {
  const { sessionId, mode, cost, open, replay, busy } = useStore();
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [health, setHealth] = useState<{ live: boolean; ledger_total: number; budget: number } | null>(null);
  const [speed, setSpeed] = useState(4);

  const refresh = () => {
    api.get<SessionInfo[]>("/api/sessions").then(setSessions).catch(() => {});
    api.get("/api/health").then(setHealth).catch(() => {});
  };
  useEffect(refresh, [sessionId, busy]);

  const newSession = async () => {
    const { id } = await api.post<{ id: string }>("/api/sessions");
    open(id);
    refresh();
  };

  return (
    <header className="flex h-12 shrink-0 items-center gap-3 border-b border-stone-200 bg-white px-4">
      <div className="flex items-baseline gap-2">
        <span className="text-[15px] font-semibold tracking-tight">sciviz</span>
        <span className="text-xs text-stone-500">Columbia University · OpenAlex 2021–2024</span>
      </div>
      <div className="ml-4 flex items-center gap-2">
        <select
          className="max-w-[360px] rounded-md border border-stone-300 bg-white px-2 py-1 text-sm"
          value={sessionId ?? ""}
          onChange={(e) => open(e.target.value)}
        >
          {!sessionId && <option value="">Select a session…</option>}
          {sessions.map((s) => (
            <option key={s.id} value={s.id}>
              {s.first_question ? s.first_question.slice(0, 70) : "(empty session)"} · {s.id}
            </option>
          ))}
        </select>
        <button className="rounded-md border border-stone-300 px-2.5 py-1 text-sm hover:bg-stone-100" onClick={newSession}>
          New session
        </button>
      </div>
      <div className="ml-auto flex items-center gap-3 text-sm">
        {sessionId && (
          <div className="flex items-center gap-1.5">
            <button
              className="rounded-md border border-stone-300 px-2.5 py-1 hover:bg-stone-100"
              onClick={() => { (useStore.setState as any)({ speed }); replay(); }}
              title="Replay this session from its recorded events (no API calls)"
            >
              ⟲ Replay
            </button>
            <select className="rounded-md border border-stone-300 px-1 py-1 text-xs" value={speed} onChange={(e) => setSpeed(+e.target.value)}>
              {[1, 2, 4, 8, 16].map((x) => <option key={x} value={x}>{x}×</option>)}
            </select>
            {mode === "replay" && (
              <button className="rounded-md bg-amber-100 px-2 py-1 text-xs text-amber-800" onClick={() => sessionId && open(sessionId)}>
                replaying · back to live
              </button>
            )}
          </div>
        )}
        <span className="text-stone-500" title="Session cost / total LLM spend (budget)">
          ${cost.toFixed(2)} · total ${health?.ledger_total?.toFixed(2) ?? "–"} / ${health?.budget ?? 50}
        </span>
        <span className={`rounded px-1.5 py-0.5 text-xs ${health?.live ? "bg-emerald-50 text-emerald-700" : "bg-stone-100 text-stone-600"}`}>
          {health?.live ? "live" : "replay only"}
        </span>
        <button className="rounded-md px-2 py-1 text-stone-600 hover:bg-stone-100" onClick={toggleDrawer} title="Toggle side panel">
          {drawerOpen ? "⇥" : "⇤"}
        </button>
      </div>
    </header>
  );
}
