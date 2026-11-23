import { Markdown, sections } from "../components/Markdown";
import { JUMPS } from "../components/Shortcuts";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { type TabItem, Tabs } from "../components/ui/Tabs";
import { api } from "../lib/api";
import { useLoad } from "../lib/useLoad";

type Guide = "lab" | "workbench" | "keys";

const TABS: TabItem<Guide>[] = [
  { key: "lab", label: "The Lab" },
  { key: "workbench", label: "The Workbench" },
  { key: "keys", label: "Keyboard shortcuts" },
];

function Keys() {
  const rows: [string, string][] = [
    ["⌘ K or /", "Search pages, stocks, strategies, runs, algorithms, the watchlist and screens"],
    ["?", "Show the shortcuts"],
    ["Esc", "Close a dialog"],
    ["⌘ Enter", "Run the algorithm (in the Lab), or save a note"],
    ["⌘ S", "Save the algorithm (in the Lab)"],
    ...JUMPS.map((j): [string, string] => [`G then ${j.key.toUpperCase()}`, `Go to ${j.label}`]),
  ];
  return (
    <Card title="Keyboard shortcuts">
      <dl className="m-0 grid grid-cols-[10rem_1fr] gap-x-6 gap-y-2 text-sm">
        {rows.map(([keys, what]) => (
          <div key={keys} className="contents">
            <dt className="font-semibold">{keys}</dt>
            <dd className="m-0 text-ink-2">{what}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

export function GuidePage({ guide, onGuide }: { guide?: string; onGuide: (guide: Guide) => void }) {
  const active: Guide = guide === "workbench" || guide === "keys" ? guide : "lab";
  const { data, error } = useLoad(() => (active === "keys" ? Promise.resolve(null) : api.guide(active)), active);
  const toc = data ? sections(data.text) : [];
  return (
    <>
      <Tabs label="Guides" tabs={TABS} active={active} onChange={onGuide} />
      {active === "keys" ? (
        <Keys />
      ) : error ? (
        <EmptyState title="The guide could not be read">Restart the Workbench server if it was just updated.</EmptyState>
      ) : !data ? (
        <p className="text-ink-2">Loading…</p>
      ) : (
        <div className="grid items-start gap-8 lg:grid-cols-[14rem_minmax(0,1fr)]">
          <nav aria-label="Sections" className="hidden flex-col gap-1 text-[13px] lg:sticky lg:top-6 lg:flex">
            {toc.map((s) => (
              <a
                key={s.anchor}
                href={`#${s.anchor}`}
                onClick={(event) => {
                  event.preventDefault();
                  document.getElementById(s.anchor)?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
                className="rounded px-2 py-1 text-ink-2 no-underline hover:bg-raised hover:text-ink"
              >
                {s.title}
              </a>
            ))}
          </nav>
          <article className="min-w-0 rounded-lg border border-line bg-surface px-6 py-5">
            <Markdown text={data.text} />
          </article>
        </div>
      )}
    </>
  );
}
