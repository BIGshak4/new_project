import { test } from "node:test";
import assert from "node:assert/strict";
import { EMPTY_OPTION, countDisplay, fromSelectValue, revealDelay, shouldScrollToNode, toSelectValue, GRADE_SEQUENCE } from "../src/lib/ui";

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

test("the path scrolls to the current node only when it is out of view", () => {
  assert.equal(shouldScrollToNode({ top: 200, bottom: 300 }, 900), false);
  assert.equal(shouldScrollToNode({ top: 850, bottom: 950 }, 900), true);
  assert.equal(shouldScrollToNode({ top: 20, bottom: 120 }, 900), true, "hidden under the top bar counts as out of view");
});

test("the counting number is a whole, non-negative value", () => {
  assert.equal(countDisplay(61.6), 62);
  assert.equal(countDisplay(-3), 0);
});
