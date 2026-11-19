import { BoardTable } from "../components/BoardTable";
import { LedgerTable } from "../components/LedgerTable";
import { ProfitChart } from "../components/charts/ProfitChart";
import { bookName, bookTotal, Orders, Positions } from "../components/PaperPanel";
import { Card, Note, Stat } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { VerdictBadge } from "../components/ui/VerdictBadge";
import { api, type Board, type BoardRow } from "../lib/api";
import { day, dollars, int, money, num, pct, plainPct } from "../lib/format";
import { timeline } from "../lib/series";
import { useLoad } from "../lib/useLoad";

interface HomeProps {
  board: Board;
  onOpen: (strategy: string, tab?: string) => void;
}

/** What works, what is being tested, what is waiting on the owner, and everything tested. */
export function Home({ board, onOpen }: HomeProps) {
  const works = board.rows.find((row) => row.group === "works" && !row.variant) ?? null;
  const testing = board.rows.filter((row) => row.group === "testing");
  const lead = testing.find((row) => row.variant) ?? testing[0] ?? null;
  const ledger = board.rows.find((row) => row.paper) ?? null;
  return (
    <>
      {works ? <Works row={works} onOpen={onOpen} /> : <EmptyState title="Nothing has passed its holdout yet">Ideas being tested and everything tried so far are below.</EmptyState>}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Being tested forward" aside={lead && <VerdictBadge group="testing" label={lead.label} />}>
          {lead ? <Testing lead={lead} rest={testing.filter((row) => row !== lead)} onOpen={onOpen} /> : <p className="m-0 text-ink-2">Nothing is in test.</p>}
          {board.waiting.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-line pt-3.5">
              <h3 className="m-0 text-[13px] font-semibold text-ink-2">Waiting on you</h3>
              {board.waiting.map((item) => (
                <div key={item.text}>{item.text}</div>
              ))}
            </div>
          )}
        </Card>
        {ledger && <PaperCard row={ledger} onOpen={onOpen} />}
      </div>
      <LedgerTable />
      <Card title="Everything tested" id="record">
        <BoardTable board={board} onOpen={onOpen} />
        <Note>Trials are every cell or run counted against the idea's family. Results from research scripts are shown beside registered runs.</Note>
      </Card>
    </>
  );
}

function Works({ row, onOpen }: { row: BoardRow; onOpen: HomeProps["onOpen"] }) {
  const { data } = useLoad(() => api.strategy(row.strategy), row.strategy);
  const period = data?.periods.find((p) => p.key === "holdout" && p.stats) ?? data?.periods.filter((p) => p.stats).at(-1) ?? null;
  const stats = period?.stats ?? null;
  const line = data ? timeline(data.periods) : null;
  return (
    <section aria-label="What works" className="grid gap-7 rounded-[10px] border border-line bg-surface px-6 py-5 lg:grid-cols-2">
      <div className="flex flex-col gap-3.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <h2 className="m-0 text-[13px] font-semibold text-ink-2">What works</h2>
          <VerdictBadge group="works" label={row.label} />
        </div>
        <div>
          <h3 className="m-0 text-3xl leading-tight font-semibold tracking-tight">{row.title}</h3>
          {row.summary && <p className="mt-2 mb-0 max-w-[46ch] text-ink-2">{row.summary}</p>}
        </div>
        {stats && period && (
          <>
            <div className="mt-1 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Net a trade" value={pct(stats.net)} note={`${int(stats.trades)} trades`} />
              <Stat label="Profit" value={dollars(stats.total)} note={period.equity ? `on ${dollars(period.equity)}` : undefined} />
              <Stat label="Sharpe" value={num(stats.sharpe)} note={`${num(stats.sharpe_2x)} at double cost`} />
              <Stat label="Worst drawdown" value={dollars(Math.abs(stats.drawdown ?? 0))} note={period.equity && stats.drawdown != null ? `${plainPct(-stats.drawdown / period.equity)} of account` : undefined} />
            </div>
            <Note>
              {period.label}, {day(period.start)} to {day(period.end)}.
            </Note>
          </>
        )}
        <button
          type="button"
          onClick={() => onOpen(row.strategy)}
          className="min-h-11 cursor-pointer self-start rounded-lg bg-accent px-4.5 font-semibold text-on-accent hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          Open the strategy
        </button>
      </div>
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="m-0 text-[13px] font-semibold text-ink-2">Cumulative profit{period?.equity ? `, ${dollars(period.equity)} book` : ""}</h3>
          {line && line.months.length > 0 && (
            <span className="text-[13px] text-ink-3">
              {line.months[0].year} to {line.months[line.months.length - 1].year}
            </span>
          )}
        </div>
        {line ? <ProfitChart timeline={line} compact height={230} /> : <div className="h-[230px]" />}
        {data?.record.chart_note && <Note>{data.record.chart_note}</Note>}
      </div>
    </section>
  );
}

function Testing({ lead, rest, onOpen }: { lead: BoardRow; rest: BoardRow[]; onOpen: HomeProps["onOpen"] }) {
  return (
    <>
      <div>
        <button type="button" onClick={() => onOpen(lead.strategy)} className="cursor-pointer text-left text-[19px] font-semibold hover:text-accent focus-visible:outline-2 focus-visible:outline-accent">
          {lead.title}
        </button>
        {lead.summary && <p className="mt-1.5 mb-0 text-ink-2">{lead.summary}</p>}
      </div>
      {lead.stats && lead.stats.length > 0 && (
        <div className="grid grid-cols-3 gap-3.5">
          {lead.stats.map((stat) => (
            <Stat key={stat.label} label={stat.label} value={stat.value} size="md" />
          ))}
        </div>
      )}
      {lead.settle && lead.settle.length > 0 && (
        <div className="flex flex-col gap-2.5 border-t border-line pt-3.5">
          <h3 className="m-0 text-[13px] font-semibold text-ink-2">What would settle it</h3>
          {lead.settle.map((item) => (
            <div key={item.text} className="flex gap-2.5">
              <span aria-hidden="true" className={`mt-[7px] size-2 shrink-0 rounded-full ${item.state === "running" ? "bg-accent" : "border-[1.5px] border-ink-3"}`} />
              <span>
                <span className="sr-only">{item.state === "running" ? "Under way: " : "Not started: "}</span>
                {item.text}
              </span>
            </div>
          ))}
        </div>
      )}
      {rest.length > 0 && (
        <div className="flex flex-col gap-2 border-t border-line pt-3.5">
          <h3 className="m-0 text-[13px] font-semibold text-ink-2">Also open</h3>
          {rest.map((row) => (
            <div key={row.idea} className="flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
              <button type="button" onClick={() => onOpen(row.strategy)} className="cursor-pointer font-semibold hover:text-accent focus-visible:outline-2 focus-visible:outline-accent">
                {row.idea}
              </button>
              <span className="text-ink-2">{row.label}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function PaperCard({ row, onOpen }: { row: BoardRow; onOpen: HomeProps["onOpen"] }) {
  const { data: paper, error } = useLoad(() => api.paper(row.strategy), row.strategy);
  const first = paper?.books.slice(0, 2) ?? [];
  const idle = paper?.books.filter((book) => !book.open && !book.trades).length ?? 0;
  return (
    <Card title="Paper trading" id="paper" aside={paper ? `To the close of ${day(paper.last_session, true)}. No order is sent anywhere.` : undefined}>
      {error && <p className="m-0 text-ink-2">The ledger has not been run yet.</p>}
      {paper && (
        <>
          <div className="grid grid-cols-3 gap-3.5">
            <Stat label="Open positions" value={int(paper.positions.length)} size="md" />
            {first.map((book) => (
              <Stat key={book.name} label={bookName(book.name)} value={money(bookTotal(book))} tone={bookTotal(book) < 0 ? "neg" : "pos"} size="md" />
            ))}
          </div>
          <Orders paper={paper} />
          <Positions positions={paper.positions} hold={paper.hold} limit={8} />
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <Note>
              {Math.min(8, paper.positions.length)} of {paper.positions.length} shown, nearest their exit first.{idle ? ` ${idle} more books are waiting for their first signal.` : ""}
            </Note>
            <button type="button" onClick={() => onOpen(row.strategy, "paper")} className="cursor-pointer text-sm font-semibold text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
              Open the ledger
            </button>
          </div>
        </>
      )}
    </Card>
  );
}
