import { useEffect, useMemo, useState } from "react";
import { day, pct } from "../lib/format";
import { median } from "../lib/screen";
import { BarChart } from "./charts/BarChart";
import { aligned, closesOf } from "./RelativeChart";
import { CsvButton } from "./CsvButton";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";

export interface Reaction {
  filed: string;
  before: number;
  after: number;
  move: number;
  next5: number | null;
  next20: number | null;
  market: number | null;
  market20: number | null;
}

function at(dates: string[], iso: string): number {
  let lo = 0;
  let hi = dates.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (dates[mid] < iso) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

const change = (values: (number | null)[], from: number, to: number) => {
  const a = values[from];
  const b = values[to];
  return a != null && b != null && a > 0 && to < values.length ? b / a - 1 : null;
};

export function reactions(dates: string[], close: (number | null)[], filed: string[], market?: (number | null)[]): Reaction[] {
  const out: Reaction[] = [];
  for (const iso of filed) {
    const first = at(dates, iso);
    const before = first - 1;
    const after = dates[first] === iso ? first + 1 : first;
    if (before < 0 || after >= dates.length) continue;
    const move = change(close, before, after);
    if (move == null) continue;
    out.push({
      filed: iso,
      before: before,
      after: after,
      move,
      next5: after + 5 < dates.length ? change(close, after, after + 5) : null,
      next20: after + 20 < dates.length ? change(close, after, after + 20) : null,
      market: market ? change(market, before, after) : null,
      market20: market && after + 20 < dates.length ? change(market, after, after + 20) : null,
    });
  }
  return out;
}

const mean = (values: (number | null)[]) => {
  const known = values.filter((v): v is number => v != null);
  return known.length ? known.reduce((a, b) => a + b, 0) / known.length : null;
};

export function Reactions({ dates, close, filed, onPick }: { dates: string[]; close: (number | null)[]; filed: string[]; onPick: (iso: string) => void }) {
  const [spy, setSpy] = useState<(number | null)[] | null>(null);
  useEffect(() => {
    let live = true;
    closesOf("SPY").then((found) => live && found && setSpy(aligned(dates, found)));
    return () => {
      live = false;
    };
  }, [dates]);
  const rows = useMemo(() => reactions(dates, close, filed, spy ?? undefined), [dates, close, filed, spy]);
  if (!rows.length) return <p className="m-0 text-ink-2">No results 8-K with prices on both sides of it.</p>;
  const ups = rows.filter((r) => r.move > 0).length;
  const columns: Column<Reaction>[] = [
    { key: "filed", header: "Results filed", align: "left", strong: true, render: (r) => day(r.filed) },
    { key: "move", header: "Reaction", signed: true, strong: true, render: (r) => pct(r.move, 1) },
    { key: "market", header: "SPY those days", signed: true, muted: true, render: (r) => pct(r.market, 1) },
    { key: "excess", header: "Beyond SPY", signed: true, render: (r) => pct(r.market == null ? null : r.move - r.market, 1) },
    { key: "next5", header: "Next 5 sessions", signed: true, render: (r) => pct(r.next5, 1) },
    { key: "next20", header: "Next 20 sessions", signed: true, render: (r) => pct(r.next20, 1) },
    { key: "market20", header: "SPY next 20", signed: true, muted: true, render: (r) => pct(r.market20, 1) },
  ];
  const recent = rows.slice(-24);
  return (
    <Card
      title="How the stock met its results"
      aside={
        <CsvButton
          filename="results_reactions.csv"
          rows={rows}
          columns={[
            { header: "filed", value: (r) => r.filed },
            { header: "close_before", value: (r) => dates[r.before] },
            { header: "close_after", value: (r) => dates[r.after] },
            { header: "reaction", value: (r) => r.move },
            { header: "spy_reaction", value: (r) => r.market },
            { header: "next_5", value: (r) => r.next5 },
            { header: "next_20", value: (r) => r.next20 },
            { header: "spy_next_20", value: (r) => r.market20 },
          ]}
        />
      }
    >
      <p className="m-0 text-sm text-ink-2">
        Up after <span className="font-semibold text-ink">{ups}</span> of {rows.length} results. The typical move was{" "}
        <span className="font-semibold text-ink">{pct(median(rows.map((r) => Math.abs(r.move))), 1).replace("+", "±")}</span>, and the 20 sessions after it averaged{" "}
        <span className="font-semibold text-ink">{pct(mean(rows.map((r) => r.next20)), 1)}</span>
        {spy && <> against {pct(mean(rows.map((r) => r.market20)), 1)} for SPY</>}.
      </p>
      <BarChart
        title="Reaction to each results filing"
        labels={recent.map((r) => day(r.filed, true) + ` ’${r.filed.slice(2, 4)}`)}
        values={recent.map((r) => r.move)}
        format={(v) => pct(v, 0)}
        height={200}
        width={1000}
        labelEvery={recent.length > 12 ? 2 : 1}
      />
      <div className="-mx-5 max-h-[420px] overflow-auto">
        <DataTable columns={columns} rows={[...rows].reverse()} rowKey={(r) => r.filed} onRowClick={(r) => onPick(r.filed)} minWidth={820} />
      </div>
      <Note>
        The reaction runs from the close before the filing day to the close after it, so it covers a filing before the open, during the day or after the close. Prices split-adjusted, without
        dividends. Click a row to see it on the chart.
      </Note>
    </Card>
  );
}
