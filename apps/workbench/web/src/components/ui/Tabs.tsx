export interface TabItem<T extends string> {
  key: T;
  label: string;
}

export function Tabs<T extends string>({ label, tabs, active, onChange }: { label: string; tabs: TabItem<T>[]; active: T; onChange: (key: T) => void }) {
  return (
    <div role="tablist" aria-label={label} className="flex flex-wrap gap-6 border-b border-line">
      {tabs.map((t) => (
        <button
          key={t.key}
          type="button"
          role="tab"
          aria-selected={active === t.key}
          onClick={() => onChange(t.key)}
          className={`-mb-px min-h-11 cursor-pointer border-b-2 px-0.5 font-medium focus-visible:outline-2 focus-visible:outline-accent ${
            active === t.key ? "border-accent text-ink" : "border-transparent text-ink-2 hover:text-ink"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
