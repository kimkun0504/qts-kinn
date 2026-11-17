import { pct, plainPct } from "../../lib/format";

const STEP = 0.1;
const LOW = -0.4;
const HIGH = 1.0;

/** How many trades ended in each band of return, losses on the left of the zero line. The
 *  bands at either end hold everything beyond them. Hover a bar for its count. */
export function ReturnBars({ returns }: { returns: number[] }) {
  const bands = Math.round((HIGH - LOW) / STEP) + 2;
  const counts = new Array<number>(bands).fill(0);
  for (const r of returns) counts[Math.min(bands - 1, Math.max(0, Math.floor((r - LOW) / STEP + 1e-9) + 1))] += 1;
  const peak = Math.max(...counts, 1);
  const from = (k: number) => LOW + (k - 1) * STEP;
  const name = (k: number) =>
    k === 0 ? `worse than ${plainPct(LOW)}` : k === bands - 1 ? `more than ${pct(HIGH, 0)}` : `${pct(from(k), 0)} to ${pct(from(k) + STEP, 0)}`;
  const zero = Math.round(-LOW / STEP) + 1; // the first band of gains
  const labels: Record<number, string> = { 0: `< ${pct(LOW, 0)}`, [zero]: "0%", [zero + 5]: "+50%", [bands - 1]: `> ${pct(HIGH, 0)}` };
  return (
    <div>
      <div role="img" aria-label={`Trades by return: ${returns.filter((r) => r > 0).length} gains and ${returns.filter((r) => r <= 0).length} losses`} className="flex h-[170px] items-end gap-[2px]">
        {counts.map((count, k) => (
          <div key={k} title={`${name(k)}: ${count} trade${count === 1 ? "" : "s"}`} className="flex h-full min-w-0 flex-1 flex-col justify-end">
            <div className={`rounded-t ${k < zero ? "bg-loss" : "bg-gain"}`} style={{ height: `${count ? Math.max(1.5, (count / peak) * 100) : 0}%` }} />
          </div>
        ))}
      </div>
      <div className="relative mt-1 flex h-[18px] gap-[2px] border-t border-ink-3 text-xs text-ink-3">
        {counts.map((_, k) => (
          <span key={k} className="relative min-w-0 flex-1">
            {labels[k] && <span className={`absolute top-0.5 whitespace-nowrap ${k === 0 ? "left-0" : k === bands - 1 ? "right-0" : "left-0 -translate-x-1/2"}`}>{labels[k]}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

export interface Dot {
  day: string; // the day the trade was closed, ISO
  symbol: string;
  value: number; // its return
}

const FLOOR = -0.6;
const CEILING = 1.5;
const TICKS = [-0.5, 0, 0.5, 1, 1.5];

/** Every trade as a dot at the day it closed and the return it made. Returns beyond the
 *  frame are drawn on its edge. Hover a dot for the stock and the figure. */
export function TradeDots({ dots }: { dots: Dot[] }) {
  if (dots.length < 2) return null;
  const times = dots.map((d) => Date.parse(d.day));
  const first = Math.min(...times);
  const last = Math.max(...times);
  const x = (t: number) => ((t - first) / (last - first || 1)) * 100;
  const y = (v: number) => (1 - (Math.min(CEILING, Math.max(FLOOR, v)) - FLOOR) / (CEILING - FLOOR)) * 100;
  const years: number[] = [];
  const firstYear = new Date(first).getUTCFullYear();
  const lastYear = new Date(last).getUTCFullYear();
  const every = Math.max(1, Math.ceil((lastYear - firstYear + 1) / 7));
  for (let year = firstYear + 1; year <= lastYear; year += every) years.push(year);
  return (
    <div className="pl-11">
      <div role="img" aria-label={`${dots.length} trades by the day they closed and their return`} className="relative h-[170px]">
        {TICKS.map((tick) => (
          <div key={tick} className={`absolute inset-x-0 border-t ${tick === 0 ? "border-ink-3" : "border-line"}`} style={{ top: `${y(tick)}%` }}>
            <span className="absolute right-full -translate-y-1/2 pr-2 text-xs text-ink-3">{tick === 0 ? "0%" : pct(tick, 0)}</span>
          </div>
        ))}
        {dots.map((d, i) => (
          <span
            key={i}
            title={`${d.symbol}, ${d.day}: ${pct(d.value, 1)}`}
            className={`absolute size-[7px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60 ring-1 ring-surface hover:opacity-100 ${d.value > 0 ? "bg-gain" : "bg-loss"}`}
            style={{ left: `${x(times[i])}%`, top: `${y(d.value)}%` }}
          />
        ))}
      </div>
      <div className="relative h-[18px] text-xs text-ink-3">
        {years.map((year) => (
          <span key={year} className="absolute top-1 -translate-x-1/2" style={{ left: `${Math.min(97, Math.max(3, x(Date.UTC(year, 0, 1))))}%` }}>
            {year}
          </span>
        ))}
      </div>
    </div>
  );
}
