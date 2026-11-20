import { useEffect, useRef } from "react";
import type { Page } from "../lib/route";

export const JUMPS: { key: string; page: Page; label: string }[] = [
  { key: "h", page: "home", label: "Home" },
  { key: "t", page: "strategies", label: "Strategies" },
  { key: "m", page: "markets", label: "Markets" },
  { key: "s", page: "stock", label: "Stocks" },
  { key: "f", page: "screener", label: "Screener" },
  { key: "u", page: "studies", label: "Studies" },
  { key: "p", page: "paper", label: "Paper trading" },
  { key: "l", page: "lab", label: "Lab" },
  { key: "r", page: "runs", label: "Runs" },
  { key: "c", page: "compare", label: "Compare" },
  { key: "d", page: "data", label: "Data" },
];

const KEYS: [string[], string][] = [
  [["⌘", "K"], "Search everything"],
  [["/"], "Search everything"],
  [["?"], "Show these shortcuts"],
  [["Esc"], "Close a dialog"],
];

function Keys({ keys }: { keys: string[] }) {
  return (
    <span className="inline-flex gap-1">
      {keys.map((k) => (
        <kbd key={k} className="min-w-6 rounded border border-line bg-raised px-1.5 py-0.5 text-center font-sans text-[12px] text-ink">
          {k}
        </kbd>
      ))}
    </span>
  );
}

export function Shortcuts({ open, onClose }: { open: boolean; onClose: () => void }) {
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    close.current?.focus();
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-[color-mix(in_srgb,var(--ink)_28%,transparent)] px-4 pt-[12vh]" onMouseDown={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
        className="w-full max-w-[560px] rounded-xl border border-line bg-surface shadow-[0_24px_64px_rgba(15,23,42,0.24)]"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line px-5 py-3">
          <h2 className="m-0 text-sm font-semibold">Keyboard shortcuts</h2>
          <button ref={close} type="button" onClick={onClose} className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent">
            Close
          </button>
        </div>
        <div className="grid gap-x-8 gap-y-2 px-5 py-4 text-sm sm:grid-cols-2">
          {KEYS.map(([keys, label]) => (
            <div key={label + keys.join("")} className="flex items-center justify-between gap-3">
              <span className="text-ink-2">{label}</span>
              <Keys keys={keys} />
            </div>
          ))}
          {JUMPS.map((jump) => (
            <div key={jump.key} className="flex items-center justify-between gap-3">
              <span className="text-ink-2">Go to {jump.label}</span>
              <Keys keys={["G", jump.key.toUpperCase()]} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
