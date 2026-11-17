import type { ReactNode } from "react";
import type { Page } from "../../lib/route";

type NavPage = Exclude<Page, "strategy">;

const ICONS: Record<NavPage, ReactNode> = {
  home: <path d="M2.5 7.5L8 3l5.5 4.5V13h-3.5V9.5h-4V13H2.5z" />,
  strategies: (
    <>
      <path d="M8 2l6 3-6 3-6-3z" />
      <path d="M2 8l6 3 6-3M2 11l6 3 6-3" />
    </>
  ),
  studies: <path d="M6 2v4L2.5 12.5a1 1 0 0 0 .9 1.5h9.2a1 1 0 0 0 .9-1.5L10 6V2M5 2h6M4.5 10h7" />,
  paper: (
    <>
      <rect x="3" y="2" width="10" height="12" rx="1.5" />
      <path d="M5.5 5.5h5M5.5 8h5M5.5 10.5h3" />
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

const LABELS: Record<NavPage, string> = {
  home: "Home",
  strategies: "Strategies",
  studies: "Studies",
  paper: "Paper trading",
  runs: "Runs",
  compare: "Compare",
  parameters: "Parameters",
  trials: "Trials",
};
const GROUPS: NavPage[][] = [
  ["home", "strategies", "studies", "paper"],
  ["runs", "compare", "parameters", "trials"],
];

interface AppShellProps {
  page: Page;
  onNavigate: (page: NavPage) => void;
  title: string | null;
  counts: Partial<Record<NavPage, string | number>>;
  runsDir: string;
  theme: "dark" | "light";
  onToggleTheme: () => void;
  onReload: () => void;
  children: ReactNode;
}

/** Side rail, top bar and the page area. Every page renders inside this. */
export function AppShell(props: AppShellProps) {
  const { page, onNavigate, counts } = props;
  const current: NavPage = page === "strategy" ? "strategies" : page;
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="flex shrink-0 flex-col gap-1 border-b border-line bg-rail px-3 py-2 md:sticky md:top-0 md:h-screen md:w-[224px] md:border-r md:border-b-0 md:py-4">
        <div className="flex items-center gap-2.5 px-3 pt-0.5 pb-1 md:pb-4">
          <span aria-hidden="true" className="inline-flex size-[26px] items-center justify-center rounded-[7px] bg-ink font-bold text-rail">
            K
          </span>
          <span className="text-base font-semibold">Kinn Research</span>
        </div>
        <nav aria-label="Sections" className="flex gap-1 overflow-x-auto md:flex-col md:overflow-visible">
          {GROUPS.map((group, g) => (
            <div key={g} className={`flex gap-1 md:flex-col ${g ? "md:mt-2 md:border-t md:border-line md:pt-3" : ""}`}>
              {group.map((key) => (
                <button
                  key={key}
                  type="button"
                  aria-current={current === key ? "page" : undefined}
                  onClick={() => onNavigate(key)}
                  className={`flex min-h-11 cursor-pointer items-center gap-2.5 rounded-lg px-3 text-left font-medium whitespace-nowrap focus-visible:outline-2 focus-visible:outline-accent ${
                    current === key ? "bg-raised text-ink" : "text-ink-2 hover:text-ink"
                  }`}
                >
                  <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className="shrink-0">
                    {ICONS[key]}
                  </svg>
                  <span className="flex-1">{LABELS[key]}</span>
                  {counts[key] != null && <span className="text-[13px] text-ink-3">{counts[key]}</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="mt-auto hidden flex-col gap-1 border-t border-line px-3 pt-3 text-[13px] text-ink-3 md:flex">
          <span>Holdout sealed from 9 Nov 2023</span>
          <span title={props.runsDir} className="truncate">
            Runs: {props.runsDir.split("/").filter(Boolean).slice(-2).join("/")}
          </span>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="mx-auto flex w-full max-w-[1260px] flex-col gap-5 px-5 pt-5 pb-12 md:px-8">
          <div className="flex min-h-10 flex-wrap items-center gap-3">
            {props.title && <h1 className="m-0 text-[26px] font-semibold tracking-tight">{props.title}</h1>}
            <div className="flex-1" />
            <button type="button" onClick={props.onToggleTheme} className="min-h-9 cursor-pointer rounded-md border border-line bg-surface px-3 text-sm font-medium hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent">
              {props.theme === "dark" ? "Light theme" : "Dark theme"}
            </button>
            <button type="button" onClick={props.onReload} className="min-h-9 cursor-pointer rounded-md border border-line bg-surface px-3 text-sm font-medium hover:bg-raised focus-visible:outline-2 focus-visible:outline-accent">
              Reload
            </button>
          </div>
          {props.children}
        </main>
      </div>
    </div>
  );
}
