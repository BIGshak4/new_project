import { test } from "node:test";
import assert from "node:assert/strict";
import { EMPTY_OPTION, countDisplay, fromSelectValue, revealDelay, shouldScrollToNode, timerTone, toSelectValue, GRADE_SEQUENCE } from "../src/lib/ui";
import { chartRows } from "../src/lib/timeline";

test("the empty filter value survives the round trip through a Radix select", () => {
  assert.equal(toSelectValue(""), EMPTY_OPTION);
  assert.equal(fromSelectValue(EMPTY_OPTION), "");
  assert.equal(fromSelectValue(toSelectValue("verification")), "verification");
  assert.notEqual(EMPTY_OPTION, "", "Radix refuses an empty item value");
});

test("reveal delays step up and stop at the cap, and vanish under reduced motion", () => {
  assert.equal(revealDelay(0), 0);
  assert.ok(Math.abs(revealDelay(1) - 0.045) < 1e-9);
  assert.ok(Math.abs(revealDelay(4) - 0.18) < 1e-9);
  assert.equal(revealDelay(40), 0.5);
  assert.equal(revealDelay(7, true), 0);
});

test("the grade sequence keeps its order", () => {
  const order = [GRADE_SEQUENCE.ring, GRADE_SEQUENCE.glyph, GRADE_SEQUENCE.band, GRADE_SEQUENCE.xp, GRADE_SEQUENCE.good, GRADE_SEQUENCE.missing, GRADE_SEQUENCE.tip];
  for (let i = 1; i < order.length; i++) assert.ok(order[i] > order[i - 1], `step ${i} comes after step ${i - 1}`);
  assert.ok(GRADE_SEQUENCE.tip < 1.5, "the whole reveal is over in under a second and a half");
});

test("the page scrolls to the day's sheet only when it starts below the first screen", () => {
  assert.equal(shouldScrollToNode({ top: 200, bottom: 700 }, 900), false);
  assert.equal(shouldScrollToNode({ top: 700, bottom: 1300 }, 900), false, "started inside the first 80 %: the title stays");
  assert.equal(shouldScrollToNode({ top: 760, bottom: 1300 }, 900), true);
});

test("the counting number is a whole, non-negative value", () => {
  assert.equal(countDisplay(61.6), 62);
  assert.equal(countDisplay(-3), 0);
});

test("the interview timer is calm, then amber for the last minute, then red for the last ten seconds", () => {
  assert.equal(timerTone(600), "calm");
  assert.equal(timerTone(61), "calm");
  assert.equal(timerTone(60), "warn");
  assert.equal(timerTone(11), "warn");
  assert.equal(timerTone(10), "danger");
  assert.equal(timerTone(0), "danger");
});

test("chart rows keep the counts and label the day in the page's language", () => {
  const rows = chartRows([
    { day: "2026-09-27", answered: 3, strong: 0, partial: 1, weak: 2, level: null },
    { day: "2026-09-29", answered: 1, strong: 1, partial: 0, weak: 0, level: 2.4 },
  ], "en");
  assert.equal(rows.length, 2);
  assert.deepEqual([rows[0].strong, rows[0].partial, rows[0].weak, rows[0].level], [0, 1, 2, null]);
  assert.equal(rows[1].level, 2.4);
  assert.match(rows[0].label, /27/);
  assert.match(chartRows([{ day: "2026-09-27", answered: 1, strong: 1, partial: 0, weak: 0, level: 1 }], "he")[0].label, /27/);
});
