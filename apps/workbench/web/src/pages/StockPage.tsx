import { useEffect, useMemo, useState } from "react";
import { movingAverage, type PriceMarker, PriceChart } from "../components/charts/PriceChart";
import { CsvButton } from "../components/CsvButton";
import { Financials } from "../components/Financials";
import { Insiders } from "../components/Insiders";
import { RelativeChart } from "../components/RelativeChart";
import { StocksLanding, useWatchlist } from "../components/StocksLanding";
import { recentStocks, rememberStock, StockSearch, years } from "../components/StockSearch";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, Note } from "../components/ui/Card";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Segmented } from "../components/ui/Segmented";
import { type TabItem, Tabs } from "../components/ui/Tabs";
import { StatStrip } from "../components/ui/StatStrip";
import { api, type StockPageData, type StockTrade } from "../lib/api";
import { compact, day, int, pct, price, priceTick } from "../lib/format";
import { href } from "../lib/route";
import { sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";
import { toggleWatch } from "../lib/watchlist";

type Range = "3m" | "1y" | "3y" | "5y" | "all";
type Source = "all" | StockTrade["source"];
type Section = "financials" | "trades" | "insiders" | "filings";

const RANGES: { value: Range; label: string; sessions: number }[] = [
  { value: "3m", label: "3M", sessions: 63 },
  { value: "1y", label: "1Y", sessions: 252 },
  { value: "3y", label: "3Y", sessions: 756 },
  { value: "5y", label: "5Y", sessions: 1260 },
  { value: "all", label: "All", sessions: Infinity },
];
const SOURCE_LABEL: Record<StockTrade["source"], string> = { run: "Strategy run", lab: "Lab", paper: "Paper" };
const MAX_MARKERS = 400;

interface Adjusted {
  date: string[];
  open: (number | null)[];
  high: (number | null)[];
  low: (number | null)[];
  close: (number | null)[];
  volume: (number | null)[];
}

function adjust(page: StockPageData): Adjusted {
  const p = page.prices;
  const scale = (values: (number | null)[]) => values.map((v, i) => (v == null ? null : v * (p.factor[i] ?? 1)));
  return { date: p.date, open: scale(p.open), high: scale(p.high), low: scale(p.low), close: scale(p.close), volume: p.volume };
}

function locate(dates: string[], iso: string | null): number | null {
  if (!iso || !dates.length || iso < dates[0] || iso > dates[dates.length - 1]) return null;
  let lo = 0;
  let hi = dates.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (dates[mid] < iso) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function tradeKey(t: StockTrade, i: number): string {
  return `${t.source}-${t.id}-${t.entry_day ?? t.signal_day}-${i}`;
}

function sourceLink(t: StockTrade): string | null {
  if (t.source === "lab") return href({ page: "lab", name: t.label, tab: t.id });
  if (t.source === "paper") return href({ page: "paper", name: t.id });
  return href({ page: "strategy", name: t.label, tab: "runs" });
}

function Landing({ onOpen }: { onOpen: (symbol: string, permaticker?: number) => void }) {
  const recent = recentStocks();
  return (
    <div className="flex flex-col gap-4">
      <Card title="Find a stock">
        <StockSearch autoFocus onPick={(hit) => onOpen(hit.ticker ?? "", hit.permaticker)} />
        {recent.length > 0 && (
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2 pt-1">
            <span className="text-[13px] text-ink-3">Recently viewed</span>
            {recent.map((r) => (
              <a key={r.permaticker} href={href({ page: "stock", name: r.ticker, tab: String(r.permaticker) })} className="text-sm font-semibold text-ink no-underline hover:underline">
                {r.ticker}
              </a>
            ))}
          </div>
        )}
      </Card>
      <StocksLanding />
    </div>
  );
}

function WatchButton({ page }: { page: StockPageData }) {
  const list = useWatchlist();
  const watched = list.some((w) => w.permaticker === page.permaticker);
  return (
    <Button aria-pressed={watched} onClick={() => toggleWatch({ ticker: page.ticker ?? page.query, name: page.name, permaticker: page.permaticker })}>
      {watched ? "On the watchlist" : "Add to the watchlist"}
    </Button>
  );
}

function Header({ page, onOpen }: { page: StockPageData; onOpen: (symbol: string, permaticker?: number) => void }) {
  const traded = page.symbols.filter((s) => s.symbol !== page.ticker);
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="flex min-w-0 flex-col gap-1.5">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <h1 className="m-0 text-[28px] leading-tight font-semibold tracking-tight">{page.ticker}</h1>
          <span className="text-lg text-ink-2">{page.name}</span>
          {page.delisted ? <Badge tone="muted">{`Delisted ${day(page.last)}`}</Badge> : <Badge tone="ok">Listed</Badge>}
          <span className="self-center">
            <WatchButton page={page} />
          </span>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-ink-2">
          {[page.exchange, page.sector, page.industry, page.category, page.location].filter(Boolean).map((part) => (
            <span key={part}>{part}</span>
          ))}
          {page.prices.date.length > 0 && (
            <span>
              Daily prices {day(page.prices.date[0])} to {day(page.prices.date[page.prices.date.length - 1])}
            </span>
          )}
        </div>
        {traded.length > 0 && <div className="text-[13px] text-ink-3">Also traded as {traded.map((s) => `${s.symbol} (${s.from?.slice(0, 4) ?? ""}–${s.to?.slice(0, 4) ?? ""})`).join(", ")}</div>}
        {page.others.length > 0 && (
          <div className="flex flex-wrap gap-x-3 text-[13px] text-ink-3">
            <span>{page.query} was also used by</span>
            {page.others.map((o) => (
              <button key={o.permaticker} type="button" onClick={() => onOpen(page.query, o.permaticker)} className="cursor-pointer text-accent hover:underline">
                {o.name} ({years(o)})
              </button>
            ))}
          </div>
        )}
      </div>
      <StockSearch onPick={(hit) => onOpen(hit.ticker ?? "", hit.permaticker)} placeholder="Another stock" />
    </header>
  );
}

function Readout({ page, data, i }: { page: StockPageData; data: Adjusted; i: number }) {
  const prev = i > 0 ? data.close[i - 1] : null;
  const c = data.close[i];
  const change = c != null && prev ? c / prev - 1 : null;
  const result = page.events.some((e) => e.results && e.date === data.date[i]);
  const symbol = page.prices.symbol[i];
  return (
    <div className="flex min-h-6 flex-wrap items-baseline gap-x-4 gap-y-1 text-[13px] text-ink-2 tabular-nums">
      <span className="font-semibold text-ink">{day(data.date[i])}</span>
      <span>O {price(data.open[i])}</span>
      <span>H {price(data.high[i])}</span>
      <span>L {price(data.low[i])}</span>
      <span>C {price(c)}</span>
      <span className={change != null && change < 0 ? "text-neg" : change ? "text-pos" : ""}>{pct(change)}</span>
      <span>Vol {compact(data.volume[i])}</span>
      <span>Value {compact(page.prices.market_cap[i], "$")}</span>
      {symbol && symbol !== page.ticker && <span>traded as {symbol}</span>}
      {result && <span className="font-medium text-ink">Results 8-K</span>}
    </div>
  );
}

function Facts({ page, data }: { page: StockPageData; data: Adjusted }) {
  const last = data.date.length - 1;
  const year = Math.max(0, last - 251);
  const lows = data.low.slice(year).filter((v): v is number => v != null);
  const highs = data.high.slice(year).filter((v): v is number => v != null);
  const now = data.close[last];
  const then = data.close[year];
  const counts = { run: 0, lab: 0, paper: 0 };
  page.trades.forEach((t) => (counts[t.source] += 1));
  return (
    <StatStrip
      items={[
        { label: "Last close", value: price(page.prices.close[last]), note: day(data.date[last]) },
        { label: "Market value", value: compact(page.prices.market_cap[last], "$"), note: "at the previous close" },
        { label: "Dollar volume", value: compact(page.prices.adv20[last], "$"), note: "median of 20 sessions" },
        { label: "One year", value: now != null && then ? pct(now / then - 1, 1) : "–", note: "split-adjusted" },
        { label: "52-week range", value: lows.length ? `${priceTick(Math.min(...lows))}–${priceTick(Math.max(...highs))}` : "–", note: "split-adjusted" },
        { label: "Trades recorded", value: int(page.trades.length), note: `${counts.run} runs, ${counts.lab} Lab, ${counts.paper} paper` },
      ]}
    />
  );
}

function tradeColumns(): Column<StockTrade>[] {
  return [
    { key: "source", header: "Source", align: "left", sortable: true, render: (t) => SOURCE_LABEL[t.source] },
    {
      key: "label",
      header: "From",
      align: "left",
      sortable: true,
      render: (t) => {
        const link = sourceLink(t);
        return link ? (
          <a href={link} onClick={(event) => event.stopPropagation()} className="font-medium text-ink no-underline hover:underline">
            {t.label}
          </a>
        ) : (
          t.label
        );
      },
    },
    { key: "detail", header: "", align: "left", muted: true, max: 180, render: (t) => t.detail ?? "" },
    { key: "entry_day", header: "Entry", sortable: true, render: (t) => day(t.entry_day ?? t.signal_day) },
    { key: "entry", header: "Price", render: (t) => price(t.entry) },
    { key: "exit_day", header: "Exit", sortable: true, render: (t) => (t.exit_day ? day(t.exit_day) : t.kind === "backtest" ? "same day" : "–") },
    { key: "exit", header: "Price", render: (t) => price(t.exit) },
    { key: "net", header: "Return", sortable: true, signed: true, strong: true, render: (t) => pct(t.net) },
    { key: "note", header: "Note", align: "left", muted: true, max: 160, render: (t) => (t.side === "short" ? `short${t.note ? `; ${t.note}` : ""}` : (t.note ?? "")) },
  ];
}

function Filings({ page, onPick }: { page: StockPageData; onPick: (iso: string) => void }) {
  const [all, setAll] = useState(false);
  const events = [...page.events].reverse();
  const shown = all ? events : events.slice(0, 12);
  const results = events.filter((e) => e.results).length;
  if (!events.length) return <p className="m-0 text-ink-2">No 8-K filing in the research data.</p>;
  return (
    <>
      <ul className="m-0 grid list-none grid-cols-1 gap-x-6 p-0 sm:grid-cols-2 xl:grid-cols-3">
        {shown.map((e) => (
          <li key={`${e.date}-${e.codes}`} className="flex items-baseline gap-3 border-b border-line-soft py-1.5 text-sm">
            <button type="button" onClick={() => onPick(e.date)} className="w-24 shrink-0 cursor-pointer text-left font-medium text-ink hover:underline">
              {day(e.date)}
            </button>
            <span className={e.results ? "font-medium" : "text-ink-2"}>{e.results ? "Results" : "8-K"}</span>
            <span className="truncate text-[12px] text-ink-3">items {e.codes.replace(/\|/g, ", ")}</span>
          </li>
        ))}
      </ul>
      <div className="flex items-center justify-between gap-3">
        <Note>
          {events.length} filings, {results} with results (item 2.02). Click a date to see it on the chart.
        </Note>
        {events.length > 12 && <Button onClick={() => setAll(!all)}>{all ? "Show fewer" : `Show all ${events.length}`}</Button>}
      </div>
    </>
  );
}

function Stock({ page, on, onOpen }: { page: StockPageData; on?: string; onOpen: (symbol: string, permaticker?: number) => void }) {
  const data = useMemo(() => adjust(page), [page]);
  const n = data.date.length;
  const [range, setRange] = useState<Range>("all");
  const [view, setView] = useState<[number, number]>([0, Math.max(0, n - 1)]);
  const [log, setLog] = useState(false);
  const [hover, setHover] = useState<number | null>(null);
  const [source, setSource] = useState<Source>("all");
  const [selected, setSelected] = useState<string | null>(null);
  const [events, setEvents] = useState(true);
  const [averages, setAverages] = useState(false);
  const overlays = useMemo(
    () =>
      averages
        ? [
            { name: "50-day average", values: movingAverage(data.close, 50), color: "var(--series-4)" },
            { name: "200-day average", values: movingAverage(data.close, 200), color: "var(--series-3)" },
          ]
        : [],
    [averages, data],
  );
  const [sort, onSort] = useSort({ key: "entry_day", dir: "desc" });
  const sections: TabItem<Section>[] = [
    ...(page.financials && (page.financials.quarterly.length || page.financials.trailing.length) ? [{ key: "financials" as const, label: "Financials" }] : []),
    { key: "trades", label: `Trades ${page.trades.length}` },
    ...(page.insiders ? [{ key: "insiders" as const, label: `Insider trades ${page.insiders.count}` }] : []),
    { key: "filings", label: `8-K filings ${page.events.length}` },
  ];
  const [section, setSection] = useState<Section>(sections[0].key);
  const visibleDates = useMemo(() => data.date.slice(view[0], view[1] + 1), [data, view]);
  const visibleCloses = useMemo(() => data.close.slice(view[0], view[1] + 1), [data, view]);

  useEffect(() => {
    rememberStock({ ticker: page.ticker ?? page.query, name: page.name, permaticker: page.permaticker });
  }, [page]);

  const keyed = useMemo(() => page.trades.map((t, i) => ({ t, key: tradeKey(t, i) })), [page]);
  const visible = keyed.filter(({ t }) => source === "all" || t.source === source);
  const resultsAt = useMemo(
    () =>
      page.events
        .filter((e) => e.results)
        .map((e) => locate(data.date, e.date))
        .filter((i): i is number => i != null),
    [page, data],
  );
  const filingsAt = useMemo(
    () =>
      page.events
        .filter((e) => !e.results)
        .map((e) => locate(data.date, e.date))
        .filter((i): i is number => i != null),
    [page, data],
  );

  const markers: PriceMarker[] = [];
  let span: [number, number] | null = null;
  for (const { t, key } of visible.slice(0, MAX_MARKERS)) {
    const at = locate(data.date, t.entry_day ?? t.signal_day);
    if (at == null) continue;
    const exitKnown = Boolean(t.exit_day) || t.kind === "backtest";
    const out = (t.exit_day ? locate(data.date, t.exit_day) : null) ?? at;
    const good = t.net == null ? null : t.net > 0;
    const f = (i: number) => page.prices.factor[i] ?? 1;
    if (t.entry != null) markers.push({ key: `${key}-in`, i: at, price: t.entry * f(at), kind: t.side === "short" ? "exit" : "entry", good });
    if (t.exit != null && exitKnown) markers.push({ key: `${key}-out`, i: out, price: t.exit * f(out), kind: t.side === "short" ? "entry" : "exit", good });
    if (key === selected) span = [at, out];
  }

  const preset = (r: Range) => {
    const sessions = RANGES.find((x) => x.value === r)?.sessions ?? Infinity;
    setRange(r);
    setView([Math.max(0, n - Math.min(n, sessions)), n - 1]);
  };
  const around = (a: number, b: number, pad = 40) => {
    setRange("all");
    setView([Math.max(0, a - pad), Math.min(n - 1, b + pad)]);
    const chart = document.getElementById("price-chart");
    if (chart && chart.getBoundingClientRect().top < 0) chart.scrollIntoView?.({ behavior: "smooth", block: "start" });
  };
  const zoomed = view[0] !== 0 || view[1] !== n - 1;
  const counts = { run: 0, lab: 0, paper: 0 };
  page.trades.forEach((t) => (counts[t.source] += 1));
  const sources: { value: Source; label: string }[] = [
    { value: "all", label: `All ${page.trades.length}` },
    ...(["run", "lab", "paper"] as const).filter((s) => counts[s]).map((s) => ({ value: s as Source, label: `${SOURCE_LABEL[s]} ${counts[s]}` })),
  ];
  const sortValue = (row: { t: StockTrade }, key: string) => {
    if (key === "entry_day") return row.t.entry_day ?? row.t.signal_day;
    return row.t[key as keyof StockTrade] as string | number | null;
  };
  const rows = sortRows(visible, sort, sortValue);
  const columns = tradeColumns().map((c) => ({ ...c, render: (row: { t: StockTrade }) => c.render(row.t) })) as Column<{ t: StockTrade; key: string }>[];

  if (!n) {
    return (
      <>
        <Header page={page} onOpen={onOpen} />
        <EmptyState title="No daily prices before the seal">This company has no bars in the research data before 9 Nov 2023.</EmptyState>
      </>
    );
  }
  return (
    <>
      <Header page={page} onOpen={onOpen} />
      <Facts page={page} data={data} />
      <Card
        id="price-chart"
        title="Daily prices"
        aside={
          <div className="flex flex-wrap items-center gap-2">
            <Segmented label="Range" options={RANGES.map(({ value, label }) => ({ value, label }))} value={zoomed && range === "all" ? ("" as Range) : range} onChange={preset} />
            <Segmented
              label="Scale"
              options={[
                { value: "linear", label: "Linear" },
                { value: "log", label: "Log" },
              ]}
              value={log ? "log" : "linear"}
              onChange={(v) => setLog(v === "log")}
            />
            <Segmented
              label="Filings"
              options={[
                { value: "on", label: "8-K days" },
                { value: "off", label: "Hide" },
              ]}
              value={events ? "on" : "off"}
              onChange={(v) => setEvents(v === "on")}
            />
            <Segmented
              label="Moving averages"
              options={[
                { value: "off", label: "None" },
                { value: "on", label: "50 and 200 days" },
              ]}
              value={averages ? "on" : "off"}
              onChange={(v) => setAverages(v === "on")}
            />
          </div>
        }
      >
        <Readout page={page} data={data} i={hover ?? view[1]} />
        {averages && (
          <div className="flex gap-4 text-[12px] text-ink-3">
            {overlays.map((o) => (
              <span key={o.name} className="inline-flex items-center gap-1.5">
                <svg aria-hidden="true" width="18" height="4">
                  <line x1="0" x2="18" y1="2" y2="2" stroke={o.color} strokeWidth="2" strokeDasharray="6 3" />
                </svg>
                {o.name} {price(o.values[hover ?? view[1]])}
              </span>
            ))}
          </div>
        )}
        <PriceChart
          data={data}
          overlays={overlays}
          from={view[0]}
          to={view[1]}
          log={log}
          markers={markers}
          results={events ? resultsAt : []}
          filings={events ? filingsAt : []}
          span={span}
          hover={hover}
          onHover={setHover}
          onZoom={(a, b) => {
            setRange("all");
            setView([a, b]);
          }}
          onReset={() => preset("all")}
          priceText={priceTick}
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Note>
            Split-adjusted to the last close; prices end {day(data.date[n - 1])} (the holdout from {day(page.sealed_from)} is sealed). Drag across the chart to zoom, double-click to see it all.
            Triangles mark entries and exits, green for a gain and red for a loss; diamonds mark results 8-Ks.
          </Note>
          {zoomed && <Button onClick={() => preset("all")}>Show all</Button>}
        </div>
      </Card>
      <RelativeChart symbol={page.ticker ?? page.query} dates={visibleDates} close={visibleCloses} />
      <Tabs label="Details" tabs={sections} active={section} onChange={setSection} />
      {section === "financials" && page.financials && <Financials data={page.financials} on={on} />}
      {section === "trades" && (
        <Card
          title="Trades in this stock"
          aside={
            <div className="flex flex-wrap items-center gap-2">
              {sources.length > 2 && <Segmented label="Source" options={sources} value={source} onChange={setSource} />}
              <CsvButton
                filename={`${page.ticker ?? page.query}_trades.csv`}
                rows={visible.map((v) => v.t)}
                columns={[
                  { header: "source", value: (t) => t.source },
                  { header: "from", value: (t) => t.label },
                  { header: "detail", value: (t) => t.detail },
                  { header: "run", value: (t) => t.id },
                  { header: "symbol", value: (t) => t.symbol },
                  { header: "signal_day", value: (t) => t.signal_day },
                  { header: "entry_day", value: (t) => t.entry_day },
                  { header: "entry", value: (t) => t.entry },
                  { header: "exit_day", value: (t) => t.exit_day },
                  { header: "exit", value: (t) => t.exit },
                  { header: "return", value: (t) => t.net },
                  { header: "side", value: (t) => t.side },
                  { header: "note", value: (t) => t.note },
                ]}
              />
            </div>
          }
        >
          <div className="-mx-5 max-h-[520px] overflow-auto">
            <DataTable
              columns={columns}
              rows={rows}
              rowKey={(row) => row.key}
              selectedKey={selected}
              onRowClick={(row) => {
                setSelected(row.key === selected ? null : row.key);
                const at = locate(data.date, row.t.entry_day ?? row.t.signal_day);
                if (at != null && row.key !== selected) around(at, locate(data.date, row.t.exit_day ?? row.t.entry_day) ?? at);
              }}
              sort={sort}
              onSort={onSort}
              minWidth={1050}
              empty="No strategy run, Lab run or paper ledger has traded this stock."
            />
          </div>
          {page.trades.some((t) => t.source === "run") && <Note>Strategy-run returns are after costs, on the trade's own money. Click a trade to see it on the chart.</Note>}
        </Card>
      )}
      {section === "insiders" && page.insiders && (
        <Insiders
          data={page.insiders}
          on={on}
          onPick={(iso) => {
            const at = locate(data.date, iso);
            if (at != null) around(at, at, 60);
          }}
        />
      )}
      {section === "filings" && (
        <Card title="8-K filings">
          <Filings
            page={page}
            onPick={(iso) => {
              const at = locate(data.date, iso);
              if (at != null) around(at, at, 30);
            }}
          />
        </Card>
      )}
    </>
  );
}

export function StockPage({ symbol, permaticker, onOpen }: { symbol?: string; permaticker?: string; onOpen: (symbol: string, permaticker?: number) => void }) {
  const key = `${symbol ?? ""}/${permaticker ?? ""}`;
  const { data, error } = useLoad(() => (symbol ? api.stock(symbol, permaticker) : Promise.resolve(null)), key);
  if (!symbol) return <Landing onOpen={onOpen} />;
  if (error)
    return (
      <>
        <Landing onOpen={onOpen} />
        <EmptyState title={`No stock called ${symbol}`}>Search by ticker or company name. If the stock page itself is new, restart the Workbench server.</EmptyState>
      </>
    );
  if (!data) return <p className="text-ink-2">Loading {symbol}…</p>;
  return <Stock key={key} page={data} on={permaticker && /^\d{4}-\d{2}-\d{2}$/.test(permaticker) ? permaticker : undefined} onOpen={onOpen} />;
}
