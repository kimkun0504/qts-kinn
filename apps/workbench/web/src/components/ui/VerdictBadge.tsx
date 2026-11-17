import type { Group } from "../../lib/api";

const TONE: Record<Group, string> = {
  works: "border-gain text-pos",
  testing: "border-accent text-accent",
  closed: "border-line text-ink-2",
};

/** Where an idea stands. The icon differs by group, so the state never rests on colour alone. */
export function VerdictBadge({ group, label }: { group: Group; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[13px] font-semibold whitespace-nowrap ${TONE[group]}`}>
      <svg aria-hidden="true" width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {group === "works" ? <path d="M2.5 7.5l3 3 6-7" /> : group === "testing" ? <circle cx="7" cy="7" r="3.5" fill="currentColor" stroke="none" /> : <path d="M3.5 7h7" />}
      </svg>
      {label}
    </span>
  );
}
