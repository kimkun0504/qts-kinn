import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  aside?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
}

/** A surface with a quiet heading. The container of the home, strategy and paper pages. */
export function Card({ title, aside, children, className = "", id }: CardProps) {
  return (
    <section id={id} aria-label={title} className={`flex min-w-0 flex-col gap-3 rounded-[10px] border border-line bg-surface px-5 py-4 ${className}`}>
      {(title || aside) && (
        <header className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          {title && <h2 className="m-0 text-[13px] font-semibold text-ink-2">{title}</h2>}
          {aside && <div className="text-[13px] text-ink-3">{aside}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

/** A headline number with its label above and an optional note below. */
export function Stat({ label, value, note, tone, size = "lg" }: { label: string; value: string; note?: string; tone?: "pos" | "neg"; size?: "lg" | "md" }) {
  const colour = tone === "pos" ? "text-pos" : tone === "neg" ? "text-neg" : "";
  return (
    <div className="min-w-0">
      <div className="text-[13px] text-ink-3">{label}</div>
      <div className={`font-semibold tracking-tight ${size === "lg" ? "text-2xl leading-tight" : "text-xl leading-snug"} ${colour}`}>{value}</div>
      {note && <div className="text-[13px] text-ink-3">{note}</div>}
    </div>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return <p className="m-0 max-w-[90ch] text-[13px] text-ink-3">{children}</p>;
}
