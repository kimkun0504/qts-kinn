import { useEffect, useMemo, useState } from "react";
import { BarChart } from "../components/charts/BarChart";
import { LineChart, type Series } from "../components/charts/LineChart";
import { Correlation } from "../components/charts/Correlation";
import { aligned, closesOf, rebase } from "../components/RelativeChart";
import { Card, Note } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import { StatStrip } from "../components/ui/StatStrip";
import { api, type ClosesData, type MarketRow } from "../lib/api";
import { day, int, isNegative, pct, plainPct, price } from "../lib/format";
import { useLoad } from "../lib/useLoad";

type Closes = ClosesData["series"][number];
type Range = "month" | "quarter" | "ytd" | "year" | "three";

const RANGES: { value: Range; label: string; sessions: number }[] = [
  { value: "month", label: "1M", sessions: 21 },
  { value: "quarter", label: "3M", sessions: 63 },
  { value: "ytd", label: "YTD", sessions: 0 },
  { value: "year", label: "1Y", sessions: 252 },
  { value: "three", label: "3Y", sessions: 756 },
];
const SLOTS: { color: string; dash?: string }[] = [{ color: "var(--series-1)" }, { color: "var(--series-4)" }, { color: "var(--series-3)" }, { color: "var(--series-2)", dash: "6 4" }];
const SPANS: { key: keyof MarketRow; header: string }[] = [
  { key: "day", header: "Day" },
  { key: "week", header: "Week" },
  { key: "month", header: "Month" },
  { key: "quarter", header: "3 months" },
  { key: "year_to_date", header: "Year to date" },
  { key: "year", header: "Year" },
  { key: "three_years", header: "3 years" },
];

interface Picked {
  symbol: string;
  slot: number;
}

export function startOf(dates: string[], range: Range): number {
  if (!dates.length) return 0;
  if (range === "ytd") {
    const year = dates[dates.length - 1].slice(0, 4);
    const first = dates.findIndex((d) => d.startsWith(year));
    return Math.max(0, first - 1);
  }
  const sessions = RANGES.find((r) => r.value === range)?.sessions ?? 252;
  return Math.max(0, dates.length - 1 - sessions);
}

function ticks(dates: string[]): { at: (i: number) => boolean; text: (i: number) => string } {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const long = dates.length > 400;
  return {
    at: (i) => i > 0 && (long ? dates[i].slice(0, 4) !== dates[i - 1].slice(0, 4) : dates[i].slice(5, 7) !== dates[i - 1].slice(5, 7)),
    text: (i) => (long || dates[i].slice(5, 7) === "01" ? dates[i].slice(0, 4) : months[Number(dates[i].slice(5, 7)) - 1]),
  };
}

function Chart({ picked, range, onRange }: { picked: Picked[]; range: Range; onRange: (r: Range) => void }) {
  const [series, setSeries] = useState<Record<string, Closes | null>>({});
  const wanted = picked.map((p) => p.symbol).join(",");
  useEffect(() => {
    let live = true;
    Promise.all(
      wanted
        .split(",")
        .filter(Boolean)
        .map(async (s) => [s, await closesOf(s)] as const),
    ).then((found) => live && setSeries(Object.fromEntries(found)));
    return () => {
      live = false;
    };
  }, [wanted]);
  const chart = useMemo(() => {
    const base = series.SPY ?? Object.values(series).find(Boolean);
    if (!base) return null;
    const from = startOf(base.date, range);
    const dates = base.date.slice(from);
    const ready = picked.filter((p) => series[p.symbol]);
    const based = rebase(ready.map((p) => aligned(dates, series[p.symbol] as Closes)));
    if (!based) return null;
    const lines: Series[] = ready.map((p, i) => ({ name: p.symbol, values: based.values[i], color: SLOTS[p.slot].color, dash: SLOTS[p.slot].dash }));
    return { lines, dates: dates.slice(based.start) };
  }, [series, picked, range]);
  const t = chart ? ticks(chart.dates) : null;
  return (
    <Card
      title={chart ? `Change since ${day(chart.dates[0])}` : "Change"}
      aside={<Segmented label="Range" value={range} onChange={onRange} options={RANGES.map((r) => ({ value: r.value, label: r.label }))} />}
    >
      {chart && t ? (
        <LineChart
          title={`${picked.map((p) => p.symbol).join(", ")} over the range`}
          labels={chart.dates.map((d) => day(d))}
          series={chart.lines}
          format={(v) => pct(v, 1)}
          labelAt={t.at}
          tickText={t.text}
          height={300}
          width={1100}
        />
      ) : (
        <p className="m-0 text-ink-2">Loading the prices…</p>
      )}
      <Note>Click a fund in the tables below to add it to the chart or take it off; four at most. Funds as traded, without dividends.</Note>
    </Card>
  );
}

function Breadth({ rows }: { rows: { date: string; advancing: number; declining: number; traded: number }[] }) {
  if (!rows.length) return null;
  const last = rows[rows.length - 1];
  const recent = rows.slice(-60);
  let total = 0;
  const line = rows.map((r) => (total += r.advancing - r.declining));
  const t = ticks(rows.map((r) => r.date));
  return (
    <Card title="US common stocks rising and falling">
      <StatStrip
        items={[
          { label: `Rose on ${day(last.date)}`, value: int(last.advancing), note: `${plainPct(last.advancing / last.traded)} of ${int(last.traded)} that traded` },
          { label: "Fell", value: int(last.declining), note: plainPct(last.declining / last.traded) },
          {
            label: "Rising, last 20 sessions",
            value: plainPct(
              rows.slice(-20).reduce((s, r) => s + r.advancing, 0) /
                Math.max(
                  1,
                  rows.slice(-20).reduce((s, r) => s + r.traded, 0),
                ),
            ),
            note: "share of stock-days",
          },
        ]}
      />
      <div className="text-[13px] font-medium text-ink">Rose minus fell, each of the last 60 sessions</div>
      <BarChart
        title="Advancing minus declining stocks"
        labels={recent.map((r) => day(r.date, true))}
        values={recent.map((r) => r.advancing - r.declining)}
        format={(v) => int(v)}
        height={180}
        width={1100}
        labelEvery={10}
      />
      <div className="text-[13px] font-medium text-ink">The running total since {day(rows[0].date)}</div>
      <LineChart
        title="Cumulative advancing minus declining"
        labels={rows.map((r) => day(r.date))}
        series={[{ name: "Rose minus fell, added up", short: "Total", values: line, color: "var(--series-1)" }]}
        format={(v) => int(v)}
        labelAt={t.at}
        tickText={t.text}
        height={220}
        width={1100}
      />
      <Note>Stocks in the research data that closed above or below their previous close, split-adjusted. A running total that falls while the index rises says fewer stocks carry the rise.</Note>
    </Card>
  );
}

export function MarketsPage() {
  const { data, error } = useLoad(() => api.markets(), "markets");
  const [picked, setPicked] = useState<Picked[]>([
    { symbol: "SPY", slot: 0 },
    { symbol: "QQQ", slot: 1 },
    { symbol: "IWM", slot: 2 },
  ]);
  const [range, setRange] = useState<Range>("year");
  if (error) return <EmptyState title="Could not read the markets">The Workbench server needs a restart after an update.</EmptyState>;
  if (!data) return <p className="text-ink-2">Reading the markets…</p>;
  const toggle = (symbol: string) =>
    setPicked((current) => {
      if (current.some((p) => p.symbol === symbol)) return current.length > 1 ? current.filter((p) => p.symbol !== symbol) : current;
      const free = SLOTS.findIndex((_, i) => !current.some((p) => p.slot === i));
      return free >= 0 ? [...current, { symbol, slot: free }] : [...current.slice(1), { symbol, slot: current[0].slot }];
    });
  return (
    <div className="flex flex-col gap-4">
      <StatStrip
        items={data.groups[0].rows
          .filter((r) => ["SPY", "QQQ", "IWM"].includes(r.symbol))
          .map((r) => ({ label: `${r.symbol}, ${r.name}`, value: pct(r.day, 2), note: `${price(r.close)} on ${day(data.on)}` }))
          .concat(
            data.breadth.length
              ? [
                  {
                    label: "US stocks that rose",
                    value: plainPct(data.breadth[data.breadth.length - 1].advancing / data.breadth[data.breadth.length - 1].traded),
                    note: `${int(data.breadth[data.breadth.length - 1].advancing)} of ${int(data.breadth[data.breadth.length - 1].traded)}`,
                  },
                ]
              : [],
          )}
      />
      <Chart picked={picked} range={range} onRange={setRange} />
      <Panel title={`Funds on ${day(data.on)}`}>
        <table className="w-full min-w-[900px] border-collapse">
          <thead>
            <tr>
              {["Fund", "", "Close", ...SPANS.map((s) => s.header)].map((header, i) => (
                <th
                  key={i}
                  scope="col"
                  className={`sticky top-0 z-[1] border-b border-line bg-surface px-3 py-2 text-[13px] font-medium whitespace-nowrap text-ink-2 ${i < 2 ? "text-left" : "text-right"}`}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          {data.groups.map((g) => (
            <tbody key={g.title}>
              <tr>
                <th colSpan={3 + SPANS.length} scope="colgroup" className="border-b border-line bg-raised px-3 pt-3 pb-1.5 text-left text-[13px] font-semibold text-ink-2">
                  {g.title}
                </th>
              </tr>
              {g.rows.map((r) => {
                const on = picked.find((p) => p.symbol === r.symbol);
                return (
                  <tr
                    key={r.symbol}
                    tabIndex={r.close == null ? undefined : 0}
                    aria-selected={r.close == null ? undefined : Boolean(on)}
                    onClick={() => r.close != null && toggle(r.symbol)}
                    onKeyDown={(event) => event.key === "Enter" && r.close != null && toggle(r.symbol)}
                    className={r.close == null ? "" : "cursor-pointer hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent"}
                  >
                    <td className="border-b border-line-soft px-3 py-2 text-sm whitespace-nowrap">
                      <span className="inline-flex items-center gap-2 font-semibold">
                        <svg aria-hidden="true" width="14" height="4">
                          <line x1="0" x2="14" y1="2" y2="2" stroke={on ? SLOTS[on.slot].color : "transparent"} strokeWidth="3" strokeDasharray={on ? SLOTS[on.slot].dash : undefined} />
                        </svg>
                        {r.symbol}
                      </span>
                    </td>
                    <td className="border-b border-line-soft px-3 py-2 text-sm whitespace-nowrap text-ink-2">{r.name}</td>
                    <td className="border-b border-line-soft px-3 py-2 text-right text-sm whitespace-nowrap">{price(r.close)}</td>
                    {SPANS.map((s) => {
                      const text = pct(r[s.key] as number | null | undefined, 1);
                      return (
                        <td
                          key={s.key}
                          className={`border-b border-line-soft px-3 py-2 text-right text-sm whitespace-nowrap ${isNegative(text) ? "text-neg" : ""} ${s.key === "day" ? "font-semibold" : ""}`}
                        >
                          {text}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          ))}
        </table>
      </Panel>
      {data.correlation && data.correlation.symbols.length > 1 && (
        <Card title={`How the funds moved together, last ${data.correlation.sessions} sessions`}>
          <Correlation symbols={data.correlation.symbols} matrix={data.correlation.matrix} names={Object.fromEntries(data.groups.flatMap((g) => g.rows.map((r) => [r.symbol, r.name])))} />
          <Note>Correlation of daily changes: 1 moves together, 0 unrelated, −1 opposite. Blue is together, red opposite.</Note>
        </Card>
      )}
      <Breadth rows={data.breadth} />
    </div>
  );
}
