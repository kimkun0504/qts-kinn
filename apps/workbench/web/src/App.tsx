import { useCallback, useEffect, useState } from "react";
import { AppShell, type Page } from "./components/layout/AppShell";
import { EmptyState } from "./components/ui/EmptyState";
import { api, type Family, type RunRow } from "./lib/api";
import { clearRunCache } from "./lib/useRun";
import { Compare } from "./pages/Compare";
import { Overview } from "./pages/Overview";
import { Parameters } from "./pages/Parameters";
import { type KindFilter, Runs } from "./pages/Runs";
import { Trials } from "./pages/Trials";

const TITLES: Record<Page, string> = { overview: "Overview", runs: "Runs", compare: "Compare", parameters: "Parameters", trials: "Trials and overfitting" };
type Theme = "dark" | "light";

function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem("kinn-theme");
    if (saved === "dark" || saved === "light") return saved;
  } catch {
    /* storage unavailable: fall through */
  }
  return "dark";
}

export default function App() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [families, setFamilies] = useState<Family[]>([]);
  const [runsDir, setRunsDir] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<Page>("overview");
  const [family, setFamily] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [compare, setCompare] = useState<string[]>([]);
  const [kind, setKind] = useState<KindFilter>("all");
  const [theme, setTheme] = useState<Theme>(initialTheme);

  const load = useCallback(() => {
    clearRunCache();
    Promise.all([api.runs(), api.families(), api.info()])
      .then(([r, f, info]) => {
        setRuns(r);
        setFamilies(f);
        setRunsDir(info.runs_dir);
        setError(null);
      })
      .catch(() => setError("The run store could not be read. Is the Workbench server running?"));
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
  const visible = runs.filter((run) => run.status !== "abandoned" && (!family || run.family === family));
  const visibleFamilies = families.filter((f) => !family || f.family === family);
  const open = (run: RunRow) => {
    setSelected(run.run_id);
    setPage("runs");
  };
  const toggleCompare = (run: RunRow) =>
    setCompare((current) => (current.includes(run.run_id) ? current.filter((id) => id !== run.run_id) : current.length < 4 ? [...current, run.run_id] : current));

  return (
    <AppShell
      page={page}
      onNavigate={setPage}
      title={TITLES[page]}
      subtitle={family ?? "All families"}
      families={families}
      family={family}
      onFamily={setFamily}
      counts={{ runs: visible.length, compare: compare.length || undefined, trials: visibleFamilies.reduce((sum, f) => sum + f.trials, 0) }}
      runsDir={runsDir}
      theme={theme}
      onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      onReload={load}
    >
      {error ? (
        <EmptyState title="Could not load runs">{error}</EmptyState>
      ) : page === "overview" ? (
        <Overview runs={visible} families={visibleFamilies} onOpen={open} />
      ) : page === "runs" ? (
        <Runs runs={visible} selected={selected} onOpen={open} compare={compare} onToggleCompare={toggleCompare} kind={kind} onKind={setKind} />
      ) : page === "compare" ? (
        <Compare ids={compare} runs={runs} />
      ) : page === "parameters" ? (
        <Parameters runs={visible} />
      ) : (
        <Trials families={visibleFamilies} runs={runs} />
      )}
    </AppShell>
  );
}
