async function check(r: Response) {
  if (!r.ok) {
    let detail = `${r.status}`;
    try { detail = (await r.json()).detail ?? detail; } catch { /* not json */ }
    throw new Error(detail);
  }
  return r.json();
}

export const api = {
  get: <T = any>(path: string): Promise<T> => fetch(path).then(check),
  post: <T = any>(path: string, body?: unknown): Promise<T> =>
    fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body ?? {}) }).then(check),
};

const cache = new Map<string, Promise<any>>();
/** Cached GET for immutable resources (manifests, artifact data, entity records). */
export function cachedGet<T = any>(path: string): Promise<T> {
  if (!cache.has(path)) cache.set(path, api.get(path).catch((e) => { cache.delete(path); throw e; }));
  return cache.get(path)!;
}
