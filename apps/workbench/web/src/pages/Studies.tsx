import { useMemo, useState } from "react";
import { CsvButton } from "../components/CsvButton";
import { Card, Note } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { Segmented } from "../components/ui/Segmented";
import { api, type StudyRow } from "../lib/api";
import { int } from "../lib/format";
import { useLoad } from "../lib/useLoad";
import { StudyTable } from "./StrategyPage";

type Outcome = "all" | "passed" | "lead" | "failed" | "note";
type Order = "newest" | "oldest" | "trials";

export function filterStudies(studies: StudyRow[], search: string, outcome: Outcome, order: Order): StudyRow[] {
  const words = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const text = (s: StudyRow) => `${s.name} ${s.strategy} ${s.strategy_title} ${s.result ?? ""}`.toLowerCase();
  const found = studies.filter((s) => (outcome === "all" || s.verdict === outcome) && words.every((w) => text(s).includes(w)));
  const by = { newest: (a: StudyRow, b: StudyRow) => b.when.localeCompare(a.when), oldest: (a: StudyRow, b: StudyRow) => a.when.localeCompare(b.when), trials: (a: StudyRow, b: StudyRow) => (b.trials ?? 0) - (a.trials ?? 0) };
  return [...found].sort(by[order]);
}

const FIRST = 25;

export function Studies({ onOpen }: { onOpen: (strategy: string) => void }) {
  const { data, error } = useLoad(() => api.studies(), "studies");
  const [search, setSearch] = useState("");
  const [outcome, setOutcome] = useState<Outcome>("all");
  const [order, setOrder] = useState<Order>("newest");
  const [all, setAll] = useState(false);
  const shown = useMemo(() => filterStudies(data ?? [], search, outcome, order), [data, search, outcome, order]);
  if (error) return <EmptyState title="The studies could not be read" />;
  if (!data) return <p className="text-ink-2">Loading the studies…</p>;
  const trials = data.reduce((sum, study) => sum + (study.trials ?? 0), 0);
  const count = (v: string) => data.filter((s) => s.verdict === v).length;
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          aria-label="Find studies"
          placeholder="Study, strategy or finding"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="min-h-8 w-72 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
        />
        <Segmented
          label="Outcome"
          value={outcome}
          onChange={setOutcome}
          options={[
            { value: "all", label: `All ${data.length}` },
            { value: "passed", label: `Passed ${count("passed")}` },
            { value: "lead", label: `Leads ${count("lead")}` },
            { value: "failed", label: `Failed ${count("failed")}` },
            { value: "note", label: `Notes ${count("note")}` },
          ]}
        />
        <Segmented
          label="Order"
          value={order}
          onChange={setOrder}
          options={[
            { value: "newest", label: "Newest" },
            { value: "oldest", label: "Oldest" },
            { value: "trials", label: "Most trials" },
          ]}
        />
      </div>
      <Card
        title={`${shown.length} of ${data.length} studies`}
        aside={
          <span className="flex items-center gap-3">
            {int(trials)} trials in all
            <CsvButton
              filename="studies.csv"
              rows={shown}
              columns={[
                { header: "study", value: (s) => s.name },
                { header: "strategy", value: (s) => s.strategy },
                { header: "date", value: (s) => s.when },
                { header: "trials", value: (s) => s.trials },
                { header: "found", value: (s) => s.result },
                { header: "outcome", value: (s) => s.verdict },
              ]}
            />
          </span>
        }
      >
        {shown.length ? <StudyTable studies={all || shown.length <= FIRST ? shown : shown.slice(0, FIRST)} withStrategy onOpen={onOpen} /> : <p className="m-0 py-6 text-ink-2">No study matches.</p>}
        {shown.length > FIRST && (
          <button type="button" onClick={() => setAll(!all)} className="cursor-pointer self-start text-[13px] font-medium text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            {all ? `Show the first ${FIRST}` : `Show all ${shown.length}`}
          </button>
        )}
        <Note>A study is one question put to the data: a search over many cells, a single test, or a measurement. Each is recorded in its strategy's folder with what it found.</Note>
      </Card>
    </>
  );
}
