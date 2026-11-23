import { LedgerView } from "../components/LedgerView";
import { EmptyState } from "../components/ui/EmptyState";
import { Tabs } from "../components/ui/Tabs";
import { api, type Board } from "../lib/api";
import { useLoad } from "../lib/useLoad";
import { Paper } from "./StrategyPage";

export function PaperPage({ board, name, onOpen }: { board: Board; name?: string; onOpen: (name: string) => void }) {
  const { data: heads, error } = useLoad(() => api.ledgers(), "ledgers");
  const books = board.rows.filter((row) => row.paper);
  const events = error ? [] : (heads ?? []);
  const tabs = [...books.map((row) => ({ key: row.strategy, label: row.title })), ...events.map((h) => ({ key: h.name, label: h.title }))];
  if (!tabs.length) return heads || error ? <EmptyState title="No ledger is kept yet" /> : <p className="text-ink-2">Loading…</p>;
  const active = tabs.some((t) => t.key === name) ? (name as string) : tabs[0].key;
  return (
    <>
      <Tabs label="Ledgers" tabs={tabs} active={active} onChange={onOpen} />
      {books.some((row) => row.strategy === active) ? <Paper name={active} /> : <LedgerView key={active} name={active} />}
    </>
  );
}
