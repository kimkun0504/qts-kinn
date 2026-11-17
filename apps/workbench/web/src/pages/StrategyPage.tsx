import { useState } from "react";
import { MonthGrid, MonthLegend } from "../components/charts/MonthGrid";
import { ProfitChart } from "../components/charts/ProfitChart";
import { YearBars } from "../components/charts/YearBars";
import { Markdown } from "../components/Markdown";
import { Books, Orders, Positions } from "../components/PaperPanel";
import { RunsTable } from "../components/RunsTable";
import { Card, Note, Stat } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { VerdictBadge } from "../components/ui/VerdictBadge";
import { api, type Evidence, type Period, type RunRow, type StrategyPageData, type StudyRow } from "../lib/api";
import { day, dollars, int, money, num, pct, plainPct } from "../lib/format";
import { byYear, timeline } from "../lib/series";
import { useLoad } from "../lib/useLoad";
import { RunDetail } from "./RunDetail";

interface StrategyPageProps {
  name: string;
  tab: string;
  runs: RunRow[];
  onTab: (tab: string) => void;
  onBack: () => void;
}

export function StrategyPage({ name, tab, runs, onTab, onBack }: StrategyPageProps) {
  const { data, error } = useLoad(() => api.strategy(name), name);
  if (error) return <EmptyState title="No such strategy">There is no strategy folder called {name} on this branch.</EmptyState>;
  if (!data) return <p className="text-ink-2">Loading the strategy…</p>;
  const record = data.record;
  const mine = runs.filter((run) => run.strategy === name);
  const tabs = [
    { key: "results", label: "Results" },
    ...(data.periods.some((p) => p.run_id) ? [{ key: "trades", label: "Trades" }] : []),
    ...(record.paper ? [{ key: "paper", label: "Paper book" }] : []),
    ...(data.has_report || data.has_hypothesis ? [{ key: "report", label: "Report" }] : []),
    { key: "studies", label: `Studies ${data.studies.length}` },
    { key: "runs", label: `Runs ${mine.length}` },
  ];
  const active = tabs.some((t) => t.key === tab) ? tab : "results";
  return (
    <>
      <header className="flex flex-col gap-2.5">
        <div className="text-sm text-ink-3">
          <button type="button" onClick={onBack} className="cursor-pointer text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            Strategies
          </button>{" "}
          / {record.title ?? name}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="m-0 text-3xl leading-tight font-semibold tracking-tight">{record.title ?? name}</h1>
          <VerdictBadge group={data.group} label={data.label} />
          {record.paper && <VerdictBadge group="testing" label="In paper trading" />}
        </div>
        {record.summary && <p className="m-0 max-w-[78ch] text-ink-2">{record.summary}</p>}
        <div role="tablist" aria-label="Strategy sections" className="mt-1.5 flex flex-wrap gap-6 border-b border-line">
          {tabs.map((t) => (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={active === t.key}
              onClick={() => onTab(t.key)}
              className={`-mb-px min-h-11 cursor-pointer border-b-2 px-0.5 font-medium focus-visible:outline-2 focus-visible:outline-accent ${
                active === t.key ? "border-accent text-ink" : "border-transparent text-ink-2 hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>
      {active === "results" && <Results data={data} />}
      {active === "trades" && <Trades periods={data.periods.filter((p) => p.run_id)} />}
      {active === "paper" && <Paper name={name} />}
      {active === "report" && <Documents name={name} />}
      {active === "studies" && <StudiesCard studies={data.studies} trials={data.trials} />}
      {active === "runs" && <StrategyRuns runs={mine} />}
    </>
  );
}

function Results({ data }: { data: StrategyPageData }) {
  const record = data.record;
  const withStats = data.periods.filter((p) => p.stats);
  const [chosen, setChosen] = useState<string | null>(null);
  const period = withStats.find((p) => p.key === chosen) ?? withStats.find((p) => p.key === "holdout") ?? withStats.at(-1) ?? null;
  const line = timeline(data.periods);
  const years = byYear(line.months);
  const holdout = data.periods.find((p) => p.key === "holdout") ?? null;
  // The periods as the owner reads them: the out-of-sample one first.
  const order = [...withStats].reverse();
  return (
    <>
      {period?.stats && (
        <Card>
          <div className="flex flex-wrap items-center gap-3">
            <div role="group" aria-label="Period" className="flex flex-wrap gap-0.5 rounded-lg bg-raised p-[3px]">
              {order.map((p) => (
                <button
                  key={p.key}
                  type="button"
                  aria-pressed={p.key === period.key}
                  onClick={() => setChosen(p.key)}
                  className={`min-h-9 cursor-pointer rounded-md px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${
                    p.key === period.key ? "bg-surface text-ink shadow-[0_0_0_1px_var(--line)]" : "text-ink-2 hover:text-ink"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
            <span className="text-[13px] text-ink-3">{period.note ?? `${day(period.start)} to ${day(period.end)}`}</span>
          </div>
          <PeriodStats period={period} />
        </Card>
      )}
      {line.months.length > 1 ? (
        <>
          <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,2.1fr)_minmax(0,1fr)]">
            <Card title={`Cumulative profit${period?.equity ? `, ${dollars(period.equity)} book` : ""}`} aside="By month, costs at the auction allowance">
              <ProfitChart timeline={line} />
              {record.chart_note && <Note>{record.chart_note}</Note>}
            </Card>
            <div className="flex flex-col gap-5">
              {holdout?.targets && holdout.stats && <Targets period={holdout} fills={record.fills} />}
              {record.weaknesses && <Weaknesses items={record.weaknesses} />}
            </div>
          </div>
          <div className="grid items-start gap-5 lg:grid-cols-2">
            <Card title="Profit by year" aside={holdout?.run_id ? "Shaded years are the holdout" : undefined}>
              <YearBars years={years} />
              <Note>Years a run covers only in part are counted as they stand. Hover a bar for its figure.</Note>
            </Card>
            {record.variants && <Variants data={data} />}
          </div>
          <div className="grid items-start gap-5 lg:grid-cols-2">
            <Card title="Profit by month" aside={<MonthLegend />}>
              <MonthGrid months={line.months} />
              <Note>Bold years are the holdout. Dashed cells were not run. Hover a cell for its figure.</Note>
            </Card>
            {record.evidence && <EvidenceCard evidence={record.evidence} />}
          </div>
        </>
      ) : (
        <div className="grid items-start gap-5 lg:grid-cols-2">
          <div className="flex flex-col gap-5">
            <Card title="Best honest result">
              <p className="m-0 text-lg font-semibold">{record.result ?? "No result recorded."}</p>
              <Note>
                {int(data.trials)} trials counted against the family. {data.runs ? `${data.runs} registered runs; the rest was measured by research scripts.` : "Measured by research scripts; no registered run."}
              </Note>
            </Card>
            {record.weaknesses && <Weaknesses items={record.weaknesses} />}
          </div>
          {record.evidence && <EvidenceCard evidence={record.evidence} />}
        </div>
      )}
    </>
  );
}

function PeriodStats({ period }: { period: Period }) {
  const s = period.stats;
  if (!s) return null;
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      <Stat label="Net a trade" value={pct(s.net)} note={`${pct(s.net_2x)} at double cost`} />
      <Stat label="Profit" value={dollars(s.total)} note={period.equity ? `on ${dollars(period.equity)}` : undefined} />
      <Stat label="Sharpe" value={num(s.sharpe)} note={`${num(s.sharpe_2x)} at double cost`} />
      <Stat label="Worst drawdown" value={dollars(Math.abs(s.drawdown ?? 0))} note="marked daily" />
      <Stat label="Winners" value={plainPct(s.win_rate)} note={`median ${pct(s.median, 1)}`} />
      <Stat label="Trades" value={int(s.trades)} note={s.signals != null ? `${int(s.signals)} signals` : undefined} />
    </div>
  );
}

function Check({ met }: { met: boolean }) {
  return (
    <svg role="img" aria-label={met ? "Met" : "Not met"} width="18" height="18" viewBox="0 0 18 18" fill="none" stroke={met ? "var(--pos)" : "var(--neg)"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0">
      <circle cx="9" cy="9" r="7.5" strokeWidth="1.5" />
      {met ? <path d="M5.5 9.3l2.4 2.4 4.6-5" /> : <path d="M6 6l6 6M12 6l-6 6" />}
    </svg>
  );
}

function Targets({ period, fills }: { period: Period; fills?: string }) {
  const equity = period.equity ?? 0;
  const rows = (period.targets ?? []).map((t) => {
    if (t.key === "net_per_trade") return { met: t.met, value: `${pct(t.value)} a trade at double cost`, need: `Needs ${plainPct(t.bar, 1)} or more` };
    if (t.key === "sharpe") return { met: t.met, value: `Sharpe ${num(t.value)} at double cost`, need: `Needs more than ${num(t.bar, 0)}` };
    return { met: t.met, value: `Drawdown ${dollars((t.value ?? 0) * equity)} at double cost`, need: `Needs under ${dollars(t.bar * equity)}, half the account` };
  });
  return (
    <Card title="Targets, on the holdout">
      {rows.map((row) => (
        <div key={row.value} className="flex items-start gap-2.5">
          <Check met={row.met} />
          <div className="min-w-0">
            <div className="font-semibold">{row.value}</div>
            <div className="text-[13px] text-ink-3">{row.need}</div>
          </div>
        </div>
      ))}
      {fills && (
        <div className="flex items-start gap-2.5">
          <Check met />
          <div className="min-w-0">
            <div className="font-semibold">Fills measured from ticks</div>
            <div className="text-[13px] text-ink-3">{fills}</div>
          </div>
        </div>
      )}
    </Card>
  );
}

function Weaknesses({ items }: { items: string[] }) {
  return (
    <Card title="Known weaknesses">
      {items.map((item) => (
        <div key={item}>{item}</div>
      ))}
    </Card>
  );
}

function Variants({ data }: { data: StrategyPageData }) {
  const record = data.record;
  return (
    <Card title="Variants" aside={record.variants_note}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[440px] border-collapse text-[14.5px]">
          <thead>
            <tr className="text-[13px] text-ink-3">
              <th scope="col" className="border-b border-line px-3 py-2.5 text-left font-semibold">Rule</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">A year</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">Sharpe</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">Drawdown</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">Worst year</th>
            </tr>
          </thead>
          <tbody>
            {(record.variants ?? []).map((v) => (
              <tr key={v.rule}>
                <td className="border-b border-line-soft px-3 py-3">
                  <div className="font-semibold">{v.rule}</div>
                  <div className="text-[13px] text-ink-3">{v.evidence}</div>
                </td>
                <td className="border-b border-line-soft px-3 py-3 text-right align-top">{dollars(v.a_year)}</td>
                <td className="border-b border-line-soft px-3 py-3 text-right align-top">{num(v.sharpe)}</td>
                <td className="border-b border-line-soft px-3 py-3 text-right align-top">{dollars(v.drawdown)}</td>
                <td className={`border-b border-line-soft px-3 py-3 text-right align-top ${v.worst_year < 0 ? "text-neg" : ""}`}>{money(v.worst_year)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {record.variants_footnote && <Note>{record.variants_footnote}</Note>}
    </Card>
  );
}

const DOT: Record<Evidence["kind"], string> = {
  found: "border-ink-3 bg-ink-3",
  passed: "border-gain bg-gain",
  failed: "border-loss bg-loss",
  running: "border-accent bg-accent",
  open: "border-accent bg-transparent",
};
const KIND: Record<Evidence["kind"], string> = { found: "Found", passed: "Passed", failed: "Failed", running: "Under way", open: "Open" };

function EvidenceCard({ evidence }: { evidence: Evidence[] }) {
  return (
    <Card title="Evidence, in the order it came">
      <ol className="m-0 flex list-none flex-col p-0">
        {evidence.map((item, i) => (
          <li key={`${item.title}-${i}`} className="flex gap-3.5">
            <div aria-hidden="true" className="flex w-3 shrink-0 flex-col items-center">
              <span className={`mt-1.5 size-2.5 rounded-full border-2 ${DOT[item.kind] ?? DOT.found}`} />
              {i < evidence.length - 1 && <span className="mt-1 w-px flex-1 bg-line" />}
            </div>
            <div className="min-w-0 pb-4">
              <div className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
                <span className="font-semibold">{item.title}</span>
                <span className="text-[13px] text-ink-3">
                  <span className="sr-only">{KIND[item.kind]}, </span>
                  {day(item.when, true)}
                </span>
              </div>
              <div className="text-ink-2">{item.text}</div>
            </div>
          </li>
        ))}
      </ol>
      <Note>Every plan was written and dated before its run. The full account is under Report.</Note>
    </Card>
  );
}

function Trades({ periods }: { periods: Period[] }) {
  const order = [...periods].reverse();
  const [key, setKey] = useState(order[0]?.key ?? "");
  const [all, setAll] = useState(false);
  const period = order.find((p) => p.key === key) ?? order[0];
  const { data } = useLoad(() => api.trades(period.run_id as string), period.run_id as string);
  const rows = data ? (all ? data.rows : data.rows.slice(0, 200)) : [];
  return (
    <Card
      title={data ? `${int(data.count)} trades, newest first` : "Trades"}
      aside={
        <div role="group" aria-label="Period" className="flex flex-wrap gap-0.5 rounded-lg bg-raised p-[3px]">
          {order.map((p) => (
            <button
              key={p.key}
              type="button"
              aria-pressed={p.key === period.key}
              onClick={() => {
                setKey(p.key);
                setAll(false);
              }}
              className={`min-h-8 cursor-pointer rounded-md px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${p.key === period.key ? "bg-surface text-ink shadow-[0_0_0_1px_var(--line)]" : "text-ink-2 hover:text-ink"}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      }
    >
      {!data ? (
        <p className="m-0 text-ink-2">Loading the trades…</p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-sm">
              <thead>
                <tr className="text-[13px] text-ink-3">
                  <th scope="col" className="border-b border-line px-3 py-2 text-left font-semibold">Sold</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-left font-semibold">Stock</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Shares</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Bought at</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Sold at</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Return</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-right font-semibold">Net</th>
                  <th scope="col" className="border-b border-line px-3 py-2 text-left font-semibold">Exit</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((t, i) => {
                  const r = t.notional ? t.net / t.notional : null;
                  return (
                    <tr key={`${t.day}-${t.symbol}-${i}`}>
                      <td className="border-b border-line-soft px-3 py-2 whitespace-nowrap text-ink-2">{day(t.day)}</td>
                      <td className="border-b border-line-soft px-3 py-2 font-semibold">{t.symbol}</td>
                      <td className="border-b border-line-soft px-3 py-2 text-right">{int(t.quantity)}</td>
                      <td className="border-b border-line-soft px-3 py-2 text-right">{num(t.entry_price)}</td>
                      <td className="border-b border-line-soft px-3 py-2 text-right">{num(t.exit_price)}</td>
                      <td className={`border-b border-line-soft px-3 py-2 text-right ${t.net < 0 ? "text-neg" : "text-pos"}`}>{pct(r, 1)}</td>
                      <td className={`border-b border-line-soft px-3 py-2 text-right ${t.net < 0 ? "text-neg" : "text-pos"}`}>{money(t.net)}</td>
                      <td className="border-b border-line-soft px-3 py-2 text-ink-2">{t.exit_reason === "time" ? "Held to the end" : "Stopped trading"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {!all && data.rows.length > 200 && (
            <button type="button" onClick={() => setAll(true)} className="min-h-9 cursor-pointer self-start rounded-md border border-line px-3.5 text-sm font-medium hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent">
              Show all {int(data.rows.length)}
            </button>
          )}
        </>
      )}
    </Card>
  );
}

export function Paper({ name }: { name: string }) {
  const { data: paper, error } = useLoad(() => api.paper(name), name);
  if (error) return <EmptyState title="The ledger has not been run yet">Run tools/owner/paper_earnings_drift.py after the close; it writes the ledger this page reads.</EmptyState>;
  if (!paper) return <p className="text-ink-2">Loading the ledger…</p>;
  const f = paper.followed;
  return (
    <>
      <Card title={`Orders after the close of ${day(paper.last_session)}`} aside="No order is sent anywhere">
        <Orders paper={paper} />
        {paper.buy_next_open.filter((b) => b.note).map((b) => (
          <Note key={b.symbol}>
            {b.symbol}: {b.note}.
          </Note>
        ))}
      </Card>
      <Card title="Books">
        <Books books={paper.books} />
        <Note>Each book takes the same signals under its own rule, so they can be compared on what happens. Total is closed profit plus open positions at the last close.</Note>
      </Card>
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,2.1fr)_minmax(0,1fr)]">
        <Card title={`${paper.positions.length} open positions`} aside="Nearest their exit first">
          <Positions positions={paper.positions} hold={paper.hold} books />
        </Card>
        <Card title="Every signal, taken or not">
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Signals" value={int(f.signals)} size="md" />
            <Stat label="Finished" value={int(f.finished)} size="md" note={f.finished ? `${f.winners} winners` : undefined} />
            <Stat label="Mean, before costs" value={pct(f.mean_gross)} size="md" tone={(f.mean_gross ?? 0) < 0 ? "neg" : undefined} />
            {f.vs_benchmark != null && <Stat label={`Against ${paper.benchmark ?? "the index"}`} value={pct(f.vs_benchmark)} size="md" />}
          </div>
          {(f.passed || f.failed) && (
            <div className="flex flex-col gap-1.5 border-t border-line pt-3">
              {f.passed && (
                <div>
                  Passed the quality test: {f.passed.finished} finished, {pct(f.passed.mean_gross)} each.
                </div>
              )}
              {f.failed && (
                <div>
                  Failed it: {f.failed.finished} finished, {pct(f.failed.mean_gross)} each.
                </div>
              )}
            </div>
          )}
          <Note>A signal is followed whether or not a book has room for it, so the skipped ones are measured too.</Note>
        </Card>
      </div>
    </>
  );
}

function Documents({ name }: { name: string }) {
  const { data } = useLoad(() => api.documents(name), name);
  const [which, setWhich] = useState<"report" | "hypothesis">("report");
  if (!data) return <p className="text-ink-2">Loading the report…</p>;
  const shown = which === "report" && data.report ? data.report : (data.hypothesis ?? data.report ?? "");
  const both = Boolean(data.report && data.hypothesis);
  return (
    <Card>
      {both && (
        <div role="group" aria-label="Document" className="flex gap-0.5 self-start rounded-lg bg-raised p-[3px]">
          {(["report", "hypothesis"] as const).map((key) => (
            <button
              key={key}
              type="button"
              aria-pressed={which === key}
              onClick={() => setWhich(key)}
              className={`min-h-9 cursor-pointer rounded-md px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${which === key ? "bg-surface text-ink shadow-[0_0_0_1px_var(--line)]" : "text-ink-2 hover:text-ink"}`}
            >
              {key === "report" ? "Report" : "Plan and its dated changes"}
            </button>
          ))}
        </div>
      )}
      <Markdown text={shown} />
    </Card>
  );
}

const STUDY: Record<string, { label: string; tone: string }> = {
  passed: { label: "Passed", tone: "text-pos" },
  failed: { label: "Failed", tone: "text-ink-2" },
  lead: { label: "Lead", tone: "text-accent" },
  note: { label: "Note", tone: "text-ink-2" },
};

export function StudyTable({ studies, withStrategy = false, onOpen }: { studies: StudyRow[]; withStrategy?: boolean; onOpen?: (strategy: string) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] border-collapse">
        <thead>
          <tr className="text-left text-[13px] text-ink-3">
            <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Study</th>
            {withStrategy && <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Strategy</th>}
            <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Date</th>
            <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">Trials</th>
            <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">What it found</th>
            <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study, i) => {
            const outcome = STUDY[study.verdict] ?? STUDY.note;
            return (
              <tr key={`${study.strategy}-${study.name}-${i}`}>
                <td className="max-w-[40ch] border-b border-line-soft px-3 py-3 align-top font-semibold">{study.name}</td>
                {withStrategy && (
                  <td className="border-b border-line-soft px-3 py-3 align-top whitespace-nowrap">
                    {onOpen ? (
                      <button type="button" onClick={() => onOpen(study.strategy)} className="cursor-pointer text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
                        {study.strategy_title}
                      </button>
                    ) : (
                      study.strategy_title
                    )}
                  </td>
                )}
                <td className="border-b border-line-soft px-3 py-3 align-top whitespace-nowrap text-ink-2">{day(study.when)}</td>
                <td className="border-b border-line-soft px-3 py-3 text-right align-top">{study.trials ? int(study.trials) : "–"}</td>
                <td className="max-w-[48ch] border-b border-line-soft px-3 py-3 align-top text-ink-2">{study.result ?? "–"}</td>
                <td className={`border-b border-line-soft px-3 py-3 align-top font-semibold whitespace-nowrap ${outcome.tone}`}>{outcome.label}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function StudiesCard({ studies, trials }: { studies: StudyRow[]; trials: number }) {
  if (!studies.length) return <EmptyState title="No study is recorded for this strategy" />;
  return (
    <Card title={`${studies.length} studies`} aside={`${int(trials)} trials counted against the family`}>
      <StudyTable studies={studies} />
    </Card>
  );
}

function StrategyRuns({ runs }: { runs: RunRow[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  if (!runs.length) return <EmptyState title="No registered run">This idea was measured by research scripts; see Studies and Report.</EmptyState>;
  return (
    <>
      <section className="overflow-x-auto rounded-[10px] border border-line bg-surface">
        <div className="max-h-[360px] overflow-y-auto">
          <RunsTable runs={runs} onOpen={(run) => setSelected(run.run_id)} selected={selected} />
        </div>
      </section>
      <RunDetail runId={selected} />
    </>
  );
}
