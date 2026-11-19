export type TruthCell = "" | "0" | "1" | "X";
export type AnswerTruthTable = {
  inputs: string[];
  outputs: string[];
  /** Output cells in binary input order, with the first input as the high bit. */
  rows: TruthCell[][];
};

export const MAX_TRUTH_INPUTS = 6;
export const MAX_TRUTH_OUTPUTS = 8;
export const MAX_TRUTH_NAME = 32;

export function createTruthTable(): AnswerTruthTable {
  return { inputs: ["A", "B"], outputs: ["Y"], rows: [[""], [""], [""], [""]] };
}

export function inputBits(row: number, inputs: number): string {
  return row.toString(2).padStart(inputs, "0");
}

const isCell = (value: unknown): value is TruthCell =>
  value === "" || value === "0" || value === "1" || value === "X";

const isName = (name: unknown): name is string =>
  typeof name === "string" && name.length <= MAX_TRUTH_NAME && !/[\u0000-\u001f\u007f\u0085\u2028\u2029]/u.test(name);

const isColumnList = (value: unknown, max: number): value is string[] =>
  Array.isArray(value) && value.length >= 1 && value.length <= max && value.every(isName);

export function isAnswerTruthTable(value: unknown): value is AnswerTruthTable {
  if (!value || typeof value !== "object") return false;
  const { inputs, outputs, rows } = value as Record<string, unknown>;
  return isColumnList(inputs, MAX_TRUTH_INPUTS)
    && isColumnList(outputs, MAX_TRUTH_OUTPUTS)
    && Array.isArray(rows)
    && rows.length === 2 ** inputs.length
    && rows.every(row => Array.isArray(row) && row.length === outputs.length && row.every(isCell));
}

/** Readable by both learners and model graders, including in clients without a table viewer. */
export function formatTruthTable(table: AnswerTruthTable): string {
  return [
    ["inputs", ...table.inputs].join("\t"),
    ["outputs", ...table.outputs].join("\t"),
    ...table.rows.map((cells, row) =>
      [inputBits(row, table.inputs.length), ...cells.map(cell => cell || "-")].join("\t")
    ),
  ].join("\n");
}

export function parseTruthTable(text: string): AnswerTruthTable | undefined {
  if (text.length > 4096) return undefined;
  const [inputLine, outputLine, ...lines] = text.split(/\r?\n/);
  if (!inputLine?.startsWith("inputs\t") || !outputLine?.startsWith("outputs\t")) return undefined;
  const inputs = inputLine.split("\t").slice(1);
  const outputs = outputLine.split("\t").slice(1);
  if (!isColumnList(inputs, MAX_TRUTH_INPUTS) || !isColumnList(outputs, MAX_TRUTH_OUTPUTS) || lines.length !== 2 ** inputs.length) return undefined;
  const rows: TruthCell[][] = [];
  for (const line of lines) {
    const [bits, ...values] = line.split("\t");
    if (bits !== inputBits(rows.length, inputs.length) || values.length !== outputs.length) return undefined;
    const row: TruthCell[] = [];
    for (const value of values) {
      if (value === "-") row.push("");
      else if (value === "0" || value === "1" || value === "X") row.push(value);
      else return undefined;
    }
    rows.push(row);
  }
  return { inputs, outputs, rows };
}

type Columns = "inputs" | "outputs";

function uniqueColumnName(table: AnswerTruthTable, columns: Columns): string {
  const taken = new Set([...table.inputs, ...table.outputs]);
  const preferred = columns === "inputs" ? "ABCDEF" : "YZ";
  for (const name of preferred) if (!taken.has(name)) return name;
  const prefix = columns === "inputs" ? "I" : "Y";
  for (let index = 1; ; index++) {
    const name = prefix + index;
    if (!taken.has(name)) return name;
  }
}

export function addTruthColumn(table: AnswerTruthTable, columns: Columns): AnswerTruthTable {
  if (table[columns].length >= (columns === "inputs" ? MAX_TRUTH_INPUTS : MAX_TRUTH_OUTPUTS)) return table;
  const names = [...table[columns], uniqueColumnName(table, columns)];
  if (columns === "outputs") return { ...table, outputs: names, rows: table.rows.map(row => [...row, ""]) };
  // Old assignments now have a trailing zero. New combinations start unanswered.
  const rows = table.rows.flatMap(row => [row, table.outputs.map((): TruthCell => "")]);
  return { ...table, inputs: names, rows };
}

export function renameTruthColumn(table: AnswerTruthTable, columns: Columns, index: number, name: string): AnswerTruthTable {
  if (!isName(name) || !Number.isInteger(index) || index < 0 || index >= table[columns].length) return table;
  return { ...table, [columns]: table[columns].map((previous, i) => i === index ? name : previous) };
}

export function removeTruthColumn(table: AnswerTruthTable, columns: Columns, index: number): AnswerTruthTable {
  if (table[columns].length <= 1 || !Number.isInteger(index) || index < 0 || index >= table[columns].length) return table;
  const names = table[columns].filter((_, i) => i !== index);
  if (columns === "outputs") {
    return { ...table, outputs: names, rows: table.rows.map(row => row.filter((_, i) => i !== index)) };
  }
  // Each pair differs only at the removed input. Keep known values; conflicting
  // answers must be re-entered for the resulting shorter input combination.
  const rows = Array.from({ length: 2 ** names.length }, (_, row) => {
    const bits = inputBits(row, names.length);
    const before = bits.slice(0, index), after = bits.slice(index);
    const low = table.rows[parseInt(before + "0" + after, 2)];
    const high = table.rows[parseInt(before + "1" + after, 2)];
    return low.map((a, col) => {
      const b = high[col];
      return a && b && a !== b ? "" : a || b;
    });
  });
  return { ...table, inputs: names, rows };
}

export function setTruthOutput(table: AnswerTruthTable, row: number, column: number, value: TruthCell): AnswerTruthTable {
  if (!Number.isInteger(row) || !Number.isInteger(column) || !isCell(value) || table.rows[row]?.[column] === undefined) return table;
  return {
    ...table,
    rows: table.rows.map((cells, i) =>
      row === i ? cells.map((cell, j) => j === column ? value : cell) : cells
    ),
  };
}
