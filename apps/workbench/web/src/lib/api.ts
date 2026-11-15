import type { Stat } from "./format";

export type RunKind = "backtest" | "event_study" | "tick_study";

export interface RunRow {
  run_id: string;
  strategy: string;
  family: string;
  config: string;
  kind: RunKind;
  agent: string;
  branch: string;
  commit: string;
  dirty: boolean;
  scratch: boolean;
  status: string;
  started_at: string;
  period: { start: string; end: string };
  data_build_id: string;
  params: Record<string, string | number | boolean | null>;
  schema_ok: boolean;
  trades: number | null;
  net_1x: number | null;
  net_2x: number | null;
  gross: number | null;
  sharpe: number | null;
  total_net: number | null;
  t_stat_2x: number | null;
}

export interface Side {
  mean_return: number | null;
  median_return: number | null;
  win_rate: number | null;
  total_net: number;
  t_stat_daily: number | null;
  sharpe: number | null;
  annual_return_on_equity: number | null;
  max_drawdown: number | null;
}

export interface Metrics {
  sessions: number;
  trades: number;
  trades_per_session: number | null;
  gross_mean_return: number | null;
  mean_notional: number | null;
  slippage_1x: Side;
  slippage_2x: Side;
  cost_bps_of_notional: Record<string, number | null>;
  exit_reasons: Record<string, number>;
  by_year: Record<string, { trades: number; mean_return_1x: number; mean_return_2x: number; net_1x: number }>;
  counts: Record<string, number>;
  equity: number;
}

export interface Three {
  gross: Stat;
  net_1x: Stat;
  net_2x: Stat;
}

export interface Study {
  events: number;
  sessions_with_events: number;
  curve: Record<string, Three>;
  mean_cost: { fees: number; slippage_1x: number };
  median_entry_price: number;
  capacity_limited_share: number;
  by_period: Record<string, { r_close: Three; r_60: Three }>;
  by_liquidity: Record<string, { r_close: Three; r_60: Three }>;
  by_time: Record<string, { r_close: Three; r_60: Three }>;
  by_year: Record<string, { r_close: Three; r_60: Three }>;
  counts: Record<string, number>;
}

export interface FillRule {
  fill_rate: number | null;
  net_per_fill: Stat;
  net_per_order: Stat;
  net_unfilled_if_bought_at_bid: number | null;
}

export interface TickGroup {
  orders: number;
  strict: FillRule;
  lenient: FillRule;
  market_at_ask: Stat;
}

export interface TickStudy {
  all: TickGroup;
  by_bucket: Record<string, TickGroup>;
  by_period: Record<string, TickGroup>;
  windows: number;
}

export interface Manifest {
  run_id: string;
  strategy: string;
  config: string;
  kind?: RunKind;
  agent: string;
  scratch: boolean;
  status: string;
  cost_calibration: string;
  data_build_id: string;
  period: { start: string; end: string };
  git: { commit: string; branch: string; dirty: boolean };
}

export interface RunDetail {
  manifest: Manifest;
  metrics?: Metrics | null;
  study?: Study | null;
  tick_study?: TickStudy | null;
  equity?: { date: string[]; cum_net: number[]; cum_net_2x: number[] };
  histogram?: { counts: number[]; edges: number[] };
}

export interface Overfitting {
  backtests: number;
  best_run: string;
  best_sharpe_annual: number;
  expected_max_sharpe_annual: number;
  deflated_sharpe: number;
  probabilistic_sharpe: number;
  pbo: { pbo: number; splits: number; trials_compared: number } | null;
  sharpes: Record<string, number>;
}

export interface Family {
  family: string;
  runs: number;
  counted: number;
  scratch: number;
  abandoned: number;
  prior_trials: number;
  trials: number;
  by_agent: Record<string, number>;
  overfitting: Overfitting | null;
}

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} answered ${response.status}`);
  return (await response.json()) as T;
}

export const api = {
  runs: () => get<RunRow[]>("/api/runs"),
  families: () => get<Family[]>("/api/families"),
  info: () => get<{ runs_dir: string }>("/api/info"),
  run: (id: string) => get<RunDetail>(`/api/runs/${encodeURIComponent(id)}`),
};
