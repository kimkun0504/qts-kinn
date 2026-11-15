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
