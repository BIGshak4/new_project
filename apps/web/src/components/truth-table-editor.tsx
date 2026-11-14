"use client";

import { Plus, Trash2 } from "lucide-react";
import {
  addTruthColumn, createTruthTable, inputBits, MAX_TRUTH_INPUTS, MAX_TRUTH_NAME,
  MAX_TRUTH_OUTPUTS, removeTruthColumn, renameTruthColumn, setTruthOutput,
  type AnswerTruthTable, type TruthCell,
} from "../lib/answer-truth-table";
import type { Lang } from "./auth";
import styles from "./truth-table-editor.module.css";

type TableProps = { value: AnswerTruthTable; lang: Lang };
type Columns = "inputs" | "outputs";

function columnLabel(columns: Columns, index: number, lang: Lang) {
  const label = columns === "inputs"
    ? (lang === "he" ? "קלט" : "Input")
    : (lang === "he" ? "פלט" : "Output");
  return `${label} ${index + 1}`;
}

function TruthTableGrid({ value, lang, onCellChange, disabled }: TableProps & {
  disabled?: boolean;
  onCellChange?: (row: number, column: number, next: TruthCell) => void;
}) {
  const he = lang === "he";
  const title = he ? "טבלת אמת" : "Truth table";
  return (
    <div className={styles.scroll} role="region" tabIndex={0} aria-label={title}>
      <table className={styles.table} dir="ltr" aria-label={title}>
        <colgroup span={value.inputs.length} />
        <colgroup span={value.outputs.length} />
        <thead>
          <tr>
            <th colSpan={value.inputs.length} scope="colgroup">{he ? "קלטים" : "Inputs"}</th>
            <th className={styles.outputs} colSpan={value.outputs.length} scope="colgroup">{he ? "פלטים" : "Outputs"}</th>
          </tr>
          <tr>
            {(["inputs", "outputs"] as const).map(columns => value[columns].map((name, i) => (
              <th className={columns === "outputs" && !i ? styles.divider : undefined} key={columns + i} scope="col">
                <bdi>{name || columnLabel(columns, i, lang)}</bdi>
              </th>
            )))}
          </tr>
        </thead>
        <tbody>
          {value.rows.map((cells, row) => {
            const bits = inputBits(row, value.inputs.length);
            return (
              <tr key={bits}>
                {bits.split("").map((bit, column) => <td key={column}>{bit}</td>)}
                {cells.map((cell, column) => (
                  <td className={column === 0 ? styles.divider : undefined} key={column}>
                    {onCellChange
                      ? <select
                          dir="ltr" disabled={disabled} value={cell}
                          aria-label={`${value.outputs[column] || columnLabel("outputs", column, lang)} · ${he ? "צירוף קלט" : "input combination"} ${bits}`}
                          onChange={event => onCellChange(row, column, event.target.value as TruthCell)}
                        >
                          <option value="" aria-label={he ? "ריק" : "Blank"}>–</option>
                          <option value="0">0</option>
                          <option value="1">1</option>
                          <option value="X">X</option>
                        </select>
                      : <strong>{cell || "–"}</strong>}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function TruthTableView({ value, lang }: TableProps) {
  return <TruthTableGrid value={value} lang={lang} />;
}

export function TruthTableEditor({ value, onChange, lang, disabled }: {
  value: AnswerTruthTable | undefined;
  onChange: (table: AnswerTruthTable | undefined) => void;
  lang: Lang;
  disabled: boolean;
}) {
  const he = lang === "he";
  const table = value ?? createTruthTable();
  const hasOutputs = table.rows.some(row => row.some(Boolean));
  function removeColumn(columns: Columns, index: number) {
    const hasAffectedValues = columns === "inputs" ? hasOutputs : table.rows.some(row => row[index]);
    if (hasAffectedValues) {
      const message = columns === "inputs"
        ? (he ? "להסיר את הקלט ולאחד את השורות? ערכי פלט שמתנגשים יתרוקנו." : "Remove this input and merge its rows? Conflicting outputs will be cleared.")
        : (he ? "להסיר את עמודת הפלט ואת הערכים שמילאתם בה?" : "Remove this output column and its values?");
      if (!window.confirm(message)) return;
    }
    onChange(removeTruthColumn(table, columns, index));
  }

  return (
    <section className={styles.editor} data-muxi-control="answer-truth-table" aria-label={he ? "עריכת טבלת אמת" : "Truth table editor"}>
      <p className={styles.hint}>
        {he
          ? <>לכל צירוף קלטים בחרו פלט. סמנו <bdi dir="ltr">X</bdi> אם שני ערכי הפלט מתאימים.</>
          : "Choose an output for each input combination. Use X when either output value is acceptable."}
      </p>
      <div className={styles.actions}>
        <button type="button" disabled={disabled || table.inputs.length >= MAX_TRUTH_INPUTS} onClick={() => onChange(addTruthColumn(table, "inputs"))}>
          <Plus size={16} aria-hidden="true" />{he ? "הוספת קלט" : "Add input"}
        </button>
        <button type="button" disabled={disabled || table.outputs.length >= MAX_TRUTH_OUTPUTS} onClick={() => onChange(addTruthColumn(table, "outputs"))}>
          <Plus size={16} aria-hidden="true" />{he ? "הוספת פלט" : "Add output"}
        </button>
      </div>
      {(table.inputs.length === MAX_TRUTH_INPUTS || table.outputs.length === MAX_TRUTH_OUTPUTS) &&
        <p className={styles.hint} role="status">
          {he ? `אפשר להוסיף עד ${MAX_TRUTH_INPUTS} קלטים ועד ${MAX_TRUTH_OUTPUTS} פלטים.` : `A table supports up to ${MAX_TRUTH_INPUTS} inputs and ${MAX_TRUTH_OUTPUTS} outputs.`}
        </p>}
      <TruthTableGrid value={table} lang={lang} disabled={disabled} onCellChange={(row, col, next) => onChange(setTruthOutput(table, row, col, next))} />
      <details className={styles.settings}>
        <summary>{he ? "שינוי שמות והסרת עמודות" : "Rename or remove columns"}</summary>
        <div className={styles.groups}>
          {(["inputs", "outputs"] as const).map(columns => (
            <fieldset key={columns} disabled={disabled}>
              <legend>{columns === "inputs" ? (he ? "קלטים" : "Inputs") : (he ? "פלטים" : "Outputs")}</legend>
              {table[columns].map((name, index) => {
                const label = columnLabel(columns, index, lang);
                return (
                  <div className={styles.column} key={index}>
                    <label>
                      <span>{label}</span>
                      <input dir="auto" value={name} maxLength={MAX_TRUTH_NAME} placeholder={label}
                        onChange={event => onChange(renameTruthColumn(table, columns, index, event.target.value))} />
                    </label>
                    <button type="button" disabled={disabled || table[columns].length === 1}
                      aria-label={he ? `הסרת ${label}` : `Remove ${label}`} onClick={() => removeColumn(columns, index)}>
                      <Trash2 size={16} aria-hidden="true" />
                    </button>
                  </div>
                );
              })}
            </fieldset>
          ))}
        </div>
        {value && <button className={styles.remove} type="button" disabled={disabled} onClick={() => {
          if (window.confirm(he ? "להסיר את כל טבלת האמת מהתשובה?" : "Remove this entire truth table from your answer?")) onChange(undefined);
        }}><Trash2 size={16} aria-hidden="true" />{he ? "הסרת הטבלה מהתשובה" : "Remove table from answer"}</button>}
      </details>
    </section>
  );
}
