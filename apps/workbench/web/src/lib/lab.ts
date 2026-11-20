/** The Lab's API (decision 0023): the owner's algorithms, runs and results. */

export interface Field {
  name: string;
  description: string;
  known: string;
}

export interface PeriodInfo {
  name: string;
  start: string;
  end: string;
  label: string;
}

export interface LabSettings {
  period: string;
  start: string | null;
  end: string | null;
  universe: {
    min_market_cap: number;
    max_market_cap: number | null;
    min_price: number;
    min_dollar_volume: number;
    exclude_blank_checks: boolean;
    tickers?: string[];
  };
  entry: { mode: "signal" | "rank"; top_n: number; rank_order: "highest" | "lowest"; side?: "long" | "short" | "both" };
  exit: { hold_days: number; stop_loss: number | null; take_profit: number | null };
  book: { position_size: number; max_positions: number; borrow_rate?: number };
}

/** What the page sends: only the settings the owner changed. */
export type SettingsPatch = {
  period?: string;
  start?: string;
  end?: string;
  universe?: Partial<LabSettings["universe"]>;
  entry?: Partial<LabSettings["entry"]>;
  exit?: Partial<LabSettings["exit"]>;
  book?: Partial<LabSettings["book"]>;
};

export interface Meta {
  fields: Field[];
  periods: PeriodInfo[];
  defaults: LabSettings;
  last_entry: string;
  max_hold: number;
  max_code: number;
  active_run: string | null;
  folder: string;
  sweepable?: string[];
}

export interface SweepRequest {
  field: string;
  values: (number | null)[];
}

export interface SweepRow {
  value: number | null;
  trades: number;
  mean_net: number | null;
  mean_net_2x: number | null;
  win_rate: number | null;
  t_weekly: number | null;
  book_profit: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  annual_return: number | null;
  average_positions: number | null;
  years_positive: number | null;
  years: number | null;
}

export interface SweepResult {
  field: string;
  base: number | null;
  rows: SweepRow[];
}

export interface Template {
  name: string;
  description: string;
  code: string;
}

export type RunState = "waiting" | "queued" | "running" | "complete" | "failed" | "cancelled" | "interrupted";

export const LIVE: RunState[] = ["waiting", "queued", "running"];

export const isLive = (state: RunState | undefined) => state != null && LIVE.includes(state);

export interface RunListRow {
  run_id: string;
  algorithm: string;
  description: string;
  created_at: string;
  state: RunState;
  stage: string | null;
  error: string | null;
  trial: boolean;
  trials?: number;
  period: string | null;
  headline: string | null;
  note?: string;
}

export interface AlgorithmRow {
  name: string;
  description: string;
  updated: string;
  runs: number;
  trials: number;
  last_run: RunListRow | null;
}

export interface AlgorithmFile {
  name: string;
  code: string;
  description: string;
  settings_in_code: SettingsPatch | null;
}

export interface Status {
  state: RunState;
  stage?: string;
  progress?: number;
  error?: string;
  signals_computed?: boolean;
  trial_number?: number;
  seconds?: number;
  updated_at?: string;
  ahead?: number;
}

export interface Lookahead {
  passed: boolean;
  checked: string[];
  detail: string;
}

export interface Summary {
  trades: number;
  headline: string;
  lookahead: Lookahead;
  win_rate?: number;
  mean_net?: number;
  median_net?: number;
  mean_gross?: number;
  mean_net_2x?: number;
  mean_over?: number;
  t_weekly?: number | null;
  t_weekly_over?: number | null;
  t_weekly_2x?: number | null;
  years_positive?: number;
  years?: number;
  best?: number;
  worst?: number;
  p05?: number;
  p95?: number;
  mean_sessions?: number;
  stocks?: number;
  taken?: number;
  skipped?: number;
  book_profit?: number;
  book_profit_2x?: number;
  max_drawdown?: number;
  capital?: number;
  annual_return?: number;
  max_drawdown_pct?: number;
  sharpe?: number | null;
  beta_spy?: number | null;
  correlation_spy?: number | null;
  average_positions?: number;
  spy_return?: number | null;
  first_entry?: string;
  last_exit?: string;
  exits?: Record<string, number>;
  fragile?: boolean;
  histogram?: { edges: number[]; counts: number[] };
  period_label?: string;
  settings?: LabSettings;
  signals?: number;
  universe_stocks?: number;
  tickers_not_found?: string[];
  sessions?: number;
  trial_number?: number;
  trials?: number;
  sweep?: { field: string; values: number } | null;
  cost_model?: string;
  has_exit_signal?: boolean;
  seconds?: number;
}

export interface RunDetail {
  run_id: string;
  status: Status;
  manifest: { algorithm: string; description: string; created_at: string; finished_at?: string; code_sha256: string; data_build_id?: string } | null;
  summary: Summary | null;
  note?: string;
}

export interface StockRow {
  ticker: string;
  name: string | null;
  sector: string | null;
  trades: number;
  wins: number;
  win_rate: number;
  mean_net: number;
  total_net: number;
  profit: number;
  book_trades: number;
  book_profit: number;
  mean_over: number | null;
  best: number;
  worst: number;
  last_entry: string;
}

export interface YearRow {
  year: number;
  trades: number;
  mean_net: number;
  median_net: number;
  win_rate: number;
  mean_over: number | null;
  mean_net_2x: number;
  book_profit: number;
}

export interface Equity {
  dates: string[];
  profit: (number | null)[];
  drawdown: (number | null)[];
  spy: (number | null)[];
  spy_matched?: (number | null)[] | null;
  positions: number[];
  shorts?: number[];
  rolling_sharpe?: (number | null)[];
  capital: number;
}

export interface FactorReport {
  buckets: { bucket: number; excess: number | null; mean: number | null; days: number }[];
  spread: number | null;
  order: "highest" | "lowest";
  hold: number;
  ic: { mean: number | null; std: number | null; t: number | null; positive: number | null; days: number; independent_days: number };
  ic_by_year: { year: number; mean: number | null; days: number }[];
}

export interface SignalPath {
  horizons: number[];
  stock: (number | null)[];
  universe: (number | null)[];
  excess: (number | null)[];
  low: (number | null)[];
  high: (number | null)[];
  count: number[];
  trades: number;
  of: number;
  hold: number;
}

export interface TradeRow {
  ticker: string;
  name: string | null;
  sector: string | null;
  signal_date: string;
  entry_date: string;
  exit_date: string;
  sessions: number;
  reason: string;
  entry_price: number;
  exit_price: number;
  shares: number;
  value: number;
  gross: number;
  net: number;
  net_2x: number;
  profit: number;
  benchmark: number;
  over: number;
  taken: boolean;
  side?: "long" | "short";
}

/** A problem the Lab's code check found (it reads the code, never runs it). */
export interface Finding {
  severity: "error" | "warning";
  message: string;
  line: number; // 1-based
  column: number; // 0-based
  end_line: number;
  end_column: number;
}

/** An earlier version of a file: what it held before a save changed it. */
export interface Version {
  version: string;
  saved_at: string;
  lines: number;
  characters: number;
  first_line: string;
}

export interface ModuleRow {
  name: string;
  description: string;
  updated: string;
}

export interface ModuleFile {
  name: string;
  code: string;
  description: string;
}

export interface TradePage {
  total: number;
  offset: number;
  limit: number;
  rows: TradeRow[];
}

export class LabError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const BASE = "/api/lab";
let token: string | null = null;

async function answer<T>(response: Response): Promise<T> {
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    /* not JSON: report the status below */
  }
  if (!response.ok) {
    const message = body && typeof body === "object" && "error" in body ? String((body as { error: unknown }).error) : `The Workbench answered ${response.status}.`;
    throw new LabError(message, response.status);
  }
  return body as T;
}

async function read<T>(path: string): Promise<T> {
  return answer<T>(await fetch(BASE + path, { cache: "no-store" }));
}

async function session(): Promise<string> {
  if (!token) token = (await read<{ token: string }>("/session")).token;
  return token;
}

/** A change: carries the session token. A restarted server has a new one, so a 403 refreshes
 *  the token and tries once more. */
async function write<T>(method: "POST" | "PUT" | "DELETE", path: string, body?: unknown): Promise<T> {
  const send = async () =>
    fetch(BASE + path, {
      method,
      headers: { "X-Kinn-Token": await session(), ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  let response = await send();
  if (response.status === 403) {
    token = null;
    response = await send();
  }
  return answer<T>(response);
}

const id = encodeURIComponent;

export const lab = {
  meta: () => read<Meta>("/meta"),
  templates: () => read<Template[]>("/templates"),
  algorithms: () => read<AlgorithmRow[]>("/algorithms"),
  algorithm: (name: string) => read<AlgorithmFile>(`/algorithms/${id(name)}`),
  save: (name: string, code: string) => write<{ name: string; description: string }>("PUT", `/algorithms/${id(name)}`, { code }),
  remove: (name: string) => write<{ deleted: string }>("DELETE", `/algorithms/${id(name)}`),
  start: (algorithm: string, code: string, settings: SettingsPatch, sweep?: SweepRequest | null) =>
    write<{ run_id: string; status: Status }>("POST", "/runs", sweep ? { algorithm, code, settings, sweep } : { algorithm, code, settings }),
  sweep: (runId: string) => read<SweepResult>(`/runs/${id(runId)}/sweep`),
  cancel: (runId: string) => write<Status>("POST", `/runs/${id(runId)}/cancel`),
  saveNote: (runId: string, note: string) => write<{ run_id: string; note: string }>("PUT", `/runs/${id(runId)}/note`, { note }),
  runs: (algorithm?: string) => read<RunListRow[]>(`/runs${algorithm ? `?algorithm=${id(algorithm)}` : ""}`),
  run: (runId: string) => read<RunDetail>(`/runs/${id(runId)}`),
  status: (runId: string) => read<Status>(`/runs/${id(runId)}/status`),
  stocks: (runId: string) => read<StockRow[]>(`/runs/${id(runId)}/stocks`),
  years: (runId: string) => read<YearRow[]>(`/runs/${id(runId)}/years`),
  equity: (runId: string) => read<Equity>(`/runs/${id(runId)}/equity`),
  code: (runId: string) => read<{ code: string }>(`/runs/${id(runId)}/code`),
  path: (runId: string) => read<SignalPath>(`/runs/${id(runId)}/path`),
  factor: (runId: string) => read<FactorReport>(`/runs/${id(runId)}/factor`),
  log: (runId: string) => read<{ log: string }>(`/runs/${id(runId)}/log`),
  trades: (runId: string, query: { ticker?: string; book?: string; sort?: string; order?: string; offset?: number; limit?: number }) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) if (value !== undefined && value !== "") params.set(key, String(value));
    return read<TradePage>(`/runs/${id(runId)}/trades?${params}`);
  },
  csvUrl: (runId: string) => `${BASE}/runs/${id(runId)}/trades.csv`,
  check: (code: string, module = false) => write<{ findings: Finding[] }>("POST", "/check", { code, module }),
  library: () => read<ModuleRow[]>("/library"),
  module: (name: string) => read<ModuleFile>(`/library/${id(name)}`),
  saveModule: (name: string, code: string) => write<{ name: string; description: string }>("PUT", `/library/${id(name)}`, { code }),
  removeModule: (name: string) => write<{ deleted: string }>("DELETE", `/library/${id(name)}`),
  history: (kind: "algorithms" | "library", name: string) => read<Version[]>(`/${kind}/${id(name)}/history`),
  version: (kind: "algorithms" | "library", name: string, version: string) => read<{ version: string; code: string }>(`/${kind}/${id(name)}/history/${id(version)}`),
};

/** A helper module's name: importable, so letters, digits and _ only. */
export const MODULE_NAME = /^[a-z][a-z0-9_]{0,63}$/;

/** A name for a new algorithm: lower-case letters, digits, - and _. */
export function cleanName(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "_")
    .replace(/^[-_]+/, "")
    .slice(0, 64)
    .replace(/[-_]+$/, "");
}

export const NAME = /^[a-z0-9][a-z0-9_-]{0,63}$/;
