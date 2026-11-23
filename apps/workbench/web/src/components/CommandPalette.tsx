import { useEffect, useMemo, useRef, useState } from "react";
import { recentStocks, useStockSearch, years } from "./StockSearch";

export interface Command {
  id: string;
  group: string;
  label: string;
  hint?: string;
  keywords?: string;
  href?: string;
  run?: () => void;
}

const GROUP_LIMIT: Record<string, number> = { Pages: 14, Watchlist: 6, Screens: 6, Strategies: 6, Studies: 5, "Paper ledgers": 4, "Lab algorithms": 6, Runs: 6, Stocks: 8, Actions: 4 };
const EMPTY_LIMIT: Record<string, number> = { Pages: 20, Watchlist: 6, Actions: 20 };
const ORDER = ["Pages", "Stocks", "Watchlist", "Screens", "Strategies", "Studies", "Lab algorithms", "Paper ledgers", "Runs", "Actions"];

export function score(text: string, query: string): number | null {
  const t = text.toLowerCase();
  const q = query.toLowerCase();
  if (!q) return 0;
  if (t.startsWith(q)) return 0;
  if (t.includes(` ${q}`) || t.includes(`_${q}`) || t.includes(`/${q}`)) return 1;
  if (t.includes(q)) return 2;
  let k = 0;
  for (const ch of t) if (ch === q[k]) k += 1;
  return k === q.length ? 3 : null;
}

export function rank(commands: Command[], query: string): Command[] {
  const q = query.trim();
  const scored = commands
    .map((c) => ({ c, s: score(`${c.label} ${c.keywords ?? ""}`, q) }))
    .filter((x): x is { c: Command; s: number } => x.s !== null)
    .sort((a, b) => a.s - b.s);
  const out: Command[] = [];
  for (const group of ORDER) {
    const inGroup = scored.filter((x) => x.c.group === group).slice(0, q ? (GROUP_LIMIT[group] ?? 6) : (EMPTY_LIMIT[group] ?? 0));
    out.push(...inGroup.map((x) => x.c));
  }
  return out;
}

export function CommandPalette({ open, onClose, commands }: { open: boolean; onClose: () => void; commands: Command[] }) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const hits = useStockSearch(open ? query : "");
  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      window.setTimeout(() => input.current?.focus(), 0);
    }
  }, [open]);
  const items = useMemo(() => {
    const stocks: Command[] = query.trim()
      ? hits.map((h) => ({ id: `stock-${h.permaticker}`, group: "Stocks", label: h.ticker ?? "", hint: `${h.name ?? ""}${h.matched ? ` (as ${h.matched})` : ""}  ${years(h)}`, href: `#/stock/${encodeURIComponent(h.ticker ?? "")}/${h.permaticker}` }))
      : recentStocks().map((r) => ({ id: `recent-${r.permaticker}`, group: "Stocks", label: r.ticker, hint: r.name ?? "", href: `#/stock/${encodeURIComponent(r.ticker)}/${r.permaticker}` }));
    const ranked = rank(commands, query);
    const stockItems = stocks.slice(0, GROUP_LIMIT.Stocks);
    const pages = ranked.filter((c) => c.group === "Pages");
    const rest = ranked.filter((c) => c.group !== "Pages");
    return query.trim() ? [...pages, ...stockItems, ...rest] : [...pages, ...stockItems.slice(0, 5), ...rest];
  }, [commands, query, hits]);
  useEffect(() => setActive((a) => Math.min(a, Math.max(0, items.length - 1))), [items.length]);
  useEffect(() => {
    const row = list.current?.querySelector<HTMLElement>(`[data-index="${active}"]`);
    if (row && typeof row.scrollIntoView === "function") row.scrollIntoView({ block: "nearest" });
  }, [active]);
  if (!open) return null;
  const choose = (c: Command | undefined) => {
    if (!c) return;
    onClose();
    if (c.run) c.run();
    else if (c.href) window.location.hash = c.href.replace(/^#/, "");
  };
  let lastGroup = "";
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-[color-mix(in_srgb,var(--ink)_28%,transparent)] px-4 pt-[12vh]" onMouseDown={onClose}>
      <div role="dialog" aria-modal="true" aria-label="Search the Workbench" className="flex max-h-[70vh] w-full max-w-[640px] flex-col overflow-hidden rounded-xl border border-line bg-surface shadow-[0_24px_64px_rgba(15,23,42,0.24)]" onMouseDown={(event) => event.stopPropagation()}>
        <div className="flex items-center gap-3 border-b border-line px-4">
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" className="shrink-0 text-ink-3">
            <circle cx="7" cy="7" r="4.5" />
            <path d="M10.5 10.5L14 14" strokeLinecap="round" />
          </svg>
          <input
            ref={input}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(0);
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActive((a) => Math.min(a + 1, items.length - 1));
              } else if (event.key === "ArrowUp") {
                event.preventDefault();
                setActive((a) => Math.max(a - 1, 0));
              } else if (event.key === "Enter") {
                event.preventDefault();
                choose(items[active]);
              } else if (event.key === "Escape") {
                onClose();
              }
            }}
            placeholder="Pages, strategies, runs, algorithms, stocks"
            aria-label="Search"
            aria-controls="palette-results"
            className="h-12 min-w-0 flex-1 bg-transparent text-[15px] text-ink placeholder:text-ink-3 focus:outline-none"
          />
          <kbd className="rounded border border-line px-1.5 py-0.5 font-sans text-[11px] text-ink-3">Esc</kbd>
        </div>
        <ul ref={list} id="palette-results" role="listbox" className="m-0 flex-1 list-none overflow-y-auto p-1.5">
          {items.length === 0 && <li className="px-3 py-6 text-center text-sm text-ink-2">Nothing matches “{query}”.</li>}
          {items.map((c, i) => {
            const header = c.group !== lastGroup ? c.group : null;
            lastGroup = c.group;
            return (
              <li key={c.id} role="presentation">
                {header && <div className="px-3 pt-2.5 pb-1 text-[12px] font-medium text-ink-3">{header === "Stocks" && !query.trim() ? "Recent stocks" : header}</div>}
                <button
                  type="button"
                  role="option"
                  aria-selected={i === active}
                  data-index={i}
                  onMouseMove={() => setActive(i)}
                  onClick={() => choose(c)}
                  className={`flex w-full cursor-pointer items-baseline gap-3 rounded-md px-3 py-2 text-left ${i === active ? "bg-raised" : ""}`}
                >
                  <span className="shrink-0 text-sm font-medium text-ink">{c.label}</span>
                  {c.hint && <span className="min-w-0 flex-1 truncate text-[13px] text-ink-3">{c.hint}</span>}
                </button>
              </li>
            );
          })}
        </ul>
        <div className="flex gap-4 border-t border-line px-4 py-2 text-[12px] text-ink-3">
          <span>
            <kbd className="font-sans">↑</kbd> <kbd className="font-sans">↓</kbd> to move
          </span>
          <span>
            <kbd className="font-sans">Enter</kbd> to open
          </span>
          <span>
            <kbd className="font-sans">/</kbd> or <kbd className="font-sans">⌘K</kbd> opens this anywhere
          </span>
        </div>
      </div>
    </div>
  );
}
