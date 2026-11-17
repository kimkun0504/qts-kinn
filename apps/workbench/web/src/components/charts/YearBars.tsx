import { money } from "../../lib/format";
import type { Year } from "../../lib/series";

/** Profit by calendar year as bars from a zero line. Years of the highlighted period are
 *  shaded and labelled; the rest give their figure on hover. */
export function YearBars({ years, highlight = "holdout" }: { years: Year[]; highlight?: string }) {
  const shown = years.filter((y) => y.months > 0);
  if (!shown.length) return null;
  const high = Math.max(0, ...shown.map((y) => y.total));
  const low = Math.min(0, ...shown.map((y) => y.total));
  const range = (high - low) * 1.2 || 1;
  const zero = (-low / range) * 100 + 4;
  const lit = (y: Year) => y.periods.includes(highlight);
  return (
    <div>
      <div className="mt-3 flex h-[190px] gap-[3px]">
        {shown.map((y) => {
          const size = (Math.abs(y.total) / range) * 100;
          const up = y.total >= 0;
          const full = y.months === 12;
          return (
            <div key={y.year} title={`${y.year}${full ? "" : ` (${y.months} months)`}: ${money(y.total)}`} className={`relative min-w-0 flex-1 ${lit(y) ? "bg-raised" : ""}`}>
              <div className="absolute inset-x-0 border-t border-ink-3" style={{ bottom: `${zero}%` }} />
              <div
                className={`absolute inset-x-[12%] ${up ? "rounded-t bg-gain" : "rounded-b bg-loss"}`}
                style={{ bottom: `${up ? zero : zero - size}%`, height: `${Math.max(size, 0.6)}%` }}
              />
              {lit(y) && full && (
                <span className="absolute -inset-x-3 text-center text-xs font-semibold" style={{ bottom: `${zero + (up ? size : 0) + 1.5}%` }}>
                  {`${y.total < 0 ? "−" : ""}$${(Math.abs(y.total) / 1000).toFixed(1)}k`}
                </span>
              )}
            </div>
          );
        })}
      </div>
      <div className="mt-1 flex gap-[3px] text-xs text-ink-3">
        {shown.map((y) => (
          <span key={y.year} className="min-w-0 flex-1 text-center">
            {String(y.year).slice(2)}
          </span>
        ))}
      </div>
    </div>
  );
}
