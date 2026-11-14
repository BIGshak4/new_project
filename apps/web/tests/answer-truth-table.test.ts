import { test } from "node:test";
import assert from "node:assert/strict";
import {
  addTruthColumn, createTruthTable, formatTruthTable, isAnswerTruthTable, MAX_TRUTH_INPUTS,
  MAX_TRUTH_NAME, MAX_TRUTH_OUTPUTS, parseTruthTable, removeTruthColumn, renameTruthColumn, setTruthOutput,
  type AnswerTruthTable,
} from "../src/lib/answer-truth-table";

test("canonical table round-trips RTL, a transient empty name, whitespace, and separate blank and don't-care outputs", () => {
  const table: AnswerTruthTable = {
    inputs: ["", "כניסה 2"], outputs: [" תוצאה ", "Y`"], rows: [["", "X"], ["1", "0"], ["X", ""], ["0", "1"]],
  };
  const text = formatTruthTable(table);
  assert.deepEqual(parseTruthTable(text), table);
  assert.deepEqual(parseTruthTable(text.replaceAll("\n", "\r\n")), table);
  assert.match(text, /00\t-\tX/);
  assert.equal(isAnswerTruthTable(table), true);
});

test("partial, duplicate, out-of-order and malformed input combinations are not consumed", () => {
  const text = formatTruthTable(createTruthTable());
  for (const bad of [
    text.slice(0, -1), text.replace("00", "01"), text.replace("01", "11"), text.replace("00\t-", "00\t?"),
    text.replace("outputs\tY", "outputs\tY\tZ"), text.replace("inputs\tA", "input\tA"),
    text + "\n", text.replace("outputs\tY", "outputs\t" + "A".repeat(MAX_TRUTH_NAME + 1)),
    text.replace("outputs\tY", "outputs\tA\u2028bad"),
  ]) assert.equal(parseTruthTable(bad), undefined);
});

test("adding an input keeps existing values on their original assignments and introduces unanswered combinations", () => {
  const table = setTruthOutput(setTruthOutput(createTruthTable(), 1, 0, "1"), 3, 0, "X");
  const extended = addTruthColumn(table, "inputs");
  assert.deepEqual(extended.inputs, ["A", "B", "C"]);
  assert.deepEqual(extended.rows, [[""], [""], ["1"], [""], [""], [""], ["X"], [""]]);
  assert.deepEqual(removeTruthColumn(extended, "inputs", 2), table);
});

test("removing the first or middle input merges correct binary pairs independently for each output", () => {
  const table: AnswerTruthTable = {
    inputs: ["A", "B", "C"], outputs: ["Y", "Z"],
    rows: [["0","1"],["1","X"],["0",""],["0","X"],["1","1"],["",""],["1","1"],["0",""]],
  };
  assert.deepEqual(removeTruthColumn(table, "inputs", 0).rows, [["","1"],["1","X"],["","1"],["0","X"]]);
  assert.deepEqual(removeTruthColumn(table, "inputs", 1).rows, [["0","1"],["","X"],["1","1"],["0",""]]);
  const moreOutputs = addTruthColumn(table, "outputs");
  assert.deepEqual(removeTruthColumn(moreOutputs, "outputs", 2), table);
  assert.deepEqual(removeTruthColumn(table, "outputs", 0).rows[1], ["X"]);
});

test("limits bound every supported table and preserve field names without splitting columns or rows", () => {
  let table = createTruthTable();
  for (let i = 0; i < 10; i++) {
    table = addTruthColumn(addTruthColumn(table, "inputs"), "outputs");
  }
  assert.equal(table.inputs.length, MAX_TRUTH_INPUTS);
  assert.equal(table.outputs.length, MAX_TRUTH_OUTPUTS);
  assert.equal(table.rows.length, 64);
  assert.equal(isAnswerTruthTable(table), true);
  for (let i = 0; i < table.inputs.length; i++) table = renameTruthColumn(table, "inputs", i, "ק".repeat(MAX_TRUTH_NAME));
  for (let i = 0; i < table.outputs.length; i++) table = renameTruthColumn(table, "outputs", i, "י".repeat(MAX_TRUTH_NAME));
  assert.deepEqual(parseTruthTable(formatTruthTable(table)), table);
  assert.equal(renameTruthColumn(table, "inputs", 0, "A\tC"), table);
  assert.equal(renameTruthColumn(table, "inputs", 0, "A\nC"), table);
  assert.equal(renameTruthColumn(table, "inputs", 0, "י".repeat(MAX_TRUTH_NAME + 1)), table);
  const minimum = removeTruthColumn(createTruthTable(), "inputs", 0);
  assert.equal(removeTruthColumn(minimum, "inputs", 0), minimum);
  assert.equal(removeTruthColumn(minimum, "outputs", 0), minimum);
});
