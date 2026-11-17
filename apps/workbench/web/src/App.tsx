import { useCallback, useEffect, useState } from "react";
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

const TITLES = { home: "Home", strategies: "Strategies", strategy: null, studies: "Studies", runs: "Runs", paper: "Paper trading", compare: "Compare", parameters: "Parameters", trials: "Trials and overfitting" };
type Theme = "dark" | "light";

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem("kinn-theme");
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
    try {
      localStorage.setItem("kinn-theme", theme);
    } catch {
      /* storage unavailable */
    }
  }, [theme]);

  // Abandoned runs never produced results; they stay out of the lists (Trials still reports them).
  const live = runs.filter((run) => run.status !== "abandoned");
  const open = (run: RunRow) => {
    setSelected(run.run_id);
    go({ page: "runs" });
  };
  const openStrategy = (name: string, tab = "results") => go({ page: "strategy", name, tab });
  const toggleCompare = (run: RunRow) =>
    setCompare((current) => (current.includes(run.run_id) ? current.filter((id) => id !== run.run_id) : current.length < 4 ? [...current, run.run_id] : current));
  const ledgers = board?.rows.filter((row) => row.paper).length ?? 0;

  return (
    <AppShell
      page={route.page}
      onNavigate={(page) => go({ page })}
      title={TITLES[route.page]}
      counts={{
        strategies: board ? board.rows.filter((row) => !row.variant).length : undefined,
        runs: live.length || undefined,
        paper: ledgers ? `${ledgers} ledger${ledgers > 1 ? "s" : ""}` : undefined,
        compare: compare.length || undefined,
      }}
      runsDir={runsDir}
      theme={theme}
      onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      onReload={load}
    >
      {error ? (
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
