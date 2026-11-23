import { useEffect, useId, useRef, useState } from "react";
import { api, type StockHit } from "../lib/api";

const RECENT_KEY = "kinn-recent-stocks";

export interface RecentStock {
  ticker: string;
  name: string | null;
  permaticker: number;
}

export function recentStocks(): RecentStock[] {
  try {
    const saved = JSON.parse(localStorage.getItem(RECENT_KEY) ?? "[]");
    return Array.isArray(saved) ? saved.slice(0, 8) : [];
  } catch {
    return [];
  }
}

export function rememberStock(stock: RecentStock) {
  try {
    const next = [stock, ...recentStocks().filter((s) => s.permaticker !== stock.permaticker)].slice(0, 8);
    localStorage.setItem(RECENT_KEY, JSON.stringify(next));
  } catch {
    return;
  }
}

export function years(hit: { first: string | null; last: string | null; delisted: boolean }): string {
  const from = hit.first?.slice(0, 4) ?? "";
  const to = hit.delisted ? (hit.last?.slice(0, 4) ?? "") : "now";
  return from ? `${from}–${to}` : "";
}

export function useStockSearch(query: string): StockHit[] {
  const [hits, setHits] = useState<StockHit[]>([]);
  useEffect(() => {
    const text = query.trim();
    if (!text) {
      setHits([]);
      return;
    }
    let live = true;
    const timer = window.setTimeout(() => {
      api
        .stocks(text)
        .then((found) => live && setHits(found))
        .catch(() => live && setHits([]));
    }, 120);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [query]);
  return hits;
}

export function StockSearch({
  onPick,
  autoFocus = false,
  placeholder = "Ticker or company name",
  label = "Find a stock",
}: {
  onPick: (hit: StockHit) => void;
  autoFocus?: boolean;
  placeholder?: string;
  label?: string;
}) {
  const results = useId();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(false);
  const hits = useStockSearch(query);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (box.current && !box.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);
  const pick = (hit: StockHit) => {
    setQuery("");
    setOpen(false);
    onPick(hit);
  };
  return (
    <div ref={box} className="relative w-full max-w-[420px]">
      <input
        type="search"
        value={query}
        autoFocus={autoFocus}
        placeholder={placeholder}
        aria-label={label}
        role="combobox"
        aria-expanded={open && hits.length > 0}
        aria-controls={results}
        onChange={(event) => {
          setQuery(event.target.value);
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive((a) => Math.min(a + 1, hits.length - 1));
          } else if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive((a) => Math.max(a - 1, 0));
          } else if (event.key === "Enter" && hits[active]) {
            pick(hits[active]);
          } else if (event.key === "Escape") {
            setOpen(false);
          }
        }}
        className="h-9 w-full rounded-md border border-line bg-surface px-3 text-sm text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
      />
      {open && hits.length > 0 && (
        <ul
          id={results}
          role="listbox"
          className="absolute top-10 right-0 left-0 z-20 m-0 max-h-[360px] list-none overflow-y-auto rounded-md border border-line bg-surface p-1 shadow-[0_8px_24px_rgba(15,23,42,0.12)]"
        >
          {hits.map((hit, i) => (
            <li key={hit.permaticker} role="option" aria-selected={i === active}>
              <button
                type="button"
                onMouseEnter={() => setActive(i)}
                onClick={() => pick(hit)}
                className={`flex w-full cursor-pointer items-baseline gap-3 rounded px-2.5 py-1.5 text-left text-sm ${i === active ? "bg-raised" : ""}`}
              >
                <span className="w-16 shrink-0 font-semibold">{hit.ticker}</span>
                <span className="min-w-0 flex-1 truncate text-ink-2">
                  {hit.name}
                  {hit.matched ? ` (traded as ${hit.matched})` : ""}
                </span>
                <span className="shrink-0 text-[12px] text-ink-3">{years(hit)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
