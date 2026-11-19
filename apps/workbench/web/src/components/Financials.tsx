import { useState } from "react";
import type { FinancialPeriod, Financials as FinancialsData } from "../lib/api";
import { compact, day, num, pct } from "../lib/format";
import { BarChart } from "./charts/BarChart";
import { CsvButton } from "./CsvButton";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";
import { Segmented } from "./ui/Segmented";

type Basis = "quarterly" | "trailing";

interface Line {
  key: string;
  label: string;
  value: (rows: FinancialPeriod[], i: number) => number | null;
  format: (v: number | null) => string;
  signed?: boolean;
  local?: boolean;
}

const COLUMNS = 8;
const CHART = 24;

const money = (v: number | null) => compact(v, "$");
const share = (v: number | null) => (v == null ? "–" : `${v < 0 ? "−" : ""}${Math.abs(100 * v).toFixed(1)}%`);
const ratio = (top: number | null, bottom: number | null) => (top == null || bottom == null || bottom <= 0 ? null : top / bottom);
const field = (name: keyof FinancialPeriod) => (rows: FinancialPeriod[], i: number) => rows[i][name] as number | null;

export const LINES: Line[] = [
  { key: "revenueusd", label: "Revenue", value: field("revenueusd"), format: money },
  { key: "growth", label: "Revenue growth, year on year", value: (rows, i) => (i >= 4 ? growth(rows[i].revenueusd, rows[i - 4].revenueusd) : null), format: (v) => pct(v, 1), signed: true },
  { key: "gp", label: "Gross profit", value: field("gp"), format: money, signed: true, local: true },
  { key: "gross_margin", label: "Gross margin", value: (rows, i) => ratio(rows[i].gp, rows[i].revenueusd), format: share, signed: true, local: true },
  { key: "opinc", label: "Operating income", value: field("opinc"), format: money, signed: true, local: true },
  { key: "operating_margin", label: "Operating margin", value: (rows, i) => ratio(rows[i].opinc, rows[i].revenueusd), format: share, signed: true, local: true },
  { key: "netinccmnusd", label: "Net income", value: field("netinccmnusd"), format: money, signed: true },
  { key: "net_margin", label: "Net margin", value: (rows, i) => ratio(rows[i].netinccmnusd, rows[i].revenueusd), format: share, signed: true },
  { key: "epsusd", label: "Earnings per share", value: field("epsusd"), format: (v) => (v == null ? "–" : `${v < 0 ? "−" : ""}$${num(Math.abs(v), 2)}`), signed: true },
  { key: "ncfo", label: "Operating cash flow", value: field("ncfo"), format: money, signed: true, local: true },
  { key: "capex", label: "Capital spending", value: field("capex"), format: money, signed: true, local: true },
  { key: "fcf", label: "Free cash flow", value: field("fcf"), format: money, signed: true, local: true },
  { key: "cashnequsd", label: "Cash", value: field("cashnequsd"), format: money },
  { key: "debtusd", label: "Debt", value: field("debtusd"), format: money },
  { key: "equityusd", label: "Shareholders' equity", value: field("equityusd"), format: money, signed: true },
  { key: "sharesbas", label: "Shares outstanding", value: field("sharesbas"), format: (v) => compact(v) },
];

function growth(now: number | null, before: number | null): number | null {
  return now == null || before == null || before <= 0 ? null : now / before - 1;
}

export function periodLabel(iso: string, basis: Basis, short = false): string {
  const [year, month] = iso.split("-").map(Number);
  const quarter = `Q${Math.ceil(month / 3)}`;
  const y = short ? `’${String(year).slice(2)}` : String(year);
  return basis === "trailing" && !short ? `Year to ${quarter} ${y}` : `${quarter} ${y}`;
}

export function Financials({ data, on }: { data: FinancialsData; on?: string | null }) {
  const [basis, setBasis] = useState<Basis>(data.quarterly.length ? "quarterly" : "trailing");
  const [chosen, setChosen] = useState("revenueusd");
  const rows = data[basis];
  if (!data.quarterly.length && !data.trailing.length) return null;
  const line = LINES.find((l) => l.key === chosen) ?? LINES[0];
  const shown = rows.map((_, i) => i).slice(-COLUMNS);
  const charted = rows.map((_, i) => i).slice(-CHART);
  const later = (i: number) => Boolean(on && rows[i].filed && rows[i].filed! >= on);
  const columns: Column<Line>[] = [
    { key: "label", header: basis === "quarterly" ? "Quarter" : "Trailing year", align: "left", strong: true, render: (l) => l.label },
    ...shown.map((i) => ({
      key: rows[i].period,
      header: periodLabel(rows[i].period, basis),
      signed: true,
      muted: later(i),
      render: (l: Line) => l.format(l.value(rows, i)),
    })),
  ];
  return (
    <Card
      title="Financials"
      aside={
        <div className="flex flex-wrap items-center gap-2">
          <Segmented
            label="Periods"
            value={basis}
            onChange={setBasis}
            options={[
              { value: "quarterly", label: "Quarterly" },
              { value: "trailing", label: "Trailing year" },
            ]}
          />
          <CsvButton
            filename={`financials_${basis}.csv`}
            rows={rows}
            columns={[
              { header: "period", value: (r) => r.period },
              { header: "filed", value: (r) => r.filed },
              ...LINES.filter((l) => !["growth", "gross_margin", "operating_margin", "net_margin"].includes(l.key)).map((l) => ({
                header: l.key,
                value: (r: FinancialPeriod) => r[l.key as keyof FinancialPeriod],
              })),
            ]}
          />
        </div>
      }
    >
      {rows.length === 0 ? (
        <Note>No {basis === "quarterly" ? "quarterly" : "trailing-year"} filings for this company in the research data.</Note>
      ) : (
        <>
          <div className="text-[13px] font-medium text-ink">{line.label}</div>
          <BarChart
            neutral
            title={`${line.label} by ${basis === "quarterly" ? "quarter" : "trailing year"}`}
            labels={charted.map((i) => periodLabel(rows[i].period, basis, true))}
            values={charted.map((i) => line.value(rows, i))}
            format={(v) => line.format(v)}
            height={200}
            width={1000}
            labelEvery={charted.length > 16 ? 2 : 1}
          />
          <div className="-mx-5 overflow-x-auto">
            <DataTable columns={columns} rows={LINES} rowKey={(l) => l.key} selectedKey={chosen} onRowClick={(l) => setChosen(l.key)} minWidth={900} />
          </div>
          <Note>
            Each period as filed, the latest filing for it before the seal; the last one was filed {day(rows[rows.length - 1].filed)}. Click a line to chart it.
            {data.currency !== "USD" && ` Gross profit, operating income and the cash flows are in ${data.currency}; the rest in US dollars.`}
            {on && " Periods filed on or after the day you came from are greyed."}
          </Note>
        </>
      )}
    </Card>
  );
}
