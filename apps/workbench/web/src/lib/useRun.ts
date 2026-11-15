import { useEffect, useState } from "react";
import { api, type RunDetail } from "./api";

const cache = new Map<string, RunDetail>();

export function clearRunCache() {
  cache.clear();
}

/** Load one run's detail (cached for the session). */
export function useRun(id: string | null): { detail: RunDetail | null; error: string | null } {
  const [state, setState] = useState<{ detail: RunDetail | null; error: string | null }>({ detail: null, error: null });
  useEffect(() => {
    if (!id) return setState({ detail: null, error: null });
    const hit = cache.get(id);
    if (hit) return setState({ detail: hit, error: null });
    let live = true;
    setState({ detail: null, error: null });
    api
      .run(id)
      .then((detail) => {
        cache.set(id, detail);
        if (live) setState({ detail, error: null });
      })
      .catch(() => live && setState({ detail: null, error: "That run folder could not be read." }));
    return () => {
      live = false;
    };
  }, [id]);
  return state;
}

export function useRuns(ids: string[]): RunDetail[] | null {
  const [details, setDetails] = useState<RunDetail[] | null>(null);
  const key = ids.join(",");
  useEffect(() => {
    let live = true;
    setDetails(null);
    Promise.all(
      ids.map(async (id) => {
        const hit = cache.get(id);
        if (hit) return hit;
        const detail = await api.run(id);
        cache.set(id, detail);
        return detail;
      }),
    ).then((all) => live && setDetails(all));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return details;
}
