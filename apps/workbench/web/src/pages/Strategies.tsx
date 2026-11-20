import { BoardTable } from "../components/BoardTable";
import { Card, Note } from "../components/ui/Card";
import { StatStrip } from "../components/ui/StatStrip";
import type { Board } from "../lib/api";
import { int } from "../lib/format";

export function Strategies({ board, onOpen }: { board: Board; onOpen: (strategy: string) => void }) {
  const variants = board.rows.filter((row) => row.variant).length;
  const trials = board.rows.reduce((sum, row) => sum + (row.trials ?? 0), 0);
  return (
    <>
      <StatStrip
        items={[
          { label: "Ideas tested", value: int(board.rows.length), note: [variants ? `${variants} of them variants` : "", board.others.length ? `and ${board.others.length} by Astra` : ""].filter(Boolean).join(", ") || undefined },
          { label: "Passed the holdout", value: int(board.counts.works) },
          { label: "Being tested", value: int(board.counts.testing), note: "leads and paper tests" },
          { label: "Parked or closed", value: int(board.counts.closed) },
          { label: "Trials charged", value: int(trials), note: "cells and runs, across the ideas" },
        ]}
      />
      <Card title="Everything tested">
        <BoardTable board={board} onOpen={onOpen} />
        <Note>Trials are every cell or run counted against the idea's family. Results from research scripts are shown beside registered runs.</Note>
      </Card>
    </>
  );
}
