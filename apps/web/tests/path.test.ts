import assert from "node:assert/strict";
import { test } from "node:test";
import {
  daysToGoLabel,
  filledBlocks,
  nodeStyle,
  pathNodes,
  pixelOffset,
  skillLevelWord,
  strengthSkills,
  strengthTone,
  todayProgress,
  zigzagOffset,
} from "../src/lib/path";
import type { PlanItem, Program, SkillProgress } from "../src/lib/practice-api";

const item = (over: Partial<PlanItem>): PlanItem => ({
  id: "x",
  day_index: 0,
  date: "2026-09-25",
  mode: "quick",
  skills: [{ key: "counters", label: "Counters" }],
  minutes: 10,
  reason: "because",
  done: false,
  status: "planned",
  carried: false,
  ...over,
});

test("the path marks done, one current, the rest locked, and interviews as their own kind", () => {
  const items = [
    item({ id: "a", status: "done", done: true }),
    item({ id: "b", carried: true }),
    item({ id: "c", day_index: 1 }),
    item({ id: "d", day_index: 2, mode: "simulation" }),
    item({ id: "e", day_index: 2, status: "skipped" }),
  ];
  const nodes = pathNodes(items, "b");
  assert.deepEqual(
    nodes.map((n) => n.state),
    ["done", "current", "locked", "locked", "skipped"],
  );
  assert.equal(nodes.filter((n) => n.state === "current").length, 1);
  assert.equal(nodes[3].kind, "interview");
  assert.equal(nodes[1].carried, true);
  assert.deepEqual(nodes.map((n) => n.dayIndex), [0, 0, 1, 2, 2]);
});

test("only the program's named next item is current; none when the program names none (today is done)", () => {
  const items = [item({ id: "a", status: "done", done: true }), item({ id: "b", status: "started" }), item({ id: "c" })];
  assert.equal(pathNodes(items, "c").find((n) => n.state === "current")?.item.id, "c");
  // no next item: the server would refuse to start tomorrow's item, so nothing offers a Start button
  assert.equal(pathNodes(items).find((n) => n.state === "current"), undefined);
  assert.equal(pathNodes(items, null).find((n) => n.state === "current"), undefined);
  assert.equal(pathNodes(items, "zzz").find((n) => n.state === "current"), undefined);
});

test("drawing order: by day, done first, carried before new, interviews last within a day", () => {
  const items = [
    item({ id: "sim", day_index: 0, mode: "simulation" }),
    item({ id: "new", day_index: 0 }),
    item({ id: "old", day_index: 0, carried: true }),
    item({ id: "done", day_index: 0, status: "done", done: true }),
    item({ id: "tomorrow", day_index: 1 }),
  ];
  assert.deepEqual(pathNodes(items, "old").map((n) => n.item.id), ["done", "old", "new", "sim", "tomorrow"]);
});

test("nothing open means no current node", () => {
  const nodes = pathNodes([item({ id: "a", status: "done", done: true })]);
  assert.deepEqual(nodes.map((n) => n.state), ["done"]);
  assert.equal(pathNodes([]).length, 0);
});

test("the zig-zag winds from the start side to the end side and back, and repeats", () => {
  const offsets = Array.from({ length: 10 }, (_, i) => zigzagOffset(i));
  assert.ok(offsets[0] < 0 && offsets[2] > 0 && offsets[4] < 0, `expected a wind, got ${offsets}`);
  assert.ok(offsets.every((o) => o >= -1 && o <= 1));
  assert.equal(zigzagOffset(8), zigzagOffset(0));
  assert.equal(zigzagOffset(-1), zigzagOffset(7));
});

test("node offsets use a logical margin (so RTL mirrors by itself) and the physical pixel offset flips sign in RTL", () => {
  assert.deepEqual(nodeStyle(-0.5, 200), { marginInlineStart: "-100px" });
  assert.deepEqual(nodeStyle(0.7, 200), { marginInlineStart: "140px" });
  assert.equal(pixelOffset(0.7, 200, "ltr"), 140);
  assert.equal(pixelOffset(0.7, 200, "rtl"), -140);
  assert.equal(pixelOffset(0, 200, "rtl"), 0);
});

test("today's progress counts done items against everything that was due", () => {
  const program = { done_today: 2, today: [item({}), item({})] } as unknown as Program;
  assert.deepEqual(todayProgress(program), { done: 2, total: 4, fraction: 0.5 });
  assert.deepEqual(todayProgress(null), { done: 0, total: 0, fraction: 0 });
  assert.deepEqual(todayProgress({ done_today: 0, today: [] } as unknown as Program), { done: 0, total: 0, fraction: 0 });
});

const skill = (over: Partial<SkillProgress>): SkillProgress => ({
  key: "k",
  label: "K",
  subject: "s",
  level: 3,
  status: "assessed",
  trend: "stable",
  required_level: 3,
  assessments: 2,
  last_assessed_at: null,
  retention_due_at: null,
  ...over,
});

test("strength tone: green at the required level, yellow below, blue when a refresh is due, grey when unassessed", () => {
  assert.equal(strengthTone(skill({})), "green");
  assert.equal(strengthTone(skill({ level: 2 })), "yellow");
  assert.equal(strengthTone(skill({ needs_refresh: true })), "blue");
  assert.equal(strengthTone(skill({ level: null, status: "not_assessed" })), "grey");
});

test("blocks and words follow the level 1..5", () => {
  assert.equal(filledBlocks(null), 0);
  assert.equal(filledBlocks(3), 3);
  assert.equal(filledBlocks(9), 5);
  assert.equal(skillLevelWord(3, "en"), "Proficient");
  assert.equal(skillLevelWord(null, "he"), "טרם הוערכה");
});

test("the strength card shows assessed skills, most demanding first, capped", () => {
  const list = [
    skill({ key: "a", label: "A", required_level: 2 }),
    skill({ key: "b", label: "B", required_level: 4 }),
    skill({ key: "c", label: "C", level: null, status: "not_assessed" }),
    skill({ key: "d", label: "D", required_level: 4 }),
  ];
  assert.deepEqual(strengthSkills(list).map((s) => s.key), ["b", "d", "a"]);
  assert.deepEqual(strengthSkills(list, 1).map((s) => s.key), ["b"]);
});

test("days to go in words", () => {
  assert.equal(daysToGoLabel(null, "en"), null);
  assert.equal(daysToGoLabel(0, "en"), "the interview is today");
  assert.equal(daysToGoLabel(1, "en"), "1 day to go");
  assert.equal(daysToGoLabel(12, "he"), "12 ימים לראיון");
  assert.equal(daysToGoLabel(-1, "en"), "the interview has passed");
});
