import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { type Command, CommandPalette } from "./components/CommandPalette";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AppShell } from "./components/layout/AppShell";
import { RunningRuns } from "./components/RunningRuns";
import { JUMPS, Shortcuts } from "./components/Shortcuts";
import { EmptyState } from "./components/ui/EmptyState";
import { api, type Board, type Family, type LedgerHead, type RunRow } from "./lib/api";
import { shortTime } from "./lib/format";
import { lab, type AlgorithmRow } from "./lib/lab";
import { href, type Route, useRoute } from "./lib/route";
import { clearRunCache } from "./lib/useRun";
import { Compare } from "./pages/Compare";
import { DataPage } from "./pages/DataPage";
import { ScreenerPage, screenerRoute } from "./pages/ScreenerPage";
import { Home } from "./pages/Home";
import { PaperPage } from "./pages/PaperPage";
import { Parameters } from "./pages/Parameters";
import { type KindFilter, Runs } from "./pages/Runs";
import { StockPage } from "./pages/StockPage";
import { Strategies } from "./pages/Strategies";
import { StrategyPage } from "./pages/StrategyPage";
import { Studies } from "./pages/Studies";
import { Trials } from "./pages/Trials";

// The Lab carries the code editor; it loads when first opened, so the other pages stay light.
const Lab = lazy(() => import("./pages/Lab").then((module) => ({ default: module.Lab })));

const TITLES = {
  home: "Home",
  strategies: "Strategies",
  strategy: null,
  stock: null,
  screener: "Screener",
  studies: "Studies",
  lab: "Lab",
  runs: "Runs",
  paper: "Paper trading",
  compare: "Compare",
  parameters: "Parameters",
  trials: "Trials and overfitting",
  data: "Data",
};
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

const COMPARE_KEY = "kinn-compare";

export function pageTitle(route: Route, board: Board | null): string {
  const named = route.name ?? "";
  if (route.page === "strategy") return board?.rows.find((row) => row.strategy === named && !row.variant)?.title ?? named;
  if (route.page === "stock") return named || "Stocks";
  if (route.page === "lab") return named ? `${named} in the Lab` : "Lab";
  if (route.page === "runs" && named) return `Run ${named}`;
  if (route.page === "paper" && named) return `${named.replace(/_/g, " ")} paper ledger`;
  return TITLES[route.page] ?? "Kinn Research";
}

function savedCompare(): string[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(COMPARE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === "string").slice(0, 4) : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [runs, setRuns] = useState<RunRow[]>([]);
  const [families, setFamilies] = useState<Family[]>([]);
  const [board, setBoard] = useState<Board | null>(null);
  const [runsDir, setRunsDir] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [route, go] = useRoute();
  const [compare, setCompare] = useState<string[]>(() => (route.page === "compare" && route.name ? route.name.split(",").slice(0, 4) : savedCompare()));
  const [kind, setKind] = useState<KindFilter>("all");
  const [theme, setTheme] = useState<Theme>(initialTheme);
  const [version, setVersion] = useState(0);
  const [heads, setHeads] = useState<LedgerHead[]>([]);
  const [palette, setPalette] = useState(false);
  const [algorithms, setAlgorithms] = useState<AlgorithmRow[]>([]);
  const [shortcuts, setShortcuts] = useState(false);
  const pending = useRef(0);
  const closeShortcuts = useCallback(() => setShortcuts(false), []);

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
    try {
      localStorage.setItem(COMPARE_KEY, JSON.stringify(compare));
    } catch {
      return;
    }
  }, [compare]);
  useEffect(() => {
    if (route.page === "compare" && route.name) setCompare(route.name.split(",").slice(0, 4));
  }, [route.page, route.name]);
  useEffect(() => {
    if (route.page === "compare") window.history.replaceState(null, "", href({ page: "compare", name: compare.join(",") || undefined }));
  }, [route.page, compare]);
  useEffect(() => {
    api
      .ledgers()
      .then(setHeads)
      .catch(() => setHeads([]));
  }, [version]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.tagName === "SELECT" || target.isContentEditable);
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPalette((open) => !open);
        return;
      }
      if (typing || event.metaKey || event.ctrlKey || event.altKey) return;
      if (event.key === "/") {
        event.preventDefault();
        setPalette(true);
      } else if (event.key === "?") {
        event.preventDefault();
        setShortcuts(true);
      } else if (pending.current && Date.now() - pending.current < 1500) {
        pending.current = 0;
        const jump = JUMPS.find((j) => j.key === event.key.toLowerCase());
        if (jump) {
          event.preventDefault();
          window.location.hash = href({ page: jump.page });
          window.scrollTo(0, 0);
        }
      } else if (event.key.toLowerCase() === "g") {
        pending.current = Date.now();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  useEffect(() => {
    if (palette)
      lab
        .algorithms()
        .then(setAlgorithms)
        .catch(() => setAlgorithms([]));
  }, [palette]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);
  useEffect(() => {
    document.title = `${pageTitle(route, board)} – Kinn Research`;
  }, [route, board]);
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
  const open = (run: RunRow) => go({ page: "runs", name: run.run_id }, { scroll: route.page !== "runs" });
  const openStrategy = (name: string, tab = "results") => go({ page: "strategy", name, tab });
  const openLab = useCallback((name?: string, runId?: string) => go({ page: "lab", name, tab: runId }, { scroll: false }), [go]);
  const toggleCompare = (run: RunRow) => setCompare((current) => (current.includes(run.run_id) ? current.filter((id) => id !== run.run_id) : current.length < 4 ? [...current, run.run_id] : current));
  const ledgers = (board?.rows.filter((row) => row.paper).length ?? 0) + heads.length;
  const pages: [string, string][] = [
    ["home", "Home"],
    ["strategies", "Strategies"],
    ["stock", "Stocks"],
    ["screener", "Screener"],
    ["studies", "Studies"],
    ["paper", "Paper trading"],
    ["lab", "Lab"],
    ["runs", "Runs"],
    ["compare", "Compare"],
    ["parameters", "Parameters"],
    ["trials", "Trials and overfitting"],
    ["data", "Data"],
  ];
  const commands: Command[] = [
    ...pages.map(([key, label]) => ({ id: `page-${key}`, group: "Pages", label, href: `#/${key}` })),
    ...(board?.rows ?? [])
      .filter((row) => !row.variant)
      .map((row) => ({
        id: `strategy-${row.strategy}`,
        group: "Strategies",
        label: row.title,
        hint: row.label ?? row.verdict,
        keywords: row.strategy,
        href: `#/strategy/${encodeURIComponent(row.strategy)}`,
      })),
    ...(board?.rows ?? [])
      .filter((row) => row.paper)
      .map((row) => ({ id: `ledger-${row.strategy}`, group: "Paper ledgers", label: row.title, hint: "paper ledger", href: `#/paper/${encodeURIComponent(row.strategy)}` })),
    ...heads.map((h) => ({ id: `ledger-${h.name}`, group: "Paper ledgers", label: h.title, hint: "paper ledger", keywords: h.name, href: `#/paper/${encodeURIComponent(h.name)}` })),
    ...algorithms.map((a) => ({ id: `algo-${a.name}`, group: "Lab algorithms", label: a.name, hint: a.description, href: `#/lab/${encodeURIComponent(a.name)}` })),
    ...live
      .slice(0, 400)
      .map((run) => ({
        id: `run-${run.run_id}`,
        group: "Runs",
        label: run.strategy,
        hint: `${run.config}  ${shortTime(run.started_at)}`,
        keywords: `${run.config} ${run.run_id} ${run.agent}`,
        href: `#/runs/${encodeURIComponent(run.run_id)}`,
      })),
    { id: "action-theme", group: "Actions", label: theme === "dark" ? "Light theme" : "Dark theme", run: () => toggleTheme() },
    { id: "action-reload", group: "Actions", label: "Reload the run store", run: () => load() },
    { id: "action-shortcuts", group: "Actions", label: "Keyboard shortcuts", hint: "?", run: () => setShortcuts(true) },
  ];

  return (
    <AppShell
      page={route.page}
      onNavigate={(page) => go({ page })}
      title={route.page === "lab" && route.name ? null : route.page === "stock" && !route.name ? "Stocks" : TITLES[route.page]}
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
      onSearch={() => setPalette(true)}
      status={<RunningRuns />}
    >
      <CommandPalette open={palette} onClose={() => setPalette(false)} commands={commands} />
      <Shortcuts open={shortcuts} onClose={closeShortcuts} />
      <ErrorBoundary key={`${route.page}/${route.name ?? ""}`}>
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
          <StrategyPage
            key={`${route.name}-${version}`}
            name={route.name}
            tab={route.tab ?? "results"}
            runs={live}
            onTab={(tab) => openStrategy(route.name as string, tab)}
            onBack={() => go({ page: "strategies" })}
          />
        ) : route.page === "stock" ? (
          <StockPage symbol={route.name} permaticker={route.tab} onOpen={(symbol, permaticker) => go({ page: "stock", name: symbol, tab: permaticker ? String(permaticker) : undefined })} />
        ) : route.page === "screener" ? (
          <ScreenerPage on={route.name} query={route.tab} onDate={(on, query) => go(screenerRoute(on, query), { scroll: false })} />
        ) : route.page === "studies" ? (
          <Studies key={version} onOpen={openStrategy} />
        ) : route.page === "paper" ? (
          <PaperPage key={version} board={board} name={route.name} onOpen={(name) => go({ page: "paper", name }, { scroll: false })} />
        ) : route.page === "runs" ? (
          <Runs runs={live} selected={route.page === "runs" ? (route.name ?? null) : null} onOpen={open} compare={compare} onToggleCompare={toggleCompare} kind={kind} onKind={setKind} />
        ) : route.page === "compare" ? (
          <Compare ids={compare} runs={runs} onToggle={toggleCompare} />
        ) : route.page === "data" ? (
          <DataPage key={version} />
        ) : route.page === "parameters" ? (
          <Parameters runs={live} />
        ) : (
          <Trials families={families} runs={runs} />
        )}
      </ErrorBoundary>
    </AppShell>
  );
}
