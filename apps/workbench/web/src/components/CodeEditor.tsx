import { autocompletion, type CompletionContext, type CompletionResult } from "@codemirror/autocomplete";
import { indentWithTab } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import { HighlightStyle, indentUnit, syntaxHighlighting } from "@codemirror/language";
import { Compartment, EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { tags } from "@lezer/highlight";
import { basicSetup } from "codemirror";
import { forwardRef, useEffect, useImperativeHandle, useRef } from "react";
import type { Field } from "../lib/lab";

export interface CodeEditorHandle {
  /** Put text at the cursor and focus the editor. */
  insert: (text: string) => void;
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
}

// Colours come from the design tokens, so the editor follows the light and dark themes.
const theme = EditorView.theme({
  "&": { backgroundColor: "var(--surface)", color: "var(--ink)", fontSize: "13.5px" },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": { fontFamily: '"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace', lineHeight: "1.55" },
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

/** The Python editor of the Lab (CodeMirror 6). Cmd/Ctrl+S saves, Cmd/Ctrl+Enter runs. */
export const CodeEditor = forwardRef<CodeEditorHandle, CodeEditorProps>(function CodeEditor(
  { value, onChange, onSave, onRun, fields = [], readOnly = false, label, minHeight = 420 },
  ref,
) {
  const host = useRef<HTMLDivElement>(null);
  const view = useRef<EditorView | null>(null);
  const handlers = useRef({ onChange, onSave, onRun });
  handlers.current = { onChange, onSave, onRun };
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
          "&": { maxHeight: "72vh" },
          ".cm-scroller": { overflow: "auto" },
          ".cm-content, .cm-gutter": { minHeight: `${minHeight}px` },
        }),
        syntaxHighlighting(highlight),
        completions.current.of(autocompletion({ override: [fieldCompletions(fields)] })),
        editable.current.of([EditorState.readOnly.of(readOnly), EditorView.editable.of(!readOnly)]),
        EditorView.contentAttributes.of({ "aria-label": label }),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) handlers.current.onChange?.(update.state.doc.toString());
        }),
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
      if (!current) return;
      const { from, to } = current.state.selection.main;
      current.dispatch({ changes: { from, to, insert: text }, selection: { anchor: from + text.length } });
      current.focus();
    },
    focus: () => view.current?.focus(),
  }));

  return <div ref={host} className="overflow-hidden" />;
});
