import { useState } from "react";
import { dollars, money } from "../../lib/format";
import { MONTHS, type Timeline } from "../../lib/series";

interface ProfitChartProps {
  timeline: Timeline;
  /** The period to shade and name in bold (the out-of-sample one). */
  highlight?: string;
  height?: number;
  /** A small chart for the home page: no axis, no hover, no drawdown. */
  compact?: boolean;
}

function scale(low: number, high: number): number[] {
  const span = high - low || 1;
  const rough = span / 4;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * power).find((s) => s >= rough) ?? rough;
  const ticks = [];
  for (let v = Math.ceil(low / step) * step; v <= high + 1e-9; v += step) ticks.push(v);
  return ticks;
}

const short = (v: number) => (v === 0 ? "$0" : `${v < 0 ? "−" : ""}$${Math.abs(v) >= 1000 ? `${Math.abs(v) / 1000}k` : Math.abs(v)}`);

/** Cumulative profit by month across a strategy's periods, with the drawdown underneath.
 *  Months no run covers are drawn flat and dashed. Hover for the month's figures. */
export function ProfitChart({ timeline, highlight = "holdout", height = 300, compact = false }: ProfitChartProps) {
  const [hover, setHover] = useState<number | null>(null);
  const { months, starts, gaps } = timeline;
  const n = months.length;
  if (n < 2) return <p className="m-0 py-6 text-ink-2">No run covers this strategy's periods yet.</p>;
  const totals = months.map((m) => m.total);
  const low = Math.min(0, ...totals);
  const top = Math.max(...totals) * 1.06 || 1;
  const x = (i: number) => (i / (n - 1)) * 100;
  const y = (v: number) => (1 - (v - low) / (top - low)) * 100;
  // Solid where a run covers the month; dashed across the stretches none does.
  const solid: string[] = [];
  let open = false;
  months.forEach((m, i) => {
    if (m.value == null) {
      open = false;
      return;
    }
    solid.push(`${open ? "L" : "M"}${(x(i) * 10).toFixed(1)} ${(y(m.total) * 3).toFixed(1)}`);
    open = true;
  });
  const dashed = gaps
    .filter(([a, b]) => a > 0 && b < n - 1)
    .map(([a, b]) => `M${(x(a - 1) * 10).toFixed(1)} ${(y(months[a - 1].total) * 3).toFixed(1)}L${(x(b + 1) * 10).toFixed(1)} ${(y(months[b + 1].total) * 3).toFixed(1)}`)
    .join("");
  const area = `${months.map((m, i) => `${i ? "L" : "M"}${(x(i) * 10).toFixed(1)} ${(y(m.total) * 3).toFixed(1)}`).join("")}L1000 300L0 300Z`;
  const lit = starts.find((s) => s.key === highlight);
  const ticks = scale(low, top);
  const deepest = timeline.deepest || -1;
  const under = `M0 0${months.map((m, i) => `L${(x(i) * 10).toFixed(1)} ${((m.under / deepest) * 92).toFixed(1)}`).join("")}L1000 0Z`;
  const years: { label: string; left: number }[] = [];
  const firstYear = months[0].year;
  const lastYear = months[n - 1].year;
  const every = Math.max(1, Math.ceil((lastYear - firstYear + 1) / 8));
  months.forEach((m, i) => {
    if (m.month === 0 && (m.year - firstYear) % every === 0) years.push({ label: String(m.year), left: x(i) });
  });
  const at = hover == null ? null : months[hover];
  const move = (event: React.MouseEvent<HTMLDivElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const share = Math.min(1, Math.max(0, (event.clientX - box.left) / box.width));
    setHover(Math.round(share * (n - 1)));
  };
  const last = months[n - 1];
  return (
    <div className="flex flex-col gap-2">
      <div
        role="img"
        aria-label={`Cumulative profit by month from ${months[0].year} to ${last.year}, ending at ${dollars(last.total)}`}
        className={`relative ${compact ? "" : "mt-5"}`}
        style={{ height }}
        onMouseMove={compact ? undefined : move}
        onMouseLeave={compact ? undefined : () => setHover(null)}
      >
        {lit && <div className="absolute inset-y-0 right-0 bg-raised" style={{ left: `${x(lit.index)}%` }} />}
        {!compact &&
          ticks.map((tick) => (
            <div key={tick} className="absolute inset-x-0 border-t border-line" style={{ top: `${y(tick)}%` }}>
              <span className="absolute left-0 -translate-y-full text-[12.5px] text-ink-3">{short(tick)}</span>
            </div>
          ))}
        {starts.map((start, i) => (
          <div key={start.key} className="absolute inset-y-0" style={{ left: `${x(start.index)}%` }}>
            {(i > 0 || start.key === highlight) && <div className="absolute inset-y-0 border-l border-dashed border-ink-3" />}
            <span className={`absolute whitespace-nowrap text-[13px] ${compact ? "top-1.5" : "-top-5"} ${i > 0 ? "pl-1.5" : ""} ${start.key === highlight ? "font-semibold text-ink" : "text-ink-2"}`}>
              {compact && start.key !== highlight ? "" : start.label}
            </span>
          </div>
        ))}
        <svg aria-hidden="true" viewBox="0 0 1000 300" preserveAspectRatio="none" className="absolute inset-0 size-full">
          {compact && <path d={area} fill="var(--series-1)" opacity="0.1" />}
          <path d={solid.join("")} fill="none" stroke="var(--series-1)" strokeWidth="2" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
          {dashed && <path d={dashed} fill="none" stroke="var(--ink-3)" strokeWidth="1.5" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />}
        </svg>
        <span className="absolute right-1.5 -translate-y-[130%] text-sm font-semibold" style={{ top: `${y(last.total)}%` }}>
          {dollars(last.total)}
        </span>
        {at && hover != null && (
          <>
            <div className="absolute inset-y-0 border-l border-ink-2" style={{ left: `${x(hover)}%` }} />
            <div className="absolute size-[9px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-series-1 ring-2 ring-surface" style={{ left: `${x(hover)}%`, top: `${y(at.total)}%` }} />
            <div
              className="pointer-events-none absolute top-2 rounded-lg border border-line bg-surface px-3 py-2 text-[13.5px] whitespace-nowrap shadow-lg"
              style={{ left: `${x(hover)}%`, transform: x(hover) > 62 ? "translateX(calc(-100% - 12px))" : "translateX(12px)" }}
            >
              <div className="font-semibold">
                {MONTHS[at.month]} {at.year}
              </div>
              <div className="text-ink-2">
                Month <span className="font-semibold text-ink">{at.value == null ? "not run" : money(at.value)}</span>
              </div>
              <div className="text-ink-2">
                Total <span className="font-semibold text-ink">{dollars(at.total)}</span>
              </div>
            </div>
          </>
        )}
      </div>
      <div className="relative h-[18px] text-[12.5px] text-ink-3">
        {years.map((year) => (
          <span key={year.label} className="absolute -translate-x-1/2" style={{ left: `${Math.min(Math.max(year.left, 2), 97)}%` }}>
            {year.label}
          </span>
        ))}
      </div>
      {!compact && (
        <>
          <div className="mt-1 flex items-baseline justify-between gap-2">
            <h3 className="m-0 text-[13px] font-semibold text-ink-2">Under its high, by month end</h3>
            <span className="text-[13px] text-ink-3">Deepest {dollars(timeline.deepest)}</span>
          </div>
          <div role="img" aria-label={`Drawdown by month end; the deepest is ${dollars(timeline.deepest)}`} className="relative h-[84px] border-t border-line">
            {lit && <div className="absolute inset-y-0 right-0 bg-raised" style={{ left: `${x(lit.index)}%` }} />}
            <svg aria-hidden="true" viewBox="0 0 1000 100" preserveAspectRatio="none" className="absolute inset-0 size-full">
              <path d={under} fill="var(--loss)" opacity="0.55" />
            </svg>
          </div>
        </>
      )}
    </div>
  );
}
