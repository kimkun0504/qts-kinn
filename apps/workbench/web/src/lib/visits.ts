const KEY = "kinn-last-visit";

function read(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

const previous = read();

try {
  localStorage.setItem(KEY, new Date().toISOString());
} catch {
  /* storage unavailable: nothing is remembered */
}

/** When the Workbench was last opened before this visit, or null on a first visit. */
export function lastVisit(): string | null {
  return previous;
}

export interface Since {
  label: string;
  count: number;
  href: string;
}

const KIND_NAMES: Record<string, [string, string]> = {
  backtest: ["backtest", "backtests"],
  event_study: ["event study", "event studies"],
  tick_study: ["tick study", "tick studies"],
  book: ["book", "books"],
  fill_check: ["fill check", "fill checks"],
  swing: ["swing run", "swing runs"],
};

export function sinceLast(since: string | null, runs: { started_at: string; agent: string; kind: string }[], labRuns: { created_at: string; state: string }[]): Since[] {
  if (!since) return [];
  const after = (iso: string) => Boolean(iso) && Date.parse(iso) > Date.parse(since);
  const out: Since[] = [];
  const fresh = runs.filter((r) => after(r.started_at));
  const agents = new Map<string, Map<string, number>>();
  for (const r of fresh) {
    const kinds = agents.get(r.agent) ?? new Map<string, number>();
    kinds.set(r.kind, (kinds.get(r.kind) ?? 0) + 1);
    agents.set(r.agent, kinds);
  }
  for (const [agent, kinds] of [...agents.entries()].sort()) {
    const parts = [...kinds.entries()].sort((a, b) => b[1] - a[1]).map(([kind, n]) => `${n} ${(KIND_NAMES[kind] ?? [kind, kind])[n === 1 ? 0 : 1]}`);
    const total = [...kinds.values()].reduce((a, b) => a + b, 0);
    out.push({ label: `${agent}: ${parts.join(", ")}`, count: total, href: "#/runs" });
  }
  const lab = labRuns.filter((r) => after(r.created_at) && r.state === "complete").length;
  if (lab) out.push({ label: `Lab: ${lab} ${lab === 1 ? "run finished" : "runs finished"}`, count: lab, href: "#/lab" });
  return out;
}
