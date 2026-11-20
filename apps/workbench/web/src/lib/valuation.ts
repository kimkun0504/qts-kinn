import type { FinancialPeriod } from "./api";

export type Multiple = "pe" | "ps" | "pb" | "fcf_yield";

export const MULTIPLES: { key: Multiple; label: string; long: string; dollarsOnly?: boolean }[] = [
  { key: "pe", label: "P/E", long: "Price to earnings" },
  { key: "ps", label: "P/S", long: "Price to sales" },
  { key: "pb", label: "P/B", long: "Price to book" },
  { key: "fcf_yield", label: "FCF yield", long: "Free cash flow yield", dollarsOnly: true },
];

const STALE_DAYS = 500;
const DAY = 86_400_000;

function of(multiple: Multiple, value: number, book: FinancialPeriod): number | null {
  const bottom = multiple === "pe" ? book.netinccmnusd : multiple === "ps" ? book.revenueusd : multiple === "pb" ? book.equityusd : null;
  if (multiple === "fcf_yield") return book.fcf == null || value <= 0 ? null : book.fcf / value;
  return bottom == null || bottom <= 0 ? null : value / bottom;
}

export interface Valuation {
  date: string[];
  value: (number | null)[];
  median: number | null;
  low: number | null;
  high: number | null;
  now: number | null;
  rank: number | null;
  since: string | null;
}

export function quantile(sorted: number[], q: number): number | null {
  if (!sorted.length) return null;
  const at = (sorted.length - 1) * q;
  const below = Math.floor(at);
  const above = Math.min(below + 1, sorted.length - 1);
  return sorted[below] + (sorted[above] - sorted[below]) * (at - below);
}

export function valuation(prices: { date: string[]; market_value?: (number | null)[] }, trailing: FinancialPeriod[], multiple: Multiple, until?: string | null): Valuation {
  const books = trailing.filter((b) => b.filed).sort((a, b) => (a.filed! < b.filed! ? -1 : 1));
  const date: string[] = [];
  const value: (number | null)[] = [];
  let k = -1;
  prices.date.forEach((d, i) => {
    if (until && d > until) return;
    while (k + 1 < books.length && books[k + 1].filed! < d) k += 1;
    if (k < 0) return;
    const book = books[k];
    const cap = prices.market_value?.[i];
    const fresh = Date.parse(d) - Date.parse(book.period) <= STALE_DAYS * DAY;
    date.push(d);
    value.push(cap != null && cap > 0 && fresh ? of(multiple, cap, book) : null);
  });
  const known = value.filter((v): v is number => v != null).sort((a, b) => a - b);
  const now = value.length ? value[value.length - 1] : null;
  const first = value.findIndex((v) => v != null);
  return {
    date,
    value,
    median: quantile(known, 0.5),
    low: quantile(known, 0.25),
    high: quantile(known, 0.75),
    now,
    rank: now == null || !known.length ? null : known.filter((v) => v < now).length / known.length,
    since: first >= 0 ? date[first] : null,
  };
}
