import { money } from "../../lib/format";
import { MONTHS, type Month } from "../../lib/series";

const CAP = 4000;

function fill(value: number | null): string | undefined {
  if (value == null) return undefined;
  if (value === 0) return "var(--raised)";
  const step = 20 + Math.round(Math.min(Math.abs(value) / CAP, 1) * 4) * 17.5;
  return `color-mix(in srgb, var(${value > 0 ? "--gain" : "--loss"}) ${step}%, var(--surface))`;
}

/** Profit by month, a row a year: one hue for gains, one for losses, grey at zero. */
export function MonthGrid({ months, highlight = "holdout" }: { months: Month[]; highlight?: string }) {
  const years = [...new Set(months.map((m) => m.year))];
  const cell = new Map(months.map((m) => [`${m.year}-${m.month}`, m]));
  const columns = { gridTemplateColumns: "40px repeat(12, minmax(0, 1fr))" };
  return (
    <div>
      <div className="grid gap-0.5 text-xs text-ink-3" style={columns}>
        <span />
        {MONTHS.map((name) => (
          <span key={name} className="text-center">
            {name.charAt(0)}
          </span>
        ))}
      </div>
      <div role="img" aria-label={`Profit by month for each year from ${years[0]} to ${years[years.length - 1]}`} className="mt-1 flex flex-col gap-0.5">
        {years.map((year) => {
          const lit = months.some((m) => m.year === year && m.period === highlight);
          return (
            <div key={year} className="grid gap-0.5" style={columns}>
              <span className={`text-[12.5px] leading-[17px] ${lit ? "font-semibold text-ink" : "text-ink-3"}`}>{year}</span>
              {MONTHS.map((name, month) => {
                const m = cell.get(`${year}-${month}`);
                const value = m?.value ?? null;
                return (
                  <div
                    key={name}
                    title={`${name} ${year}: ${value == null ? "not run" : money(value)}`}
                    className={`h-[17px] rounded-sm ${value == null ? "border border-dashed border-line" : ""}`}
                    style={{ background: fill(value) }}
                  />
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function MonthLegend() {
  const swatch = (colour: string) => <span className="h-3 w-4 rounded-sm" style={{ background: colour }} />;
  const mix = (name: string, share: number) => `color-mix(in srgb, var(${name}) ${share}%, var(--surface))`;
  return (
    <span className="inline-flex items-center gap-1.5">
      −${CAP.toLocaleString("en-US")}
      <span aria-hidden="true" className="inline-flex gap-0.5">
        {swatch(mix("--loss", 90))}
        {swatch(mix("--loss", 45))}
        {swatch("var(--raised)")}
        {swatch(mix("--gain", 45))}
        {swatch(mix("--gain", 90))}
      </span>
      +${CAP.toLocaleString("en-US")}
    </span>
  );
}
