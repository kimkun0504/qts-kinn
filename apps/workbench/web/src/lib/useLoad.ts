import { useEffect, useState } from "react";

/** Load something once per key. `data` is null while loading and after an error. */
export function useLoad<T>(load: () => Promise<T>, key: string): { data: T | null; error: boolean } {
  const [state, setState] = useState<{ key: string; data: T | null; error: boolean }>({ key, data: null, error: false });
  useEffect(() => {
    let live = true;
    load()
      .then((data) => live && setState({ key, data, error: false }))
      .catch(() => live && setState({ key, data: null, error: true }));
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  return state.key === key ? { data: state.data, error: state.error } : { data: null, error: false };
}
