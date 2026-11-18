import { autocompletion, type CompletionContext, type CompletionResult } from "@codemirror/autocomplete";
import { indentWithTab } from "@codemirror/commands";
import { type Diagnostic, lintGutter, linter } from "@codemirror/lint";
import { python } from "@codemirror/lang-python";
import { HighlightStyle, indentUnit, syntaxHighlighting } from "@codemirror/language";
import { Compartment, EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { tags } from "@lezer/highlight";
import { basicSetup } from "codemirror";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type { Field, Finding } from "../lib/lab";

export interface CodeEditorHandle {
  /** Put text at the cursor and focus the editor. False, and nothing changes, when the owner
   *  has not put a cursor in the editor yet: text is never dropped at an unseen place. */
  insert: (text: string) => boolean;
  /** Put the cursor on a line (1-based) and column (0-based) and show it. */
  reveal: (line: number, column?: number) => void;
  focus: () => void;
}

interface CodeEditorProps {
  value: string;
  onChange?: (value: string) => void;
  onSave?: () => void;
  onRun?: () => void;
  fields?: Field[];
  readOnly?: boolean;
  label: string;
  minHeight?: number;
  /** Checks the code (the page asks the server, which reads it without running it). */
  check?: (code: string) => Promise<Finding[]>;
  /** What the last check found. */
  onFindings?: (findings: Finding[]) => void;
}

// Colours come from the design tokens, so the editor follows the light and dark themes.
const theme = EditorView.theme({
  "&": { backgroundColor: "var(--surface)", color: "var(--ink)", fontSize: "13.5px" },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": { fontFamily: "var(--code-font)", lineHeight: "1.6" },
  ".cm-content": { caretColor: "var(--ink)", padding: "10px 0" },
  ".cm-gutters": { backgroundColor: "var(--surface)", color: "var(--ink-3)", border: "none", borderRight: "1px solid var(--line-soft)" },
  ".cm-activeLine": { backgroundColor: "color-mix(in srgb, var(--raised) 60%, transparent)" },
  ".cm-activeLineGutter": { backgroundColor: "var(--raised)", color: "var(--ink-2)" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection": { backgroundColor: "color-mix(in srgb, var(--accent) 22%, transparent) !important" },
  ".cm-cursor": { borderLeftColor: "var(--ink)" },
  ".cm-matchingBracket": { backgroundColor: "color-mix(in srgb, var(--accent) 18%, transparent)", outline: "none" },
  ".cm-tooltip": { backgroundColor: "var(--raised)", border: "1px solid var(--line)", color: "var(--ink)" },
  ".cm-tooltip-autocomplete ul li[aria-selected]": { backgroundColor: "var(--accent)", color: "var(--on-accent)" },
  ".cm-completionDetail": { color: "var(--ink-3)", fontStyle: "normal", marginLeft: "0.8em" },
  ".cm-panels": { backgroundColor: "var(--raised)", color: "var(--ink)" },
  ".cm-searchMatch": { backgroundColor: "color-mix(in srgb, var(--warn) 25%, transparent)" },
  ".cm-foldPlaceholder": { backgroundColor: "var(--raised)", border: "1px solid var(--line)", color: "var(--ink-2)" },
  // Problems: a plain label in front of the message, not a coloured stripe.
  ".cm-diagnostic": { borderLeft: "none", padding: "6px 10px", maxWidth: "520px", fontFamily: "var(--font-sans)", fontSize: "13px" },
  ".cm-diagnostic-error::before": { content: '"Error  "', color: "var(--neg)", fontWeight: "600" },
  ".cm-diagnostic-warning::before": { content: '"Warning  "', color: "var(--warn)", fontWeight: "600" },
  ".cm-lintRange-error": { backgroundImage: "none", textDecoration: "underline wavy var(--neg)", textUnderlineOffset: "3px" },
  ".cm-lintRange-warning": { backgroundImage: "none", textDecoration: "underline wavy var(--warn)", textUnderlineOffset: "3px" },
  ".cm-gutter-lint": { width: "14px" },
});

const highlight = HighlightStyle.define([
  { tag: [tags.keyword, tags.controlKeyword, tags.operatorKeyword, tags.definitionKeyword, tags.moduleKeyword], color: "var(--series-1)", fontWeight: "600" },
  { tag: [tags.string, tags.special(tags.string)], color: "var(--pos)" },
  { tag: [tags.number, tags.bool, tags.null], color: "var(--warn)" },
  { tag: [tags.comment, tags.lineComment, tags.blockComment], color: "var(--ink-3)", fontStyle: "italic" },
  { tag: [tags.function(tags.definition(tags.variableName)), tags.definition(tags.className)], color: "var(--ink)", fontWeight: "700" },
  { tag: [tags.propertyName], color: "var(--ink-2)" },
  { tag: [tags.operator, tags.punctuation, tags.bracket], color: "var(--ink-2)" },
  { tag: tags.invalid, color: "var(--neg)" },
]);

/** Completes the Lab's fields after `data.`. */
function fieldCompletions(fields: Field[]) {
  return (context: CompletionContext): CompletionResult | null => {
    const word = context.matchBefore(/data\.\w*/);
    if (!word || (word.from === word.to && !context.explicit)) return null;
    return {
      from: word.from + 5,
      options: fields.map((f) => ({ label: f.name, type: "property", detail: f.known, info: f.description })),
      validFor: /^\w*$/,
    };
  };
}

function toDiagnostics(view: EditorView, findings: Finding[]): Diagnostic[] {
  const doc = view.state.doc;
  const at = (line: number, column: number) => {
    const row = doc.line(Math.min(Math.max(line, 1), doc.lines));
    return Math.min(row.from + Math.max(column, 0), row.to);
  };
  return findings.map((f) => {
    const from = at(f.line, f.column);
    const to = Math.max(at(f.end_line, f.end_column), from);
    return { from, to: to === from ? Math.min(from + 1, doc.length) : to, severity: f.severity, message: f.message };
  });
}

/** The Python editor of the Lab (CodeMirror 6). Cmd/Ctrl+S saves, Cmd/Ctrl+Enter runs. */
export const CodeEditor = forwardRef<CodeEditorHandle, CodeEditorProps>(function CodeEditor(
  { value, onChange, onSave, onRun, fields = [], readOnly = false, label, minHeight = 200, check, onFindings },
  ref,
) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const touched = useRef(false);
  const handlers = useRef({ onChange, onSave, onRun, check, onFindings });
  handlers.current = { onChange, onSave, onRun, check, onFindings };
  const completions = useRef(new Compartment());
  const editable = useRef(new Compartment());

  useEffect(() => {
    if (!host.current) return;
    const state = EditorState.create({
      doc: value,
      extensions: [
        basicSetup,
        python(),
        indentUnit.of("    "),
        EditorState.tabSize.of(4),
        keymap.of([
          { key: "Mod-s", preventDefault: true, run: () => (handlers.current.onSave?.(), true) },
          { key: "Mod-Enter", preventDefault: true, run: () => (handlers.current.onRun?.(), true) },
          indentWithTab,
        ]),
        theme,
        EditorView.theme({
          "&": { height: "100%" },
          ".cm-scroller": { overflow: "auto" },
          ".cm-content, .cm-gutter": { minHeight: `${minHeight}px` },
        }),
        syntaxHighlighting(highlight),
        completions.current.of(autocompletion({ override: [fieldCompletions(fields)] })),
        editable.current.of([EditorState.readOnly.of(readOnly), EditorView.editable.of(!readOnly)]),
        EditorView.contentAttributes.of({ "aria-label": label }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) handlers.current.onChange?.(update.state.doc.toString());
          if (update.focusChanged && update.view.hasFocus) touched.current = true;
        }),
        ...(readOnly
          ? []
          : [
              lintGutter(),
              linter(
                async (current) => {
                  const run = handlers.current.check;
                  if (!run) return [];
                  try {
                    const findings = await run(current.state.doc.toString());
                    handlers.current.onFindings?.(findings);
                    return toDiagnostics(current, findings);
                  } catch {
                    return []; // the check is a help, never a gate on typing
                  }
                },
                { delay: 400 },
              ),
            ]),
      ],
    });
    view.current = new EditorView({ state, parent: host.current });
    return () => {
      view.current?.destroy();
      view.current = null;
    };
    // The editor is made once; later props reach it through the effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // A new document from outside (another algorithm, a restored run): replace the text.
  useEffect(() => {
    const current = view.current;
    if (current && current.state.doc.toString() !== value) {
      current.dispatch({ changes: { from: 0, to: current.state.doc.length, insert: value } });
    }
  }, [value]);

  useEffect(() => {
    view.current?.dispatch({ effects: completions.current.reconfigure(autocompletion({ override: [fieldCompletions(fields)] })) });
  }, [fields]);

  useEffect(() => {
    view.current?.dispatch({ effects: editable.current.reconfigure([EditorState.readOnly.of(readOnly), EditorView.editable.of(!readOnly)]) });
  }, [readOnly]);

  useImperativeHandle(ref, () => ({
    insert: (text: string) => {
      const current = view.current;
      if (!current || !touched.current) return false;
      const { from, to } = current.state.selection.main;
      current.dispatch({ changes: { from, to, insert: text }, selection: { anchor: from + text.length }, scrollIntoView: true });
      current.focus();
      return true;
    },
    reveal: (line: number, column = 0) => {
      const current = view.current;
      if (!current) return;
      const doc = current.state.doc;
      const row = doc.line(Math.min(Math.max(line, 1), doc.lines));
      const anchor = Math.min(row.from + column, row.to);
      current.dispatch({ selection: { anchor }, effects: EditorView.scrollIntoView(anchor, { y: "center" }) });
      current.focus();
    },
    focus: () => view.current?.focus(),
  }));

  return <div ref={host} className="h-full min-h-0 overflow-hidden" />;
});
