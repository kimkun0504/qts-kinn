import { useMemo } from "react";
import { api } from "../lib/api";
import { compact, day, int, num, pct } from "../lib/format";
import { median, rowsOf, type ScreenRow } from "../lib/screen";
import { useLoad } from "../lib/useLoad";
import { StockLink } from "./StockLink";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";
import { StatStrip } from "./ui/StatStrip";

const SHOWN = 15;

export function peersOf(rows: ScreenRow[], permaticker: number, industry: string | null): { peers: ScreenRow[]; rank: number | null; total: number } {
  if (!industry) return { peers: [], rank: null, total: 0 };
  const all = rows.filter((r) => r.industry === industry).sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0));
  const at = all.findIndex((r) => r.permaticker === permaticker);
  const top = all.slice(0, SHOWN);
  const peers = at >= SHOWN ? [...top.slice(0, SHOWN - 1), all[at]] : top;
  return { peers, rank: at >= 0 ? at + 1 : null, total: all.length };
}

const ratio = (v: number | null | undefined) => (v == null ? "–" : num(v, 1));

export function Peers({ permaticker, symbol, industry, on }: { permaticker: number; symbol: string; industry: string | null; on?: string | null }) {
  const { data, error } = useLoad(() => api.screen(on ?? undefined), on ?? "last");
  const rows = useMemo(() => (data ? rowsOf(data) : []), [data]);
  const { peers, rank, total } = useMemo(() => peersOf(rows, permaticker, industry), [rows, permaticker, industry]);
  if (error) return <p className="m-0 text-ink-2">The peers could not be read. Restart the Workbench server if it was updated.</p>;
  if (!data) return <p className="m-0 text-ink-2">Reading every stock on {on ? day(on) : "the last session"}…</p>;
  if (!industry || !total) return <p className="m-0 text-ink-2">No industry on record for this company, so no peers.</p>;
  const all = rows.filter((r) => r.industry === industry);
  const self = all.find((r) => r.permaticker === permaticker);
  const columns: Column<ScreenRow>[] = [
    { key: "symbol", header: "Symbol", align: "left", render: (r) => <StockLink symbol={r.symbol} on={data.on} /> },
    { key: "name", header: "Company", align: "left", muted: true, max: 220, render: (r) => r.name ?? "–" },
    { key: "market_cap", header: "Market value", render: (r) => compact(r.market_cap, "$") },
    { key: "ret_1y", header: "1 year", signed: true, render: (r) => pct(r.ret_1y, 1) },
    { key: "from_high", header: "From 52-week high", signed: true, render: (r) => pct(r.from_high, 1) },
    { key: "pe", header: "P/E", render: (r) => ratio(r.pe) },
    { key: "ps", header: "P/S", render: (r) => ratio(r.ps) },
    { key: "pb", header: "P/B", render: (r) => ratio(r.pb) },
    { key: "revenue_growth", header: "Revenue growth", signed: true, render: (r) => pct(r.revenue_growth, 1) },
    { key: "fcf_yield", header: "FCF yield", signed: true, render: (r) => pct(r.fcf_yield, 1) },
  ];
  const against = (label: string, key: keyof ScreenRow, format: (v: number | null) => string) => ({
    label: `${label}, industry median`,
    value: format(median(all.map((r) => r[key] as number | null))),
    note: `${symbol} ${format((self?.[key] as number | null) ?? null)}`,
  });
  return (
    <Card title={`${industry} on ${day(data.on)}`}>
      <StatStrip
        items={[
          { label: "Companies that traded", value: int(total), note: rank ? `${symbol} is number ${rank} by market value` : `${symbol} did not trade that day` },
          against("1-year return", "ret_1y", (v) => pct(v, 1)),
          against("P/E", "pe", ratio),
          against("Revenue growth", "revenue_growth", (v) => pct(v, 1)),
        ]}
      />
      <div className="-mx-5 overflow-x-auto">
        <DataTable columns={columns} rows={peers} rowKey={(r) => String(r.permaticker)} selectedKey={String(permaticker)} minWidth={980} />
      </div>
      <Note>
        The largest {Math.min(SHOWN, total)} of the {int(total)} companies in the industry by market value{rank && rank > SHOWN ? `, and ${symbol}` : ""}. Valuations use filings made before the day;
        P/E only for profitable companies.{" "}
        <a href={`#/screener/${data.on}/${encodeURIComponent(new URLSearchParams({ kind: "all", industry }).toString())}`} className="font-medium text-accent no-underline hover:underline">
          Screen the whole industry
        </a>
      </Note>
    </Card>
  );
}
