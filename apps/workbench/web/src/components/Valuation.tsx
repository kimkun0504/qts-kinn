import { useMemo, useState } from "react";
import type { Financials, StockPageData } from "../lib/api";
import { day, num, pct, plainPct } from "../lib/format";
import { MULTIPLES, type Multiple, valuation } from "../lib/valuation";
import { LineChart } from "./charts/LineChart";
import { Card, Note } from "./ui/Card";
import { Segmented } from "./ui/Segmented";
import { StatStrip } from "./ui/StatStrip";

export function Valuation({ prices, financials, on }: { prices: StockPageData["prices"]; financials: Financials; on?: string | null }) {
  const choices = MULTIPLES.filter((m) => !m.dollarsOnly || financials.currency === "USD");
  const [multiple, setMultiple] = useState<Multiple>("pe");
  const spec = choices.find((m) => m.key === multiple) ?? choices[0];
  const v = useMemo(() => valuation(prices, financials.trailing, spec.key, on), [prices, financials, spec.key, on]);
  const yieldLike = spec.key === "fcf_yield";
  const show = (x: number | null) => (x == null ? "–" : yieldLike ? pct(x, 1).replace("+", "") : `${num(x, 1)}×`);
  const flat = (x: number | null) => v.value.map(() => x);
  const known = v.value.some((x) => x != null);
  return (
    <Card title="Valuation" aside={<Segmented label="Measure" value={spec.key} onChange={setMultiple} options={choices.map((m) => ({ value: m.key, label: m.label }))} />}>
      {!known ? (
        <Note>
          No {spec.long.toLowerCase()} to show: it needs a trailing year with{" "}
          {spec.key === "pe" ? "a profit" : spec.key === "ps" ? "revenue" : spec.key === "pb" ? "positive equity" : "free cash flow"} filed in the last 16 months.
        </Note>
      ) : (
        <>
          <StatStrip
            items={[
              { label: on ? `On ${day(on)}` : "Now", value: show(v.now), note: v.now == null ? "no figure that day" : undefined },
              { label: "Median", value: show(v.median), note: `since ${day(v.since)}` },
              { label: "Middle half", value: `${show(v.low)} to ${show(v.high)}` },
              {
                label: yieldLike ? "Higher yield than" : "Dearer than",
                value: v.rank == null ? "–" : plainPct(v.rank),
                note: "of the sessions shown",
              },
            ]}
          />
          <LineChart
            title={`${spec.long} by session`}
            labels={v.date}
            series={[
              { name: spec.long, short: spec.label, values: v.value, color: "var(--series-1)" },
              { name: "Median", short: "Median", values: flat(v.median), color: "var(--ink-3)", dash: "5 4" },
              { name: "Upper quartile", short: "75th", values: flat(v.high), color: "var(--ink-3)", dash: "1 4" },
              { name: "Lower quartile", short: "25th", values: flat(v.low), color: "var(--ink-3)", dash: "1 4" },
            ]}
            format={(x) => show(x)}
            height={260}
            width={1000}
          />
          <Note>
            The market value at each session&apos;s close {yieldLike ? "set against" : "divided by"} the latest trailing year filed before it (
            {spec.key === "pe" ? "net income" : spec.key === "ps" ? "revenue" : spec.key === "pb" ? "shareholders' equity" : "free cash flow"}
            ). Gaps are sessions with a loss, no equity or no filing in the last 16 months. The dotted lines mark the middle half of the sessions shown.
          </Note>
        </>
      )}
    </Card>
  );
}
