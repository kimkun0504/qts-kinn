const MINUS = "−";

export function pct(value: number | null | undefined, digits = 2): string {
  if (value == null) return "–";
  return (value >= 0 ? "+" : MINUS) + Math.abs(100 * value).toFixed(digits) + "%";
}

export function plainPct(value: number | null | undefined, digits = 0): string {
  return value == null ? "–" : (100 * value).toFixed(digits) + "%";
}

export function num(value: number | null | undefined, digits = 2): string {
  if (value == null) return "–";
  const text = Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  return (value < 0 ? MINUS : "") + text;
}

export function int(value: number | null | undefined): string {
  return value == null ? "–" : Math.round(value).toLocaleString("en-US");
}

export function money(value: number | null | undefined): string {
  if (value == null) return "–";
  return (value < 0 ? MINUS + "$" : "+$") + Math.abs(Math.round(value)).toLocaleString("en-US");
}

/** Dollars without a plus sign: for totals and levels, where a sign would read as a change. */
export function dollars(value: number | null | undefined): string {
  if (value == null) return "–";
  return (value < 0 ? MINUS : "") + "$" + Math.abs(Math.round(value)).toLocaleString("en-US");
}

/** "2026-11-16" as "16 Nov 2026" (or "16 Nov" when short). */
export function day(iso: string | null | undefined, short = false): string {
  if (!iso) return "–";
  const names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return `${d} ${names[m - 1]}${short ? "" : ` ${y}`}`;
}

export function isNegative(text: string): boolean {
  return text.startsWith(MINUS);
}

export function shortTime(iso: string): string {
  return iso.slice(5, 16).replace("T", " ");
}

export function interval(stat: Stat): string {
  if (stat.mean == null) return "–";
  if (stat.low == null || stat.high == null) return pct(stat.mean);
  return `${pct(stat.mean)} (${pct(stat.low)} to ${pct(stat.high)})`;
}

export interface Stat {
  n: number;
  mean: number | null;
  low: number | null;
  high: number | null;
}

export function compact(value: number | null | undefined, prefix = ""): string {
  if (value == null) return "–";
  const size = Math.abs(value);
  const [scale, unit] = size >= 1e12 ? [1e12, "T"] : size >= 1e9 ? [1e9, "B"] : size >= 1e6 ? [1e6, "M"] : size >= 1e3 ? [1e3, "K"] : [1, ""];
  const digits = size / scale >= 100 || !unit ? 0 : 1;
  return (value < 0 ? MINUS : "") + prefix + (size / scale).toFixed(digits) + unit;
}

export function price(value: number | null | undefined): string {
  if (value == null) return "–";
  return "$" + value.toFixed(Math.abs(value) < 1 ? 4 : 2);
}

export function priceTick(value: number): string {
  if (value === 0) return "$0";
  const size = Math.abs(value);
  const digits = size >= 100 ? 0 : size >= 1 ? 2 : Math.min(6, 1 - Math.floor(Math.log10(size)));
  return "$" + value.toFixed(digits);
}
