import { Card, Note } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";
import { int } from "../lib/format";
import { useLoad } from "../lib/useLoad";
import { StudyTable } from "./StrategyPage";

/** Every study recorded in a strategy folder, newest first. */
export function Studies({ onOpen }: { onOpen: (strategy: string) => void }) {
  const { data, error } = useLoad(() => api.studies(), "studies");
  if (error) return <EmptyState title="The studies could not be read" />;
  if (!data) return <p className="text-ink-2">Loading the studies…</p>;
  const trials = data.reduce((sum, study) => sum + (study.trials ?? 0), 0);
  return (
    <Card title={`${data.length} studies`} aside={`${int(trials)} trials in all`}>
      <StudyTable studies={data} withStrategy onOpen={onOpen} />
      <Note>A study is one question put to the data: a search over many cells, a single test, or a measurement. Each is recorded in its strategy's folder with what it found.</Note>
    </Card>
  );
}
