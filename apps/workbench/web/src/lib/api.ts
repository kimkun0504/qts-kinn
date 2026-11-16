import type { Stat } from "./format";

export type RunKind = "backtest" | "event_study" | "tick_study" | "book" | "fill_check";
/** Which research period a run covers. Searches happen on development; validation is run once. */
export type Phase = "development" | "validation" | "full";

export interface TargetItem {
  key: string;
  label: string;
  value: number | null;
  bar: number;
  met: boolean;
}

/** The owner's four targets for one out-of-sample backtest (decision 0017). */
export interface Targets {
  items: TargetItem[];
  fills: "confirmed" | "failed" | "not checked";
  fills_run: string | null;
  met: number;
  of: number;
  all_met: boolean;
}

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
  phase: Phase | null;
  targets: Targets | null;
  sharpe_2x: number | null;
  drawdown_2x: number | null;
  total_net_2x: number | null;
  fill_check_passed: boolean | null;
}

/** One strategy folder: what its strategy.yaml declares and how its candidate did. */
export interface StrategyInfo {
  strategy: string;
  status: string;
  state: string;
  owner: string | null;
  family: string;
  runs: number;
  candidate_config: string | null;
  candidate_run: RunRow | null;
  validation_run: RunRow | null;
  ready_for_paper: boolean;
}

export interface FillResult {
  trades: number;
  net_per_trade_1x: number | null;
  net_per_trade_2x: number | null;
  total_net_1x: number;
  total_net_2x: number;
  share_of_simulated_net_2x?: number | null;
}

export interface FillGroup {
  orders: number;
  covered: number;
  coverage: number | null;
  confirmed?: number | null;
  confirmed_after_5s?: number | null;
  in_full_size?: number | null;
  through_volume_multiple_median?: number;
  bid_fell_below_limit?: number | null;
  simulated?: FillResult;
  tick_rule_0s?: FillResult;
  tick_rule_5s?: FillResult;
  tick_rule_30s?: FillResult;
}

export interface UnfilledGroup {
  orders: number;
  covered: number;
  rule_missed_a_fill?: number | null;
  printed_at_the_limit_only?: number | null;
  at_the_limit_in_full_size?: number | null;
  if_touches_filled?: FillResult;
}

export interface FillPeriod {
  run: string;
  all: FillGroup;
  by_cap: Record<string, FillGroup>;
  by_rung?: Record<string, FillGroup>;
  before_2007: FillGroup;
  from_2007: FillGroup;
  unfilled: Record<string, { all: UnfilledGroup; by_cap: Record<string, UnfilledGroup> }>;
}

/** A fill check: a run's minute-bar fills compared with real trades (schema fill-check-1). */
export interface FillCheck {
  plan: string;
  main_delay_seconds: number;
  conditions_source: string;
  periods: Record<string, FillPeriod>;
  all_traded: FillGroup;
  verdict: {
    passed: boolean;
    bars: Record<string, boolean>;
    coverage: number;
    validation_net_per_trade_2x: number | null;
    share_of_simulated_net_2x: Record<string, number | null>;
  };
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

export interface BookSide {
  total_net: number;
  total_return: number;
  annual_return: number;
  annual_volatility: number;
  sharpe: number;
  t_stat_daily: number;
  max_drawdown: number;
  max_drawdown_pct: number;
}

/** Summary of a multi-day book (metrics schema book-metrics-1). */
export interface BookMetrics {
  sessions: number;
  account: number;
  fills?: number;
  slippage_1x: BookSide;
  slippage_2x: BookSide;
  by_year: Record<string, { return_1x: number; return_2x: number; net_1x: number }>;
  exposure: { gross_mean: number; gross_max: number; net_mean: number; long_names_mean: number; short_names_mean: number };
  turnover_annual: number;
  costs: { commission: number; fees: number; slippage: number; borrow: number; trading_bps_of_traded: number };
  attribution: { long_pnl: number; short_pnl: number; trading_costs: number; borrow: number };
  counts: Record<string, number>;
}

export interface Position {
  permaticker: number;
  symbol: string;
  sector: string;
  shares: number;
  price: number;
  value: number;
  weight: number;
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
  metrics?: Metrics | BookMetrics | null;
  study?: Study | null;
  exposure?: { date: string[]; equity: number[]; long_value: number[]; short_value: number[]; n_long: number[]; n_short: number[] };
  positions?: { date: string; count: number; rows: Position[] };
  fills?: number | null;
  tick_study?: TickStudy | null;
  fill_check?: FillCheck | null;
  phase?: Phase | null;
  targets?: Targets | null;
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
  strategies: () => get<StrategyInfo[]>("/api/strategies"),
  info: () => get<{ runs_dir: string }>("/api/info"),
  run: (id: string) => get<RunDetail>(`/api/runs/${encodeURIComponent(id)}`),
};
