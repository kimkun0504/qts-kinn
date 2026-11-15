import type { ReactNode } from "react";

interface PanelProps {
  title?: string;
  aside?: ReactNode;
  children: ReactNode;
  padded?: boolean;
  className?: string;
}

/** A bordered surface with an optional header row. The basic container of every page. */
export function Panel({ title, aside, children, padded = false, className = "" }: PanelProps) {
  return (
    <section className={`min-w-0 rounded-lg border border-line bg-surface ${className}`}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <h2 className="m-0 text-[13px] font-semibold">{title}</h2>
          {aside && <div className="text-xs text-ink-2">{aside}</div>}
        </header>
      )}
      <div className={padded ? "p-4" : "overflow-x-auto"}>{children}</div>
    </section>
  );
}

export function PanelNote({ children }: { children: ReactNode }) {
  return <p className="m-0 max-w-[80ch] px-4 py-3 text-xs text-ink-2">{children}</p>;
}
