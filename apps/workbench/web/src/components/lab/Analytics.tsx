import { useMemo, useState } from "react";
import { diffLines, flatten, hunks } from "../../lib/diff";
import { dollars, int, money, num, pct, plainPct } from "../../lib/format";
import { type Equity, lab, type RunDetail, type Summary, type SweepRow } from "../../lib/lab";
import { NUMBERS } from "../../lib/labSettings";
import { useLoad } from "../../lib/useLoad";
import { BarChart } from "../charts/BarChart";
import { DivergingBars } from "../charts/DivergingBars";
import { LineChart } from "../charts/LineChart";
import { Panel, PanelNote } from "../ui/Panel";
import { Segmented } from "../ui/Segmented";

type BookView = "profit" | "drawdown" | "sharpe" | "positions";

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function filled(values: (number | null | undefined)[]): number[] {
  let last = 0;
  return values.map((v) => (v == null ? last : (last = v)));
}

export function BookPanel({ summary, equity }: { summary: Summary; equity: Equity | null }) {
  const [view, setView] = useState<BookView>("profit");
  const size = summary.settings?.book.position_size;
  const side = summary.settings?.entry.side ?? "long";
  const short = side === "short";
  const aside = (
    <Segmented
      label="Book view"
      value={view}
      onChange={setView}
      options={[
        { value: "profit", label: "Profit" },
        { value: "drawdown", label: "Drawdown" },
        { value: "sharpe", label: "Rolling Sharpe" },
        { value: "positions", label: "Positions" },
      ]}
    />
  );
  const title = `The book: ${summary.settings?.book.max_positions || "any number of"} positions of ${dollars(size)}`;
  if (!equity) {
    return (
      <Panel title={title} aside={aside}>
        <p className="m-0 px-4 py-6 text-ink-2">Loading the curve…</p>
      </Panel>
    );
  }
  const matched = equity.spy_matched ?? null;
  const invested = equity.positions.map((p) => Math.min(p * (size ?? 0), equity.capital));
  const average = invested.reduce((a, b) => a + b, 0) / Math.max(1, invested.length);
  return (
    <Panel title={title} aside={aside}>
      {view === "profit" && (
        <LineChart
          title="The book's profit beside SPY"
          labels={equity.dates}
          series={[
            { name: "The book", short: "Book", values: filled(equity.profit), color: "var(--series-1)" },
            ...(matched
              ? [
                  {
                    name: side === "both" ? "SPY at the book's net exposure" : short ? "SPY sold short with the money the book had at stake" : "SPY on the money the book had invested",
                    short: short ? "SPY short" : "SPY matched",
                    values: filled(matched),
                    color: "var(--series-4)",
                    dash: "2 3",
                  },
                ]
              : []),
            { name: "SPY on all the capital", short: "SPY all-in", values: filled(equity.spy), color: "var(--series-2)", dash: "5 4" },
          ]}
          format={(v) => money(v)}
        />
      )}
      {view === "sharpe" &&
        (equity.rolling_sharpe && equity.rolling_sharpe.some((v) => v != null) ? (
          <LineChart
            title="Sharpe over the year before each session"
            labels={equity.dates}
            series={[{ name: "Sharpe over the past year", short: "Sharpe", values: equity.rolling_sharpe, color: "var(--series-1)" }]}
            format={(v) => num(v, 2)}
          />
        ) : (
          <p className="m-0 px-4 py-6 text-ink-2">{equity.rolling_sharpe ? "The book has less than a year of sessions." : "Run again to see the rolling Sharpe."}</p>
        ))}
      {view === "drawdown" && (
        <LineChart
          title="How far the book was below its best"
          labels={equity.dates}
          series={[{ name: "Below the high", short: "Drawdown", values: filled(equity.drawdown), color: "var(--loss)" }]}
          format={(v) => money(v)}
        />
      )}
      {view === "positions" && (
        <LineChart
          title="Open positions"
          labels={equity.dates}
          series={
            side === "both" && equity.shorts
              ? [
                  { name: "Long", short: "Long", values: equity.positions.map((p, i) => p - (equity.shorts?.[i] ?? 0)), color: "var(--series-1)" },
                  { name: "Short", short: "Short", values: equity.shorts, color: "var(--series-2)", dash: "5 4" },
                ]
              : [{ name: "Open positions", short: "Positions", values: equity.positions, color: "var(--series-1)" }]
          }
          format={(v) => int(v)}
        />
      )}
      <PanelNote>
        {view === "profit" &&
          (matched
            ? side === "both"
              ? `Longs and shorts together: the dotted line holds SPY at the book's net exposure each day (long value less short value), so it shows how much of the profit the market's direction explains; the dashed line holds SPY with all the capital.`
              : short
                ? `The book was short ${dollars(average)} on average (${plainPct(average / equity.capital)} of ${dollars(equity.capital)}). The dotted line sells that much SPY short on the same days, so it is the fair comparison; the dashed line holds SPY with all the capital.`
                : `SPY on the same capital is fully invested every day; the book held ${dollars(average)} on average (${plainPct(average / equity.capital)} of ${dollars(equity.capital)}). The dotted line puts that money in SPY on the same days, so it is the fair comparison.`
            : "SPY is shown fully invested on the same capital. Run again to see it at the book's own exposure.")}
        {view === "profit" && summary.beta_spy != null && ` Beta to SPY ${num(summary.beta_spy, 2)}, correlation ${num(summary.correlation_spy ?? null, 2)} (daily, over the book's sessions).`}
        {view === "sharpe" && `The annualised Sharpe of the book's daily profit over the 252 sessions before each one; ${num(summary.sharpe ?? null, 2)} over the whole period.`}
        {view === "drawdown" && `Worst ${money(summary.max_drawdown)} (${pct(summary.max_drawdown_pct ?? null, 1)} of the capital), measured on each session's close.`}
        {view === "positions" && `${num(summary.average_positions ?? null, 1)} open on average, at most ${int(Math.max(0, ...equity.positions))}.`}
      </PanelNote>
    </Panel>
  );
}

interface MonthCell {
  value: number;
  partial: boolean;
}

export function monthReturns(equity: Equity): { year: number; months: (MonthCell | null)[]; total: number }[] {
  const last = new Map<string, number>();
  equity.dates.forEach((d, i) => {
    const v = equity.profit[i];
    if (v != null) last.set(d.slice(0, 7), v);
  });
  const keys = [...last.keys()].sort();
  const rows = new Map<number, { year: number; months: (MonthCell | null)[]; total: number }>();
  let previous = 0;
  keys.forEach((key, k) => {
    const [y, m] = key.split("-").map(Number);
    const value = (last.get(key)! - previous) / equity.capital;
    previous = last.get(key)!;
    const row = rows.get(y) ?? { year: y, months: new Array(12).fill(null), total: 0 };
    row.months[m - 1] = { value, partial: k === 0 || k === keys.length - 1 };
    row.total += value;
    rows.set(y, row);
  });
  return [...rows.values()].sort((a, b) => a.year - b.year);
}

function shade(value: number): string {
  const step = 12 + Math.round(Math.min(Math.abs(value) / 0.04, 1) * 4) * 14;
  return `color-mix(in srgb, var(${value >= 0 ? "--gain" : "--loss"}) ${step}%, var(--surface))`;
}

export function MonthTable({ equity }: { equity: Equity }) {
  const rows = monthReturns(equity);
  if (!rows.length) return null;
  return (
    <Panel title="By month" aside={`Profit as a share of the ${dollars(equity.capital)} capital`}>
      <table className="w-full min-w-[860px] border-collapse text-[12.5px] tabular-nums">
        <thead>
          <tr>
            <th scope="col" className="px-2 py-2 text-left font-medium text-ink-2">
              Year
            </th>
            {MONTH_NAMES.map((name) => (
              <th key={name} scope="col" className="px-1 py-2 text-right font-medium text-ink-2">
                {name}
              </th>
            ))}
            <th scope="col" className="px-2 py-2 text-right font-medium text-ink">
              Year
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.year} className="border-t border-line-soft">
              <th scope="row" className="px-2 py-1 text-left font-medium">
                {row.year}
              </th>
              {row.months.map((cell, m) => (
                <td key={m} className="px-0.5 py-0.5">
                  {cell ? (
                    <div title={cell.partial ? "Part of a month" : undefined} className={`rounded-sm px-1.5 py-1 text-right ${cell.partial ? "italic" : ""}`} style={{ background: shade(cell.value) }}>
                      {Math.abs(cell.value) < 0.0005 ? "0.0%" : pct(cell.value, 1)}
                    </div>
                  ) : (
                    <div className="px-1.5 py-1 text-right text-ink-3">·</div>
                  )}
                </td>
              ))}
              <td className={`px-2 py-1 text-right font-semibold ${row.total < 0 ? "text-neg" : ""}`}>{pct(row.total, 1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

export interface SectorRow {
  sector: string;
  trades: number;
  stocks: number;
  wins: number;
  net: number;
  profit: number;
}

export function bySector(stocks: { sector: string | null; trades: number; wins: number; total_net: number; profit: number }[]): SectorRow[] {
  const groups = new Map<string, SectorRow>();
  for (const s of stocks) {
    const name = s.sector || "Unknown";
    const row = groups.get(name) ?? { sector: name, trades: 0, stocks: 0, wins: 0, net: 0, profit: 0 };
    row.trades += s.trades;
    row.stocks += 1;
    row.wins += s.wins;
    row.net += s.total_net;
    row.profit += s.profit;
    groups.set(name, row);
  }
  return [...groups.values()].sort((a, b) => b.profit - a.profit);
}

export function SectorPanel({ rows, onSector }: { rows: SectorRow[]; onSector?: (sector: string) => void }) {
  if (rows.length < 2) return null;
  const trades = rows.reduce((a, r) => a + r.trades, 0);
  const top = rows.reduce((a, r) => (r.trades > a.trades ? r : a), rows[0]);
  return (
    <Panel title="By sector" aside="every trade, at the position size">
      <div className="grid gap-x-8 gap-y-3 px-4 py-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <DivergingBars items={rows.map((r) => ({ label: r.sector, value: r.profit, note: `${int(r.trades)} trades` }))} format={(v) => money(v)} onPick={onSector} />
        <table className="w-full border-collapse text-[13px] tabular-nums">
          <thead>
            <tr className="text-ink-2">
              <th className="pb-1.5 text-left font-medium">Sector</th>
              <th className="pb-1.5 text-right font-medium">Trades</th>
              <th className="pb-1.5 text-right font-medium">Share</th>
              <th className="pb-1.5 text-right font-medium">Won</th>
              <th className="pb-1.5 text-right font-medium">A trade</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.sector} className="border-t border-line-soft">
                <td className="max-w-[180px] truncate py-1 pr-2 text-ink">{r.sector}</td>
                <td className="py-1 text-right">{int(r.trades)}</td>
                <td className="py-1 text-right text-ink-2">{r.trades / Math.max(trades, 1) < 0.005 ? "<1%" : plainPct(r.trades / Math.max(trades, 1))}</td>
                <td className="py-1 text-right">{plainPct(r.wins / Math.max(r.trades, 1))}</td>
                <td className={`py-1 text-right ${r.net < 0 ? "text-neg" : ""}`}>{pct(r.net / Math.max(r.trades, 1))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PanelNote>
        {top.sector} had the most trades ({plainPct(top.trades / Math.max(trades, 1))} of them). A result that comes mostly from one sector may be a bet on that sector rather than on the rule.
      </PanelNote>
    </Panel>
  );
}

export function luckVerdict(beaten: number): string {
  if (beaten >= 0.975) return "better than almost every draw";
  if (beaten >= 0.9) return "better than most draws";
  if (beaten > 0.1) return "within what chance gives";
  return "worse than most draws";
}

export function LuckPanel({ runId }: { runId: string }) {
  const { data } = useLoad(() => lab.luck(runId), `luck-${runId}`);
  if (!data) return null;
  const rows = [
    { key: "same", label: "Random stocks the book could have bought, same days", draws: data.same_days },
    { key: "other", label: "The same stocks on random days of the period", draws: data.other_days },
  ].filter((r) => r.draws);
  return (
    <Panel title="Against random picks" aside={`${int(data.draws)} draws, each trade held ${data.hold} sessions`}>
      <div className="overflow-x-auto px-4 py-3">
        <table className="w-full min-w-[640px] border-collapse text-[13px] tabular-nums">
          <thead>
            <tr className="text-ink-2">
              <th className="pb-1.5 text-left font-medium">Picks</th>
              <th className="pb-1.5 pl-3 text-right font-medium">Their average</th>
              <th className="pb-1.5 pl-3 text-right font-medium">95% of draws</th>
              <th className="pb-1.5 pl-3 text-right font-medium">This run</th>
              <th className="pb-1.5 pl-3 text-left font-medium">The run is</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.key} className="border-t border-line-soft">
                <td className="py-2 pr-3 text-ink">{r.label}</td>
                <td className={`py-2 pl-3 text-right ${r.draws!.mean < 0 ? "text-neg" : ""}`}>{pct(r.draws!.mean)}</td>
                <td className="py-2 pl-3 text-right text-ink-2">
                  {pct(r.draws!.low)} to {pct(r.draws!.high)}
                </td>
                <td className={`py-2 pl-3 text-right font-semibold ${data.mean < 0 ? "text-neg" : ""}`}>{pct(data.mean)}</td>
                <td className="py-2 pl-3">
                  {luckVerdict(r.draws!.beaten)} ({plainPct(r.draws!.beaten)})
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PanelNote>
        Every trade and every random pick is held the same way: from the next open to the close {data.hold} sessions later, before costs, without stops, targets or exit signals
        {data.of && data.of > data.trades ? `, on ${int(data.trades)} of the ${int(data.of)} trades picked at random` : ""}. Beating random stocks on the same days says the rule picks stocks; beating
        the same stocks on other days says it picks moments.
      </PanelNote>
    </Panel>
  );
}

export function SignalPathPanel({ runId, short = false }: { runId: string; short?: boolean }) {
  const { data, error } = useLoad(() => lab.path(runId), `path-${runId}`);
  const [around, setAround] = useState(false);
  if (error || !data) return null;
  const start = around ? 0 : Math.max(0, data.horizons.indexOf(0));
  const cut = <T,>(values: T[]) => values.slice(start);
  const horizons = cut(data.horizons);
  const exit = horizons.indexOf(data.hold);
  const labels = horizons.map((h) => (h > 0 ? `+${h}` : String(h)));
  const at = (values: (number | null)[], h: number) => values[data.horizons.indexOf(h)] ?? null;
  return (
    <Panel
      title="After the signal"
      aside={
        <Segmented
          label="Sessions shown"
          value={around ? "around" : "after"}
          onChange={(v) => setAround(v === "around")}
          options={[
            { value: "after", label: "After it" },
            { value: "around", label: "From 20 before" },
          ]}
        />
      }
    >
      <LineChart
        title="The average move of the traded stocks around the signal"
        labels={labels}
        labelAt={(i) => horizons[i] % 10 === 0}
        marks={[...(around ? [{ i: horizons.indexOf(0), label: "signal" }] : []), ...(exit >= 0 ? [{ i: exit, label: "exit" }] : [])]}
        series={[
          { name: "Over the universe", short: "Excess", values: filled(cut(data.excess)), color: "var(--series-1)" },
          { name: "The stocks", short: "Stocks", values: filled(cut(data.stock)), color: "var(--series-2)", dash: "5 4" },
          { name: "The universe", short: "Universe", values: filled(cut(data.universe)), color: "var(--series-3)", dash: "2 3" },
        ]}
        band={{ low: filled(cut(data.low)), high: filled(cut(data.high)), color: "var(--series-1)" }}
        format={(v) => pct(v, 1)}
        height={280}
      />
      <PanelNote>
        {short ? "Moves are as held: a short's line rises when its price falls. " : ""}
        {int(data.trades)} trades{data.trades < data.of ? ` of ${int(data.of)}` : ""}, split-adjusted, measured in sessions from the close of the signal day, so the next open is not yet paid. Over the
        universe at the exit: {pct(at(data.excess, data.hold), 2)}; ten sessions later {pct(at(data.excess, data.hold + 10), 2)}. The band is 95% around the average. A line still rising at the exit
        says a longer hold had more to give; a line that peaks before it says the hold is too long.
      </PanelNote>
    </Panel>
  );
}

const METRICS: { label: string; value: (s: Summary) => number | null | undefined; text: (v: number | null | undefined) => string; diff: (a: number, b: number) => string }[] = [
  { label: "Trades", value: (s) => s.trades, text: int, diff: (a, b) => int(a - b) },
  { label: "A trade after costs", value: (s) => s.mean_net, text: (v) => pct(v), diff: (a, b) => pct(a - b) },
  { label: "At 2× costs", value: (s) => s.mean_net_2x, text: (v) => pct(v), diff: (a, b) => pct(a - b) },
  { label: "Won", value: (s) => s.win_rate, text: (v) => plainPct(v), diff: (a, b) => pct(a - b, 0) },
  { label: "Weekly t", value: (s) => s.t_weekly, text: (v) => num(v ?? null), diff: (a, b) => num(a - b) },
  { label: "Book profit", value: (s) => s.book_profit, text: (v) => money(v), diff: (a, b) => money(a - b) },
  { label: "A year", value: (s) => s.annual_return, text: (v) => pct(v ?? null, 1), diff: (a, b) => pct(a - b, 1) },
  { label: "Sharpe", value: (s) => s.sharpe, text: (v) => num(v ?? null), diff: (a, b) => num(a - b) },
  { label: "Worst drawdown", value: (s) => s.max_drawdown, text: (v) => money(v), diff: (a, b) => money(a - b) },
  { label: "Average positions", value: (s) => s.average_positions, text: (v) => num(v ?? null, 1), diff: (a, b) => num(a - b, 1) },
  { label: "Signals", value: (s) => s.signals, text: int, diff: (a, b) => int(a - b) },
];

function overlay(a: Equity, b: Equity) {
  const dates = [...new Set([...a.dates, ...b.dates])].sort();
  const along = (e: Equity) => {
    const at = new Map(e.dates.map((d, i) => [d, e.profit[i]]));
    let last = 0;
    return dates.map((d) => (at.has(d) && at.get(d) != null ? (last = at.get(d) as number) : last));
  };
  return { dates, a: along(a), b: along(b) };
}

export interface CompareRun {
  run_id: string;
  label: string;
}

export function Compare({ detail, runs }: { detail: RunDetail; runs: CompareRun[] }) {
  const others = runs.filter((r) => r.run_id !== detail.run_id);
  const [other, setOther] = useState(others[0]?.run_id ?? "");
  const { data: them } = useLoad(() => (other ? lab.run(other) : Promise.resolve(null)), `cmp-run-${other}`);
  const { data: mine } = useLoad(() => lab.equity(detail.run_id), `cmp-eq-${detail.run_id}`);
  const { data: theirs } = useLoad(() => (other ? lab.equity(other) : Promise.resolve(null)), `cmp-eq-${other}`);
  const { data: codeA } = useLoad(() => lab.code(detail.run_id), `cmp-code-${detail.run_id}`);
  const { data: codeB } = useLoad(() => (other ? lab.code(other) : Promise.resolve(null)), `cmp-code-${other}`);
  const a = detail.summary;
  const b = them?.summary ?? null;
  const settings = useMemo(() => {
    if (!a?.settings || !b?.settings) return [];
    const left = flatten(a.settings);
    const right = flatten(b.settings);
    return [...new Set([...Object.keys(left), ...Object.keys(right)])].filter((k) => left[k] !== right[k]).map((k) => ({ key: k, a: left[k] ?? "–", b: right[k] ?? "–" }));
  }, [a, b]);
  const diff = useMemo(() => (codeA && codeB ? hunks(diffLines(codeB.code, codeA.code)) : null), [codeA, codeB]);
  const label = (id: string) => runs.find((r) => r.run_id === id)?.label ?? id;
  if (!others.length) return <Panel padded>Run the algorithm again with other settings or code to compare two runs.</Panel>;
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="font-medium">{label(detail.run_id)}</span>
        <span className="text-ink-3">against</span>
        <select
          aria-label="Run to compare with"
          value={other}
          onChange={(e) => setOther(e.target.value)}
          className="h-8 max-w-[360px] rounded-md border border-line bg-surface px-2 text-[13px] text-ink focus-visible:outline-2 focus-visible:outline-accent"
        >
          {others.map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.label}
            </option>
          ))}
        </select>
      </div>
      {!a || !b ? (
        <Panel padded>{them && !them.summary ? "That run has no results to compare." : "Loading…"}</Panel>
      ) : (
        <>
          <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
            <Panel title="Side by side">
              <table className="w-full border-collapse text-sm tabular-nums">
                <thead>
                  <tr className="text-[13px] text-ink-2">
                    <th scope="col" className="px-4 py-2 text-left font-medium" />
                    <th scope="col" className="px-3 py-2 text-right font-medium">
                      This run
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-medium">
                      The other
                    </th>
                    <th scope="col" className="px-4 py-2 text-right font-medium">
                      Difference
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {METRICS.map((m) => {
                    const x = m.value(a);
                    const y = m.value(b);
                    const d = x != null && y != null ? m.diff(x, y) : "–";
                    return (
                      <tr key={m.label} className="border-t border-line-soft">
                        <th scope="row" className="px-4 py-1.5 text-left font-normal text-ink-2">
                          {m.label}
                        </th>
                        <td className="px-3 py-1.5 text-right font-semibold">{m.text(x)}</td>
                        <td className="px-3 py-1.5 text-right">{m.text(y)}</td>
                        <td className={`px-4 py-1.5 text-right ${d.startsWith("−") ? "text-neg" : "text-ink-2"}`}>{d}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>
            <Panel title="Settings that differ" aside={a.period_label === b.period_label ? a.period_label : undefined}>
              {settings.length ? (
                <table className="w-full border-collapse text-sm">
                  <tbody>
                    {settings.map((s) => (
                      <tr key={s.key} className="border-t border-line-soft first:border-t-0">
                        <th scope="row" className="px-4 py-1.5 text-left font-mono text-[12.5px] font-normal text-ink-2">
                          {s.key}
                        </th>
                        <td className="px-3 py-1.5 text-right font-semibold">{s.a}</td>
                        <td className="px-4 py-1.5 text-right text-ink-2">{s.b}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <PanelNote>The same settings.</PanelNote>
              )}
            </Panel>
          </div>
          {mine && theirs && (
            <Panel title="Profit, both runs">
              {(() => {
                const both = overlay(mine, theirs);
                return (
                  <LineChart
                    title="Both runs' book profit"
                    labels={both.dates}
                    series={[
                      { name: "This run", short: "This", values: both.a, color: "var(--series-1)" },
                      { name: "The other", short: "Other", values: both.b, color: "var(--series-2)", dash: "5 4" },
                    ]}
                    format={(v) => money(v)}
                  />
                );
              })()}
            </Panel>
          )}
          <Panel title="Code" aside={diff && diff.length ? "what changed from the other run to this one" : undefined}>
            {!diff ? (
              <PanelNote>Loading…</PanelNote>
            ) : diff.length === 0 ? (
              <PanelNote>The same code.</PanelNote>
            ) : (
              <pre className="m-0 overflow-x-auto py-2 font-mono text-[12.5px] leading-relaxed">
                {diff.map((line, k) =>
                  line === null ? (
                    <div key={k} className="px-4 text-ink-3">
                      ⋯
                    </div>
                  ) : (
                    <div
                      key={k}
                      className={`flex px-4 ${line.kind === "added" ? "bg-[color-mix(in_srgb,var(--gain)_14%,transparent)]" : line.kind === "removed" ? "bg-[color-mix(in_srgb,var(--loss)_14%,transparent)]" : ""}`}
                    >
                      <span className="w-6 shrink-0 text-ink-3 select-none">{line.kind === "added" ? "+" : line.kind === "removed" ? "−" : ""}</span>
                      <span className="whitespace-pre">{line.text}</span>
                    </div>
                  ),
                )}
              </pre>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}

export function FactorPanel({ runId }: { runId: string }) {
  const { data, error } = useLoad(() => lab.factor(runId), `factor-${runId}`);
  if (error || !data) return null;
  const top = data.order === "highest" ? data.buckets.length - 1 : 0;
  const ic = data.ic;
  return (
    <Panel title="How the scores sorted the stocks" aside={`Tenths by score, ${data.hold}-session return from the next open, before costs`}>
      <div className="grid gap-x-8 gap-y-3 px-4 pt-3 sm:grid-cols-4">
        {[
          ["Top tenth over bottom", pct(data.spread, 2), data.order === "highest" ? "highest scores less lowest" : "lowest scores less highest"],
          ["Rank correlation (IC)", num(ic.mean, 3), `${plainPct(ic.positive)} of days above zero`],
          ["IC t-stat", num(ic.t, 2), `on ${int(ic.independent_days)} days ${data.hold} sessions apart`],
          ["Days measured", int(ic.days), "with 30 or more scored stocks"],
        ].map(([label, value, note]) => (
          <div key={label}>
            <div className="text-[13px] text-ink-2">{label}</div>
            <div className={`text-xl font-semibold tracking-tight ${value.startsWith("−") ? "text-neg" : ""}`}>{value}</div>
            <div className="text-[12px] text-ink-3">{note}</div>
          </div>
        ))}
      </div>
      <div className="grid gap-5 px-1 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <BarChart
          title="Average return over the day's average, by tenth of the scores"
          labels={data.buckets.map((b) => (b.bucket === 1 ? "1 low" : b.bucket === data.buckets.length ? `${b.bucket} high` : String(b.bucket)))}
          values={data.buckets.map((b) => b.excess)}
          marked={[top]}
          format={(v) => pct(v, 2)}
        />
        <BarChart title="IC by year" labels={data.ic_by_year.map((y) => String(y.year))} values={data.ic_by_year.map((y) => y.mean)} format={(v) => num(v, 2)} width={480} height={240} />
      </div>
      <PanelNote>
        Each day the stocks the book could have taken are split into tenths by score; the bold tenth is the end the book takes. A ranking that works rises steadily from one end to the other and keeps
        its IC above zero in most years. The IC t-stat uses days {data.hold} sessions apart so the returns do not overlap.
      </PanelNote>
    </Panel>
  );
}

type SweepMetric = "mean_net" | "book_profit" | "sharpe" | "max_drawdown";

const SWEEP_METRICS: { value: SweepMetric; label: string; format: (v: number) => string }[] = [
  { value: "mean_net", label: "A trade", format: (v) => pct(v, 2) },
  { value: "book_profit", label: "Book profit", format: (v) => money(v) },
  { value: "sharpe", label: "Sharpe", format: (v) => num(v, 2) },
  { value: "max_drawdown", label: "Drawdown", format: (v) => money(v) },
];

export function sweepValue(field: string, value: number | null): string {
  const spec = NUMBERS.find((s) => s.path === field);
  if (value == null) return "none";
  if (!spec) return String(value);
  const shownValue = Math.round((value / spec.scale) * 1e6) / 1e6;
  return spec.unit === "%" ? `${shownValue}%` : spec.unit === "sessions" ? `${shownValue} days` : String(shownValue);
}

export function SweepPanel({ runId }: { runId: string }) {
  const { data, error } = useLoad(() => lab.sweep(runId), `sweep-${runId}`);
  const [metric, setMetric] = useState<SweepMetric>("mean_net");
  if (error || !data) return null;
  const spec = NUMBERS.find((s) => s.path === data.field);
  const chosen = SWEEP_METRICS.find((m) => m.value === metric) ?? SWEEP_METRICS[0];
  const label = (row: SweepRow) => sweepValue(data.field, row.value);
  const base = data.rows.findIndex((r) => r.value === data.base);
  return (
    <Panel
      title={`Sweep: ${spec?.label ?? data.field}`}
      aside={<Segmented label="Measure" value={metric} onChange={setMetric} options={SWEEP_METRICS.map(({ value, label: text }) => ({ value, label: text }))} />}
    >
      <div className="px-1">
        <BarChart
          title={`${chosen.label} by ${spec?.label ?? data.field}`}
          labels={data.rows.map(label)}
          values={data.rows.map((r) => r[metric] ?? null)}
          format={chosen.format}
          marked={base >= 0 ? [base] : []}
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-sm tabular-nums">
          <thead>
            <tr className="text-[13px] text-ink-2">
              {[spec?.label ?? data.field, "Trades", "A trade", "At 2× costs", "Won", "Weekly t", "Book profit", "A year", "Sharpe", "Drawdown"].map((h, i) => (
                <th key={h} scope="col" className={`border-t border-line px-3 py-2 font-medium ${i ? "text-right" : "text-left"}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={label(r)} className={`border-t border-line-soft ${i === base ? "bg-raised font-semibold" : ""}`}>
                <th scope="row" className="px-3 py-1.5 text-left font-medium">
                  {label(r)}
                  {i === base ? " (this run)" : ""}
                </th>
                <td className="px-3 py-1.5 text-right">{int(r.trades)}</td>
                <td className={`px-3 py-1.5 text-right ${(r.mean_net ?? 0) < 0 ? "text-neg" : ""}`}>{pct(r.mean_net)}</td>
                <td className={`px-3 py-1.5 text-right ${(r.mean_net_2x ?? 0) < 0 ? "text-neg" : ""}`}>{pct(r.mean_net_2x)}</td>
                <td className="px-3 py-1.5 text-right">{plainPct(r.win_rate)}</td>
                <td className="px-3 py-1.5 text-right">{num(r.t_weekly)}</td>
                <td className={`px-3 py-1.5 text-right ${(r.book_profit ?? 0) < 0 ? "text-neg" : ""}`}>{money(r.book_profit)}</td>
                <td className="px-3 py-1.5 text-right">{pct(r.annual_return, 1)}</td>
                <td className="px-3 py-1.5 text-right">{num(r.sharpe)}</td>
                <td className="px-3 py-1.5 text-right">{money(r.max_drawdown)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PanelNote>
        Every value ran on the same signals and the same costs; only {spec?.label.toLowerCase() ?? data.field} changed. Each counts as a trial, so the best of them is less trustworthy than any one
        alone: prefer a setting whose neighbours do nearly as well.
      </PanelNote>
    </Panel>
  );
}
