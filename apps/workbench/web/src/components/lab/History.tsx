import { useEffect, useState } from "react";
import { lab, type Version } from "../../lib/lab";
import { Button } from "../ui/Button";
import { when } from "./RunResults";

interface HistoryProps {
  kind: "algorithms" | "library";
  name: string;
  /** Changes after each save, so the list is read again. */
  refresh: number;
  onRestore: (code: string, version: Version) => void;
}

/** Every earlier version of the file, newest first, each one a click from the editor. */
export function History({ kind, name, refresh, onRestore }: HistoryProps) {
  const [versions, setVersions] = useState<Version[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState<string | null>(null);
  const [preview, setPreview] = useState<Record<string, string>>({});

  useEffect(() => {
    let live = true;
    lab
      .history(kind, name)
      .then((found) => live && (setVersions(found), setFailed(false)))
      .catch(() => live && setFailed(true));
    return () => {
      live = false;
    };
  }, [kind, name, refresh]);

  const show = (version: string) => {
    setOpen(open === version ? null : version);
    if (!preview[version]) lab.version(kind, name, version).then((found) => setPreview((p) => ({ ...p, [version]: found.code })));
  };

  if (failed) return <p className="m-0 px-4 py-6 text-[13px] text-ink-2">History needs the Workbench restarted once after the update.</p>;
  if (!versions) return <p className="m-0 px-4 py-6 text-[13px] text-ink-2">Loading…</p>;
  if (!versions.length) return <p className="m-0 px-4 py-6 text-[13px] text-ink-2">No earlier versions yet. Each save keeps the one before it here.</p>;
  return (
    <ul className="m-0 list-none p-0">
      {versions.map((v) => (
        <li key={v.version} className="border-b border-line-soft">
          <button
            type="button"
            aria-expanded={open === v.version}
            onClick={() => show(v.version)}
            className="flex w-full cursor-pointer flex-col gap-0.5 px-4 py-2.5 text-left hover:bg-raised focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-accent"
          >
            <span className="flex items-baseline justify-between gap-3">
              <span className="text-[13px] font-semibold text-ink">{when(v.saved_at)}</span>
              <span className="shrink-0 text-[12px] text-ink-3">{v.lines} lines</span>
            </span>
            <span className="truncate font-mono text-[12px] text-ink-2">{v.first_line || " "}</span>
          </button>
          {open === v.version && (
            <div className="flex flex-col gap-2 px-4 pb-3">
              <pre className="m-0 max-h-56 overflow-auto rounded-md bg-raised p-2.5 font-mono text-[12px] leading-relaxed whitespace-pre">{preview[v.version] ?? "Loading…"}</pre>
              <Button variant="primary" disabled={!preview[v.version]} onClick={() => preview[v.version] && onRestore(preview[v.version], v)} className="self-start">
                Restore this version
              </Button>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
