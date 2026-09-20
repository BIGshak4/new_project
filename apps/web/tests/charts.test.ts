import assert from "node:assert/strict";
import { test } from "node:test";
import {
  arc,
  bandFraction,
  chartSubjects,
  coveragePercent,
  donutSegments,
  whyLabel,
} from "../src/lib/charts";
import type { SubjectProgress } from "../src/lib/practice-api";

const subject = (over: Partial<SubjectProgress>): SubjectProgress => ({
  key: "digital_fundamentals",
  label: "Digital fundamentals",
  skills_total: 4,
  skills_assessed: 1,
  skills_started: 2,
  levels: { "1": 0, "2": 1, "3": 0, "4": 0, "5": 0 },
  average_level: 2,
  bands: { STRONG: 2, PARTIAL: 1, WEAK: 1 },
  attempts: 4,
  weight: 0.4,
  questions_available: 10,
  ...over,
});

test("donut segments cover the ring once, strongest first, skipping empty bands", () => {
  const segments = donutSegments({ STRONG: 2, PARTIAL: 0, WEAK: 2 });
  assert.deepEqual(
    segments.map((s) => [s.key, s.fraction, s.offset]),
    [
      ["STRONG", 0.5, 0],
      ["WEAK", 0.5, 0.5],
    ],
  );
  assert.equal(segments.reduce((n, s) => n + s.fraction, 0), 1);
  assert.deepEqual(donutSegments({}), []);
});

test("an arc is a dash the length of its share, offset by what came before", () => {
  const radius = 10;
  const circumference = 2 * Math.PI * radius;
  const { dasharray, dashoffset } = arc({ fraction: 0.25, offset: 0.5 }, radius);
  const [dash, gap] = dasharray.split(" ").map(Number);
  assert.ok(Math.abs(dash - (circumference / 4 - 1.5)) < 1e-9);
  assert.ok(Math.abs(dash + gap - circumference) < 1e-9);
  assert.ok(Math.abs(dashoffset + circumference / 2) < 1e-9);
});

test("the band ring lights a third, two thirds or all of the ring", () => {
  assert.equal(bandFraction("WEAK"), 1 / 3);
  assert.equal(bandFraction("PARTIAL"), 2 / 3);
  assert.equal(bandFraction("STRONG"), 1);
  assert.equal(bandFraction(null), 0);
});

test("subjects outside the plan and never practised are hidden; heaviest first", () => {
  const shown = chartSubjects([
    subject({ key: "b", label: "B", weight: 0.1 }),
    subject({ key: "a", label: "A", weight: 0.5 }),
    subject({ key: "none", label: "None", weight: 0, skills_total: 0, attempts: 0 }),
    subject({ key: "practised", label: "P", weight: 0, skills_total: 0, attempts: 2 }),
  ]);
  assert.deepEqual(
    shown.map((s) => s.key),
    ["a", "b", "practised"],
  );
});

test("coverage is assessed skills over plan skills, rounded", () => {
  assert.equal(
    coveragePercent([subject({ skills_total: 4, skills_assessed: 1 }), subject({ skills_total: 2, skills_assessed: 1 })]),
    33,
  );
  assert.equal(coveragePercent([]), 0);
});

test("why labels exist in both languages", () => {
  assert.equal(whyLabel("reinforce", "en"), "Reinforce");
  assert.equal(whyLabel("explore", "he"), "נושא חדש");
});
