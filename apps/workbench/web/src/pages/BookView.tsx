import { LineChart } from "../components/charts/LineChart";
import { type Column, DataTable } from "../components/ui/DataTable";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import type { BookMetrics, Position, RunDetail } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { int, money, num, pct, plainPct } from "../lib/format";

type Pair = { name: string; value: number };
const dollars = (v: number) => money(v).replace("+", "");

/** Results of a multi-day book: returns, exposure through time, where the profit came from, holdings. */
export function BookView({ detail, metrics: m }: { detail: RunDetail; metrics: BookMetrics }) {
  const a = m.slippage_1x;
  const b = m.slippage_2x;
  const years = Object.entries(m.by_year).map(([year, row]) => ({ year, ...row }));
  const sources: Pair[] = [
    { name: "Long positions", value: m.attribution.long_pnl },
    { name: "Short positions", value: m.attribution.short_pnl },
    { name: "Commission and fees", value: -(m.costs.commission + m.costs.fees) },
    { name: "Slippage, 1×", value: -m.costs.slippage },
    { name: "Borrow fee on shorts", value: -m.costs.borrow },
    { name: "Total net", value: a.total_net },
  ];
  const checks: Pair[] = [
    { name: "Rebalances", value: m.counts.rebalances ?? 0 },
    { name: "Early rebalances (exposure too high)", value: m.counts.early_rebalances ?? 0 },
    { name: "Rebalances with no valid portfolio", value: m.counts.no_portfolio ?? 0 },
    { name: "Lookahead replays passed", value: m.counts.lookahead_checks ?? 0 },
    { name: "Positions closed on delisting", value: m.counts.forced_exits ?? 0 },
    { name: "Fills", value: m.fills ?? detail.fills ?? 0 },
  ];
  const pairColumns = (label: string, render: (v: number) => string, signed = false): Column<Pair>[] => [
    { key: "name", header: label, align: "left", render: (r) => r.name },
    { key: "value", header: signed ? "Dollars" : "Count", signed, render: (r) => render(r.value) },
  ];
  const holdings: Column<Position>[] = [
    { key: "symbol", header: "Symbol", align: "left", strong: true, render: (p) => p.symbol },
    { key: "sector", header: "Sector", align: "left", muted: true, render: (p) => p.sector },
    { key: "shares", header: "Shares", signed: true, render: (p) => int(p.shares) },
    { key: "weight", header: "Weight", signed: true, strong: true, render: (p) => pct(p.weight, 1) },
  ];
  return (
    <>
      <StatStrip
        items={[
          { label: "Return a year", value: pct(a.annual_return, 1), note: `2× slippage ${pct(b.annual_return, 1)}` },
          { label: "Sharpe ratio", value: num(a.sharpe), note: `2× ${num(b.sharpe)}; t ${num(a.t_stat_daily)}` },
          { label: "Total net", value: money(a.total_net), note: `on $${int(m.account)}; 2× ${money(b.total_net)}` },
          { label: "Worst drawdown", value: pct(a.max_drawdown_pct, 1), note: money(a.max_drawdown) },
          { label: "Gross exposure", value: `${num(m.exposure.gross_mean)}×`, note: `highest ${num(m.exposure.gross_max)}× of equity` },
          { label: "Holdings", value: `${num(m.exposure.long_names_mean, 0)} / ${num(m.exposure.short_names_mean, 0)}`, note: `long / short; turnover ${num(m.turnover_annual, 1)}× a year` },
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title="Cumulative net profit, dollars">
          {detail.equity ? (
            <LineChart
              title="Cumulative net profit at 1x and 2x slippage"
              labels={detail.equity.date}
              format={dollars}
              series={[
                { name: "1× slippage", short: "1×", values: detail.equity.cum_net, color: SERIES[0] },
                { name: "2× slippage", short: "2×", values: detail.equity.cum_net_2x, color: SERIES[1], dash: DASHES[1] },
              ]}
            />
          ) : (
            <PanelNote>No equity series in this run.</PanelNote>
          )}
        </Panel>
        <Panel title="Account equity and exposure, dollars">
          {detail.exposure ? (
            <LineChart
              title="Equity, long value and short value through time"
              labels={detail.exposure.date}
              format={dollars}
              series={[
                { name: "Equity", short: "Equity", values: detail.exposure.equity, color: SERIES[0] },
                { name: "Long value", short: "Long", values: detail.exposure.long_value, color: SERIES[2] },
                { name: "Short value", short: "Short", values: detail.exposure.short_value, color: SERIES[3], dash: DASHES[1] },
              ]}
            />
          ) : (
            <PanelNote>No exposure series in this run.</PanelNote>
          )}
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.25fr)]">
        <Panel title="By year">
          <DataTable
            rows={years}
            rowKey={(r) => r.year}
            columns={[
              { key: "year", header: "Year", align: "left", render: (r) => r.year },
              { key: "r1", header: "Return, 1×", signed: true, strong: true, render: (r) => pct(r.return_1x, 1) },
              { key: "r2", header: "Return, 2×", signed: true, render: (r) => pct(r.return_2x, 1) },
              { key: "net", header: "Net $, 1×", signed: true, render: (r) => money(r.net_1x) },
            ]}
          />
        </Panel>
        <div className="flex flex-col gap-4">
          <Panel title="Where the result came from">
            <DataTable rows={sources} rowKey={(r) => r.name} columns={pairColumns("Source", money, true)} />
            <PanelNote>
              Trading cost {num(m.costs.trading_bps_of_traded, 1)} bps of every dollar traded. Volatility {plainPct(a.annual_volatility, 1)} a year.
            </PanelNote>
          </Panel>
          <Panel title="Run checks">
            <DataTable rows={checks} rowKey={(r) => r.name} columns={pairColumns("Check", int)} />
          </Panel>
        </div>
        <Panel title={detail.positions ? `Holdings on ${detail.positions.date} (${detail.positions.count})` : "Holdings"}>
          {detail.positions ? (
            <div className="max-h-[560px] overflow-y-auto">
              <DataTable rows={detail.positions.rows} rowKey={(p) => String(p.permaticker)} columns={holdings} />
            </div>
          ) : (
            <PanelNote>The book held nothing at the end of the run.</PanelNote>
          )}
        </Panel>
      </div>
    </>
  );
}
