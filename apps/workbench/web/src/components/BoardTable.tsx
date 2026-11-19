import { useState } from "react";
import type { Board, BoardRow, Group } from "../lib/api";
import { int } from "../lib/format";
import { VerdictBadge } from "./ui/VerdictBadge";

type Filter = "all" | Group;

const WHO: Record<string, string> = { claude: "Claude", gpt: "Astra", human: "Owner" };

/** Everything tested, one row an idea, filtered by where it stands. Rows open the strategy. */
export function BoardTable({ board, onOpen, limit }: { board: Board; onOpen: (strategy: string) => void; limit?: number }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [others, setOthers] = useState(false);
  const [all, setAll] = useState(false);
  const matching = board.rows.filter((row) => filter === "all" || row.group === filter);
  const cut = limit != null && !all && matching.length > limit;
  const rows = cut ? matching.slice(0, limit) : matching;
  const chips: { value: Filter; label: string }[] = [
    { value: "all", label: `All ${board.rows.length}` },
    { value: "works", label: `Works ${board.counts.works}` },
    { value: "testing", label: `In test ${board.counts.testing}` },
    { value: "closed", label: `Parked or closed ${board.counts.closed}` },
  ];
  const astra = board.others.filter((o) => o.agent === "gpt");
  return (
    <div className="flex flex-col gap-3">
      <div role="group" aria-label="Filter by verdict" className="flex flex-wrap gap-2">
        {chips.map((chip) => (
          <button
            key={chip.value}
            type="button"
            aria-pressed={filter === chip.value}
            onClick={() => setFilter(chip.value)}
            className={`min-h-9 cursor-pointer rounded-full border px-3.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-accent ${
              filter === chip.value ? "border-ink-3 bg-raised text-ink" : "border-line text-ink-2 hover:text-ink"
            }`}
          >
            {chip.label}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse">
          <thead>
            <tr className="text-left text-[13px] text-ink-3">
              <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Idea</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Horizon</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 text-right font-semibold">Trials</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Best honest result</th>
              <th scope="col" className="border-b border-line px-3 py-2.5 font-semibold">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <Row key={`${row.strategy}:${row.idea}`} row={row} onOpen={onOpen} />
            ))}
            {!cut && (filter === "all" || filter === "closed") && astra.length > 0 && (
              <tr>
                <td className="border-b border-line-soft px-3 py-3 align-top">
                  <button type="button" aria-expanded={others} onClick={() => setOthers(!others)} className="cursor-pointer text-left font-semibold text-ink hover:text-accent focus-visible:outline-2 focus-visible:outline-accent">
                    {astra.length} intraday ideas
                  </button>
                  <div className="text-[13px] text-ink-3">Astra</div>
                </td>
                <td className="border-b border-line-soft px-3 py-3 align-top whitespace-nowrap text-ink-2">Intraday</td>
                <td className="border-b border-line-soft px-3 py-3 text-right align-top whitespace-nowrap">{int(astra.reduce((sum, o) => sum + o.runs, 0))} runs</td>
                <td className="border-b border-line-soft px-3 py-3 align-top text-ink-2">None passed its own rules. Their reports are on Astra's branches.</td>
                <td className="border-b border-line-soft px-3 py-3 align-top">
                  <VerdictBadge group="closed" label="Parked" />
                </td>
              </tr>
            )}
            {others &&
              (filter === "all" || filter === "closed") &&
              astra.map((o) => (
                <tr key={o.strategy} className="text-[13.5px] text-ink-2">
                  <td className="border-b border-line-soft py-1.5 pr-3 pl-7">{o.strategy.replace(/_/g, " ")}</td>
                  <td className="border-b border-line-soft px-3 py-1.5" />
                  <td className="border-b border-line-soft px-3 py-1.5 text-right">{o.runs}</td>
                  <td className="border-b border-line-soft px-3 py-1.5" colSpan={2}>
                    {o.status === "not declared" ? "Folder not on this branch" : o.status}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      {limit != null && matching.length > limit && (
        <button type="button" onClick={() => setAll(!all)} className="cursor-pointer self-start text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
          {all ? `Show the first ${limit}` : `Show all ${matching.length}`}
        </button>
      )}
    </div>
  );
}

function Row({ row, onOpen }: { row: BoardRow; onOpen: (strategy: string) => void }) {
  return (
    <tr>
      <td className="border-b border-line-soft px-3 py-3 align-top">
        <button type="button" onClick={() => onOpen(row.strategy)} className="cursor-pointer text-left font-semibold text-ink hover:text-accent focus-visible:outline-2 focus-visible:outline-accent">
          {row.idea}
        </button>
        <div className="text-[13px] text-ink-3">{WHO[row.owner] ?? row.owner}</div>
      </td>
      <td className="border-b border-line-soft px-3 py-3 align-top whitespace-nowrap text-ink-2">{row.horizon ?? "–"}</td>
      <td className="border-b border-line-soft px-3 py-3 text-right align-top whitespace-nowrap">{row.trials == null ? <span className="text-ink-3">counted above</span> : int(row.trials)}</td>
      <td className="max-w-[46ch] border-b border-line-soft px-3 py-3 align-top text-ink-2">{row.result ?? "–"}</td>
      <td className="border-b border-line-soft px-3 py-3 align-top">
        <VerdictBadge group={row.group} label={row.label} />
      </td>
    </tr>
  );
}
