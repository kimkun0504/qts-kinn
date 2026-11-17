import type { Period } from "./api";

/** One calendar month on a strategy's timeline. `value` is null where no run covers it. */
export interface Month {
  key: string; // "2024-03"
  year: number;
  month: number; // 0 to 11
  value: number | null;
  total: number; // cumulative profit to the end of this month
  under: number; // how far the total sits under its high (zero or negative)
  period: string | null;
}

export interface Timeline {
  months: Month[];
  /** Where each period starts on the timeline, in order. */
  starts: { key: string; label: string; index: number }[];
  /** Stretches of months no run covers, as [first, last] indexes. */
  gaps: [number, number][];
  deepest: number;
}

const index = (key: string) => Number(key.slice(0, 4)) * 12 + Number(key.slice(5, 7)) - 1;

/** Join the periods' monthly profits end to end into one timeline, oldest first. Months
 *  between two periods that no run covers stay on the line with a null value. */
export function timeline(periods: Period[]): Timeline {
  const covered = periods.filter((p) => p.months.length).sort((a, b) => index(a.months[0][0]) - index(b.months[0][0]));
  if (!covered.length) return { months: [], starts: [], gaps: [], deepest: 0 };
  const first = index(covered[0].months[0][0]);
  const last = Math.max(...covered.map((p) => index(p.months[p.months.length - 1][0])));
  const values = new Map<number, { value: number; period: string }>();
  const starts: Timeline["starts"] = [];
  for (const period of covered) {
    starts.push({ key: period.key, label: period.label, index: index(period.months[0][0]) - first });
    for (const [key, value] of period.months) values.set(index(key), { value, period: period.key });
  }
  const months: Month[] = [];
  const gaps: [number, number][] = [];
  let total = 0;
  let high = 0;
  for (let i = first; i <= last; i++) {
    const hit = values.get(i);
    total += hit?.value ?? 0;
    high = Math.max(high, total);
    const at = i - first;
    if (!hit) {
      const open = gaps[gaps.length - 1];
      if (open && open[1] === at - 1) open[1] = at;
      else gaps.push([at, at]);
    }
    months.push({
      key: `${Math.floor(i / 12)}-${String((i % 12) + 1).padStart(2, "0")}`,
      year: Math.floor(i / 12),
      month: i % 12,
      value: hit ? hit.value : null,
      total,
      under: total - high,
      period: hit?.period ?? null,
    });
  }
  return { months, starts, gaps, deepest: Math.min(0, ...months.map((m) => m.under)) };
}

export interface Year {
  year: number;
  total: number;
  months: number; // months with a run
  periods: string[];
}

export function byYear(months: Month[]): Year[] {
  const years = new Map<number, Year>();
  for (const m of months) {
    const year = years.get(m.year) ?? { year: m.year, total: 0, months: 0, periods: [] };
    if (m.value != null) {
      year.total += m.value;
      year.months += 1;
      if (m.period && !year.periods.includes(m.period)) year.periods.push(m.period);
    }
    years.set(m.year, year);
  }
  return [...years.values()].sort((a, b) => a.year - b.year);
}

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
