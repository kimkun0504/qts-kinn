import { memo, useEffect, useMemo, useState } from "react";
import { api, type ClosesData } from "../lib/api";
import { day, pct } from "../lib/format";
import { LineChart, type Series } from "./charts/LineChart";
import { StockSearch } from "./StockSearch";
import { Card, Note } from "./ui/Card";

type Closes = ClosesData["series"][number];

interface Compared {
  symbol: string;
  slot: number;
}

const KEY = "kinn-compare-with";
const BENCHMARKS = ["SPY", "QQQ", "IWM"];
const SLOTS: { color: string; dash?: string }[] = [{ color: "var(--series-4)" }, { color: "var(--series-3)" }, { color: "var(--series-2)", dash: "6 4" }];
const cache = new Map<string, Closes | null>();

export async function closesOf(symbol: string): Promise<Closes | null> {
  if (!cache.has(symbol)) {
    try {
      const data = await api.closes([symbol]);
      cache.set(symbol, data.series.find((x) => x.symbol === symbol) ?? null);
    } catch {
      return null;
    }
  }
  return cache.get(symbol) ?? null;
}

function saved(): Compared[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(KEY) ?? "null");
    if (Array.isArray(parsed)) return parsed.filter((c) => typeof c?.symbol === "string" && typeof c?.slot === "number").slice(0, SLOTS.length);
  } catch {
    return [{ symbol: "SPY", slot: 0 }];
  }
  return [{ symbol: "SPY", slot: 0 }];
}

function save(list: Compared[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    return;
  }
}

export function aligned(dates: string[], other: Closes): (number | null)[] {
  const out: (number | null)[] = [];
  let j = 0;
  let last: number | null = null;
  for (const d of dates) {
    while (j < other.date.length && other.date[j] <= d) {
      if (other.close[j] != null) last = other.close[j];
      j += 1;
    }
    out.push(j > 0 ? last : null);
  }
  return out;
}

export function rebase(lines: (number | null)[][]): { start: number; values: number[][] } | null {
  const n = lines[0]?.length ?? 0;
  let start = 0;
  while (start < n && lines.some((l) => l[start] == null || (l[start] as number) <= 0)) start += 1;
  if (n - start < 2) return null;
  return {
    start,
    values: lines.map((l) => {
      let carry = l[start] as number;
      return l.slice(start).map((v) => {
        if (v != null) carry = v;
        return carry / (l[start] as number) - 1;
      });
    }),
  };
}

function ticks(dates: string[]): { at: (i: number) => boolean; text: (i: number) => string } {
  const first = new Date(dates[0]).getTime();
  const last = new Date(dates[dates.length - 1]).getTime();
  const years = (last - first) / (365.25 * 864e5);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  if (years > 3) {
    const every = Math.ceil(years / 10);
    return { at: (i) => i > 0 && dates[i].slice(0, 4) !== dates[i - 1].slice(0, 4) && Number(dates[i].slice(0, 4)) % every === 0, text: (i) => dates[i].slice(0, 4) };
  }
  const every = Math.max(1, Math.ceil((years * 12) / 8));
  return {
    at: (i) => i > 0 && dates[i].slice(5, 7) !== dates[i - 1].slice(5, 7) && (Number(dates[i].slice(5, 7)) - 1) % every === 0,
    text: (i) => {
      const month = Number(dates[i].slice(5, 7));
      return month === 1 ? dates[i].slice(0, 4) : months[month - 1];
    },
  };
}

export const RelativeChart = memo(function RelativeChart({ symbol, dates, close }: { symbol: string; dates: string[]; close: (number | null)[] }) {
  const [compared, setCompared] = useState<Compared[]>(saved);
  const [loaded, setLoaded] = useState(0);
  const symbols = compared.map((c) => c.symbol).filter((s) => s !== symbol);
  const wanted = symbols.filter((s) => !cache.has(s)).join(",");
  useEffect(() => {
    if (!wanted) return;
    const asked = wanted.split(",");
    api
      .closes(asked)
      .then((data) => {
        for (const s of asked) cache.set(s, data.series.find((x) => x.symbol === s) ?? null);
        setLoaded((n) => n + 1);
      })
      .catch(() => {
        for (const s of asked) cache.set(s, null);
        setLoaded((n) => n + 1);
      });
  }, [wanted]);
  const update = (next: Compared[]) => {
    setCompared(next);
    save(next);
  };
  const toggle = (s: string) => {
    if (compared.some((c) => c.symbol === s)) return update(compared.filter((c) => c.symbol !== s));
    const free = SLOTS.findIndex((_, i) => !compared.some((c) => c.slot === i));
    if (free >= 0) update([...compared, { symbol: s, slot: free }]);
  };
  const ready = compared.filter((c) => c.symbol !== symbol && cache.get(c.symbol));
  const missing = compared.filter((c) => cache.has(c.symbol) && cache.get(c.symbol) === null).map((c) => c.symbol);
  const chart = useMemo(() => {
    const lines = [close, ...ready.map((c) => aligned(dates, cache.get(c.symbol) as Closes))];
    const based = rebase(lines);
    if (!based) return null;
    const series: Series[] = [
      { name: symbol, values: based.values[0], color: "var(--series-1)" },
      ...ready.map((c, i) => ({ name: c.symbol, values: based.values[i + 1], color: SLOTS[c.slot].color, dash: SLOTS[c.slot].dash })),
    ];
    return { series, dates: dates.slice(based.start) };
  }, [close, dates, ready.map((c) => `${c.symbol}:${c.slot}`).join(","), symbol, loaded]);
  const full = compared.length >= SLOTS.length;
  const pill = (pressed: boolean) =>
    `min-h-7 cursor-pointer rounded-md border px-2.5 text-[13px] font-medium focus-visible:outline-2 focus-visible:outline-accent ${pressed ? "border-ink-3 bg-raised text-ink" : "border-line text-ink-2 hover:text-ink"}`;
  const t = chart ? ticks(chart.dates) : null;
  return (
    <Card title={chart ? `Change since ${day(chart.dates[0])}` : "Change over the period"}>
      <div className="flex flex-wrap items-center gap-2">
        {BENCHMARKS.filter((b) => b !== symbol).map((b) => {
          const on = compared.some((c) => c.symbol === b);
          return (
            <button key={b} type="button" aria-pressed={on} disabled={!on && full} onClick={() => toggle(b)} className={`${pill(on)} disabled:cursor-default disabled:opacity-50`}>
              {b}
            </button>
          );
        })}
        {compared
          .filter((c) => !BENCHMARKS.includes(c.symbol))
          .map((c) => (
            <button key={c.symbol} type="button" aria-pressed onClick={() => toggle(c.symbol)} className={pill(true)} aria-label={`Stop comparing with ${c.symbol}`}>
              {c.symbol} ×
            </button>
          ))}
        <div className="w-56">{!full && <StockSearch label="Compare with a stock" placeholder="Compare with a stock" onPick={(hit) => hit.ticker && toggle(hit.ticker)} />}</div>
      </div>
      {chart && t ? (
        <LineChart
          title={`${symbol} against ${ready.map((c) => c.symbol).join(", ") || "nothing"}`}
          labels={chart.dates.map((d) => day(d))}
          series={chart.series}
          format={(v) => pct(v, 1)}
          labelAt={t.at}
          tickText={t.text}
          height={300}
          width={1100}
        />
      ) : (
        <Note>Not enough prices in this range to compare.</Note>
      )}
      <Note>
        Price change from the first day every line has a price; follows the zoom of the chart above. Funds are as traded, without dividends.
        {missing.length > 0 && ` No prices for ${missing.join(", ")}.`}
      </Note>
    </Card>
  );
});
