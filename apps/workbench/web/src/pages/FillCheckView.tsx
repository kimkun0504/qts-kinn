import { Badge } from "../components/ui/Badge";
import { type Column, DataTable } from "../components/ui/DataTable";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import type { FillCheck, FillGroup, FillPeriod, UnfilledGroup } from "../lib/api";
import { int, money, num, pct, plainPct } from "../lib/format";

const BARS: Record<string, string> = {
  coverage_at_least_95pct: "Tick data for at least 95% of the filled orders",
  confirmed_at_least_97pct_each_period: "At least 97% confirmed by a real trade below the limit, in each period",
  validation_net_2x_at_least_1pct: "Validation net per trade at 2×, on real fills, of at least +1.0%",
  tick_rule_keeps_80pct_of_net_each_period: "Keeps at least 80% of the simulated profit, in each period",
};
const UNFILLED: Record<string, string> = {
  touched: "Price touched the limit",
  near: "Came within 1% of the limit",
  far: "Stayed further away",
};

interface GroupRow {
  name: string;
  group: FillGroup;
}

function groups(period: FillPeriod): GroupRow[] {
  return [
    { name: "All", group: period.all },
    ...Object.entries(period.by_cap).map(([name, group]) => ({ name: `Market cap ${name}`, group })),
    ...Object.entries(period.by_rung ?? {}).map(([name, group]) => ({ name: `Rung ${name.replace("o", "")}% below`, group })),
    { name: "2003 to 2006", group: period.before_2007 },
    { name: "2007 on", group: period.from_2007 },
  ].filter((row) => row.group.orders > 0);
}

/** A fill check: were the backtest's minute-bar fills real trades, in the order's size? */
export function FillCheckView({ check }: { check: FillCheck }) {
  const v = check.verdict;
  const real = (g: FillGroup) => g.tick_rule_5s;
  const columns: Column<GroupRow>[] = [
    { key: "name", header: "Orders", align: "left", strong: true, render: (r) => r.name },
    { key: "orders", header: "Filled in the backtest", render: (r) => int(r.group.orders) },
    { key: "covered", header: "With tick data", muted: true, render: (r) => int(r.group.covered) },
    { key: "confirmed", header: "Confirmed by a real trade", render: (r) => plainPct(r.group.confirmed, 1) },
    { key: "full", header: "In full size", render: (r) => plainPct(r.group.in_full_size, 1) },
    { key: "bid", header: "Best bid fell below limit", muted: true, render: (r) => plainPct(r.group.bid_fell_below_limit) },
    { key: "sim", header: "Net 2×, simulated", signed: true, render: (r) => pct(r.group.simulated?.net_per_trade_2x) },
    { key: "real", header: "Net 2×, real fills", signed: true, strong: true, render: (r) => pct(real(r.group)?.net_per_trade_2x) },
    { key: "simtotal", header: "Total 2×, simulated", signed: true, muted: true, render: (r) => money(r.group.simulated?.total_net_2x) },
    { key: "realtotal", header: "Total 2×, real fills", signed: true, render: (r) => money(real(r.group)?.total_net_2x) },
    { key: "kept", header: "Profit kept", render: (r) => plainPct(real(r.group)?.share_of_simulated_net_2x) },
  ];
  return (
    <>
      <StatStrip
        items={[
          { label: "Verdict", value: v.passed ? "Passed" : "Failed", note: `${Object.values(v.bars).filter(Boolean).length} of ${Object.keys(v.bars).length} bars met` },
          { label: "Filled orders checked", value: int(check.all_traded.orders), note: `${plainPct(v.coverage, 1)} with tick data` },
          { label: "Confirmed by a real trade", value: plainPct(check.all_traded.confirmed, 1), note: `${plainPct(check.all_traded.in_full_size, 1)} in the order's full size` },
          { label: "Validation net per trade at 2×", value: pct(v.validation_net_per_trade_2x), note: "on real fills, 5 seconds of latency" },
          { label: "Median volume through the limit", value: `${num(check.all_traded.through_volume_multiple_median, 0)}×`, note: "of the order's size" },
        ]}
      />
      <Panel title="Bars set before the data">
        <DataTable
          rows={Object.entries(v.bars)}
          rowKey={([key]) => key}
          columns={[
            { key: "bar", header: "Bar", align: "left", render: ([key]) => BARS[key] ?? key.replace(/_/g, " ") },
            { key: "met", header: "Result", align: "left", render: ([, met]) => <Badge tone={met ? "ok" : "bad"}>{met ? "Met" : "Missed"}</Badge> },
          ]}
        />
        <PanelNote>
          An order is confirmed when a real, eligible trade printed at least one tick below its limit while it was live. "Real fills" cuts each order to the shares that
          printed below the limit from {check.main_delay_seconds} seconds after the event bar, with the same exit and costs. Plan {check.plan}; trade conditions from the{" "}
          {check.conditions_source}.
        </PanelNote>
      </Panel>
      {Object.entries(check.periods).map(([label, period]) => {
        const all = period.all;
        const sample = Object.entries(period.unfilled).map(([kind, part]) => ({ kind, group: part.all }));
        const sampleColumns: Column<{ kind: string; group: UnfilledGroup }>[] = [
          { key: "kind", header: "Orders the backtest left unfilled", align: "left", render: (r) => UNFILLED[r.kind] ?? r.kind },
          { key: "n", header: "Sampled", render: (r) => int(r.group.orders) },
          { key: "missed", header: "Real trades would have filled", render: (r) => plainPct(r.group.rule_missed_a_fill) },
          { key: "touch", header: "Printed at the limit only", render: (r) => plainPct(r.group.printed_at_the_limit_only) },
          { key: "size", header: "... in full size", muted: true, render: (r) => plainPct(r.group.at_the_limit_in_full_size) },
          { key: "net", header: "Net 2× if those had filled", signed: true, render: (r) => pct(r.group.if_touches_filled?.net_per_trade_2x) },
        ];
        return (
          <Panel key={label} title={`${label[0].toUpperCase()}${label.slice(1)} run`} aside={period.run}>
            <DataTable rows={groups(period)} rowKey={(r) => r.name} columns={columns} minWidth={1180} />
            {all.tick_rule_0s && all.tick_rule_5s && all.tick_rule_30s && (
              <PanelNote>
                Latency. With the order in the book 0, 5 and 30 seconds after the bar: {pct(all.tick_rule_0s.net_per_trade_2x)}, {pct(all.tick_rule_5s.net_per_trade_2x)} and{" "}
                {pct(all.tick_rule_30s.net_per_trade_2x)} a trade at 2×; totals {money(all.tick_rule_0s.total_net_2x)}, {money(all.tick_rule_5s.total_net_2x)} and{" "}
                {money(all.tick_rule_30s.total_net_2x)}.
              </PanelNote>
            )}
            <DataTable rows={sample} rowKey={(r) => r.kind} columns={sampleColumns} />
            <PanelNote>The backtest fills an order only when the price trades through the limit. Orders that only touched it are left out; live, some of them would fill.</PanelNote>
          </Panel>
        );
      })}
    </>
  );
}
