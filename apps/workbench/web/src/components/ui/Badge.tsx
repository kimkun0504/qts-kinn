export type Tone = "ok" | "warn" | "info" | "muted" | "bad";

const TONES: Record<Tone, string> = {
  ok: "text-pos",
  warn: "text-warn",
  info: "text-accent-soft",
  muted: "text-ink-2",
  bad: "text-neg",
};

/** A status label: a dot and a word, so state never depends on colour alone. */
export function Badge({ tone, children }: { tone: Tone; children: string }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${TONES[tone]}`}>
      <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
      {children}
    </span>
  );
}
