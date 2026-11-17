import { BoardTable } from "../components/BoardTable";
import { Card, Note } from "../components/ui/Card";
import type { Board } from "../lib/api";

export function Strategies({ board, onOpen }: { board: Board; onOpen: (strategy: string) => void }) {
  return (
    <Card title="Everything tested">
      <BoardTable board={board} onOpen={onOpen} />
      <Note>Trials are every cell or run counted against the idea's family. Results from research scripts are shown beside registered runs.</Note>
    </Card>
  );
}
