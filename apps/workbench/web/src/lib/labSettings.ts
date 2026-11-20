import type { LabSettings, SettingsPatch, SweepRequest } from "./lab";

/** One number on the settings form: where it lives, how it is shown and how it is checked. */
export interface NumberSpec {
  path: `${"universe" | "entry" | "exit" | "book"}.${string}`;
  label: string;
  unit?: string;
  /** Shown value × scale = the setting (market cap in $M, stops in %). */
  scale: number;
  min: number;
  max?: number;
  integer?: boolean;
  /** 0 or blank on the form clears it (no stop, no cap). */
  optional?: boolean;
}

export const NUMBERS: NumberSpec[] = [
  { path: "universe.min_market_cap", label: "Min market cap", unit: "$M", scale: 1e6, min: 0 },
  { path: "universe.max_market_cap", label: "Max market cap", unit: "$M", scale: 1e6, min: 0, optional: true },
  { path: "universe.min_price", label: "Min price", unit: "$", scale: 1, min: 0 },
  { path: "universe.min_dollar_volume", label: "Min dollar volume", unit: "$K", scale: 1e3, min: 0 },
  { path: "entry.top_n", label: "Stocks a day", scale: 1, min: 1, max: 500, integer: true },
  { path: "exit.hold_days", label: "Hold", unit: "sessions", scale: 1, min: 1, max: 250, integer: true },
  { path: "exit.stop_loss", label: "Stop loss", unit: "%", scale: 0.01, min: 0.1, max: 99, optional: true },
  { path: "exit.take_profit", label: "Take profit", unit: "%", scale: 0.01, min: 0.1, max: 10000, optional: true },
  { path: "book.position_size", label: "Position size", unit: "$", scale: 1, min: 100, max: 10_000_000 },
  { path: "book.max_positions", label: "Max open positions", scale: 1, min: 0, max: 10_000, integer: true },
  { path: "book.borrow_rate", label: "Borrow fee a year", unit: "%", scale: 0.01, min: 0, max: 100 },
];

/** The form's state: what the owner typed (blank = keep the code's or the Lab's value). */
export interface Draft {
  period?: string;
  start?: string;
  end?: string;
  mode?: "signal" | "rank";
  rank_order?: "highest" | "lowest";
  side?: "long" | "short";
  exclude_blank_checks?: boolean;
  tickers?: string;
  numbers: Record<string, string>;
  sweep_field?: string;
  sweep_values?: string;
}

export const SWEEPABLE = ["exit.hold_days", "exit.stop_loss", "exit.take_profit", "book.max_positions", "entry.top_n", "book.borrow_rate"];

export function toSweep(draft: Draft): { sweep: SweepRequest | null; error: string | null } {
  if (!draft.sweep_field) return { sweep: null, error: null };
  const spec = NUMBERS.find((s) => s.path === draft.sweep_field);
  if (!spec) return { sweep: null, error: "Pick a setting to sweep." };
  const parts = (draft.sweep_values ?? "").split(/[\s,]+/).filter(Boolean);
  if (parts.length < 2 || parts.length > 12) return { sweep: null, error: `A sweep of ${spec.label.toLowerCase()} needs 2 to 12 values.` };
  const values: (number | null)[] = [];
  for (const part of parts) {
    if (spec.optional && /^(none|off|-)$/i.test(part)) {
      values.push(null);
      continue;
    }
    const shown = Number(part);
    if (!Number.isFinite(shown)) return { sweep: null, error: `"${part}" is not a number.` };
    if (shown < spec.min || (spec.max != null && shown > spec.max)) return { sweep: null, error: `${spec.label} must be from ${spec.min} to ${spec.max ?? "any"}${spec.unit ? ` ${spec.unit}` : ""}.` };
    if (spec.integer && !Number.isInteger(shown)) return { sweep: null, error: `${spec.label} takes whole numbers.` };
    values.push(Math.round(shown * spec.scale * 1e9) / 1e9);
  }
  if (new Set(values.map(String)).size !== values.length) return { sweep: null, error: "Each value of a sweep must differ." };
  return { sweep: { field: spec.path, values }, error: null };
}

export const EMPTY_DRAFT: Draft = { numbers: {} };

export function readTickers(text: string): { tickers: string[]; bad: string[] } {
  const words = text
    .toUpperCase()
    .split(/[\s,;]+/)
    .filter(Boolean);
  if (words.length === 1 && /^(ALL|EVERY)$/.test(words[0])) return { tickers: [], bad: [] };
  const valid = (w: string) => /^[A-Z][A-Z0-9.-]{0,9}$/.test(w);
  return { tickers: [...new Set(words.filter(valid))].sort(), bad: words.filter((w) => !valid(w)) };
}

type Section = "universe" | "entry" | "exit" | "book";

function deepMerge<T>(base: T, patch: unknown): T {
  if (!patch || typeof patch !== "object") return base;
  const out = { ...(base as Record<string, unknown>) };
  for (const [key, value] of Object.entries(patch as Record<string, unknown>)) {
    const current = out[key];
    out[key] = current && typeof current === "object" && value && typeof value === "object" && !Array.isArray(value) ? deepMerge(current, value) : value;
  }
  return out as T;
}

/** The Lab's defaults with the algorithm's SETTINGS over them. */
export function base(defaults: LabSettings, inCode: SettingsPatch | null): LabSettings {
  return deepMerge(defaults, inCode ?? {});
}

function get(settings: LabSettings, path: string): number | null {
  const [section, key] = path.split(".") as [Section, string];
  const value = (settings[section] as Record<string, unknown>)[key];
  return typeof value === "number" ? value : null;
}

/** The value a number field shows when the owner has not typed one. */
export function shown(settings: LabSettings, spec: NumberSpec): string {
  const value = get(settings, spec.path);
  if (value == null) return "none";
  const display = value / spec.scale;
  return String(Number(display.toFixed(6)));
}

/** Check the draft and turn it into the settings to send. Errors name the field. */
export function toPatch(draft: Draft): { patch: SettingsPatch; errors: string[] } {
  const patch: SettingsPatch = {};
  const errors: string[] = [];
  if (draft.period) patch.period = draft.period;
  if (draft.period === "custom") {
    if (!draft.start || !draft.end) errors.push("A custom period needs a start and an end.");
    else if (draft.start > draft.end) errors.push("The start must come before the end.");
    patch.start = draft.start;
    patch.end = draft.end;
  }
  const put = (section: Section, key: string, value: unknown) => {
    patch[section] = { ...(patch[section] as object), [key]: value } as never;
  };
  if (draft.mode) put("entry", "mode", draft.mode);
  if (draft.rank_order) put("entry", "rank_order", draft.rank_order);
  if (draft.side) put("entry", "side", draft.side);
  if (draft.exclude_blank_checks !== undefined) put("universe", "exclude_blank_checks", draft.exclude_blank_checks);
  if (draft.tickers !== undefined && draft.tickers.trim()) {
    const { tickers, bad } = readTickers(draft.tickers);
    if (bad.length) errors.push(`Only these stocks: not a ticker: ${bad.slice(0, 5).join(", ")}.`);
    else put("universe", "tickers", tickers);
  }
  for (const spec of NUMBERS) {
    const text = (draft.numbers[spec.path] ?? "").trim().replace(/,/g, "");
    if (!text) continue;
    const [section, key] = spec.path.split(".") as [Section, string];
    const value = Number(text);
    if (!Number.isFinite(value)) {
      errors.push(`${spec.label}: not a number.`);
      continue;
    }
    if (spec.optional && value === 0) {
      put(section, key, null);
      continue;
    }
    if (value < spec.min || (spec.max != null && value > spec.max)) {
      errors.push(`${spec.label}: from ${spec.min}${spec.max != null ? ` to ${spec.max}` : " up"}.`);
      continue;
    }
    if (spec.integer && !Number.isInteger(value)) {
      errors.push(`${spec.label}: a whole number.`);
      continue;
    }
    put(section, key, spec.scale === 1 ? value : Number((value * spec.scale).toPrecision(12)));
  }
  return { patch, errors };
}

/** The settings a past run used, as a draft, so they can be run again. */
export function fromSettings(settings: LabSettings, against: LabSettings): Draft {
  const draft: Draft = { numbers: {} };
  if (settings.period !== against.period) draft.period = settings.period;
  if (settings.period === "custom") {
    draft.period = "custom";
    draft.start = settings.start ?? undefined;
    draft.end = settings.end ?? undefined;
  }
  if (settings.entry.mode !== against.entry.mode) draft.mode = settings.entry.mode;
  if (settings.entry.rank_order !== against.entry.rank_order) draft.rank_order = settings.entry.rank_order;
  if ((settings.entry.side ?? "long") !== (against.entry.side ?? "long")) draft.side = settings.entry.side ?? "long";
  if (settings.universe.exclude_blank_checks !== against.universe.exclude_blank_checks) draft.exclude_blank_checks = settings.universe.exclude_blank_checks;
  const named = (settings.universe.tickers ?? []).join(", ");
  if (named !== (against.universe.tickers ?? []).join(", ")) draft.tickers = named || "all";
  for (const spec of NUMBERS) {
    const value = get(settings, spec.path);
    if (value === get(against, spec.path)) continue;
    draft.numbers[spec.path] = value == null ? "0" : String(Number((value / spec.scale).toFixed(6)));
  }
  return draft;
}

export function changed(draft: Draft): boolean {
  return Boolean(
    draft.period ||
    draft.mode ||
    draft.rank_order ||
    draft.side ||
    draft.exclude_blank_checks !== undefined ||
    draft.tickers?.trim() ||
    draft.sweep_field ||
    Object.values(draft.numbers).some((v) => v.trim()),
  );
}
