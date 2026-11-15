import type { ReactNode } from "react";

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-line px-6 py-10 text-center">
      <p className="m-0 font-semibold">{title}</p>
      {children && <p className="mx-auto mt-1 mb-0 max-w-[60ch] text-ink-2">{children}</p>}
    </div>
  );
}
