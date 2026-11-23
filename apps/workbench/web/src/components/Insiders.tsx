import { useState } from "react";
import type { InsiderTrade, Insiders as InsidersData } from "../lib/api";
import { compact, day, int } from "../lib/format";
import { sortRows, useSort } from "../lib/sort";
import { CsvButton } from "./CsvButton";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";
import { Segmented } from "./ui/Segmented";

type Side = "all" | "buy" | "sell";

export function lastYear(rows: InsiderTrade[], end: string): { buys: number; bought: number; sells: number; sold: number } {
  const start = `${Number(end.slice(0, 4)) - 1}${end.slice(4)}`;
  const recent = rows.filter((r) => r.filed > start && r.filed <= end);
  const sum = (side: "buy" | "sell") => recent.filter((r) => r.side === side).reduce((total, r) => total + (r.amount ?? 0), 0);
  return { buys: recent.filter((r) => r.side === "buy").length, bought: sum("buy"), sells: recent.filter((r) => r.side === "sell").length, sold: sum("sell") };
}

const traded = (r: InsiderTrade) => (!r.traded_from ? "–" : r.traded_to && r.traded_to !== r.traded_from ? `${day(r.traded_from, true)} to ${day(r.traded_to)}` : day(r.traded_from));

const columns: Column<InsiderTrade>[] = [
  { key: "filed", header: "Filed", align: "left", sortable: true, render: (r) => day(r.filed) },
  { key: "insider", header: "Insider", align: "left", sortable: true, strong: true, max: 220, render: (r) => r.insider ?? "–" },
  { key: "role", header: "Role", align: "left", muted: true, max: 220, render: (r) => r.role || "–" },
  {
    key: "side",
    header: "Trade",
    align: "left",
    sortable: true,
    render: (r) => <span className={r.side === "buy" ? "font-semibold text-pos" : "text-ink-2"}>{r.side === "buy" ? "Bought" : "Sold"}</span>,
  },
  { key: "shares", header: "Shares", sortable: true, render: (r) => int(r.shares) },
  { key: "amount", header: "Value", sortable: true, render: (r) => compact(r.amount, "$") },
  { key: "traded", header: "Traded", muted: true, render: traded },
];

export function Insiders({ data, on, onPick }: { data: InsidersData; on?: string | null; onPick: (iso: string) => void }) {
  const [side, setSide] = useState<Side>("all");
  const [sort, onSort] = useSort({ key: "filed", dir: "desc" });
  const shown = sortRows(
    data.rows.filter((r) => side === "all" || r.side === side),
    sort,
    (row, key) => row[key as keyof InsiderTrade] as string | number | null,
  );
  const end = on ?? data.last ?? "";
  const year = end ? lastYear(data.rows, end) : null;
  const buys = data.rows.filter((r) => r.side === "buy").length;
  return (
    <Card
      title="Insider trades"
      aside={
        <div className="flex flex-wrap items-center gap-2">
          <Segmented
            label="Side"
            value={side}
            onChange={setSide}
            options={[
              { value: "all", label: `All ${int(data.rows.length)}` },
              { value: "buy", label: `Bought ${int(buys)}` },
              { value: "sell", label: `Sold ${int(data.rows.length - buys)}` },
            ]}
          />
          <CsvButton
            filename="insider_trades.csv"
            rows={shown}
            columns={[
              { header: "filed", value: (r) => r.filed },
              { header: "symbol", value: (r) => r.symbol },
              { header: "insider", value: (r) => r.insider },
              { header: "role", value: (r) => r.role },
              { header: "side", value: (r) => r.side },
              { header: "shares", value: (r) => r.shares },
              { header: "value", value: (r) => r.amount },
              { header: "traded_from", value: (r) => r.traded_from },
              { header: "traded_to", value: (r) => r.traded_to },
            ]}
          />
        </div>
      }
    >
      {year && (
        <p className="m-0 text-sm text-ink-2">
          In the year to {day(end)}: <span className="font-semibold text-ink">{int(year.buys)}</span> {year.buys === 1 ? "purchase" : "purchases"} worth{" "}
          <span className="font-semibold text-ink">{compact(year.bought, "$")}</span> and <span className="font-semibold text-ink">{int(year.sells)}</span> {year.sells === 1 ? "sale" : "sales"} worth{" "}
          <span className="font-semibold text-ink">{compact(year.sold, "$")}</span>.
        </p>
      )}
      <div className="-mx-5 max-h-[420px] overflow-auto">
        <DataTable
          columns={columns}
          rows={shown}
          rowKey={(r) => `${r.accession}-${r.side}-${r.insider}`}
          onRowClick={(r) => onPick(r.filed)}
          sort={sort}
          onSort={onSort}
          minWidth={860}
          empty="No open-market trades by insiders in the filings."
        />
      </div>
      <Note>
        Open-market purchases and sales reported on Form 4, filed {data.first ? `${day(data.first)} to ${day(data.last)}` : "so far"}; grants, option exercises and shares withheld for tax are left
        out.
        {data.count > data.rows.length && ` The latest ${int(data.rows.length)} of ${int(data.count)} are shown.`} Click a trade to see it on the chart.
      </Note>
    </Card>
  );
}
