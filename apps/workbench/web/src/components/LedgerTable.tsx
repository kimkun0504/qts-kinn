import { api, type LedgerHead } from "../lib/api";
import { day, int, money, pct } from "../lib/format";
import { href } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import { Card } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";

const columns: Column<LedgerHead>[] = [
  {
    key: "title",
    header: "Ledger",
    align: "left",
    render: (h) => (
      <a href={href({ page: "paper", name: h.name })} className="font-semibold text-ink no-underline hover:underline">
        {h.title}
      </a>
    ),
  },
  { key: "side", header: "Side", align: "left", muted: true, render: (h) => (h.side === "short" ? "Short" : "Long") },
  { key: "last", header: "Up to", render: (h) => day(h.last_evening, true) },
  { key: "signals", header: "Signals", render: (h) => int(h.summary.signals) },
  { key: "open", header: "Open", render: (h) => int(h.summary.open + h.summary.waiting) },
  { key: "closed", header: "Closed", render: (h) => int(h.summary.closed) },
  { key: "mean", header: "A trade after costs", signed: true, strong: true, render: (h) => pct(h.summary.mean) },
  { key: "won", header: "Won", render: (h) => (h.summary.closed ? `${h.summary.winners} of ${h.summary.closed}` : "–") },
  { key: "profit", header: "Profit at $2,000", signed: true, render: (h) => (h.summary.closed ? money(h.summary.profit) : "–") },
];

export function LedgerTable() {
  const { data, error } = useLoad(() => api.ledgers(), "home-ledgers");
  if (error || !data?.length) return null;
  return (
    <Card title="Leads on paper" aside="Every signal is recorded; no order is sent">
      <div className="-mx-5 overflow-x-auto">
        <DataTable columns={columns} rows={data} rowKey={(h) => h.name} minWidth={760} />
      </div>
    </Card>
  );
}
