import { EmptyState } from "../components/ui/EmptyState";
import type { Board } from "../lib/api";
import { Paper } from "./StrategyPage";

/** The paper ledgers. One strategy keeps one today. */
export function PaperPage({ board }: { board: Board }) {
  const ledgers = board.rows.filter((row) => row.paper);
  if (!ledgers.length) return <EmptyState title="No strategy is paper traded yet" />;
  return (
    <>
      {ledgers.map((row) => (
        <div key={row.strategy} className="flex flex-col gap-5">
          <h2 className="m-0 text-xl font-semibold">{row.title}</h2>
          <Paper name={row.strategy} />
        </div>
      ))}
    </>
  );
}
