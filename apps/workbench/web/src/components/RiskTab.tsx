import { useEffect, useMemo, useState } from "react";
import { day, int, num, pct, plainPct } from "../lib/format";
import { beta, drawdowns, type Drawdown, returns, type Season, seasons, volatility } from "../lib/risk";
import { BarChart } from "./charts/BarChart";
import { aligned, closesOf } from "./RelativeChart";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";
import { StatStrip } from "./ui/StatStrip";

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const YEAR = 252;

function sessionsBetween(dates: string[], from: string, to: string | null): number | null {
  if (!to) return null;
  return dates.indexOf(to) - dates.indexOf(from);
}

export function RiskTab({ symbol, dates, close, onPick }: { symbol: string; dates: string[]; close: (number | null)[]; onPick: (from: string, to: string) => void }) {
  const [spy, setSpy] = useState<(number | null)[] | null>(null);
  useEffect(() => {
    let live = true;
    closesOf("SPY").then((found) => live && found && setSpy(aligned(dates, found)));
    return () => {
      live = false;
    };
  }, [dates]);
  const daily = useMemo(() => returns(close), [close]);
  const market = useMemo(() => (spy ? returns(spy) : null), [spy]);
  const falls = useMemo(() => drawdowns(dates, close), [dates, close]);
  const months = useMemo(() => seasons(dates, close), [dates, close]);
  const oneYear = market ? beta(daily, market, YEAR) : null;
  const threeYears = market ? beta(daily, market, 3 * YEAR) : null;
  const worst = falls[0];
  const fallColumns: Column<Drawdown>[] = [
    { key: "peak", header: "High", align: "left", strong: true, render: (d) => day(d.peak) },
    { key: "trough", header: "Low", align: "left", render: (d) => day(d.trough) },
    { key: "depth", header: "Fall", signed: true, strong: true, render: (d) => pct(d.depth, 1) },
    { key: "recovered", header: "Back at the high", align: "left", muted: true, render: (d) => (d.recovered ? day(d.recovered) : "not by the seal") },
    { key: "took", header: "Sessions, high to high", muted: true, render: (d) => int(sessionsBetween(dates, d.peak, d.recovered)) },
  ];
  const monthColumns: Column<Season>[] = [
    { key: "month", header: "Month", align: "left", strong: true, render: (s) => MONTHS[s.month - 1] },
    { key: "mean", header: "Average", signed: true, render: (s) => pct(s.mean, 1) },
    { key: "median", header: "Median", signed: true, render: (s) => pct(s.median, 1) },
    { key: "up", header: "Years up", render: (s) => (s.years ? `${s.up} of ${s.years}` : "–") },
  ];
  return (
    <div className="flex flex-col gap-4">
      <StatStrip
        items={[
          { label: "Beta to SPY, last year", value: oneYear ? num(oneYear.beta, 2) : "–", note: oneYear ? `correlation ${num(oneYear.correlation, 2)}` : spy ? "too few sessions" : "reading SPY…" },
          { label: "Beta to SPY, three years", value: threeYears ? num(threeYears.beta, 2) : "–", note: threeYears ? `correlation ${num(threeYears.correlation, 2)}` : undefined },
          { label: "Volatility, last year", value: plainPct(volatility(daily, YEAR), 1), note: market ? `SPY ${plainPct(volatility(market, YEAR), 1)}` : undefined },
          {
            label: "Deepest fall from a high",
            value: worst ? pct(worst.depth, 1) : "–",
            note: worst ? `${day(worst.peak, true)} ’${worst.peak.slice(2, 4)} to ${day(worst.trough, true)} ’${worst.trough.slice(2, 4)}` : undefined,
          },
        ]}
      />
      <Card title={`The deepest falls of ${symbol}`}>
        <div className="-mx-5 overflow-x-auto">
          <DataTable columns={fallColumns} rows={falls} rowKey={(d) => d.peak} onRowClick={(d) => onPick(d.peak, d.recovered ?? dates[dates.length - 1])} minWidth={720} />
        </div>
        <Note>From a closing high to the lowest close before the stock closed above that high again; split-adjusted, without dividends. Click a fall to see it on the chart.</Note>
      </Card>
      <Card title="Month by month">
        <BarChart
          neutral={false}
          title={`${symbol}'s average return in each calendar month`}
          labels={MONTHS.map((m) => m.slice(0, 3))}
          values={months.map((s) => s.mean)}
          format={(v) => pct(v, 1)}
          height={200}
          width={1000}
        />
        <div className="-mx-5 overflow-x-auto">
          <DataTable columns={monthColumns} rows={months} rowKey={(s) => String(s.month)} minWidth={560} />
        </div>
        <Note>
          Each month's change from the last close of the month before, over every year in the data. A handful of years is a small sample: a month that looks strong is as likely to be chance.
        </Note>
      </Card>
    </div>
  );
}
