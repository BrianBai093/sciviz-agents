import { useEffect, useState } from "react";
import { api } from "./api";
import { useStore } from "./store";
import TopBar from "./components/TopBar";
import Chat from "./components/Chat";
import ViewsArea from "./components/ViewsArea";
import Drawer from "./components/Drawer";

/** Connects to the session's event stream (live tail or accelerated replay) and feeds the store. */
function useEventStream() {
  const { sessionId, mode, replayNonce, apply, setBusy } = useStore();
  const speed = useStore((s) => (s as any).speed ?? 4);
  useEffect(() => {
    if (!sessionId) return;
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
    if (fromUrl) { open(fromUrl, replay ? "replay" : "live"); return; }
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
