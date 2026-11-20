import { type FormEvent, useEffect, useState } from "react";
import { BarChart } from "../components/charts/BarChart";
import { Card, Note } from "../components/ui/Card";
import { Segmented } from "../components/ui/Segmented";
import { StatStrip } from "../components/ui/StatStrip";
import { api, type CostEstimate, type CostLeg, type CostQuote } from "../lib/api";
import { compact, day, int, num } from "../lib/format";

const KEY = "kinn-costs";

interface Inputs {
  price: string;
  value: string;
  adv: string;
  side: "long" | "short";
  entry: "auction" | "marketable";
  exit: "auction" | "marketable";
}

const START: Inputs = { price: "20", value: "2000", adv: "5", side: "long", entry: "auction", exit: "auction" };

function saved(): Inputs {
  try {
    return { ...START, ...(JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<Inputs>) };
  } catch {
    return START;
  }
}

const dollars = (v: number) => `$${v.toFixed(v < 10 ? 2 : 0)}`;
const bps = (v: number) => `${num(v, 1)} bps`;
const field = "h-9 w-full rounded-md border border-line bg-surface px-2.5 text-right text-sm tabular-nums text-ink focus-visible:outline-2 focus-visible:outline-accent";

function Money({ id, label, unit, value, onChange }: { id: string; label: string; unit?: string; value: string; onChange: (value: string) => void }) {
  return (
    <label htmlFor={id} className="flex flex-col gap-1 text-[13px] text-ink-2">
      {label}
      <span className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-2.5 flex items-center text-ink-3">$</span>
        <input id={id} inputMode="decimal" autoComplete="off" value={value} onChange={(event) => onChange(event.target.value)} className={`${field} pl-6 ${unit ? "pr-8" : ""}`} />
        {unit && <span className="pointer-events-none absolute inset-y-0 right-2.5 flex items-center text-ink-3">{unit}</span>}
      </span>
    </label>
  );
}

export function legLabel(leg: CostLeg, short: boolean, opening: boolean): string {
  const what = opening ? (short ? "Sell short" : "Buy") : short ? "Buy back" : "Sell";
  const how = leg.fill === "auction" ? (opening ? "at the open" : "at the close") : "marketable";
  return `${what} ${how}`;
}

export function CostsPage() {
  const [inputs, setInputs] = useState<Inputs>(saved);
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ticker, setTicker] = useState("");
  const [quote, setQuote] = useState<CostQuote | null>(null);
  const [quoteError, setQuoteError] = useState<string | null>(null);
  const set = (patch: Partial<Inputs>) => setInputs((current) => ({ ...current, ...patch }));

  useEffect(() => {
    try {
      localStorage.setItem(KEY, JSON.stringify(inputs));
    } catch {
      return;
    }
  }, [inputs]);

  useEffect(() => {
    let live = true;
    const adv = inputs.adv.trim() ? String(Number(inputs.adv.replace(/,/g, "")) * 1e6) : "";
    const timer = window.setTimeout(() => {
      api
        .costs({ price: inputs.price.replace(/,/g, ""), value: inputs.value.replace(/,/g, ""), adv, side: inputs.side, entry: inputs.entry, exit: inputs.exit })
        .then((found) => {
          if (!live) return;
          setEstimate(found);
          setError(null);
        })
        .catch((e: Error) => {
          if (!live) return;
          setEstimate(null);
          setError(e.message);
        });
    }, 200);
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [inputs]);

  const lookUp = (event: FormEvent) => {
    event.preventDefault();
    if (!ticker.trim()) return;
    api
      .costQuote(ticker.trim())
      .then((found) => {
        setQuote(found);
        setQuoteError(null);
        set({ price: String(found.price), adv: found.adv != null ? String(Number((found.adv / 1e6).toPrecision(4))) : "" });
      })
      .catch(() => {
        setQuote(null);
        setQuoteError(`No stock ${ticker.trim().toUpperCase()} in the research data.`);
      });
  };

  const short = inputs.side === "short";
  const legs = estimate?.legs ?? [];
  const rows: [string, (leg: CostLeg) => number][] = [
    ["Commission", (leg) => leg.commission],
    ["Exchange, clearing and regulatory fees", (leg) => leg.fees],
    ["Slippage", (leg) => leg.slippage],
  ];
  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-5 lg:grid-cols-[340px_minmax(0,1fr)]">
        <Card title="The trade">
          <form onSubmit={lookUp} className="flex items-end gap-2">
            <label htmlFor="cost-ticker" className="flex min-w-0 flex-1 flex-col gap-1 text-[13px] text-ink-2">
              From a stock
              <input
                id="cost-ticker"
                autoComplete="off"
                spellCheck={false}
                value={ticker}
                placeholder="Ticker"
                onChange={(event) => setTicker(event.target.value)}
                className="h-9 w-full min-w-0 rounded-md border border-line bg-surface px-2.5 text-sm text-ink uppercase placeholder:text-ink-3 placeholder:normal-case focus-visible:outline-2 focus-visible:outline-accent"
              />
            </label>
            <button
              type="submit"
              className="h-9 cursor-pointer rounded-md border border-line bg-surface px-3 text-sm font-medium whitespace-nowrap text-ink hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent"
            >
              Look up
            </button>
          </form>
          {quote && (
            <Note>
              {quote.ticker}
              {quote.name ? ` (${quote.name})` : ""}: ${num(quote.price, 2)} on {day(quote.date)}, {quote.adv != null ? `${compact(quote.adv, "$")} traded a day over 20 sessions` : "no volume figure"}
              .
            </Note>
          )}
          {quoteError && <p className="m-0 text-[13px] text-neg">{quoteError}</p>}
          <div className="grid grid-cols-2 gap-3">
            <Money id="cost-price" label="Price" value={inputs.price} onChange={(price) => set({ price })} />
            <Money id="cost-value" label="Position" value={inputs.value} onChange={(value) => set({ value })} />
          </div>
          <Money id="cost-adv" label="Average daily dollar volume" unit="M" value={inputs.adv} onChange={(adv) => set({ adv })} />
          <div className="flex flex-col gap-1 text-[13px] text-ink-2">
            Side
            <Segmented
              label="Side"
              value={inputs.side}
              onChange={(side) => set({ side })}
              options={[
                { value: "long", label: "Long" },
                { value: "short", label: "Short" },
              ]}
            />
          </div>
          <div className="flex flex-col gap-3 text-[13px] text-ink-2">
            <div className="flex flex-col gap-1">
              Opens
              <Segmented
                label="Opens"
                value={inputs.entry}
                onChange={(entry) => set({ entry })}
                options={[
                  { value: "auction", label: "Open auction" },
                  { value: "marketable", label: "Marketable" },
                ]}
              />
            </div>
            <div className="flex flex-col gap-1">
              Closes
              <Segmented
                label="Closes"
                value={inputs.exit}
                onChange={(exit) => set({ exit })}
                options={[
                  { value: "auction", label: "Close auction" },
                  { value: "marketable", label: "Marketable" },
                ]}
              />
            </div>
          </div>
        </Card>
        <div className="flex min-w-0 flex-col gap-5">
          {error && (
            <p role="alert" className="m-0 rounded-lg border border-neg bg-surface px-4 py-3 text-sm text-neg">
              {error}
            </p>
          )}
          {estimate && (
            <>
              <StatStrip
                items={[
                  { label: "The round trip", value: dollars(estimate.cost), note: bps(estimate.bps) },
                  { label: "At 2× slippage", value: dollars(estimate.cost_2x), note: bps(estimate.bps_2x) },
                  { label: "To break even", value: `+${num(estimate.bps / 100, 2)}%`, note: `+${num(estimate.bps_2x / 100, 2)}% at 2×` },
                  { label: "Shares", value: int(legs[0]?.shares), note: `${compact(legs[0]?.value ?? 0, "$")} at $${num(estimate.price, 2)}` },
                ]}
              />
              <Card title="Where it goes" aside={estimate.model}>
                <table className="w-full border-collapse text-sm tabular-nums">
                  <thead>
                    <tr className="text-[13px] text-ink-2">
                      <th className="pb-2 text-left font-medium" />
                      {legs.map((leg, i) => (
                        <th key={i} className="pb-2 text-right font-medium">
                          {legLabel(leg, short, i === 0)}
                        </th>
                      ))}
                      <th className="pb-2 text-right font-medium">Both</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map(([label, value]) => (
                      <tr key={label} className="border-t border-line-soft">
                        <td className="py-2 pr-3 text-ink-2">{label}</td>
                        {legs.map((leg, i) => (
                          <td key={i} className="py-2 text-right">
                            {dollars(value(leg))}
                          </td>
                        ))}
                        <td className="py-2 text-right font-medium">{dollars(legs.reduce((a, leg) => a + value(leg), 0))}</td>
                      </tr>
                    ))}
                    <tr className="border-t border-line">
                      <td className="py-2 pr-3 font-semibold">Total</td>
                      {legs.map((leg, i) => (
                        <td key={i} className="py-2 text-right font-semibold">
                          {dollars(leg.commission + leg.fees + leg.slippage)}
                        </td>
                      ))}
                      <td className="py-2 text-right font-semibold">{dollars(estimate.cost)}</td>
                    </tr>
                  </tbody>
                </table>
                <Note>
                  An auction fill pays an allowance of {num(estimate.auction_bps, 0)} bps; a marketable fill pays the half-spread, {num(estimate.half_spread_bps, 1)} bps for this price and liquidity.
                  The Lab and the backtests charge the same model; every result is also shown at 2× slippage.
                </Note>
              </Card>
              <div className="grid gap-5 xl:grid-cols-2">
                <Card title="The round trip by position size" aside={`at $${num(estimate.price, 2)}`}>
                  <BarChart
                    neutral
                    title="Round-trip cost in basis points by position size"
                    labels={estimate.sizes.map((s) => compact(s.value, "$"))}
                    values={estimate.sizes.map((s) => s.bps)}
                    marked={estimate.sizes.map((s, i) => (Math.abs(s.value - (legs[0]?.value ?? 0)) < 1 ? i : -1)).filter((i) => i >= 0)}
                    format={bps}
                    height={200}
                    width={560}
                  />
                </Card>
                <Card title="The round trip by price" aside={`a ${compact(Number(inputs.value) || 0, "$")} position`}>
                  <BarChart
                    neutral
                    title="Round-trip cost in basis points by share price"
                    labels={estimate.prices.map((p) => `$${p.price}`)}
                    values={estimate.prices.map((p) => p.bps)}
                    format={bps}
                    height={200}
                    width={560}
                  />
                </Card>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
