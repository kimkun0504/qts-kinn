import { useEffect, useMemo, useState } from "react";
import { isLive, lab, type RunDetail, type RunListRow, type RunState, type StockRow, type TradePage, type TradeRow, type YearRow } from "../../lib/lab";
import { day, dollars, int, money, num, pct, plainPct } from "../../lib/format";
import { useLoad } from "../../lib/useLoad";
import { Histogram } from "../charts/Histogram";
import { YearBars } from "../charts/YearBars";
import { StockLink } from "../StockLink";
import { CodeEditor } from "../CodeEditor";
import { Badge, type Tone } from "../ui/Badge";
import { Button } from "../ui/Button";
import { type Column, DataTable, type Sort } from "../ui/DataTable";
import { Panel } from "../ui/Panel";
import { Segmented } from "../ui/Segmented";
import { StatStrip } from "../ui/StatStrip";
import { BookPanel, bySector, Compare, FactorPanel, LuckPanel, MonthTable, SectorPanel, SignalPathPanel, SweepPanel } from "./Analytics";
import { RunNote } from "./RunNote";

type Tab = "overview" | "stocks" | "trades" | "years" | "code";

const field = "min-h-8 rounded-md border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-ink-3 focus-visible:outline-2 focus-visible:outline-accent";

const stockColumns: Column<StockRow>[] = [
  { key: "ticker", header: "Stock", align: "left", sortable: true, render: (r) => <StockLink symbol={r.ticker} on={r.last_entry} /> },
  { key: "name", header: "Company", align: "left", muted: true, max: 220, sortable: true, render: (r) => r.name ?? "–" },
  { key: "sector", header: "Sector", align: "left", muted: true, max: 160, sortable: true, render: (r) => r.sector ?? "–" },
  { key: "trades", header: "Trades", sortable: true, render: (r) => int(r.trades) },
  { key: "win_rate", header: "Won", sortable: true, render: (r) => plainPct(r.win_rate) },
  { key: "mean_net", header: "A trade", signed: true, sortable: true, render: (r) => pct(r.mean_net) },
  { key: "mean_over", header: "Vs universe", signed: true, sortable: true, render: (r) => pct(r.mean_over) },
  { key: "profit", header: "Profit", signed: true, strong: true, sortable: true, render: (r) => money(r.profit) },
  { key: "book_profit", header: "In the book", signed: true, sortable: true, render: (r) => (r.book_trades ? money(r.book_profit) : "–") },
  { key: "best", header: "Best", signed: true, sortable: true, render: (r) => pct(r.best, 1) },
  { key: "worst", header: "Worst", signed: true, sortable: true, render: (r) => pct(r.worst, 1) },
  { key: "last_entry", header: "Last entry", muted: true, sortable: true, render: (r) => day(r.last_entry) },
];

const tradeColumns = (side: string): Column<TradeRow>[] => [
  { key: "ticker", header: "Stock", align: "left", sortable: true, render: (r) => <StockLink symbol={r.ticker} on={r.entry_date} /> },
  { key: "signal_date", header: "Signal", muted: true, sortable: true, render: (r) => day(r.signal_date) },
  ...(side === "both" ? [{ key: "side", header: "Side", align: "left" as const, sortable: true, render: (r: TradeRow) => (r.side === "short" ? "short" : "long") }] : []),
  { key: "entry_date", header: { short: "Shorted", both: "Opened" }[side] ?? "Bought", sortable: true, render: (r) => day(r.entry_date) },
  { key: "exit_date", header: { short: "Covered", both: "Closed" }[side] ?? "Sold", sortable: true, render: (r) => day(r.exit_date) },
  { key: "sessions", header: "Sessions", sortable: true, render: (r) => int(r.sessions) },
  { key: "reason", header: "Exit", align: "left", muted: true, sortable: true, render: (r) => r.reason },
  { key: "entry_price", header: { short: "Short price", both: "Open price" }[side] ?? "Buy price", render: (r) => num(r.entry_price) },
  { key: "exit_price", header: { short: "Cover price", both: "Close price" }[side] ?? "Sell price", render: (r) => num(r.exit_price) },
  { key: "gross", header: "Before costs", signed: true, sortable: true, render: (r) => pct(r.gross) },
  { key: "net", header: "After costs", signed: true, strong: true, sortable: true, render: (r) => pct(r.net) },
  { key: "net_2x", header: "2× costs", signed: true, sortable: true, render: (r) => pct(r.net_2x) },
  { key: "over", header: "Vs universe", signed: true, sortable: true, render: (r) => pct(r.over) },
  { key: "profit", header: "Profit", signed: true, sortable: true, render: (r) => money(r.profit) },
  { key: "taken", header: "Book", align: "left", render: (r) => (r.taken ? "took" : "skipped") },
];

function compare(a: unknown, b: unknown): number {
  if (a == null) return b == null ? 0 : 1;
  if (b == null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b));
}

function Overview({ detail, stocks, onStock, onAllStocks }: { detail: RunDetail; stocks: StockRow[] | null; onStock: (ticker: string) => void; onAllStocks: () => void }) {
  const s = detail.summary!;
  const { data: equity } = useLoad(() => lab.equity(detail.run_id), `equity-${detail.run_id}`);
  if (!s.trades) return <Panel padded>The algorithm made no trades in this period with these settings.</Panel>;
  const best = (stocks ?? []).slice(0, 8);
  const worst = (stocks ?? [])
    .slice(-8)
    .reverse()
    .filter((row) => !best.includes(row));
  const small: Column<StockRow>[] = [stockColumns[0], stockColumns[3], stockColumns[4], stockColumns[5], stockColumns[7]];
  const exits = Object.entries(s.exits ?? {}).sort((a, b) => b[1] - a[1]);
  return (
    <div className="flex flex-col gap-5">
      <StatStrip
        items={[
          { label: "Trades", value: int(s.trades), note: `${int(s.stocks)} stocks; the book took ${int(s.taken)}` },
          { label: "A trade after costs", value: pct(s.mean_net), note: `median ${pct(s.median_net)}; at 2× costs ${pct(s.mean_net_2x)}` },
          { label: "Won", value: plainPct(s.win_rate), note: `${s.years_positive} of ${s.years} years up` },
          { label: "Weekly t", value: num(s.t_weekly ?? null), note: `vs the universe ${num(s.t_weekly_over ?? null)}` },
          { label: "Book profit", value: money(s.book_profit), note: `${pct(s.annual_return ?? null, 1)} a year on ${dollars(s.capital)}; Sharpe ${num(s.sharpe ?? null)}` },
        ]}
      />
      <BookPanel summary={s} equity={equity} />
      {s.sweep && <SweepPanel runId={detail.run_id} />}
      {s.settings?.entry.mode === "rank" && <FactorPanel runId={detail.run_id} />}
      <SignalPathPanel runId={detail.run_id} short={(s.settings?.entry.side ?? "long") !== "long"} />
      <LuckPanel runId={detail.run_id} />
      {stocks && <SectorPanel rows={bySector(stocks)} />}
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="Best stocks" aside={<LinkButton onClick={onAllStocks}>All {int(stocks?.length ?? 0)} stocks</LinkButton>}>
          <DataTable columns={small} rows={best} rowKey={(r) => r.ticker} onRowClick={(r) => onStock(r.ticker)} />
        </Panel>
        <Panel title="Worst stocks">
          <DataTable columns={small} rows={worst} rowKey={(r) => r.ticker} onRowClick={(r) => onStock(r.ticker)} />
        </Panel>
      </div>
      {equity && <MonthTable equity={equity} />}
      <div className="grid gap-5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <Panel title="Trades by return after costs" aside={`middle 90%: ${pct(s.p05, 1)} to ${pct(s.p95, 1)}`} padded>
          {s.histogram && <Histogram counts={s.histogram.counts} edges={s.histogram.edges} label="Trades by return after costs" />}
        </Panel>
        <Panel title="How trades ended" padded>
          <dl className="m-0 grid grid-cols-[1fr_auto] gap-x-6 gap-y-1.5 text-sm">
            {exits.map(([reason, count]) => (
              <div key={reason} className="contents">
                <dt className="text-ink-2">{reason[0].toUpperCase() + reason.slice(1)}</dt>
                <dd className="m-0 text-right">{int(count)}</dd>
              </div>
            ))}
            <dt className="text-ink-2">Average hold</dt>
            <dd className="m-0 text-right">{num(s.mean_sessions ?? null, 1)} sessions</dd>
            <dt className="text-ink-2">Before costs</dt>
            <dd className="m-0 text-right">{pct(s.mean_gross)}</dd>
            <dt className="text-ink-2">Vs the universe</dt>
            <dd className="m-0 text-right">{pct(s.mean_over)}</dd>
          </dl>
        </Panel>
      </div>
      <Facts detail={detail} />
    </div>
  );
}

function Facts({ detail }: { detail: RunDetail }) {
  const s = detail.summary!;
  const rows: [string, string][] = [
    ["Period", s.period_label ?? "–"],
    ["First entry to last exit", `${day(s.first_entry)} to ${day(s.last_exit)}`],
    [
      "Side",
      s.settings?.entry.side === "both"
        ? `Long one end, short the other; borrow at ${plainPct(s.settings.book.borrow_rate ?? 0)} a year`
        : s.settings?.entry.side === "short"
          ? `Short, borrow at ${plainPct(s.settings.book.borrow_rate ?? 0)} a year`
          : "Long",
    ],
    ["Stocks in the universe", int(s.universe_stocks)],
    ...(s.tickers_not_found?.length ? [["Named but not in it", s.tickers_not_found.join(", ")] as [string, string]] : []),
    [s.settings?.entry.mode === "rank" ? "Scores given" : "Signals", int(s.signals)],
    ["Trial", s.trial_number ? `#${s.trial_number} for this algorithm` : "–"],
    ["Costs", `${s.cost_model ?? "–"}; 2× doubles the slippage`],
    ["Exit signal", s.has_exit_signal ? "yes" : "no"],
    ["Took", `${num(s.seconds ?? null, 1)} s`],
    ["Code", detail.manifest?.code_sha256.slice(0, 12) ?? "–"],
    ["Data build", detail.manifest?.data_build_id ?? "–"],
  ];
  return (
    <Panel title="About this run" padded>
      <dl className="m-0 grid grid-cols-1 gap-x-8 gap-y-1.5 text-sm sm:grid-cols-2">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 border-b border-line-soft pb-1.5">
            <dt className="text-ink-2">{label}</dt>
            <dd className="m-0 text-right">{value}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

function LinkButton({ onClick, children }: { onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" onClick={onClick} className="cursor-pointer text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
      {children}
    </button>
  );
}

const PAGE = 200;

function Stocks({ stocks, onStock }: { stocks: StockRow[]; onStock: (ticker: string) => void }) {
  const [search, setSearch] = useState("");
  const [sector, setSector] = useState("");
  const [sort, setSort] = useState<Sort>({ key: "profit", dir: "desc" });
  const [shown, setShown] = useState(PAGE);
  const sectors = useMemo(() => [...new Set(stocks.map((s) => s.sector).filter(Boolean))].sort() as string[], [stocks]);
  const rows = useMemo(() => {
    const words = search.trim().toLowerCase();
    const found = stocks.filter((s) => (!sector || s.sector === sector) && (!words || s.ticker.toLowerCase().includes(words) || (s.name ?? "").toLowerCase().includes(words)));
    const sign = sort.dir === "asc" ? 1 : -1;
    return [...found].sort((a, b) => sign * compare(a[sort.key as keyof StockRow], b[sort.key as keyof StockRow]));
  }, [stocks, search, sector, sort]);
  const winners = stocks.filter((s) => s.profit > 0).length;
  const onSort = (key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "desc" ? "asc" : "desc" }));
  return (
    <Panel title="Every stock it traded" aside={`${int(winners)} made money, ${int(stocks.length - winners)} lost; profit is every trade at the position size`}>
      <div className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3">
        <input type="search" aria-label="Find a stock" placeholder="Find a stock or company" value={search} onChange={(e) => setSearch(e.target.value)} className={`${field} w-64`} />
        <select aria-label="Sector" value={sector} onChange={(e) => setSector(e.target.value)} className={field}>
          <option value="">All sectors</option>
          {sectors.map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
        <Segmented
          label="Order"
          value={sort.key === "profit" ? sort.dir : "other"}
          onChange={(value) => value !== "other" && setSort({ key: "profit", dir: value as "asc" | "desc" })}
          options={[
            { value: "desc", label: "Best first" },
            { value: "asc", label: "Worst first" },
          ]}
        />
        <span className="text-[13px] text-ink-3">{int(rows.length)} shown</span>
      </div>
      <DataTable
        columns={stockColumns}
        rows={rows.slice(0, shown)}
        rowKey={(r) => r.ticker}
        onRowClick={(r) => onStock(r.ticker)}
        sort={sort}
        onSort={onSort}
        minWidth={1100}
        empty="No stock matches."
      />
      {rows.length > shown && (
        <div className="flex justify-center p-3">
          <Button onClick={() => setShown((n) => n + PAGE)}>Show {int(Math.min(PAGE, rows.length - shown))} more</Button>
        </div>
      )}
    </Panel>
  );
}

function Trades({ runId, side, ticker, onTicker }: { runId: string; side: string; ticker: string; onTicker: (ticker: string) => void }) {
  const [book, setBook] = useState<"all" | "taken" | "skipped">("all");
  const [sort, setSort] = useState<Sort>({ key: "entry_date", dir: "asc" });
  const [offset, setOffset] = useState(0);
  const [typed, setTyped] = useState(ticker);
  const [page, setPage] = useState<TradePage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const limit = 100;
  useEffect(() => setTyped(ticker), [ticker]);
  useEffect(() => {
    let live = true;
    lab
      .trades(runId, { ticker, book: book === "all" ? undefined : book, sort: sort.key, order: sort.dir, offset, limit })
      .then((found) => live && (setPage(found), setError(null)))
      .catch((e: Error) => live && setError(e.message));
    return () => {
      live = false;
    };
  }, [runId, ticker, book, sort, offset]);
  const onSort = (key: string) => {
    setOffset(0);
    setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }));
  };
  const total = page?.total ?? 0;
  return (
    <Panel
      title={ticker ? `Trades in ${ticker}` : "Every trade"}
      aside={
        <a href={lab.csvUrl(runId)} className="font-medium text-accent hover:underline" download>
          Download all as CSV
        </a>
      }
    >
      <form
        className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3"
        onSubmit={(event) => {
          event.preventDefault();
          setOffset(0);
          onTicker(typed.trim().toUpperCase());
        }}
      >
        <input type="search" aria-label="Stock" placeholder="Stock, e.g. AAPL" value={typed} onChange={(e) => setTyped(e.target.value)} className={`${field} w-48`} />
        <Button type="submit">Show</Button>
        {ticker && (
          <Button
            onClick={() => {
              setOffset(0);
              onTicker("");
            }}
          >
            All stocks
          </Button>
        )}
        <Segmented
          label="Book"
          value={book}
          onChange={(value) => {
            setOffset(0);
            setBook(value);
          }}
          options={[
            { value: "all", label: "All" },
            { value: "taken", label: "The book took" },
            { value: "skipped", label: "The book skipped" },
          ]}
        />
      </form>
      {error ? (
        <p role="alert" className="m-0 px-4 py-6 text-neg">
          {error}
        </p>
      ) : (
        <DataTable
          columns={tradeColumns(side)}
          rows={page?.rows ?? []}
          rowKey={(r) => `${r.ticker}-${r.entry_date}`}
          sort={sort}
          onSort={onSort}
          minWidth={1250}
          empty={page ? "No trades match." : "Loading…"}
        />
      )}
      {total > limit && (
        <div className="flex items-center justify-end gap-3 px-4 py-3 text-[13px] text-ink-2">
          <span>
            {int(offset + 1)} to {int(Math.min(offset + limit, total))} of {int(total)}
          </span>
          <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>
            Previous
          </Button>
          <Button disabled={offset + limit >= total} onClick={() => setOffset(offset + limit)}>
            Next
          </Button>
        </div>
      )}
    </Panel>
  );
}

const yearColumns: Column<YearRow>[] = [
  { key: "year", header: "Year", align: "left", strong: true, render: (r) => String(r.year) },
  { key: "trades", header: "Trades", render: (r) => int(r.trades) },
  { key: "win_rate", header: "Won", render: (r) => plainPct(r.win_rate) },
  { key: "mean_net", header: "A trade", signed: true, render: (r) => pct(r.mean_net) },
  { key: "mean_net_2x", header: "At 2× costs", signed: true, render: (r) => pct(r.mean_net_2x) },
  { key: "mean_over", header: "Vs universe", signed: true, render: (r) => pct(r.mean_over) },
  { key: "book_profit", header: "Book profit", signed: true, strong: true, render: (r) => money(r.book_profit) },
];

function Years({ runId }: { runId: string }) {
  const { data } = useLoad(() => lab.years(runId), `years-${runId}`);
  if (!data) return <p className="text-ink-2">Loading…</p>;
  const bars = data.map((y) => ({ year: y.year, total: y.book_profit, months: 12, periods: ["all"] }));
  return (
    <div className="flex flex-col gap-5">
      <Panel title="Book profit by year" padded>
        <YearBars years={bars} highlight="all" />
      </Panel>
      <Panel title="Each year">
        <DataTable columns={yearColumns} rows={data} rowKey={(r) => String(r.year)} />
      </Panel>
    </div>
  );
}

function Code({ runId, onRestoreCode, onUseSettings }: { runId: string; onRestoreCode: (code: string) => void; onUseSettings: () => void }) {
  const { data } = useLoad(() => lab.code(runId), `code-${runId}`);
  return (
    <Panel
      title="The code this run used"
      aside={
        <span className="flex gap-4">
          <LinkButton onClick={onUseSettings}>Use its settings</LinkButton>
          {data && <LinkButton onClick={() => onRestoreCode(data.code)}>Put it in the editor</LinkButton>}
        </span>
      }
    >
      {data ? (
        <div className="h-[420px]">
          <CodeEditor value={data.code} readOnly label="The code this run used" />
        </div>
      ) : (
        <p className="m-0 px-4 py-6 text-ink-2">Loading…</p>
      )}
    </Panel>
  );
}

export interface RunRow extends RunListRow {
  /** The trial number: the runs of this algorithm that computed signals, oldest first. */
  number: number | null;
}

const STATE_TONE: Record<RunState, Tone> = {
  waiting: "muted",
  queued: "info",
  running: "info",
  complete: "ok",
  failed: "bad",
  cancelled: "muted",
  interrupted: "warn",
};
export const STATE_LABEL: Record<RunState, string> = {
  waiting: "In the queue",
  queued: "Starting",
  running: "Running",
  complete: "Done",
  failed: "Failed",
  cancelled: "Cancelled",
  interrupted: "Stopped",
};

/** "18 Nov 14:22" in the viewer's time. */
export function when(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso.slice(0, 16).replace("T", " ");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getDate()} ${months[date.getMonth()]} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function runLabel(run: RunRow): string {
  const count = Math.max(1, run.trials ?? 1);
  const trial = run.number ? (count > 1 ? `Trials ${run.number}–${run.number + count - 1}` : `Trial ${run.number}`) : "Not a trial";
  return [trial, when(run.created_at), run.period].filter(Boolean).join(", ");
}

/** The line of an error that says what went wrong (a traceback ends with it). */
function lastLine(text: string): string {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  return lines[lines.length - 1] ?? text;
}

const runColumns: Column<RunRow>[] = [
  { key: "trial", header: "Trial", align: "left", render: (r) => (r.number ? ((r.trials ?? 1) > 1 ? `${r.number}–${r.number + (r.trials ?? 1) - 1}` : String(r.number)) : "–") },
  { key: "created", header: "Started", align: "left", muted: true, render: (r) => when(r.created_at) },
  { key: "period", header: "Period", align: "left", muted: true, render: (r) => r.period ?? "–" },
  { key: "state", header: "State", align: "left", render: (r) => <Badge tone={STATE_TONE[r.state]}>{STATE_LABEL[r.state]}</Badge> },
  { key: "headline", header: "Result", align: "left", max: 420, render: (r) => r.headline ?? (r.error ? lastLine(r.error) : (r.stage ?? "–")) },
  { key: "note", header: "Note", align: "left", muted: true, max: 280, render: (r) => r.note || "–" },
];

function Failure({ detail }: { detail: RunDetail }) {
  const [log, setLog] = useState<string | null>(null);
  const status = detail.status;
  const ours = (status.error ?? "").startsWith("The Lab failed");
  return (
    <Panel padded>
      <div role="alert" className="flex flex-col gap-2">
        <Badge tone={STATE_TONE[status.state]}>{STATE_LABEL[status.state]}</Badge>
        {status.error && <pre className="m-0 max-h-[360px] overflow-auto rounded-md bg-raised p-3 font-mono text-[13px] leading-relaxed whitespace-pre-wrap">{status.error}</pre>}
        {status.signals_computed && <span className="text-[13px] text-ink-3">It got as far as the signals, so it counts as trial {status.trial_number}.</span>}
        {ours && log == null && (
          <button type="button" onClick={() => lab.log(detail.run_id).then((found) => setLog(found.log))} className="cursor-pointer self-start text-[13px] font-medium text-accent hover:underline">
            Show the worker's log
          </button>
        )}
        {log != null && <pre className="m-0 max-h-[360px] overflow-auto rounded-md bg-raised p-3 font-mono text-[13px] whitespace-pre-wrap">{log || "The log is empty."}</pre>}
      </div>
    </Panel>
  );
}

interface RunResultsProps {
  onChanged?: () => void;
  /** The run on screen, once loaded. */
  detail: RunDetail | null;
  runs: RunRow[];
  selected: string | null;
  onSelect: (runId: string) => void;
  onRestoreCode: (code: string) => void;
  onUseSettings: (detail: RunDetail) => void;
}

/** The results of the run on screen, a choice of run, and every run of the algorithm. */
export function RunResults({ detail, runs, selected, onSelect, onRestoreCode, onUseSettings, onChanged }: RunResultsProps) {
  const [tab, setTab] = useState<Tab | "runs" | "compare">("overview");
  const [ticker, setTicker] = useState("");
  const complete = detail?.status.state === "complete" && detail.summary ? detail : null;
  const { data: stocks } = useLoad(() => (complete ? lab.stocks(complete.run_id) : Promise.resolve(null)), `stocks-${complete?.run_id ?? "none"}`);
  useEffect(() => setTicker(""), [selected]);
  const s = complete?.summary;
  const openStock = (name: string) => {
    setTicker(name);
    setTab("trades");
  };
  const finished = runs.filter((r) => r.state === "complete").map((r) => ({ run_id: r.run_id, label: runLabel(r) }));
  const tabs: { key: Tab | "runs" | "compare"; label: string }[] = complete
    ? [
        { key: "overview", label: "Overview" },
        { key: "stocks", label: `Stocks${stocks ? ` ${int(stocks.length)}` : ""}` },
        { key: "trades", label: `Trades ${int(s?.trades)}` },
        { key: "years", label: "Years" },
        { key: "code", label: "Code" },
        ...(finished.length > 1 ? [{ key: "compare" as const, label: "Compare" }] : []),
        { key: "runs", label: `Runs ${runs.length}` },
      ]
    : [
        { key: "overview", label: "Result" },
        { key: "code", label: "Code" },
        { key: "runs", label: `Runs ${runs.length}` },
      ];
  const active = tabs.some((t) => t.key === tab) ? tab : "overview";
  const current = runs.find((r) => r.run_id === selected);
  return (
    <section aria-label="Results" className="flex flex-col gap-4">
      {current && <p className="m-0 hidden text-sm text-ink-2 print:block">{runLabel(current)}</p>}
      <div data-print="hide" className="flex flex-wrap items-end gap-x-6 gap-y-2 border-b border-line">
        <div role="tablist" aria-label="Run results" className="flex flex-wrap gap-6">
          {tabs.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={active === t.key}
              onClick={() => setTab(t.key)}
              className={`-mb-px cursor-pointer border-b-2 pb-2.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${
                active === t.key ? "border-accent text-ink" : "border-transparent text-ink-2 hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        {runs.length > 1 && (
          <select
            aria-label="Run shown"
            value={selected ?? ""}
            onChange={(e) => onSelect(e.target.value)}
            className="mb-2 h-8 max-w-[340px] rounded-md border border-line bg-surface px-2 text-[13px] text-ink focus-visible:outline-2 focus-visible:outline-accent"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {runLabel(r)}
              </option>
            ))}
          </select>
        )}
        {runs.length === 1 && current && <span className="mb-2.5 text-[13px] text-ink-3">{runLabel(current)}</span>}
      </div>
      {detail && active !== "runs" && <RunNote key={detail.run_id} runId={detail.run_id} note={detail.note ?? ""} onSaved={onChanged} />}
      {complete && !s?.lookahead.passed && active !== "runs" && (
        <div role="alert" className="rounded-lg border border-neg bg-surface px-4 py-3">
          <Badge tone="bad">The code looks ahead</Badge>
          <p className="m-0 mt-1 max-w-[100ch] text-sm text-ink-2">{s?.lookahead.detail}</p>
        </div>
      )}
      {complete && (s?.settings?.universe.tickers?.length ?? 0) > 0 && active !== "runs" && (
        <div className="rounded-lg border border-warn bg-surface px-4 py-3">
          <Badge tone="warn">Hand-picked stocks</Badge>
          <p className="m-0 mt-1 max-w-[100ch] text-sm text-ink-2">
            A list chosen today already knows which companies lasted and grew, so this result describes these {int(s?.universe_stocks)} stocks; it is not evidence that the rule works on stocks picked
            in advance.
          </p>
        </div>
      )}
      {complete && s?.fragile && active !== "runs" && (
        <div className="rounded-lg border border-warn bg-surface px-4 py-3">
          <Badge tone="warn">Fragile</Badge>
          <p className="m-0 mt-1 text-sm text-ink-2">It makes money at the expected costs and loses at twice the slippage.</p>
        </div>
      )}
      {active === "compare" && complete ? (
        <Compare detail={complete} runs={finished} />
      ) : active === "runs" ? (
        <Panel>
          <DataTable
            columns={runColumns}
            rows={runs}
            rowKey={(r) => r.run_id}
            selectedKey={selected}
            onRowClick={(r) => {
              onSelect(r.run_id);
              setTab("overview");
            }}
          />
        </Panel>
      ) : active === "code" && detail ? (
        <Code runId={detail.run_id} onRestoreCode={onRestoreCode} onUseSettings={() => onUseSettings(detail)} />
      ) : !detail ? (
        <p className="m-0 text-ink-2">Loading the run…</p>
      ) : !complete ? (
        isLive(detail.status.state) ? (
          <p className="m-0 text-ink-2">The results appear here when the run ends.</p>
        ) : (
          <Failure detail={detail} />
        )
      ) : active === "overview" ? (
        <Overview detail={complete} stocks={stocks} onStock={openStock} onAllStocks={() => setTab("stocks")} />
      ) : active === "stocks" ? (
        stocks ? (
          <Stocks stocks={stocks} onStock={openStock} />
        ) : (
          <p className="text-ink-2">Loading…</p>
        )
      ) : active === "trades" ? (
        <Trades runId={complete.run_id} side={complete.summary?.settings?.entry.side ?? "long"} ticker={ticker} onTicker={setTicker} />
      ) : (
        <Years runId={complete.run_id} />
      )}
    </section>
  );
}
