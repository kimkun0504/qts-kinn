import type { Phase, RunRow, Targets } from "../lib/api";
import { Badge, type Tone } from "./ui/Badge";

export const PHASE: Record<Phase, string> = { development: "Development", validation: "Validation", holdout: "Holdout", full: "Full sample" };

const STATES: Record<string, { label: string; tone: Tone }> = {
  candidate: { label: "Candidate", tone: "ok" },
  developing: { label: "Developing", tone: "info" },
  parked: { label: "Parked", tone: "muted" },
  retired: { label: "Retired", tone: "muted" },
  canary: { label: "Canary", tone: "muted" },
};

/** A strategy's standing: candidate, developing or parked, as its strategy.yaml declares. */
export function StateBadge({ state }: { state: string }) {
  const known = STATES[state];
  return <Badge tone={known?.tone ?? "muted"}>{known?.label ?? "Not declared"}</Badge>;
}

export function targetsText(targets: Targets): string {
  return `${targets.met} of ${targets.of} targets`;
}

/** How an out-of-sample backtest did against the four targets. Development runs get none. */
export function TargetsBadge({ targets }: { targets: Targets | null }) {
  if (!targets) return null;
  const onlyFillsLeft = !targets.all_met && targets.met === targets.of - 1 && targets.fills === "not checked";
  return <Badge tone={targets.all_met ? "ok" : onlyFillsLeft ? "warn" : "bad"}>{targetsText(targets)}</Badge>;
}

/** The result cell of a runs table: targets for validation backtests, the verdict for fill checks. */
export function ResultBadge({ run }: { run: RunRow }) {
  if (run.kind === "fill_check" && run.fill_check_passed != null)
    return <Badge tone={run.fill_check_passed ? "ok" : "bad"}>{run.fill_check_passed ? "Passed" : "Failed"}</Badge>;
  return <TargetsBadge targets={run.targets} />;
}

export function isSuccess(run: RunRow): boolean {
  return run.kind === "fill_check" ? run.fill_check_passed === true : run.targets?.all_met === true;
}
