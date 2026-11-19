import type { ScreenData } from "./api";

export type ScreenKey =
  "close" | "market_cap" | "adv20" | "ret_1d" | "ret_1m" | "ret_3m" | "ret_6m" | "ret_1y" | "from_high" | "vol_60" | "pe" | "ps" | "pb" | "fcf_yield" | "revenue" | "revenue_growth" | "net_income";

export type FieldKind = "money" | "percent" | "ratio" | "price";

export interface ScreenField {
  key: ScreenKey;
  label: string;
  kind: FieldKind;
}

export const FIELDS: ScreenField[] = [
  { key: "market_cap", label: "Market value", kind: "money" },
  { key: "adv20", label: "Dollar volume, 20 days", kind: "money" },
  { key: "close", label: "Price", kind: "price" },
  { key: "ret_1d", label: "Return, 1 day", kind: "percent" },
  { key: "ret_1m", label: "Return, 1 month", kind: "percent" },
  { key: "ret_3m", label: "Return, 3 months", kind: "percent" },
  { key: "ret_6m", label: "Return, 6 months", kind: "percent" },
  { key: "ret_1y", label: "Return, 1 year", kind: "percent" },
  { key: "from_high", label: "From 52-week high", kind: "percent" },
  { key: "vol_60", label: "Volatility, 60 days", kind: "percent" },
  { key: "pe", label: "Price to earnings", kind: "ratio" },
  { key: "ps", label: "Price to sales", kind: "ratio" },
  { key: "pb", label: "Price to book", kind: "ratio" },
  { key: "fcf_yield", label: "Free cash flow yield", kind: "percent" },
  { key: "revenue", label: "Revenue, trailing year", kind: "money" },
  { key: "revenue_growth", label: "Revenue growth, 1 year", kind: "percent" },
  { key: "net_income", label: "Net income, trailing year", kind: "money" },
];

export const FIELD = Object.fromEntries(FIELDS.map((f) => [f.key, f])) as Record<ScreenKey, ScreenField>;

export const KINDS: { value: string; label: string; categories: string[] }[] = [
  { value: "us", label: "US common stock", categories: ["Domestic Common Stock", "Domestic Common Stock Primary Class", "Domestic Common Stock Secondary Class"] },
  { value: "adr", label: "ADRs", categories: ["ADR Common Stock", "ADR Common Stock Primary Class", "ADR Common Stock Secondary Class"] },
  { value: "canada", label: "Canadian common stock", categories: ["Canadian Common Stock"] },
  { value: "preferred", label: "Preferred stock", categories: ["Domestic Preferred Stock"] },
  { value: "all", label: "Every kind", categories: [] },
];

export interface Condition {
  field: ScreenKey;
  min: string;
  max: string;
}

export interface Screen {
  text: string;
  kind: string;
  sector: string;
  industry: string;
  exchange: string;
  conditions: Condition[];
}

export const EMPTY: Screen = { text: "", kind: "us", sector: "", industry: "", exchange: "", conditions: [] };

export interface ScreenRow {
  symbol: string;
  permaticker: number;
  name: string | null;
  sector: string | null;
  industry: string | null;
  category: string | null;
  exchange: string | null;
  close: number | null;
  market_cap: number | null;
  adv20: number | null;
  ret_1d: number | null;
  ret_1m: number | null;
  ret_3m: number | null;
  ret_6m: number | null;
  ret_1y: number | null;
  from_high: number | null;
  vol_60: number | null;
  pe: number | null;
  ps: number | null;
  pb: number | null;
  fcf_yield: number | null;
  revenue: number | null;
  revenue_growth: number | null;
  net_income: number | null;
  filed: string | null;
}

export function rowsOf(data: ScreenData): ScreenRow[] {
  return data.rows.map((values) => Object.fromEntries(data.columns.map((name, i) => [name, values[i]])) as unknown as ScreenRow);
}

const SCALE: Record<string, number> = { k: 1e3, m: 1e6, b: 1e9, t: 1e12 };

export function parseValue(text: string, kind: FieldKind): number | null | undefined {
  const clean = text
    .trim()
    .replace(/[$,%\s]/g, "")
    .replace(/^−/, "-")
    .toLowerCase();
  if (!clean) return null;
  const match = /^(-?\d*\.?\d+)([kmbt])?$/.exec(clean);
  if (!match || (match[2] && kind !== "money")) return undefined;
  const value = Number(match[1]) * (match[2] ? SCALE[match[2]] : 1);
  return kind === "percent" ? value / 100 : value;
}

export function bounds(condition: Condition): { min: number | null; max: number | null; valid: boolean } {
  const kind = FIELD[condition.field].kind;
  const min = parseValue(condition.min, kind);
  const max = parseValue(condition.max, kind);
  return { min: min ?? null, max: max ?? null, valid: min !== undefined && max !== undefined };
}

export function matcher(screen: Screen): (row: ScreenRow) => boolean {
  const words = screen.text.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const kinds = new Set(KINDS.find((k) => k.value === screen.kind)?.categories ?? []);
  const tests = screen.conditions.map((c) => ({ field: c.field, ...bounds(c) })).filter((c) => c.valid && (c.min != null || c.max != null));
  return (row) => {
    if (kinds.size && !kinds.has(row.category ?? "")) return false;
    if (screen.sector && row.sector !== screen.sector) return false;
    if (screen.industry && row.industry !== screen.industry) return false;
    if (screen.exchange && row.exchange !== screen.exchange) return false;
    if (words.length) {
      const text = `${row.symbol} ${row.name ?? ""}`.toLowerCase();
      if (!words.every((w) => text.includes(w))) return false;
    }
    for (const t of tests) {
      const value = row[t.field];
      if (value == null) return false;
      if (t.min != null && value < t.min) return false;
      if (t.max != null && value > t.max) return false;
    }
    return true;
  };
}

export function encode(screen: Screen): string {
  const params = new URLSearchParams();
  if (screen.text) params.set("q", screen.text);
  if (screen.kind !== EMPTY.kind) params.set("kind", screen.kind);
  if (screen.sector) params.set("sector", screen.sector);
  if (screen.industry) params.set("industry", screen.industry);
  if (screen.exchange) params.set("exchange", screen.exchange);
  for (const c of screen.conditions) params.append("f", `${c.field}:${c.min}:${c.max}`);
  return params.toString();
}

export function decode(text: string | undefined): Screen {
  if (!text) return EMPTY;
  const params = new URLSearchParams(text);
  const kind = params.get("kind") ?? EMPTY.kind;
  return {
    text: params.get("q") ?? "",
    kind: KINDS.some((k) => k.value === kind) ? kind : EMPTY.kind,
    sector: params.get("sector") ?? "",
    industry: params.get("industry") ?? "",
    exchange: params.get("exchange") ?? "",
    conditions: params
      .getAll("f")
      .map((part) => part.split(":"))
      .filter(([field]) => field in FIELD)
      .map(([field, min = "", max = ""]) => ({ field: field as ScreenKey, min, max })),
  };
}

export const STARTS: { name: string; screen: Screen }[] = [
  { name: "Large caps", screen: { ...EMPTY, conditions: [{ field: "market_cap", min: "10B", max: "" }] } },
  {
    name: "Small caps",
    screen: {
      ...EMPTY,
      conditions: [
        { field: "market_cap", min: "300M", max: "2B" },
        { field: "adv20", min: "1M", max: "" },
      ],
    },
  },
  {
    name: "Near the 52-week high",
    screen: {
      ...EMPTY,
      conditions: [
        { field: "from_high", min: "-3", max: "" },
        { field: "market_cap", min: "1B", max: "" },
      ],
    },
  },
  {
    name: "Down a third in a year",
    screen: {
      ...EMPTY,
      conditions: [
        { field: "ret_1y", min: "", max: "-33" },
        { field: "market_cap", min: "300M", max: "" },
      ],
    },
  },
  {
    name: "Cheap on earnings",
    screen: {
      ...EMPTY,
      conditions: [
        { field: "pe", min: "0", max: "12" },
        { field: "market_cap", min: "1B", max: "" },
      ],
    },
  },
  {
    name: "Fast growers",
    screen: {
      ...EMPTY,
      conditions: [
        { field: "revenue_growth", min: "30", max: "" },
        { field: "market_cap", min: "1B", max: "" },
      ],
    },
  },
];

export function median(values: (number | null)[]): number | null {
  const sorted = values.filter((v): v is number => v != null).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
