import assert from "node:assert/strict";
import { test } from "node:test";
import { dayLabel, levelSteps, modeLabel, planByDay, tickDays, timelineLayout } from "../src/lib/timeline";
import type { PlanItem, TimelinePoint } from "../src/lib/practice-api";

const point = (over: Partial<TimelinePoint>): TimelinePoint => ({
  day: "2026-09-20",
  answered: 3,
  strong: 1,
  partial: 1,
  weak: 1,
  level: 2,
  ...over,
});

test("bars stack weak, partial, strong from the baseline and never exceed the plot", () => {
  const layout = timelineLayout([point({}), point({ day: "2026-09-21", answered: 6, strong: 6, partial: 0, weak: 0, level: 3 })], 400, 160);
  assert.equal(layout.bars.length, 2);
  assert.equal(layout.maxAnswers, 6);
  const first = layout.bars[0];
  assert.deepEqual(
    first.segments.map((s) => s[0]),
    ["WEAK", "PARTIAL", "STRONG"],
  );
  const total = first.segments.reduce((n, s) => n + s[2], 0);
  const plotHeight = 160 - layout.padding.top - layout.padding.bottom;
  assert.ok(Math.abs(total - plotHeight / 2) < 1.5, `three of six answers fill half the plot, got ${total}`);
  const tallest = layout.bars[1];
  assert.equal(tallest.segments.length, 1);
  assert.ok(Math.abs(tallest.segments[0][2] - plotHeight) < 1.5);
  for (const bar of layout.bars) {
    assert.ok(bar.x >= layout.padding.left && bar.x + bar.width <= 400 - layout.padding.right);
  }
});

test("the level line uses only days with a level, mapped 1..5 onto the plot", () => {
  const layout = timelineLayout([point({ level: null }), point({ day: "2026-09-21", level: 1 }), point({ day: "2026-09-22", level: 5 })], 400, 160);
  assert.equal(layout.levelPoints.length, 2);
  assert.ok(layout.levelPath?.startsWith("M"));
  const [low, high] = layout.levelPoints;
  assert.ok(Math.abs(low.y - (160 - layout.padding.bottom)) < 0.01, "level 1 sits on the baseline");
  assert.ok(Math.abs(high.y - layout.padding.top) < 0.01, "level 5 touches the top");
  assert.equal(timelineLayout([], 400, 160).levelPath, null);
});

test("tick days keep the first and the last day and thin the middle", () => {
  const points = Array.from({ length: 14 }, (_, i) => point({ day: `2026-09-${String(i + 1).padStart(2, "0")}` }));
  const ticks = tickDays(points, 6);
  assert.ok(ticks.has("2026-09-01") && ticks.has("2026-09-14"));
  assert.ok(ticks.size <= 7);
  assert.equal(tickDays([]).size, 0);
});

test("the plan groups by day, in order, summing the minutes", () => {
  const item = (day_index: number, mode: string, minutes: number): PlanItem => ({
    day_index,
    date: `2026-09-2${day_index}`,
    mode,
    skills: [{ key: "boolean_algebra", label: "Boolean algebra" }],
    minutes,
    reason: "because",
    done: false,
  });
  const days = planByDay([item(1, "deep", 25), item(0, "quick", 10), item(0, "quick", 10)]);
  assert.deepEqual(
    days.map((d) => [d.day_index, d.minutes, d.items.length]),
    [
      [0, 20, 2],
      [1, 25, 1],
    ],
  );
});

test("labels are localised and never throw on odd input", () => {
  assert.equal(dayLabel("2026-09-23", 0, "he"), "היום");
  assert.equal(dayLabel("2026-09-24", 1, "en"), "Tomorrow");
  assert.ok(dayLabel("2026-09-27", 4, "en").length > 3);
  assert.equal(dayLabel("not-a-date", 4, "en"), "not-a-date");
  assert.equal(modeLabel("deep", "en"), "Deep practice");
  assert.equal(modeLabel("unknown_mode", "he"), "unknown_mode");
  assert.equal(levelSteps("en").length, 6);
  assert.equal(levelSteps("he")[0], "בתחילת הדרך");
});
