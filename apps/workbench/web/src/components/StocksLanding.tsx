import { useEffect, useMemo, useState } from "react";
import { Button } from "./ui/Button";
import { api } from "../lib/api";
import { compact, day, num, pct, price } from "../lib/format";
import { href } from "../lib/route";
import { KINDS, median, rowsOf, type ScreenRow } from "../lib/screen";
import { onWatchlist, toggleWatch, type Watched, watchlist } from "../lib/watchlist";
import { useLoad } from "../lib/useLoad";
import { DivergingBars } from "./charts/DivergingBars";
import { StockLink } from "./StockLink";
import { type Column, DataTable } from "./ui/DataTable";
import { Panel } from "./ui/Panel";

const US = new Set(KINDS[0].categories);
const MOVERS = 8;
const LARGE = 2e9;
const SECTOR_FLOOR = 3e8;

export function useWatchlist(): Watched[] {
  const [list, setList] = useState<Watched[]>(watchlist);
  useEffect(() => onWatchlist(() => setList(watchlist())), []);
  return list;
}

export function movers(rows: ScreenRow[], direction: "up" | "down"): ScreenRow[] {
  const sign = direction === "up" ? -1 : 1;
  return rows
    .filter((r) => US.has(r.category ?? "") && (r.market_cap ?? 0) >= LARGE && r.ret_1d != null && (direction === "up" ? r.ret_1d > 0 : r.ret_1d < 0))
    .sort((a, b) => sign * ((a.ret_1d as number) - (b.ret_1d as number)))
    .slice(0, MOVERS);
}

export function sectorMonths(rows: ScreenRow[]): { label: string; value: number; note: string }[] {
  const groups = new Map<string, (number | null)[]>();
  for (const r of rows) {
    if (!r.sector || !US.has(r.category ?? "") || (r.market_cap ?? 0) < SECTOR_FLOOR) continue;
    groups.set(r.sector, [...(groups.get(r.sector) ?? []), r.ret_1m]);
  }
  return [...groups].map(([label, values]) => ({ label, value: median(values) ?? 0, note: `median of ${values.length} stocks` })).sort((a, b) => b.value - a.value);
}

function moveColumns(on: string): Column<ScreenRow>[] {
  return [
    { key: "symbol", header: "Symbol", align: "left", render: (r) => <StockLink symbol={r.symbol} on={on} /> },
    { key: "name", header: "Company", align: "left", muted: true, max: 180, render: (r) => r.name ?? "–" },
    { key: "close", header: "Close", render: (r) => price(r.close) },
    { key: "ret_1d", header: "Day", signed: true, strong: true, render: (r) => pct(r.ret_1d, 1) },
    { key: "market_cap", header: "Market value", render: (r) => compact(r.market_cap, "$") },
  ];
}

function Watchlist({ list, rows, on }: { list: Watched[]; rows: Map<number, ScreenRow>; on: string }) {
  const columns: Column<Watched>[] = [
    { key: "symbol", header: "Symbol", align: "left", render: (w) => <StockLink symbol={w.ticker} /> },
    { key: "name", header: "Company", align: "left", muted: true, max: 220, render: (w) => w.name ?? "–" },
    { key: "close", header: "Close", render: (w) => (rows.has(w.permaticker) ? price(rows.get(w.permaticker)?.close) : <span className="text-ink-3">no trade that day</span>) },
    { key: "ret_1d", header: "Day", signed: true, render: (w) => pct(rows.get(w.permaticker)?.ret_1d, 1) },
    { key: "ret_1m", header: "1 month", signed: true, render: (w) => pct(rows.get(w.permaticker)?.ret_1m, 1) },
    { key: "ret_1y", header: "1 year", signed: true, render: (w) => pct(rows.get(w.permaticker)?.ret_1y, 1) },
    { key: "from_high", header: "From 52-week high", signed: true, render: (w) => pct(rows.get(w.permaticker)?.from_high, 1) },
    { key: "market_cap", header: "Market value", render: (w) => compact(rows.get(w.permaticker)?.market_cap, "$") },
    { key: "pe", header: "P/E", render: (w) => num(rows.get(w.permaticker)?.pe, 1) },
    {
      key: "remove",
      header: "",
      render: (w) => (
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            toggleWatch(w);
          }}
          className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent"
        >
          Remove
        </button>
      ),
    },
  ];
  return (
    <Panel title={list.length ? `Watchlist on ${day(on)}` : "Watchlist"} aside={<AddTickers />}>
      {list.length ? (
        <DataTable
          columns={columns}
          rows={list}
          rowKey={(w) => String(w.permaticker)}
          onRowClick={(w) => {
            window.location.hash = href({ page: "stock", name: w.ticker, tab: String(w.permaticker) });
          }}
          minWidth={900}
        />
      ) : (
        <p className="m-0 px-4 py-5 text-ink-2">Add tickers here, or with “Add to the watchlist” on a stock’s page or picked stocks in the screener.</p>
      )}
    </Panel>
  );
}

export function tickersIn(text: string): string[] {
  return [
    ...new Set(
      text
        .toUpperCase()
        .split(/[\s,;]+/)
        .filter((t) => /^[A-Z][A-Z0-9.\-]{0,9}$/.test(t)),
    ),
  ];
}

function AddTickers() {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const add = async () => {
    const tickers = tickersIn(text);
    if (!tickers.length) return;
    setBusy(true);
    const have = new Set(watchlist().map((w) => w.permaticker));
    const missing: string[] = [];
    let added = 0;
    for (const ticker of tickers) {
      const hits = await api.stocks(ticker).catch(() => []);
      const hit = hits.find((h) => (h.ticker ?? "").toUpperCase() === ticker);
      if (!hit) missing.push(ticker);
      else if (!have.has(hit.permaticker)) {
        toggleWatch({ ticker: hit.ticker ?? ticker, name: hit.name, permaticker: hit.permaticker });
        have.add(hit.permaticker);
        added += 1;
      }
    }
    setBusy(false);
    setText("");
    setNote(`${added} added${missing.length ? `; not found: ${missing.join(", ")}` : ""}`);
  };
  return (
    <form
      className="flex items-center gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        void add();
      }}
    >
      {note && (
        <span role="status" className="text-[13px] text-ink-3">
          {note}
        </span>
      )}
      <input
        aria-label="Tickers to add"
        placeholder="AAPL, MSFT, NVDA"
        value={text}
        onChange={(event) => {
          setText(event.target.value);
          setNote(null);
        }}
        className="min-h-8 w-48 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
      />
      <Button type="submit" disabled={busy || !tickersIn(text).length}>
        {busy ? "Adding…" : "Add"}
      </Button>
    </form>
  );
}

export function StocksLanding() {
  const list = useWatchlist();
  const { data } = useLoad(() => api.screen(), "last");
  const rows = useMemo(() => (data ? rowsOf(data) : []), [data]);
  const byPerm = useMemo(() => new Map(rows.map((r) => [r.permaticker, r])), [rows]);
  const sectors = useMemo(() => sectorMonths(rows), [rows]);
  if (!data) return list.length ? <p className="text-ink-2">Loading the watchlist…</p> : null;
  return (
    <>
      <Watchlist list={list} rows={byPerm} on={data.on} />
      <div className="grid gap-4 xl:grid-cols-2">
        <Panel title={`Largest rises on ${day(data.on)}`}>
          <DataTable columns={moveColumns(data.on)} rows={movers(rows, "up")} rowKey={(r) => String(r.permaticker)} empty="No US stock above $2B rose that day." />
        </Panel>
        <Panel title={`Largest falls on ${day(data.on)}`}>
          <DataTable columns={moveColumns(data.on)} rows={movers(rows, "down")} rowKey={(r) => String(r.permaticker)} empty="No US stock above $2B fell that day." />
        </Panel>
      </div>
      {sectors.length > 0 && (
        <Panel title="Sectors over the last month" padded>
          <DivergingBars
            items={sectors}
            format={(v) => pct(v, 1)}
            onPick={(sector) => {
              window.location.hash = href({ page: "screener", name: "latest", tab: new URLSearchParams({ sector }).toString() });
            }}
          />
        </Panel>
      )}
    </>
  );
}
