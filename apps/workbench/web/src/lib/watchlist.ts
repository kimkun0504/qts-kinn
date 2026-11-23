export interface Watched {
  ticker: string;
  name: string | null;
  permaticker: number;
}

const KEY = "kinn-watchlist";
const EVENT = "kinn-watchlist";

export function watchlist(): Watched[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((w) => typeof w?.ticker === "string" && typeof w?.permaticker === "number") : [];
  } catch {
    return [];
  }
}

function store(list: Watched[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    return;
  }
  window.dispatchEvent(new Event(EVENT));
}

export function isWatched(permaticker: number): boolean {
  return watchlist().some((w) => w.permaticker === permaticker);
}

export function toggleWatch(entry: Watched): boolean {
  const list = watchlist();
  const watched = list.some((w) => w.permaticker === entry.permaticker);
  store(watched ? list.filter((w) => w.permaticker !== entry.permaticker) : [...list, entry]);
  return !watched;
}

export function onWatchlist(listener: () => void): () => void {
  window.addEventListener(EVENT, listener);
  window.addEventListener("storage", listener);
  return () => {
    window.removeEventListener(EVENT, listener);
    window.removeEventListener("storage", listener);
  };
}
