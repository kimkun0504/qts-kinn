import { Histogram } from "../components/charts/Histogram";
import { LineChart } from "../components/charts/LineChart";
import { Badge } from "../components/ui/Badge";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import { PHASE } from "../components/Verdict";
import type { BookMetrics, Manifest, Metrics, Phase, RunDetail as Detail, Study, Targets, Three, TickGroup, TickStudy } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { int, interval, money, num, pct, plainPct } from "../lib/format";
import { useRun } from "../lib/useRun";
import { BookView } from "./BookView";
import { FillCheckView } from "./FillCheckView";

export function RunDetail({ runId }: { runId: string | null }) {
  const { detail, error } = useRun(runId);
  if (!runId) return <EmptyState title="Pick a run">Choose a row in the runs table to see its results.</EmptyState>;
  if (error) return <EmptyState title="Could not read the run">{error}</EmptyState>;
  if (!detail) return <p className="text-ink-2">Loading the run…</p>;
  const { manifest } = detail;
  return (
    <>
      <RunHeader manifest={manifest} phase={detail.phase ?? null} />
      {manifest.status !== "complete" ? (
        <EmptyState title={manifest.status === "abandoned" ? "This run was abandoned before it produced results" : "This run has not finished"}>
          {manifest.status === "abandoned" ? "It is not counted as a trial." : `Continue it with: uv run kinn ${manifest.kind === "book" ? "book" : "run"} --resume ${manifest.run_id}`}
        </EmptyState>
      ) : detail.study ? (
        <StudyView study={detail.study} />
      ) : detail.tick_study ? (
        <TickView tick={detail.tick_study} />
      ) : detail.fill_check ? (
        <FillCheckView check={detail.fill_check} />
      ) : manifest.kind === "book" && detail.metrics ? (
        <BookView detail={detail} metrics={detail.metrics as BookMetrics} />
      ) : detail.metrics ? (
        <>
          {detail.targets && <TargetsPanel targets={detail.targets} />}
          <BacktestView detail={detail} metrics={detail.metrics as Metrics} />
        </>
      ) : (
        <EmptyState title="No results in this run folder" />
      )}
    </>
  );
}

/** The owner's four targets against this out-of-sample run. */
function TargetsPanel({ targets }: { targets: Targets }) {
  const show = (key: string, value: number | null) => (key === "sharpe" ? num(value) : key === "drawdown" ? plainPct(value, 1) : pct(value));
  const bar = (key: string, value: number) => (key === "sharpe" ? `above ${num(value)}` : key === "drawdown" ? `under ${plainPct(value)}` : `at least ${pct(value)}`);
  const rows = [
    ...targets.items.map((item) => ({ key: item.key, label: item.label, bar: bar(item.key, item.bar), value: show(item.key, item.value), met: item.met as boolean | null })),
    {
      key: "fills",
      label: "Fills confirmed against real trades",
      bar: "a passed fill check",
      value: targets.fills === "not checked" ? "not checked yet" : targets.fills,
      met: targets.fills === "confirmed" ? true : targets.fills === "failed" ? false : null,
    },
  ];
  return (
    <Panel title="Targets for paper trading" aside={`${targets.met} of ${targets.of} met`}>
      <DataTable
        rows={rows}
        rowKey={(r) => r.key}
        columns={[
          { key: "label", header: "Target", align: "left", render: (r) => r.label },
          { key: "bar", header: "Bar", align: "left", muted: true, render: (r) => r.bar },
          { key: "value", header: "This run", align: "left", strong: true, render: (r) => r.value },
          {
            key: "met",
            header: "Result",
            align: "left",
            render: (r) => <Badge tone={r.met == null ? "warn" : r.met ? "ok" : "bad"}>{r.met == null ? "Open" : r.met ? "Met" : "Missed"}</Badge>,
          },
        ]}
      />
      {targets.fills_run && <PanelNote>Fill check: {targets.fills_run}</PanelNote>}
    </Panel>
  );
}

function RunHeader({ manifest, phase }: { manifest: Manifest; phase: Phase | null }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="m-0 text-lg font-semibold">
            {manifest.strategy} <span className="font-normal text-ink-2">{manifest.config}</span>
          </h2>
          <Badge tone={manifest.scratch || manifest.status === "abandoned" ? "muted" : "info"}>
            {manifest.scratch ? "Scratch, not counted" : manifest.status === "abandoned" ? "Abandoned, not counted" : "Counted trial"}
          </Badge>
          {phase && <Badge tone={phase === "validation" || phase === "holdout" ? "info" : "muted"}>{phase === "development" ? "Development: a search result" : phase === "validation" ? "Validation: out of sample" : phase === "holdout" ? "Holdout: the one clean test" : PHASE[phase]}</Badge>}
          {manifest.git.dirty && <Badge tone="warn">Uncommitted code</Badge>}
        </div>
        <div className="text-xs text-ink-3">{manifest.run_id}</div>
      </div>
      <div className="text-right text-xs text-ink-2">
        {manifest.period.start} to {manifest.period.end}
        <br />
        {manifest.agent} on {manifest.git.branch} at {manifest.git.commit.slice(0, 8)}, {manifest.cost_calibration}
      </div>
    </div>
  );
}

function BacktestView({ detail, metrics: m }: { detail: Detail; metrics: Metrics }) {
  const a = m.slippage_1x;
  const b = m.slippage_2x;
  const years = Object.entries(m.by_year).map(([year, row]) => ({ year, ...row }));
  const pairs = (record: Record<string, number | null>) => Object.entries(record).map(([name, value]) => ({ name: name.replace(/_/g, " "), value }));
  const funnel = [
    { name: "Signals", value: m.counts.signals },
    { name: "Refused: capital or duplicate", value: m.counts.rejected_capital },
    { name: "Refused: position too small", value: m.counts.rejected_size },
    ...(m.counts.rejected_risk ? [{ name: "Refused: risk rule", value: m.counts.rejected_risk }] : []),
    { name: "Entry never filled", value: m.counts.unfilled },
    ...(m.counts.paused_sessions ? [{ name: "Sessions paused by the circuit breaker", value: m.counts.paused_sessions }] : []),
    { name: "Trades", value: m.trades },
    { name: "Lookahead replays passed", value: m.counts.lookahead_checks },
  ];
  const pairColumns = (label: string, digits: number): Column<{ name: string; value: number | null }>[] => [
    { key: "name", header: label, align: "left", render: (r) => r.name },
    { key: "value", header: digits ? "bps" : "Count", render: (r) => (digits ? num(r.value, digits) : int(r.value)) },
  ];
  return (
    <>
      <StatStrip
        items={[
          { label: "Net per trade", value: pct(a.mean_return), note: `2× slippage ${pct(b.mean_return)}` },
          { label: "Trades", value: int(m.trades), note: `${num(m.trades_per_session, 1)} a session` },
          { label: "Total net", value: money(a.total_net), note: `2× ${money(b.total_net)}` },
          { label: "t-stat, daily P&L", value: num(a.t_stat_daily), note: `2× ${num(b.t_stat_daily)}` },
          { label: "Worst drawdown", value: money(a.max_drawdown), note: `on $${int(m.equity)} equity` },
          { label: "Win rate", value: plainPct(a.win_rate, 1), note: `gross ${pct(m.gross_mean_return)} a trade` },
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel title="Cumulative net profit, dollars">
          {detail.equity ? (
            <LineChart
              title="Cumulative net profit at 1x and 2x slippage"
              labels={detail.equity.date}
              format={(v) => money(v).replace("+", "")}
              series={[
                { name: "1× slippage", short: "1×", values: detail.equity.cum_net, color: SERIES[0] },
                { name: "2× slippage", short: "2×", values: detail.equity.cum_net_2x, color: SERIES[1], dash: DASHES[1] },
              ]}
            />
          ) : (
            <PanelNote>No equity series in this run.</PanelNote>
          )}
        </Panel>
        <Panel title="Net return per trade, 1× slippage" padded>
          {detail.histogram ? (
            <>
              <Histogram counts={detail.histogram.counts} edges={detail.histogram.edges} label="Distribution of net return per trade" />
              <p className="m-0 pt-2 text-xs text-ink-3">Clipped at the 1st and 99th percentiles.</p>
            </>
          ) : (
            <p className="m-0 text-ink-2">Too few trades for a distribution.</p>
          )}
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel title="By year">
          <DataTable
            rows={years}
            rowKey={(r) => r.year}
            columns={[
              { key: "year", header: "Year", align: "left", render: (r) => r.year },
              { key: "trades", header: "Trades", render: (r) => int(r.trades) },
              { key: "n1", header: "Net / trade, 1×", signed: true, strong: true, render: (r) => pct(r.mean_return_1x) },
              { key: "n2", header: "Net / trade, 2×", signed: true, render: (r) => pct(r.mean_return_2x) },
              { key: "net", header: "Net $, 1×", signed: true, render: (r) => money(r.net_1x) },
            ]}
          />
        </Panel>
        <div className="flex flex-col gap-4">
          <Panel title="Round-trip costs, bps of entry notional">
            <DataTable rows={pairs(m.cost_bps_of_notional)} rowKey={(r) => r.name} columns={pairColumns("Cost", 1)} />
          </Panel>
          <Panel title="From signal to trade">
            <DataTable rows={funnel} rowKey={(r) => r.name} columns={pairColumns("Stage", 0)} />
          </Panel>
          <Panel title="Exits">
            <DataTable rows={pairs(m.exit_reasons)} rowKey={(r) => r.name} columns={pairColumns("Reason", 0)} />
          </Panel>
        </div>
      </div>
    </>
  );
}

const horizonLabel = (column: string) => (column === "r_close" ? "close" : column.slice(2));

function StudyView({ study: s }: { study: Study }) {
  if (!s.events) return <EmptyState title="The study found no events" />;
  const columns = Object.keys(s.curve);
  const close = s.curve.r_close;
  const cost = s.mean_cost;
  const split = (title: string, groups: Record<string, { r_close: Three; r_60: Three }>) => (
    <Panel title={title}>
      <DataTable
        rows={Object.entries(groups).map(([name, g]) => ({ name, ...g }))}
        rowKey={(r) => r.name}
        minWidth={720}
        columns={[
          { key: "name", header: "", align: "left", render: (r) => r.name },
          { key: "n", header: "Events", muted: true, render: (r) => int(r.r_close.gross.n) },
          { key: "gross", header: "Gross to close", signed: true, render: (r) => pct(r.r_close.gross.mean) },
          { key: "n1", header: "Net 1× to close (95% interval)", signed: true, strong: true, render: (r) => interval(r.r_close.net_1x) },
          { key: "n2", header: "Net 2× to close", signed: true, render: (r) => pct(r.r_close.net_2x.mean) },
          { key: "h60", header: "Net 1× at 60 min", signed: true, render: (r) => interval(r.r_60.net_1x) },
        ]}
      />
    </Panel>
  );
  return (
    <>
      <StatStrip
        items={[
          { label: "Net, held to close", value: pct(close.net_1x.mean), note: `${pct(close.net_1x.low)} to ${pct(close.net_1x.high)}` },
          { label: "Net at 2× slippage", value: pct(close.net_2x.mean) },
          { label: "Gross", value: pct(close.gross.mean), note: "before costs" },
          { label: "Round-trip cost, 1×", value: plainPct(cost.fees + cost.slippage_1x, 2), note: `fees ${plainPct(cost.fees, 2)}, slippage ${plainPct(cost.slippage_1x, 2)}` },
          { label: "Events", value: int(s.events), note: `on ${int(s.sessions_with_events)} sessions` },
        ]}
      />
      <Panel title="Mean return after the event, by minutes held">
        <LineChart
          title="Mean forward return by minutes held: gross, net at 1x with its 95% interval, net at 2x"
          labels={columns.map(horizonLabel)}
          everyLabel
          format={(v) => pct(v)}
          band={{ low: columns.map((c) => s.curve[c].net_1x.low ?? 0), high: columns.map((c) => s.curve[c].net_1x.high ?? 0), color: SERIES[0] }}
          series={[
            { name: "Net, 1× slippage", short: "net 1×", values: columns.map((c) => s.curve[c].net_1x.mean ?? 0), color: SERIES[0] },
            { name: "Net, 2× slippage", short: "net 2×", values: columns.map((c) => s.curve[c].net_2x.mean ?? 0), color: SERIES[1], dash: DASHES[1] },
            { name: "Gross", short: "gross", values: columns.map((c) => s.curve[c].gross.mean ?? 0), color: SERIES[2], dash: DASHES[2] },
          ]}
          caption="Minutes held after entry, not to scale, capped at the close. The band is the 95% interval for net at 1×, resampling whole sessions."
        />
      </Panel>
      {split("By period", s.by_period)}
      {split("By liquidity", s.by_liquidity)}
      {split("By time of the event", s.by_time)}
      {split("By year", s.by_year)}
    </>
  );
}

function TickView({ tick }: { tick: TickStudy }) {
  const rows = [{ name: "All", ...tick.all }, ...Object.entries({ ...tick.by_bucket, ...tick.by_period }).map(([name, g]) => ({ name, ...g }))];
  const columns = (rule: "strict" | "lenient"): Column<TickGroup & { name: string }>[] => [
    { key: "name", header: "", align: "left", render: (r) => r.name },
    { key: "orders", header: "Orders", muted: true, render: (r) => int(r.orders) },
    { key: "rate", header: "Fill rate", render: (r) => plainPct(r[rule].fill_rate) },
    { key: "fill", header: "Net per fill (95% interval)", signed: true, strong: true, render: (r) => interval(r[rule].net_per_fill) },
    { key: "order", header: "Net per order placed", signed: true, render: (r) => pct(r[rule].net_per_order.mean) },
    { key: "missed", header: "Unfilled, had they been bought", signed: true, render: (r) => pct(r[rule].net_unfilled_if_bought_at_bid) },
    { key: "market", header: "Market order at the ask", signed: true, render: (r) => pct(r.market_at_ask.mean) },
  ];
  const all = tick.all.strict;
  return (
    <>
      <StatStrip
        items={[
          { label: "Net per fill", value: pct(all.net_per_fill.mean), note: `${pct(all.net_per_fill.low)} to ${pct(all.net_per_fill.high)}` },
          { label: "Fill rate", value: plainPct(all.fill_rate), note: `${int(all.net_per_fill.n)} of ${int(tick.all.orders)} orders` },
          { label: "Net per order placed", value: pct(all.net_per_order.mean) },
          { label: "Market order, same events", value: pct(tick.all.market_at_ask.mean) },
        ]}
      />
      <Panel title="Strict fill rule: a trade strictly below the limit">
        <DataTable rows={rows} rowKey={(r) => r.name} columns={columns("strict")} minWidth={900} />
      </Panel>
      <Panel title="Lenient fill rule: a trade at or below the limit">
        <DataTable rows={rows} rowKey={(r) => r.name} columns={columns("lenient")} minWidth={900} />
        <PanelNote>The truth about queue position lies between the two rules.</PanelNote>
      </Panel>
    </>
  );
}
