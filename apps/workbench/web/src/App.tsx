import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { EmptyState } from "./components/ui/EmptyState";
import { api, type Board, type Family, type RunRow } from "./lib/api";
import { useRoute } from "./lib/route";
import { clearRunCache } from "./lib/useRun";
import { Compare } from "./pages/Compare";
import { Home } from "./pages/Home";
import { PaperPage } from "./pages/PaperPage";
import { Parameters } from "./pages/Parameters";
import { type KindFilter, Runs } from "./pages/Runs";
import { Strategies } from "./pages/Strategies";
import { StrategyPage } from "./pages/StrategyPage";
import { Studies } from "./pages/Studies";
import { Trials } from "./pages/Trials";

// The Lab carries the code editor; it loads when first opened, so the other pages stay light.
const Lab = lazy(() => import("./pages/Lab").then((module) => ({ default: module.Lab })));

const TITLES = { home: "Home", strategies: "Strategies", strategy: null, studies: "Studies", lab: "Lab", runs: "Runs", paper: "Paper trading", compare: "Compare", parameters: "Parameters", trials: "Trials and overfitting" };
type Theme = "dark" | "light";

// Light unless the owner picked dark. The key is new so the old app's auto-saved "dark" is ignored.
const THEME_KEY = "kinn-theme-choice";

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem(THEME_KEY);
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    /* storage unavailable: fall through */
  }
  return "light";
}

export default function App() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [families, setFamilies] = useState<Family[]>([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [runsDir, setRunsDir] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [route, go] = useRoute();
  const [selected, setSelected] = useState<string | null>(null);
  const [compare, setCompare] = useState<string[]>([]);
  const [kind, setKind] = useState<KindFilter>("all");
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [version, setVersion] = useState(0);

  const load = useCallback(() => {
    clearRunCache();
    Promise.all([api.runs(), api.families(), api.info(), api.board()])
      .then(([r, f, info, b]) => {
        setRuns(r);
        setFamilies(f);
        setBoard(b);
        setRunsDir(info.runs_dir);
        setError(null);
        setVersion((v) => v + 1);
      })
      .catch(() => setError("The run store could not be read. Is the Workbench server running, and restarted since the last update?"));
  }, []);
  useEffect(load, [load]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      /* storage unavailable: the choice lasts for this visit */
    }
  };

  // Abandoned runs never produced results; they stay out of the lists (Trials still reports them).
  const live = runs.filter((run) => run.status !== "abandoned");
  const open = (run: RunRow) => {
    setSelected(run.run_id);
    go({ page: "runs" });
  };
  const openStrategy = (name: string, tab = "results") => go({ page: "strategy", name, tab });
  const openLab = useCallback((name?: string, runId?: string) => go({ page: "lab", name, tab: runId }, { scroll: false }), [go]);
  const toggleCompare = (run: RunRow) =>
    setCompare((current) => (current.includes(run.run_id) ? current.filter((id) => id !== run.run_id) : current.length < 4 ? [...current, run.run_id] : current));
  const ledgers = board?.rows.filter((row) => row.paper).length ?? 0;

  return (
    <AppShell
      page={route.page}
      onNavigate={(page) => go({ page })}
      title={route.page === "lab" && route.name ? null : TITLES[route.page]}
      counts={{
        strategies: board ? board.rows.filter((row) => !row.variant).length : undefined,
        runs: live.length || undefined,
        paper: ledgers || undefined,
        compare: compare.length || undefined,
      }}
      runsDir={runsDir}
      theme={theme}
      onToggleTheme={toggleTheme}
      onReload={load}
    >
      {route.page === "lab" ? (
        <Suspense fallback={<p className="text-ink-2">Loading the Lab…</p>}>
          <Lab name={route.name} runId={route.tab} onOpen={openLab} />
        </Suspense>
      ) : error ? (
        <EmptyState title="Could not load the Workbench">{error}</EmptyState>
      ) : !board ? (
        <p className="text-ink-2">Loading…</p>
      ) : route.page === "home" ? (
        <Home key={version} board={board} onOpen={openStrategy} />
      ) : route.page === "strategies" ? (
        <Strategies board={board} onOpen={openStrategy} />
      ) : route.page === "strategy" && route.name ? (
        <StrategyPage key={`${route.name}-${version}`} name={route.name} tab={route.tab ?? "results"} runs={live} onTab={(tab) => openStrategy(route.name as string, tab)} onBack={() => go({ page: "strategies" })} />
      ) : route.page === "studies" ? (
        <Studies key={version} onOpen={openStrategy} />
      ) : route.page === "paper" ? (
        <PaperPage key={version} board={board} />
      ) : route.page === "runs" ? (
        <Runs runs={live} selected={selected} onOpen={open} compare={compare} onToggleCompare={toggleCompare} kind={kind} onKind={setKind} />
      ) : route.page === "compare" ? (
        <Compare ids={compare} runs={runs} />
      ) : route.page === "parameters" ? (
        <Parameters runs={live} />
      ) : (
        <Trials families={families} runs={runs} />
      )}
    </AppShell>
  );
}
