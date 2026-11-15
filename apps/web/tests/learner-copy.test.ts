import assert from "node:assert/strict";
import test from "node:test";
import { learnerCopy } from "../src/lib/learner-copy";

test("a provenance aside never removes the circuit task sharing its paragraph", () => {
  const en = "A. Implement a half adder using logic gates. B. Implement a full adder using HAs only. The source’s “2” enumerates its second part; it is not a two-gate budget. Part A allows XOR and AND primitives. The original four-bit construction is retained.";
  const he = "א. ממשו Half Adder בעזרת שערים לוגיים. ב. ממשו Full Adder באמצעות HA בלבד. „2” שבצילום הוא מספור הסעיף השני, לא מגבלה לשני שערים. בחלק א נבחר XOR ו־AND כשערים בסיסיים מותרים.";
  assert.equal(learnerCopy(en), "A. Implement a half adder using logic gates. B. Implement a full adder using HAs only. There is no two-gate limit. Part A allows XOR and AND primitives.");
  assert.equal(learnerCopy(he), "א. ממשו מחבר למחצה (HA) בעזרת שערים לוגיים. ב. ממשו מחבר מלא (FA) באמצעות מחברים למחצה בלבד. אין מגבלה של שני שערים. בסעיף א מותר להשתמש בשערי XOR ו־AND.");
  assert.equal(learnerCopy("הבהרה שנבחרה: A,B אינם מסומנים, אין carry-in חיצוני."), "הנחה: A ו־B הם מספרים ללא סימן, אין carry-in חיצוני.");
});

test("necessary diagram reading and signal names survive archive cleanup", () => {
  const en = "The attached clean diagram defines their order; the source screenshot remains in the archive. Read D0=Q3, D1=Q2.";
  assert.equal(learnerCopy(en), "Use the diagram to determine their order. Read D0=Q3, D1=Q2.");
  assert.equal(learnerCopy("התרשים המצורף מגדיר את סדר הגלאים; צילום המקור נשמר בארכיון."), "התרשים מגדיר את סדר הגלאים.");
});

test("source terminals, program text, original buffers, photographs and screenshots as input retain their meanings", () => {
  for (const technical of [
    "The source supplies a new byte every 5X seconds. Copy the original source frame.",
    "A MOSFET connects its source to ground. Find the voltage at the source.",
    "When the photo is taken, two members of the family are missing.",
    "מהצילום של המצלמה קראו את מיקום העצם. העתיקו מהמקור אל מערך הפלט.",
    "שחזרו את מצב התוכנה בעזרת צילום מצב. המקור מנותק, והקבל מחובר לסליל.",
  ]) assert.equal(learnerCopy(technical), technical);
});

test("archival Markdown links disappear without affecting actual technical reference links or neighboring facts", () => {
  const image = "![צילום וריאציית מאה האנשים](../sources/prep-012-hundred-people-2026-09-28.png)";
  const table = "[Supplied explanatory table screenshot](../sources/prep-015-driver-table.png).";
  assert.equal(learnerCopy(image), "");
  assert.equal(learnerCopy("Use row 4. "+table), "Use row 4.");
  assert.equal(learnerCopy("[Variant verification](../checks/run.py) checked 350 output periods."), "Variant verification checked 350 output periods.");
  assert.equal(learnerCopy("[MIT circuit diagram](https://ocw.mit.edu/resources/diagram.png)."), "[MIT circuit diagram](https://ocw.mit.edu/resources/diagram.png).");
  assert.equal(learnerCopy("Voltage is 5 V. Evidence: checks/batch1103-native-verification.json."), "Voltage is 5 V.");
});

test("literal programs and explicit math remain byte-identical when adjacent prose changes", () => {
  const snippets = [
    "$The source says x+y$", "$$The source says x+y$$", "\\(The source says x+y\\)",
    "`The source says`", "`[diagram](../sources/a.png)`",
    "```text\nThe source says x.\n[scan](../sources/a.png)\n```",
    "~~~text\nThe source says x.\n~~~",
    "  ```c\n  puts(\"The source says\");\n  ```",
    "[datasheet](https://example.org/sources/original.pdf)",
  ];
  for (const literal of snippets) {
    const out = learnerCopy("The source says A=1.\n"+literal+"\nThe source says B=2.");
    assert.equal(out, "The problem says A=1.\n"+literal+"\nThe problem says B=2.");
    assert.equal(learnerCopy(out), out);
  }
});

test("removing an archive link preserves sentence spacing and authored line breaks", () => {
  const archive = "[Supplied table screenshot](../sources/prep-015.png).";
  assert.equal(learnerCopy(archive+" Use the table."), "Use the table.");
  assert.equal(learnerCopy("Use row 4. "+archive+" Use column 2."), "Use row 4. Use column 2.");
  assert.equal(learnerCopy("The source says A=1.\n```text\nx  \n```  \n"), "The problem says A=1.\n```text\nx  \n```  \n");
});

test("technical facts in notes remain available after operational wording is removed", () => {
  assert.equal(learnerCopy("The archived Hebrew wording includes the original byte/bit typo and states eight pixels per element."), "There are eight pixels per element.");
  assert.equal(learnerCopy("הנוסח המקורי “בית ביטים” נשמר בארכיון; הוא מציין שמונה פיקסלים לאיבר."), "כל איבר מייצג שמונה פיקסלים.");
  assert.match(learnerCopy("The source provides raw text rather than a token list; splitting, ties and empty behavior are explicit."), /raw text.+split.+ties.+empty/);
});
