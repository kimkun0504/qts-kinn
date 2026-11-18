import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CodeEditor, type CodeEditorHandle } from "../components/CodeEditor";
import { History } from "../components/lab/History";
import { Inspector } from "../components/lab/Inspector";
import { type RunRow, RunResults, STATE_LABEL, when } from "../components/lab/RunResults";
import { Button } from "../components/ui/Button";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel } from "../components/ui/Panel";
import { int } from "../lib/format";
import {
  type AlgorithmFile,
  type AlgorithmRow,
  type Finding,
  cleanName,
  lab,
  LabError,
  type Meta,
  MODULE_NAME,
  type ModuleRow,
  NAME,
  type RunDetail,
  type RunListRow,
  type RunState,
  type Status,
  type Template,
} from "../lib/lab";
import { base as baseSettings, changed, type Draft, EMPTY_DRAFT, fromSettings, toPatch } from "../lib/labSettings";

interface LabProps {
  name?: string;
  runId?: string;
  onOpen: (name?: string, runId?: string) => void;
}

const BLANK = `"""My idea in one line."""

SETTINGS = {"exit": {"hold_days": 20}}


def signal(data):
    # A table of True/False by date and stock: True buys the stock at the next open.
    return data.returns > 0.05
`;

const STARTER_MODULE = `"""Helpers shared by my algorithms."""


def zscore(table, window):
    """How far each value is from its own recent average, in standard deviations."""
    mean = table.rolling(window).mean()
    spread = table.rolling(window).std()
    return (table - mean) / spread
`;

const LIVE: RunState[] = ["queued", "running"];
const field = "h-8 rounded-md border border-line bg-surface px-2.5 text-sm text-ink placeholder:text-ink-3 focus-visible:outline-2 focus-visible:outline-accent";

function loadDraft(name: string): Draft {
  try {
    const saved = localStorage.getItem(`kinn-lab-draft:${name}`);
    return saved ? { ...EMPTY_DRAFT, ...JSON.parse(saved) } : EMPTY_DRAFT;
  } catch {
    return EMPTY_DRAFT;
  }
}

function keepDraft(name: string, draft: Draft) {
  try {
    if (changed(draft)) localStorage.setItem(`kinn-lab-draft:${name}`, JSON.stringify(draft));
    else localStorage.removeItem(`kinn-lab-draft:${name}`);
  } catch {
    /* storage unavailable: the draft lasts for this visit */
  }
}

function Message({ text, onClose, tone = "bad" }: { text: string; onClose: () => void; tone?: "bad" | "note" }) {
  return (
    <div role={tone === "bad" ? "alert" : "status"} className={`flex items-start gap-3 rounded-lg border bg-surface px-4 py-3 text-sm ${tone === "bad" ? "border-neg" : "border-line"}`}>
      <span className="flex-1 whitespace-pre-wrap">{text}</span>
      <button type="button" aria-label="Dismiss" onClick={onClose} className="cursor-pointer text-ink-3 hover:text-ink">
        ×
      </button>
    </div>
  );
}

// -- the list of algorithms -------------------------------------------------------------------
function NewAlgorithm({ templates, taken, onCreate, onCancel }: { templates: Template[]; taken: string[]; onCreate: (name: string, code: string) => void; onCancel: () => void }) {
  const [text, setText] = useState("");
  const [from, setFrom] = useState("");
  const name = cleanName(text);
  const problem = !name
    ? null
    : !NAME.test(name)
      ? "Use letters, digits, - and _."
      : name === "library"
        ? "That word is kept for the library."
        : taken.includes(name)
          ? "That name is taken."
          : null;
  return (
    <form
      aria-label="New algorithm"
      className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (name && !problem) onCreate(name, templates.find((t) => t.name === from)?.code ?? BLANK);
      }}
    >
      <input autoFocus aria-label="Name" value={text} onChange={(e) => setText(e.target.value)} placeholder="Name, e.g. gap_fade" className={`${field} w-56`} />
      <select aria-label="Start from" value={from} onChange={(e) => setFrom(e.target.value)} className={`${field} w-56`}>
        <option value="">Start from a blank file</option>
        {templates.map((t) => (
          <option key={t.name} value={t.name}>
            Start from {t.name}
          </option>
        ))}
      </select>
      <Button type="submit" variant="primary" disabled={!name || Boolean(problem)}>
        Create
      </Button>
      <Button onClick={onCancel}>Cancel</Button>
      {problem ? <span className="text-[13px] text-neg">{problem}</span> : name && name !== text ? <span className="text-[13px] text-ink-3">Saved as {name}</span> : null}
    </form>
  );
}

const algorithmColumns: Column<AlgorithmRow>[] = [
  { key: "name", header: "Algorithm", align: "left", strong: true, render: (a) => a.name },
  { key: "description", header: "What it does", align: "left", muted: true, max: 420, render: (a) => a.description || "–" },
  { key: "result", header: "Last run", align: "left", max: 320, render: (a) => (a.last_run ? (a.last_run.headline ?? STATE_LABEL[a.last_run.state]) : "–") },
  { key: "trials", header: "Trials", render: (a) => int(a.trials) },
  { key: "updated", header: "Changed", muted: true, render: (a) => when(a.updated) },
];

function NewModule({ taken, onCreate, onCancel }: { taken: string[]; onCreate: (name: string) => void; onCancel: () => void }) {
  const [text, setText] = useState("");
  const name = text.trim().toLowerCase();
  const problem = !name ? null : !MODULE_NAME.test(name) ? "Letters, digits and _, starting with a letter." : taken.includes(name) ? "That name is taken." : null;
  return (
    <form
      aria-label="New helper module"
      className="flex flex-wrap items-center gap-3 border-b border-line px-4 py-3"
      onSubmit={(event) => {
        event.preventDefault();
        if (name && !problem) onCreate(name);
      }}
    >
      <input autoFocus aria-label="Module name" value={text} onChange={(e) => setText(e.target.value)} placeholder="Name, e.g. helpers" className={`${field} w-56`} />
      <Button type="submit" variant="primary" disabled={!name || Boolean(problem)}>
        Create
      </Button>
      <Button onClick={onCancel}>Cancel</Button>
      {problem ? <span className="text-[13px] text-neg">{problem}</span> : name ? <span className="text-[13px] text-ink-3">Import it with: from lab.{name} import …</span> : null}
    </form>
  );
}

function LabIndex({
  algorithms,
  templates,
  modules,
  onOpen,
  onCreate,
  onOpenModule,
  onCreateModule,
}: {
  algorithms: AlgorithmRow[];
  templates: Template[];
  modules: ModuleRow[];
  onOpen: (name: string) => void;
  onCreate: (name: string, code: string) => Promise<void>;
  onOpenModule: (name: string) => void;
  onCreateModule: (name: string) => Promise<void>;
}) {
  const [newModule, setNewModule] = useState(false);
  const [creating, setCreating] = useState(!algorithms.length);
  const sorted = [...algorithms].sort((a, b) => b.updated.localeCompare(a.updated));
  const taken = algorithms.map((a) => a.name);
  const copyName = (base: string) => {
    let name = base;
    for (let k = 2; taken.includes(name); k += 1) name = `${base}_${k}`;
    return name;
  };
  return (
    <div className="flex flex-col gap-5">
      <Panel title="Your algorithms" aside={creating ? undefined : <Button variant="primary" onClick={() => setCreating(true)}>New algorithm</Button>}>
        {creating && <NewAlgorithm templates={templates} taken={taken} onCreate={onCreate} onCancel={() => setCreating(false)} />}
        <DataTable columns={algorithmColumns} rows={sorted} rowKey={(a) => a.name} onRowClick={(a) => onOpen(a.name)} empty="None yet. Name one above, or copy a template below." />
      </Panel>
      <Panel title="Library" aside={newModule ? undefined : <Button onClick={() => setNewModule(true)}>New helper module</Button>}>
        {newModule && <NewModule taken={modules.map((m) => m.name)} onCreate={onCreateModule} onCancel={() => setNewModule(false)} />}
        <DataTable
          columns={[
            { key: "name", header: "Module", align: "left", strong: true, render: (m) => `lab.${m.name}` },
            { key: "description", header: "What it holds", align: "left", muted: true, max: 520, render: (m) => m.description || "–" },
            { key: "updated", header: "Changed", muted: true, render: (m) => when(m.updated) },
          ]}
          rows={modules}
          rowKey={(m) => m.name}
          onRowClick={(m) => onOpenModule(m.name)}
          empty="Helper functions several algorithms share go here. An algorithm imports one with from lab.<name> import …"
        />
      </Panel>
      <Panel title="Templates">
        <DataTable
          columns={[
            { key: "name", header: "Template", align: "left", strong: true, render: (t) => t.name },
            { key: "description", header: "What it does", align: "left", muted: true, render: (t) => <span className="whitespace-normal">{t.description}</span> },
            {
              key: "copy",
              header: "",
              render: (t) => (
                <Button
                  onClick={(event) => {
                    event.stopPropagation();
                    onCreate(copyName(t.name), t.code);
                  }}
                >
                  Make a copy
                </Button>
              ),
            },
          ]}
          rows={templates}
          rowKey={(t) => t.name}
        />
      </Panel>
    </div>
  );
}

// -- one algorithm --------------------------------------------------------------------------
function Workspace({ name, runId, meta, onOpen, onChanged }: { name: string; runId?: string; meta: Meta; onOpen: (name?: string, runId?: string) => void; onChanged: () => void }) {
  const [file, setFile] = useState<AlgorithmFile | null>(null);
  const [code, setCode] = useState("");
  const [saved, setSaved] = useState("");
  const [draft, setDraft] = useState<Draft>(() => loadDraft(name));
  const [runs, setRuns] = useState<RunListRow[]>([]);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [historyKey, setHistoryKey] = useState(0);
  const editor = useRef<CodeEditorHandle>(null);
  const results = useRef<HTMLDivElement>(null);
  const startedHere = useRef<string | null>(null); // a run this page started, to show when it ends
  const dirty = file != null && code !== saved;

  const refreshRuns = useCallback(() => lab.runs(name).then(setRuns), [name]);

  useEffect(() => {
    let live = true;
    lab
      .algorithm(name)
      .then((found) => {
        if (!live) return;
        setFile(found);
        setCode(found.code);
        setSaved(found.code);
      })
      .catch((e: Error) => {
        if (!live) return;
        if (e instanceof LabError && e.status === 404) onOpen(undefined, undefined);
        else setMessage(e.message);
      });
    refreshRuns().catch(() => undefined);
    return () => {
      live = false;
    };
  }, [name, refreshRuns, onOpen]);

  useEffect(() => keepDraft(name, draft), [name, draft]);

  // Leaving (another algorithm, another page) keeps the work: unsaved code is saved on the way out.
  const pending = useRef({ code, dirty });
  pending.current = { code, dirty };
  useEffect(
    () => () => {
      if (pending.current.dirty) lab.save(name, pending.current.code).catch(() => undefined);
    },
    [name],
  );
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  // The run on screen: the one in the address, else the latest. Followed until it ends.
  const shown = runId ?? runs[0]?.run_id ?? null;
  useEffect(() => {
    if (!shown) {
      setDetail(null);
      setStatus(null);
      return;
    }
    let live = true;
    let timer: number | undefined;
    // When a run started from this page ends (however fast), show its results.
    const reveal = () => {
      if (startedHere.current !== shown) return;
      startedHere.current = null;
      window.setTimeout(() => results.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 150);
    };
    const load = () =>
      lab
        .run(shown)
        .then((found) => {
          if (!live) return;
          setDetail(found);
          setStatus(found.status);
          if (LIVE.includes(found.status.state)) timer = window.setTimeout(tick, 1000);
          else reveal();
        })
        .catch(() => live && setDetail(null));
    const tick = () =>
      lab
        .status(shown)
        .then((found) => {
          if (!live) return;
          setStatus(found);
          if (LIVE.includes(found.state)) timer = window.setTimeout(tick, 1000);
          else {
            load();
            refreshRuns();
            onChanged();
          }
        })
        .catch(() => live && (timer = window.setTimeout(tick, 3000)));
    load();
    return () => {
      live = false;
      window.clearTimeout(timer);
    };
  }, [shown, refreshRuns, onChanged]);

  const save = useCallback(async () => {
    if (!dirty) return true;
    try {
      await lab.save(name, code);
      setSaved(code);
      setHistoryKey((k) => k + 1);
      onChanged();
      return true;
    } catch (e) {
      setMessage((e as Error).message);
      return false;
    }
  }, [name, code, dirty, onChanged]);

  const running = status != null && LIVE.includes(status.state);

  const errors = findings.filter((f) => f.severity === "error");
  const warnings = findings.filter((f) => f.severity === "warning");

  const run = useCallback(async () => {
    if (busy || running) return;
    const blocking = findings.find((f) => f.severity === "error");
    if (blocking) {
      setMessage(`Fix line ${blocking.line} first: ${blocking.message}`);
      editor.current?.reveal(blocking.line, blocking.column);
      return;
    }
    const { patch, errors: wrong } = toPatch(draft);
    if (wrong.length) {
      setMessage(wrong.join(" "));
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const started = await lab.start(name, code, patch);
      startedHere.current = started.run_id;
      setSaved(code);
      setHistoryKey((k) => k + 1);
      setStatus(started.status);
      await refreshRuns();
      onChanged();
      onOpen(name, started.run_id);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, [busy, running, findings, draft, name, code, refreshRuns, onChanged, onOpen]);

  const checkCode = useCallback(
    (text: string) =>
      lab.check(text).then(
        (found) => found.findings,
        (e) => {
          if (e instanceof LabError && e.status === 404) return []; // a server from before the check
          throw e;
        },
      ),
    [],
  );

  const cancel = async () => {
    if (!shown) return;
    try {
      setStatus(await lab.cancel(shown));
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  const remove = async () => {
    try {
      await lab.remove(name);
      pending.current.dirty = false;
      onChanged();
      onOpen(undefined, undefined);
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  const base = useMemo(() => baseSettings(meta.defaults, file?.settings_in_code ?? null), [meta, file]);
  const numbered: RunRow[] = useMemo(() => {
    const trial = new Map<string, number>();
    [...runs]
      .reverse()
      .filter((r) => r.trial)
      .forEach((r, i) => trial.set(r.run_id, i + 1));
    return runs.map((r) => ({ ...r, number: trial.get(r.run_id) ?? null }));
  }, [runs]);
  const share = Math.round(100 * (status?.progress ?? 0));

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2.5">
        <div className="text-sm text-ink-3">
          <button type="button" onClick={() => onOpen(undefined, undefined)} className="cursor-pointer text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            Lab
          </button>{" "}
          / {name}
        </div>
        <h1 className="m-0 text-3xl leading-tight font-semibold tracking-tight">{name}</h1>
      </header>

      {message && <Message text={message} onClose={() => setMessage(null)} />}
      {note && <Message tone="note" text={note} onClose={() => setNote(null)} />}

      <section aria-label="Workspace" className="overflow-hidden rounded-lg border border-line bg-surface">
        <div className="relative flex min-h-12 flex-wrap items-center gap-3 border-b border-line px-4 py-2">
          <span className="text-[13px] text-ink-2" aria-live="polite">
            {running ? `${status?.stage ?? "Starting"} (${share}%)` : dirty ? "Unsaved changes" : file ? "Saved" : "Opening"}
          </span>
          {(errors.length > 0 || warnings.length > 0) && (
            <button
              type="button"
              onClick={() => {
                const first = errors[0] ?? warnings[0];
                editor.current?.reveal(first.line, first.column);
              }}
              title={(errors[0] ?? warnings[0]).message}
              className={`cursor-pointer text-[13px] font-semibold hover:underline focus-visible:outline-2 focus-visible:outline-accent ${errors.length ? "text-neg" : "text-warn"}`}
            >
              {[errors.length ? `${errors.length} ${errors.length === 1 ? "error" : "errors"}` : "", warnings.length ? `${warnings.length} ${warnings.length === 1 ? "warning" : "warnings"}` : ""]
                .filter(Boolean)
                .join(", ")}
              {errors.length ? `, line ${errors[0].line}` : ""}
            </button>
          )}
          {!running && detail && detail.run_id === shown && !LIVE.includes(detail.status.state) && (
            <button
              type="button"
              onClick={() => results.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
              className={`max-w-[46ch] cursor-pointer truncate text-[13px] hover:underline focus-visible:outline-2 focus-visible:outline-accent ${detail.status.state === "complete" ? "text-ink-2" : "font-semibold text-neg"}`}
            >
              {detail.status.state === "complete" ? `Last run: ${detail.summary?.headline ?? "done"}` : `Last run ${STATE_LABEL[detail.status.state].toLowerCase()}: see why`}
            </button>
          )}
          <div className="flex-1" />
          {confirmDelete ? (
            <span className="flex items-center gap-2 text-[13px]">
              Delete {name}? Its runs are kept.
              <Button variant="danger" onClick={remove}>
                Delete
              </Button>
              <Button onClick={() => setConfirmDelete(false)}>Keep</Button>
            </span>
          ) : (
            <button type="button" onClick={() => setConfirmDelete(true)} className="cursor-pointer px-1 text-[13px] font-medium text-ink-3 hover:text-neg focus-visible:outline-2 focus-visible:outline-accent">
              Delete
            </button>
          )}
          <Button onClick={save} disabled={!dirty} title="Save (⌘S)">
            Save
          </Button>
          {running ? (
            <Button onClick={cancel} className="min-w-[84px]">
              Cancel
            </Button>
          ) : (
            <Button variant="primary" onClick={run} disabled={busy || !file} title="Run over every stock (⌘↵)" className="min-w-[84px]">
              Run
            </Button>
          )}
          {running && (
            <div aria-hidden="true" className="absolute inset-x-0 -bottom-px h-0.5 bg-raised">
              <div className="h-full bg-accent transition-[width] duration-500" style={{ width: `${Math.max(share, 2)}%` }} />
            </div>
          )}
        </div>
        <div className="grid lg:h-[min(64vh,680px)] lg:grid-cols-[minmax(0,1fr)_336px]">
          <div className="h-[460px] min-w-0 lg:h-full">
            {file ? (
              <CodeEditor ref={editor} value={code} onChange={setCode} onSave={save} onRun={run} fields={meta.fields} label={`${name}.py`} check={checkCode} onFindings={setFindings} />
            ) : (
              <p className="m-0 px-4 py-6 text-ink-2">Opening {name}…</p>
            )}
          </div>
          <aside aria-label="Settings and data" className="min-h-0 border-t border-line lg:border-t-0 lg:border-l">
            <Inspector
              meta={meta}
              base={base}
              draft={draft}
              onChange={setDraft}
              name={name}
              historyKey={historyKey}
              onRestore={(older, version) => {
                setCode(older);
                setNote(`Restored the version saved ${when(version.saved_at)}. Save to keep it; ⌘Z in the editor undoes the restore.`);
              }}
            />
          </aside>
        </div>
      </section>

      <div ref={results} className="scroll-mt-4" />
      {runs.length ? (
        <RunResults
          key={shown ?? "none"}
          detail={detail && detail.run_id === shown ? detail : null}
          runs={numbered}
          selected={shown}
          onSelect={(id) => onOpen(name, id)}
          onRestoreCode={setCode}
          onUseSettings={(found) => found.summary?.settings && setDraft(fromSettings(found.summary.settings, base))}
        />
      ) : (
        <p className="m-0 text-ink-2">Press Run to test {name} over every stock in the universe. ⌘↵ runs, ⌘S saves.</p>
      )}
    </div>
  );
}

function ModuleWorkspace({ module, meta, onOpen, onChanged }: { module: string; meta: Meta; onOpen: (name?: string, runId?: string) => void; onChanged: () => void }) {
  const [code, setCode] = useState<string | null>(null);
  const [saved, setSaved] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [historyKey, setHistoryKey] = useState(0);
  const editor = useRef<CodeEditorHandle>(null);
  const dirty = code != null && code !== saved;

  useEffect(() => {
    let live = true;
    lab
      .module(module)
      .then((found) => {
        if (!live) return;
        setCode(found.code);
        setSaved(found.code);
      })
      .catch((e: Error) => live && setMessage(e.message));
    return () => {
      live = false;
    };
  }, [module]);

  const pending = useRef({ code, dirty });
  pending.current = { code, dirty };
  useEffect(
    () => () => {
      if (pending.current.dirty && pending.current.code != null) lab.saveModule(module, pending.current.code).catch(() => undefined);
    },
    [module],
  );

  const save = useCallback(async () => {
    if (!dirty || code == null) return;
    try {
      await lab.saveModule(module, code);
      setSaved(code);
      setHistoryKey((k) => k + 1);
      onChanged();
    } catch (e) {
      setMessage((e as Error).message);
    }
  }, [module, code, dirty, onChanged]);

  const remove = async () => {
    try {
      await lab.removeModule(module);
      pending.current.dirty = false;
      onChanged();
      onOpen(undefined, undefined);
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  const checkCode = useCallback(
    (text: string) =>
      lab.check(text, true).then(
        (found) => found.findings,
        (e) => {
          if (e instanceof LabError && e.status === 404) return [];
          throw e;
        },
      ),
    [],
  );
  const errors = findings.filter((f) => f.severity === "error");

  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-col gap-2.5">
        <div className="text-sm text-ink-3">
          <button type="button" onClick={() => onOpen(undefined, undefined)} className="cursor-pointer text-accent hover:underline focus-visible:outline-2 focus-visible:outline-accent">
            Lab
          </button>{" "}
          / Library / {module}
        </div>
        <h1 className="m-0 text-3xl leading-tight font-semibold tracking-tight">lab.{module}</h1>
      </header>
      {message && <Message text={message} onClose={() => setMessage(null)} />}
      {note && <Message tone="note" text={note} onClose={() => setNote(null)} />}
      <section aria-label="Helper module" className="overflow-hidden rounded-lg border border-line bg-surface">
        <div className="flex min-h-12 flex-wrap items-center gap-3 border-b border-line px-4 py-2">
          <span className="text-[13px] text-ink-2">{dirty ? "Unsaved changes" : code == null ? "Opening" : "Saved"}</span>
          {errors.length > 0 && (
            <button type="button" onClick={() => editor.current?.reveal(errors[0].line, errors[0].column)} className="cursor-pointer text-[13px] font-semibold text-neg hover:underline">
              {errors.length} {errors.length === 1 ? "error" : "errors"}, line {errors[0].line}
            </button>
          )}
          <span className="text-[13px] text-ink-3">
            Import with <code className="font-mono text-ink-2">from lab.{module} import …</code>
          </span>
          <div className="flex-1" />
          {confirmDelete ? (
            <span className="flex items-center gap-2 text-[13px]">
              Delete lab.{module}? Algorithms that import it will stop with an error; past runs keep their copy.
              <Button variant="danger" onClick={remove}>
                Delete
              </Button>
              <Button onClick={() => setConfirmDelete(false)}>Keep</Button>
            </span>
          ) : (
            <button type="button" onClick={() => setConfirmDelete(true)} className="cursor-pointer px-1 text-[13px] font-medium text-ink-3 hover:text-neg focus-visible:outline-2 focus-visible:outline-accent">
              Delete
            </button>
          )}
          <Button variant="primary" onClick={save} disabled={!dirty} title="Save (⌘S)" className="min-w-[84px]">
            Save
          </Button>
        </div>
        <div className="grid lg:h-[min(64vh,680px)] lg:grid-cols-[minmax(0,1fr)_336px]">
          <div className="h-[460px] min-w-0 lg:h-full">
            {code != null ? (
              <CodeEditor ref={editor} value={code} onChange={setCode} onSave={save} fields={meta.fields} label={`lab/${module}.py`} check={checkCode} onFindings={setFindings} />
            ) : (
              <p className="m-0 px-4 py-6 text-ink-2">Opening {module}…</p>
            )}
          </div>
          <aside aria-label="History" className="flex min-h-0 flex-col border-t border-line lg:border-t-0 lg:border-l">
            <div className="flex h-11 shrink-0 items-end border-b border-line px-4">
              <span className="border-b-2 border-ink pb-2.5 text-[13px] font-semibold text-ink">History</span>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <History
                kind="library"
                name={module}
                refresh={historyKey}
                onRestore={(older, version) => {
                  setCode(older);
                  setNote(`Restored the version saved ${when(version.saved_at)}. Save to keep it; ⌘Z in the editor undoes the restore.`);
                }}
              />
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}

/** The Lab: the owner's algorithms, each run over every stock. */
export function Lab({ name, runId, onOpen }: LabProps) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [algorithms, setAlgorithms] = useState<AlgorithmRow[] | null>(null);
  const [modules, setModules] = useState<ModuleRow[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(() => {
    lab.algorithms().then(setAlgorithms).catch(() => undefined);
    lab.library().then(setModules).catch(() => setModules([]));
  }, []);

  useEffect(() => {
    Promise.all([lab.meta(), lab.templates(), lab.algorithms()])
      .then(([m, t, a]) => {
        setMeta(m);
        setTemplates(t);
        setAlgorithms(a);
      })
      .catch((e: Error) => setMessage(`${e.message} Restart the Workbench server after updating.`));
    lab.library().then(setModules).catch(() => setModules([])); // a server from before the library
  }, []);

  const create = async (newName: string, code: string) => {
    try {
      await lab.save(newName, code);
      refresh();
      onOpen(newName, undefined);
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  if (!meta || !algorithms) {
    return message ? <EmptyState title="The Lab is not available">{message}</EmptyState> : <p className="text-ink-2">Loading the Lab…</p>;
  }
  if (name === "library" && runId) return <ModuleWorkspace key={runId} module={runId} meta={meta} onOpen={onOpen} onChanged={refresh} />;
  if (name && name !== "library") return <Workspace key={name} name={name} runId={runId} meta={meta} onOpen={onOpen} onChanged={refresh} />;
  const createModule = async (module: string) => {
    try {
      await lab.saveModule(module, STARTER_MODULE);
      refresh();
      onOpen("library", module);
    } catch (e) {
      setMessage((e as Error).message);
    }
  };
  return (
    <>
      {message && <Message text={message} onClose={() => setMessage(null)} />}
      <LabIndex
        algorithms={algorithms}
        templates={templates}
        modules={modules}
        onOpen={(next) => onOpen(next, undefined)}
        onCreate={create}
        onOpenModule={(module) => onOpen("library", module)}
        onCreateModule={createModule}
      />
    </>
  );
}
