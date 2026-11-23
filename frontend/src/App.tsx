import { useEffect, useState } from "react";
import { api } from "./api";
import { useStore } from "./store";
import TopBar from "./components/TopBar";

export const DIRECTOR = new URLSearchParams(location.search).get("director") === "1";
import Chat from "./components/Chat";
import ViewsArea from "./components/ViewsArea";
import Drawer from "./components/Drawer";

/** Connects to the session's event stream (live tail or accelerated replay) and feeds the store. */
function useEventStream() {
  const { sessionId, mode, replayNonce, apply, setBusy } = useStore();
  const speed = useStore((s) => (s as any).speed ?? 4);
  useEffect(() => {
    if (!sessionId) return;
    if (DIRECTOR) {
      // Director mode (used to record narrated demo videos): load all recorded events, then let a script apply
      // them at a controlled pace with window.__director.playTo(index, ms).
      const buf: any[] = [];
      let idx = 0;
      let timer: number | undefined;
      const es = new EventSource(`/api/sessions/${sessionId}/events?replay=1&speed=1000000`);
      const d: any = {
        loaded: false,
        events: () => buf.map((e, i) => ({ i, kind: e.kind, agent: e.agent, payload: e.payload })),
        index: () => idx,
        playTo: (target: number, ms: number) => new Promise<void>((resolve) => {
          window.clearInterval(timer);
          const end = Math.min(target, buf.length);
          const n = Math.max(0, end - idx);
          if (!n) { resolve(); return; }
          timer = window.setInterval(() => {
            if (idx >= end) { window.clearInterval(timer); resolve(); return; }
            apply(buf[idx++]);
          }, Math.max(12, ms / n));
        }),
      };
      (window as any).__director = d;
      es.addEventListener("ev", (e) => buf.push(JSON.parse((e as MessageEvent).data)));
      es.addEventListener("replay_end", () => { d.loaded = true; es.close(); });
      return () => es.close();
    }
    const url = `/api/sessions/${sessionId}/events` + (mode === "replay" ? `?replay=1&speed=${speed}` : "");
    const es = new EventSource(url);
    es.addEventListener("ev", (e) => apply(JSON.parse((e as MessageEvent).data)));
    es.addEventListener("replay_end", () => { setBusy(false); (window as any).__replayDone = true; es.close(); });
    if (mode === "live") {
      // the server knows whether a run is in progress (older sessions have no 'done' events)
      api.get(`/api/sessions/${sessionId}`).then((st) => setBusy(st.busy, st.question)).catch(() => {});
    }
    return () => es.close();
  }, [sessionId, mode, replayNonce]);
}

export default function App() {
  useEventStream();
  const [drawerOpen, setDrawerOpen] = useState(true);
  const sessionId = useStore((s) => s.sessionId);
  const open = useStore((s) => s.open);

  useEffect(() => {
    const fromUrl = new URLSearchParams(location.search).get("session");
    const replay = new URLSearchParams(location.search).get("replay") === "1";
    const speed = Number(new URLSearchParams(location.search).get("speed") || 0);
    if (speed > 0) (useStore.setState as any)({ speed });
    if (fromUrl) { open(fromUrl, replay || DIRECTOR ? "replay" : "live"); return; }
    api.get<any[]>("/api/sessions").then((list) => { if (list.length) open(list[0].id); }).catch(() => {});
  }, []);

  return (
    <div className="flex h-full flex-col">
      <TopBar drawerOpen={drawerOpen} toggleDrawer={() => setDrawerOpen((x) => !x)} />
      <div className="flex min-h-0 flex-1">
        <aside className="flex w-[380px] shrink-0 flex-col border-r border-stone-200 bg-white"><Chat /></aside>
        <main className="min-w-0 flex-1 overflow-hidden">{sessionId ? <ViewsArea /> : <Welcome />}</main>
        {drawerOpen && <aside className="w-[400px] shrink-0 border-l border-stone-200 bg-white"><Drawer /></aside>}
      </div>
    </div>
  );
}

function Welcome() {
  return <div className="flex h-full items-center justify-center text-stone-500">Create a session to start.</div>;
}
