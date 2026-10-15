import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { Goal, ProgressOverview } from "../src/lib/practice-api";
import { OverviewCard } from "../src/components/progress-board";

const empty: ProgressOverview = { answered: 0, strong: 0, partial: 0, weak: 0, skills_assessed: 0, skills_total: 25, level: "בתחילת הדרך", level_rank: 0, message: "Start", xp_total: 0, streak_days: 0 };
const noop = () => {};
function render(overview: ProgressOverview, complete = true, lang: "he" | "en" = "he") {
  return renderToStaticMarkup(createElement(OverviewCard, { overview, goal: { complete } as Goal, lang, onEditGoal: noop, onStartPractice: noop, onOpenLibrary: noop }));
}

test("first use offers a real next step instead of empty scores or a level meter", () => {
  const html = render(empty);
  assert.match(html, /לתרגול הראשון שלי/);
  assert.match(html, /לבחור שאלה מהמאגר/);
  assert.doesNotMatch(html, /stat-tiles|level-meter|מיומנויות שהוערכו|XP/);
  assert.match(render(empty, false), /להגדיר יעד ולהתחיל/);
  assert.match(render(empty, true, "en"), /Go to my first practice/);
});

test("answered users retain their actual metrics without duplicated level or assessed counts", () => {
  const html = render({ ...empty, answered: 1, strong: 1, xp_total: 10 });
  assert.match(html, /stat-tiles/);
  assert.match(html, /10/);
  assert.equal(html.split("בתחילת הדרך").length - 1, 1);
  assert.doesNotMatch(html, /איפה אתם עומדים|מיומנויות שהוערכו/);
});
