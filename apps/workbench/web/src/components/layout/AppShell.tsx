import { Fragment, type ReactNode } from "react";
import type { Family } from "../../lib/api";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";

export type Page = "overview" | "runs" | "compare" | "parameters" | "trials";

const ICONS: Record<Page, ReactNode> = {
  overview: (
    <>
      <rect x="2" y="2" width="5" height="5" rx="1" />
      <rect x="9" y="2" width="5" height="5" rx="1" />
      <rect x="2" y="9" width="5" height="5" rx="1" />
      <rect x="9" y="9" width="5" height="5" rx="1" />
    </>
  ),
  runs: <path d="M2 4h12M2 8h12M2 12h12" />,
  compare: <path d="M2 12l4-5 3 3 5-6" />,
  parameters: (
    <>
      <path d="M3 3v10M8 3v10M13 3v10" />
      <circle cx="3" cy="6" r="1.5" />
      <circle cx="8" cy="10" r="1.5" />
      <circle cx="13" cy="5" r="1.5" />
    </>
  ),
  trials: <path d="M8 2v12M3 5h10M4 5l-2 4h4zM12 5l-2 4h4z" />,
};

const LABELS: Record<Page, string> = {
  overview: "Overview",
  runs: "Runs",
  compare: "Compare",
  parameters: "Parameters",
  trials: "Trials",
};

function Icon({ page }: { page: Page }) {
  return (
    <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[page]}
    </svg>
  );
}

interface AppShellProps {
  page: Page;
  onNavigate: (page: Page) => void;
  title: string;
  subtitle?: string;
  families: Family[];
  family: string | null;
  strategies: Record<string, { name: string; runs: number }[]>;
  strategy: string | null;
  onFamily: (family: string | null, strategy?: string | null) => void;
  counts: Partial<Record<Page, number>>;
  runsDir: string;
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onReload: () => void;
  children: ReactNode;
}

/** Side rail, top bar and the page area. Every page renders inside this. */
export function AppShell(props: AppShellProps) {
  const { page, onNavigate, families, family, onFamily, counts, strategies, strategy } = props;
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="flex shrink-0 flex-col gap-0.5 border-b border-line bg-surface px-2.5 py-3.5 md:w-[232px] md:border-r md:border-b-0">
        <div className="flex items-center gap-2.5 px-2.5 pt-1 pb-4">
          <span aria-hidden="true" className="inline-flex size-6 items-center justify-center rounded-md bg-ink text-[13px] font-bold text-ground">
            K
          </span>
          <span className="text-sm font-semibold">Kinn Research</span>
        </div>
        <nav aria-label="Sections" className="flex flex-col gap-0.5">
          {(Object.keys(LABELS) as Page[]).map((key) => (
            <button
              key={key}
              type="button"
              aria-current={page === key ? "page" : undefined}
              onClick={() => onNavigate(key)}
              className={`flex min-h-9 cursor-pointer items-center gap-2.5 rounded-md px-2.5 text-left text-[13px] focus-visible:outline-2 focus-visible:outline-accent ${
                page === key ? "bg-raised font-semibold text-ink" : "font-medium text-ink-2 hover:text-ink"
              }`}
            >
              <Icon page={key} />
              <span className="flex-1">{LABELS[key]}</span>
              {counts[key] != null && <span className="text-xs text-ink-3">{counts[key]}</span>}
            </button>
          ))}
        </nav>
        <div className="px-2.5 pt-4 pb-1.5 text-xs text-ink-3">Strategy families, trials charged</div>
        <FamilyButton label="All families" count={null} active={family === null} onClick={() => onFamily(null)} />
        {families.map((f) => (
          <Fragment key={f.family}>
            <FamilyButton label={f.family} count={f.trials} active={family === f.family && strategy === null} onClick={() => onFamily(f.family)} />
            {(strategies[f.family] ?? []).map((item) => (
              <FamilyButton key={item.name} nested label={item.name} count={null} active={strategy === item.name} onClick={() => onFamily(f.family, item.name)} />
            ))}
          </Fragment>
        ))}
        <div className="mt-auto flex flex-col gap-1.5 border-t border-line px-2.5 pt-3 text-xs text-ink-2">
          <Badge tone="ok">Holdout sealed from 9 Nov 2023</Badge>
          <span className="break-all text-ink-3">{props.runsDir}</span>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-[52px] flex-wrap items-center gap-4 border-b border-line px-6">
          <h1 className="m-0 text-[15px] font-semibold">{props.title}</h1>
          {props.subtitle && <span className="text-ink-3">{props.subtitle}</span>}
          <div className="flex-1" />
          <Button onClick={props.onToggleTheme}>{props.theme === "dark" ? "Light theme" : "Dark theme"}</Button>
          <Button onClick={props.onReload}>Reload</Button>
        </header>
        <main className="flex flex-col gap-4 px-6 pt-5 pb-8">{props.children}</main>
      </div>
    </div>
  );
}

function FamilyButton({ label, count, active, onClick, nested = false }: { label: string; count: number | null; active: boolean; onClick: () => void; nested?: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`flex cursor-pointer items-center justify-between rounded-md text-left ${nested ? "ml-3 min-h-7 border-l border-line pl-3 pr-2.5 text-[13px]" : "min-h-8 px-2.5"} focus-visible:outline-2 focus-visible:outline-accent ${
        active ? "bg-raised text-ink" : "text-ink-2 hover:text-ink"
      }`}
    >
      <span className="truncate">{label}</span>
      {count != null && <span className="text-ink-3">{count}</span>}
    </button>
  );
}
