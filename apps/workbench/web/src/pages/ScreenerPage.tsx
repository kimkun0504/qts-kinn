import { useEffect, useMemo, useRef, useState } from "react";
import { CsvButton } from "../components/CsvButton";
import { StockLink } from "../components/StockLink";
import { Bars } from "../components/ui/Bars";
import { Button } from "../components/ui/Button";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import { StatStrip } from "../components/ui/StatStrip";
import { api, type ScreenAhead } from "../lib/api";
import { compact, day, int, num, pct, plainPct, price } from "../lib/format";
import { href, type Route } from "../lib/route";
import { bounds, type Condition, decode, EMPTY, encode, FIELD, FIELDS, KINDS, matcher, median, NEXT, rowsOf, type Screen, type ScreenKey, type ScreenRow, STARTS } from "../lib/screen";
import { sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";
import { toggleWatch, watchlist } from "../lib/watchlist";
import { compareWith } from "../components/RelativeChart";

const PAGE = 100;

export function screenerRoute(on: string | undefined, query: string): Route {
  return {
    page: "screener",
    name: on ?? (query ? "latest" : undefined),
    tab: query || undefined,
  };
}
const SAVED_KEY = "kinn-screens";

type View = "overview" | "performance" | "valuation" | "next";

interface Saved {
  name: string;
  query: string;
}

export function readSaved(): Saved[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(SAVED_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((s) => typeof s?.name === "string" && typeof s?.query === "string") : [];
  } catch {
    return [];
  }
}

function writeSaved(saved: Saved[]) {
  try {
    localStorage.setItem(SAVED_KEY, JSON.stringify(saved));
  } catch {
    return;
  }
}

const control = "min-h-8 rounded-md border border-line bg-surface px-2 text-[13px] text-ink focus:border-accent focus:outline-none";

const money = (v: number | null) => compact(v, "$");
const ratio = (v: number | null) => (v == null ? "–" : num(v, 1));

function show(key: ScreenKey, row: ScreenRow): string {
  const value = row[key];
  const kind = FIELD[key].kind;
  if (key === "vol_60") return plainPct(value, 1);
  if (kind === "money") return money(value);
  if (kind === "percent") return pct(value, 1);
  if (kind === "price") return price(value);
  return ratio(value);
}

function numeric(key: ScreenKey, header?: string): Column<ScreenRow> {
  const kind = FIELD[key].kind;
  return {
    key,
    header: header ?? FIELD[key].label,
    sortable: true,
    signed: kind === "percent" || key === "net_income",
    render: (r) => show(key, r),
  };
}

function columns(view: View, on: string, picked: Set<number>, onPick: (row: ScreenRow) => void, known: Record<string, boolean> = {}): Column<ScreenRow>[] {
  const head: Column<ScreenRow>[] = [
    {
      key: "pick",
      header: "",
      align: "left",
      render: (r) => (
        <input type="checkbox" aria-label={`Pick ${r.symbol}`} checked={picked.has(r.permaticker)} onClick={(event) => event.stopPropagation()} onChange={() => onPick(r)} className="cursor-pointer" />
      ),
    },
    {
      key: "symbol",
      header: "Symbol",
      align: "left",
      sortable: true,
      render: (r) => <StockLink symbol={r.symbol} on={on} />,
    },
    {
      key: "name",
      header: "Company",
      align: "left",
      sortable: true,
      max: 200,
      render: (r) => r.name ?? "–",
    },
  ];
  if (view === "performance")
    return [
      ...head,
      numeric("close"),
      numeric("ret_1d", "1 day"),
      numeric("ret_1m", "1 month"),
      numeric("ret_3m", "3 months"),
      numeric("ret_6m", "6 months"),
      numeric("ret_1y", "1 year"),
      numeric("from_high", "From 52-week high"),
      numeric("vol_60", "Volatility, 60 days"),
    ];
  if (view === "next")
    return [
      ...head,
      numeric("market_cap"),
      numeric("ret_1y", "Year before"),
      ...NEXT.filter((n) => known[n.key]).map((n) => ({ key: n.key, header: n.label, sortable: true, signed: true, strong: n.key === "next_3m", render: (r: ScreenRow) => pct(r[n.key], 1) })),
      { key: "stopped", header: "Stopped trading", sortable: true, muted: true, render: (r: ScreenRow) => (r.stopped ? day(r.stopped) : "") },
    ];
  if (view === "valuation")
    return [
      ...head,
      numeric("market_cap"),
      numeric("pe", "P/E"),
      numeric("ps", "P/S"),
      numeric("pb", "P/B"),
      numeric("fcf_yield", "FCF yield"),
      numeric("revenue", "Revenue"),
      numeric("revenue_growth", "Revenue growth"),
      numeric("net_income", "Net income"),
      {
        key: "filed",
        header: "Last filing",
        sortable: true,
        muted: true,
        render: (r) => day(r.filed),
      },
    ];
  return [
    ...head,
    {
      key: "sector",
      header: "Sector",
      align: "left",
      sortable: true,
      muted: true,
      max: 150,
      render: (r) => r.sector ?? "–",
    },
    {
      key: "industry",
      header: "Industry",
      align: "left",
      sortable: true,
      muted: true,
      max: 170,
      render: (r) => r.industry ?? "–",
    },
    numeric("close"),
    numeric("market_cap"),
    numeric("adv20", "Dollar volume"),
    numeric("ret_1y", "1 year"),
  ];
}

function counts(rows: ScreenRow[], key: "sector" | "industry" | "exchange"): [string, number][] {
  const out = new Map<string, number>();
  for (const row of rows) {
    const value = row[key];
    if (value) out.set(value, (out.get(value) ?? 0) + 1);
  }
  return [...out].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

function Pick({ label, value, onChange, all, items }: { label: string; value: string; onChange: (v: string) => void; all: string; items: [string, number][] }) {
  return (
    <label className="inline-flex">
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} className={`${control} max-w-56 cursor-pointer font-medium`}>
        <option value="">{all}</option>
        {items.map(([name, n]) => (
          <option key={name} value={name}>
            {name} ({int(n)})
          </option>
        ))}
        {value && !items.some(([name]) => name === value) && <option value={value}>{value} (0)</option>}
      </select>
    </label>
  );
}

const PLACEHOLDERS: Record<string, [string, string]> = {
  money: ["300M", "2B"],
  percent: ["−20", "50"],
  ratio: ["0", "15"],
  price: ["5", "100"],
};
const UNITS: Record<string, string> = {
  money: "$",
  percent: "%",
  ratio: "×",
  price: "$",
};

function ConditionRow({ condition, onChange, onRemove }: { condition: Condition; onChange: (c: Condition) => void; onRemove: () => void }) {
  const field = FIELD[condition.field];
  const parsed = bounds(condition);
  const [low, high] = PLACEHOLDERS[field.kind];
  const box = (bad: boolean) => `${control} w-24 tabular-nums ${bad ? "border-neg" : ""}`;
  return (
    <li className="flex flex-wrap items-center gap-2">
      <label className="inline-flex">
        <span className="sr-only">Measure</span>
        <select value={condition.field} onChange={(event) => onChange({ ...condition, field: event.target.value as ScreenKey })} className={`${control} w-56 cursor-pointer font-medium`}>
          {FIELDS.map((f) => (
            <option key={f.key} value={f.key}>
              {f.label}
            </option>
          ))}
        </select>
      </label>
      <input
        aria-label={`${field.label}, at least`}
        placeholder={low}
        value={condition.min}
        onChange={(event) => onChange({ ...condition, min: event.target.value })}
        className={box(parsed.min == null && condition.min.trim() !== "")}
      />
      <span className="text-[13px] text-ink-3">to</span>
      <input
        aria-label={`${field.label}, at most`}
        placeholder={high}
        value={condition.max}
        onChange={(event) => onChange({ ...condition, max: event.target.value })}
        className={box(parsed.max == null && condition.max.trim() !== "")}
      />
      <span className="w-3 text-[13px] text-ink-3">{UNITS[field.kind]}</span>
      <button type="button" onClick={onRemove} className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent">
        Remove
      </button>
    </li>
  );
}

function AheadSummary({ ahead, passing, every }: { ahead: ScreenAhead; passing: ScreenRow[]; every: ScreenRow[] }) {
  const rows = NEXT.filter((n) => ahead.known[n.key]).map((n) => ({
    key: n.key,
    label: n.label,
    passing: median(passing.map((r) => r[n.key] ?? null)),
    every: median(every.map((r) => r[n.key] ?? null)),
    spy: ahead.spy[n.key] ?? null,
  }));
  return (
    <div className="border-b border-line">
      <DataTable
        rows={rows}
        rowKey={(r) => r.key}
        columns={[
          { key: "label", header: `From the close of ${day(ahead.on)}`, align: "left", strong: true, render: (r) => r.label },
          { key: "passing", header: "Median of the stocks that pass", signed: true, strong: true, render: (r) => pct(r.passing, 1) },
          { key: "every", header: "Median of every stock that traded", signed: true, render: (r) => pct(r.every, 1) },
          { key: "spy", header: "SPY", signed: true, render: (r) => pct(r.spy, 1) },
        ]}
      />
      <p className="m-0 px-4 py-2.5 text-[13px] text-ink-3">
        Price change from the close of the screen's day, split-adjusted, without dividends, up to {day(ahead.through)}; a stock that stopped trading counts to its last close. Looking at what came next
        is research on the same years the strategies are tested on.
      </p>
    </div>
  );
}

interface ScreenerPageProps {
  on?: string;
  query?: string;
  onDate: (on: string | undefined, query: string) => void;
}

export function ScreenerPage({ on, query, onDate }: ScreenerPageProps) {
  const [screen, setScreen] = useState<Screen>(() => decode(query));
  const [view, setView] = useState<View>("overview");
  const [sort, onSort] = useSort({ key: "market_cap", dir: "desc" });
  const [page, setPage] = useState(0);
  const [saved, setSaved] = useState<Saved[]>(readSaved);
  const [naming, setNaming] = useState<string | null>(null);
  const { data, error } = useLoad(() => api.screen(on), on ?? "last");
  const all = useMemo(() => (data ? rowsOf(data) : []), [data]);
  const encoded = encode(screen);

  useEffect(() => {
    window.history.replaceState(null, "", href(screenerRoute(on, encoded)));
  }, [on, encoded]);
  useEffect(() => setPage(0), [encoded, sort, on]);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (box.current) box.current.scrollTop = 0;
  }, [page, encoded, sort]);

  const canLookAhead = Boolean(data && data.on < data.last);
  const activeView: View = view === "next" && !canLookAhead ? "overview" : view;
  const { data: ahead } = useLoad(() => (activeView === "next" && data ? api.screenAhead(data.on) : Promise.resolve(null)), activeView === "next" && data ? `ahead-${data.on}` : "none");
  const withAhead = useMemo(() => {
    if (!ahead) return all;
    const found = new Map(ahead.rows.map((r) => [r[0] as number, r]));
    return all.map((row) => {
      const values = found.get(row.permaticker);
      return values ? { ...row, ...Object.fromEntries(ahead.columns.map((name, i) => [name, values[i]])), permaticker: row.permaticker } : row;
    });
  }, [all, ahead]);
  const kindRows = useMemo(() => all.filter(matcher({ ...EMPTY, kind: screen.kind })), [all, screen.kind]);
  const sectors = useMemo(() => counts(kindRows, "sector"), [kindRows]);
  const industries = useMemo(() => counts(screen.sector ? kindRows.filter((r) => r.sector === screen.sector) : kindRows, "industry"), [kindRows, screen.sector]);
  const exchanges = useMemo(() => counts(kindRows, "exchange"), [kindRows]);
  const matched = useMemo(() => withAhead.filter(matcher(screen)), [withAhead, screen]);
  const shown = useMemo(() => sortRows(matched, sort, (row, key) => row[key as keyof ScreenRow]), [matched, sort]);
  const bySector = useMemo(() => counts(matched, "sector"), [matched]);
  const byIndustry = useMemo(() => counts(matched, "industry"), [matched]);

  const [picked, setPicked] = useState<Map<number, ScreenRow>>(new Map());
  const [watched, setWatched] = useState<string | null>(null);
  const togglePick = (row: ScreenRow) => {
    setWatched(null);
    setPicked((current) => {
      const next = new Map(current);
      if (next.has(row.permaticker)) next.delete(row.permaticker);
      else if (next.size < 20) next.set(row.permaticker, row);
      return next;
    });
  };
  const watchPicked = () => {
    const have = new Set(watchlist().map((w) => w.permaticker));
    const added = [...picked.values()].filter((r) => !have.has(r.permaticker));
    for (const r of added) toggleWatch({ ticker: r.symbol, name: r.name, permaticker: r.permaticker });
    setWatched(`${added.length} added to the watchlist${added.length < picked.size ? `, ${picked.size - added.length} already on it` : ""}`);
    setPicked(new Map());
  };
  const chartPicked = () => {
    const [first, ...rest] = [...picked.values()];
    compareWith(rest.map((r) => r.symbol));
    window.location.hash = href({ page: "stock", name: first.symbol, tab: String(first.permaticker) });
  };
  const update = (next: Partial<Screen>) => setScreen((current) => ({ ...current, ...next }));
  const setCondition = (i: number, c: Condition) =>
    update({
      conditions: screen.conditions.map((old, j) => (j === i ? c : old)),
    });
  const used = new Set(screen.conditions.map((c) => c.field));
  const addCondition = () =>
    update({
      conditions: [
        ...screen.conditions,
        {
          field: FIELDS.find((f) => !used.has(f.key))?.key ?? "market_cap",
          min: "",
          max: "",
        },
      ],
    });
  const current = saved.find((s) => s.query === encoded);
  const start = (value: string) => {
    if (value.startsWith("start:")) setScreen(STARTS[Number(value.slice(6))].screen);
    if (value.startsWith("saved:")) setScreen(decode(saved[Number(value.slice(6))]?.query));
  };
  const save = (name: string) => {
    const clean = name.trim();
    if (!clean) return;
    const next = [...saved.filter((s) => s.name !== clean), { name: clean, query: encoded }].sort((a, b) => a.name.localeCompare(b.name));
    setSaved(next);
    writeSaved(next);
    setNaming(null);
  };
  const forget = (name: string) => {
    const next = saved.filter((s) => s.name !== name);
    setSaved(next);
    writeSaved(next);
  };

  if (error) return <EmptyState title="Could not screen the stocks">The Workbench server needs a data build and a restart after an update.</EmptyState>;
  const asOf = data?.on ?? on;
  const rows = shown.slice(page * PAGE, (page + 1) * PAGE);
  return (
    <div className="flex flex-col gap-4">
      <Panel
        title="Screen"
        aside={
          <div className="flex flex-wrap items-center gap-2">
            <label className="inline-flex items-center gap-2">
              <span className="text-ink-2">On</span>
              <input
                type="date"
                aria-label="Screen as of"
                min={data?.first ?? "2000-01-01"}
                max={data?.last}
                value={asOf ?? ""}
                onChange={(event) => event.target.value && onDate(event.target.value, encoded)}
                className={`${control} tabular-nums`}
              />
            </label>
            {on && data && on !== data.last && (
              <Button onClick={() => onDate(undefined, encoded)} title="Screen as of the last session before the seal">
                Last session
              </Button>
            )}
          </div>
        }
        padded
      >
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="search"
              aria-label="Find a company"
              placeholder="Symbol or company"
              value={screen.text}
              onChange={(event) => update({ text: event.target.value })}
              className={`${control} w-52 placeholder:text-ink-3`}
            />
            <label className="inline-flex">
              <span className="sr-only">Kind of security</span>
              <select value={screen.kind} onChange={(event) => update({ kind: event.target.value, sector: "", industry: "" })} className={`${control} cursor-pointer font-medium`}>
                {KINDS.map((k) => (
                  <option key={k.value} value={k.value}>
                    {k.label}
                  </option>
                ))}
              </select>
            </label>
            <Pick label="Sector" value={screen.sector} onChange={(sector) => update({ sector, industry: "" })} all="Every sector" items={sectors} />
            <Pick label="Industry" value={screen.industry} onChange={(industry) => update({ industry })} all="Every industry" items={industries} />
            <Pick label="Exchange" value={screen.exchange} onChange={(exchange) => update({ exchange })} all="Every exchange" items={exchanges} />
          </div>
          {screen.conditions.length > 0 && (
            <ul className="m-0 flex list-none flex-col gap-2 p-0">
              {screen.conditions.map((c, i) => (
                <ConditionRow
                  key={i}
                  condition={c}
                  onChange={(next) => setCondition(i, next)}
                  onRemove={() =>
                    update({
                      conditions: screen.conditions.filter((_, j) => j !== i),
                    })
                  }
                />
              ))}
            </ul>
          )}
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={addCondition}>Add a filter</Button>
            <label className="inline-flex">
              <span className="sr-only">Start from a screen</span>
              <select value="" onChange={(event) => start(event.target.value)} className={`${control} cursor-pointer font-medium`}>
                <option value="">Start from…</option>
                <optgroup label="Starting points">
                  {STARTS.map((s, i) => (
                    <option key={s.name} value={`start:${i}`}>
                      {s.name}
                    </option>
                  ))}
                </optgroup>
                {saved.length > 0 && (
                  <optgroup label="Saved screens">
                    {saved.map((s, i) => (
                      <option key={s.name} value={`saved:${i}`}>
                        {s.name}
                      </option>
                    ))}
                  </optgroup>
                )}
              </select>
            </label>
            {naming == null ? (
              <Button onClick={() => setNaming(current?.name ?? "")} disabled={!encoded}>
                Save screen
              </Button>
            ) : (
              <form
                className="inline-flex items-center gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  save(naming);
                }}
              >
                <input
                  autoFocus
                  aria-label="Name of the screen"
                  placeholder="Name"
                  value={naming}
                  onChange={(event) => setNaming(event.target.value)}
                  onKeyDown={(event) => event.key === "Escape" && setNaming(null)}
                  className={`${control} w-48`}
                />
                <Button type="submit" variant="primary" disabled={!naming.trim()}>
                  Save
                </Button>
                <Button onClick={() => setNaming(null)}>Cancel</Button>
              </form>
            )}
            {current && naming == null && (
              <button
                type="button"
                onClick={() => forget(current.name)}
                className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent"
              >
                Delete “{current.name}”
              </button>
            )}
            <div className="flex-1" />
            {encoded && (
              <button
                type="button"
                onClick={() => setScreen(EMPTY)}
                className="cursor-pointer text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent"
              >
                Clear the screen
              </button>
            )}
          </div>
        </div>
      </Panel>
      {!data ? (
        <p className="text-ink-2">Screening every stock on {asOf ? day(asOf) : "the last session"}…</p>
      ) : (
        <>
          <StatStrip
            items={[
              {
                label: "Stocks that pass",
                value: int(matched.length),
                note: `of ${int(all.length)} that traded on ${day(data.on)}`,
              },
              {
                label: "Median 1-year return",
                value: pct(median(matched.map((r) => r.ret_1y)), 1),
              },
              {
                label: "Median P/E",
                value: ratio(median(matched.map((r) => r.pe))),
                note: "profitable companies",
              },
              {
                label: "Combined market value",
                value: money(matched.reduce((sum, r) => sum + (r.market_cap ?? 0), 0)),
              },
            ]}
          />
          <Panel
            title={`${int(matched.length)} ${matched.length === 1 ? "stock" : "stocks"} on ${day(data.on)}`}
            aside={
              <div className="flex flex-wrap items-center gap-2">
                <Segmented
                  label="Columns"
                  value={activeView}
                  onChange={setView}
                  options={[
                    { value: "overview", label: "Overview" },
                    { value: "performance", label: "Performance" },
                    { value: "valuation", label: "Valuation" },
                    ...(canLookAhead ? [{ value: "next" as const, label: "What came next" }] : []),
                  ]}
                />
                <CsvButton
                  filename={`screen-${data.on}.csv`}
                  rows={shown}
                  columns={[
                    { header: "symbol", value: (r) => r.symbol },
                    { header: "company", value: (r) => r.name },
                    { header: "sector", value: (r) => r.sector },
                    { header: "industry", value: (r) => r.industry },
                    { header: "category", value: (r) => r.category },
                    { header: "exchange", value: (r) => r.exchange },
                    ...FIELDS.map((f) => ({
                      header: f.key,
                      value: (r: ScreenRow) => r[f.key],
                    })),
                    { header: "last_filing", value: (r) => r.filed },
                  ]}
                />
              </div>
            }
          >
            {activeView === "next" &&
              (ahead ? <AheadSummary ahead={ahead} passing={matched} every={withAhead} /> : <p className="m-0 border-b border-line px-4 py-3 text-[13px] text-ink-2">Reading what came next…</p>)}
            {picked.size > 0 && (
              <div className="flex flex-wrap items-center gap-2 border-b border-line bg-raised px-4 py-2 text-[13px]">
                <span className="font-medium text-ink">{[...picked.values()].map((r) => r.symbol).join(", ")}</span>
                <div className="flex-1" />
                <Button onClick={watchPicked}>Add to the watchlist</Button>
                <Button onClick={chartPicked} disabled={picked.size < 2} title="The first on its stock page, the rest beside it">
                  Chart them together
                </Button>
                <Button onClick={() => setPicked(new Map())}>Clear</Button>
              </div>
            )}
            {picked.size === 0 && watched && (
              <div role="status" className="flex flex-wrap items-center gap-2 border-b border-line bg-raised px-4 py-2 text-[13px] text-ink">
                {watched}.
                <a href={href({ page: "stock" })} className="font-medium text-accent no-underline hover:underline">
                  See the watchlist
                </a>
              </div>
            )}
            <div ref={box} className="max-h-[max(420px,68vh)] overflow-y-auto">
              <DataTable
                columns={columns(activeView, data.on, new Set(picked.keys()), togglePick, ahead?.known)}
                rows={rows}
                rowKey={(r) => String(r.permaticker)}
                onRowClick={(r) => {
                  window.location.hash = href({
                    page: "stock",
                    name: r.symbol,
                    tab: data.on,
                  });
                }}
                sort={sort}
                onSort={onSort}
                minWidth={900}
                empty="No stock passes this screen. Loosen a filter or clear the screen."
              />
            </div>
            {shown.length > PAGE && (
              <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-2.5 text-[13px] text-ink-2">
                <span className="tabular-nums">
                  {int(page * PAGE + 1)} to {int(Math.min(shown.length, (page + 1) * PAGE))} of {int(shown.length)}
                </span>
                <div className="flex gap-2">
                  <Button onClick={() => setPage(page - 1)} disabled={page === 0}>
                    Previous
                  </Button>
                  <Button onClick={() => setPage(page + 1)} disabled={(page + 1) * PAGE >= shown.length}>
                    Next
                  </Button>
                </div>
              </div>
            )}
          </Panel>
          {screen.sector
            ? byIndustry.length > 0 && (
                <Panel title={`Industries in ${screen.sector}`} padded>
                  <Bars
                    items={byIndustry}
                    total={matched.length}
                    picked={screen.industry}
                    onPick={(industry) =>
                      update({
                        industry: screen.industry === industry ? "" : industry,
                      })
                    }
                  />
                </Panel>
              )
            : bySector.length > 0 && (
                <Panel title="Sectors" padded>
                  <Bars items={bySector} total={matched.length} onPick={(sector) => update({ sector, industry: "" })} />
                </Panel>
              )}
        </>
      )}
    </div>
  );
}
