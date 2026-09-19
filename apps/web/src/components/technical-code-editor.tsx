"use client";

import { useEffect, useRef } from "react";
import { basicSetup } from "codemirror";
import { Compartment, EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import { indentWithTab } from "@codemirror/commands";
import { StreamLanguage } from "@codemirror/language";
import { cpp } from "@codemirror/lang-cpp";
import { python } from "@codemirror/lang-python";
import { javascript } from "@codemirror/lang-javascript";
import { verilog } from "@codemirror/legacy-modes/mode/verilog";
import { vhdl } from "@codemirror/legacy-modes/mode/vhdl";
import type { AnswerLanguage } from "../lib/technical-answer";

function syntax(language: AnswerLanguage) {
  if (language === "c" || language === "cpp") return cpp();
  if (language === "python") return python();
  if (language === "javascript") return javascript();
  if (language === "verilog" || language === "systemverilog")
    return StreamLanguage.define(verilog);
  if (language === "vhdl") return StreamLanguage.define(vhdl);
  return [];
}

type Props = {
  value: string;
  language: AnswerLanguage;
  disabled: boolean;
  label: string;
  onChange: (value: string) => void;
};
export default function TechnicalCodeEditor(props: Props) {
  const host = useRef<HTMLDivElement>(null),
    view = useRef<EditorView | null>(null);
  const current = useRef(props);
  current.current = props;
  const compartments = useRef({
    language: new Compartment(),
    access: new Compartment(),
    label: new Compartment(),
  });
  useEffect(() => {
    if (!host.current) return;
    const c = compartments.current;
    const editor = new EditorView({
      parent: host.current,
      state: EditorState.create({
        doc: current.current.value,
        extensions: [
          basicSetup,
          keymap.of([indentWithTab]),
          c.language.of(syntax(current.current.language)),
          c.access.of([
            EditorState.readOnly.of(current.current.disabled),
            EditorView.editable.of(!current.current.disabled),
          ]),
          c.label.of(
            EditorView.contentAttributes.of({
              "aria-label": current.current.label,
              "aria-describedby": "code-keyboard-help",
              spellcheck: "false",
              dir: "ltr",
            }),
          ),
          EditorView.updateListener.of((update) => {
            if (update.docChanged)
              current.current.onChange(update.state.doc.toString());
          }),
          EditorView.theme({
            "&": {
              fontSize: "14px",
              backgroundColor: "#fbfcf8",
              color: "#172c27",
            },
            ".cm-content": {
              minHeight: "260px",
              fontFamily: "Consolas, 'Courier New', monospace",
              caretColor: "#225d48",
            },
            ".cm-scroller": { overflow: "auto", maxHeight: "540px" },
            ".cm-gutters": {
              backgroundColor: "#f0f3ec",
              color: "#626c61",
              border: "none",
            },
            "&.cm-focused": {
              outline: "2px solid #225d48",
              outlineOffset: "2px",
            },
          }),
        ],
      }),
    });
    view.current = editor;
    return () => {
      editor.destroy();
      view.current = null;
    };
  }, []);
  useEffect(() => {
    const editor = view.current;
    if (editor && props.value !== editor.state.doc.toString())
      editor.dispatch({
        changes: { from: 0, to: editor.state.doc.length, insert: props.value },
      });
  }, [props.value]);
  useEffect(() => {
    view.current?.dispatch({
      effects: compartments.current.language.reconfigure(
        syntax(props.language),
      ),
    });
  }, [props.language]);
  useEffect(() => {
    view.current?.dispatch({
      effects: compartments.current.access.reconfigure([
        EditorState.readOnly.of(props.disabled),
        EditorView.editable.of(!props.disabled),
      ]),
    });
  }, [props.disabled]);
  useEffect(() => {
    view.current?.dispatch({
      effects: compartments.current.label.reconfigure(
        EditorView.contentAttributes.of({
          "aria-label": props.label,
          "aria-describedby": "code-keyboard-help",
          spellcheck: "false",
          dir: "ltr",
        }),
      ),
    });
  }, [props.label]);
  return <div className="technical-code-editor" dir="ltr" ref={host} />;
}
