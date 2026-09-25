/**
 * Pure helpers behind the Learn home: the saved program drawn as a winding path of nodes, the skill-strength
 * bars and the small numbers the side column shows. No DOM, so node:test can run them with tsx.
 */

import type { PlanItem, Program, SkillProgress } from "./practice-api";

export type NodeState = "done" | "current" | "locked" | "skipped";
export type NodeKind = "practice" | "interview";

export type PathNode = {
  item: PlanItem;
  key: string;
  state: NodeState;
  kind: NodeKind;
  /** the horizontal offset from the centre line, -1 (inline start) .. 1 (inline end) */
  offset: number;
  /** the item was planned for an earlier day and carried forward */
  carried: boolean;
  /** 0 = today's section, 1 = tomorrow ... : the day the node belongs to */
  dayIndex: number;
};

/** The zig-zag the mockup draws: start side, near centre, far end side, centre, far start side, repeat. */
const ZIGZAG = [-0.9, -0.2, 0.7, 0.1, -0.8, -0.3, 0.6, 0.2];

export function zigzagOffset(index: number): number {
  return ZIGZAG[((index % ZIGZAG.length) + ZIGZAG.length) % ZIGZAG.length];
}

/**
 * The state of one plan item on the path. Only the program's own "start now" item (`nextId`) is current: when the
 * program names none (today is done), tomorrow's first item stays locked, because the server would refuse to start it.
 */
export function nodeState(item: PlanItem, nextId: string | null | undefined): NodeState {
  if (item.done || item.status === "done") return "done";
  if (item.status === "skipped") return "skipped";
  return nextId && item.id === nextId ? "current" : "locked";
}

/** Plan order for drawing: by day; within a day done first, then carried, practice before interviews (the server's
 * order for "next"), so the current node never sits below a locked one of the same day. */
export function pathOrder(items: PlanItem[]): PlanItem[] {
  const rank = (i: PlanItem) => (i.done || i.status === "done" ? 0 : i.status === "skipped" ? 3 : i.mode === "simulation" ? 2 : 1);
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) =>
      a.item.day_index - b.item.day_index ||
      rank(a.item) - rank(b.item) ||
      Number(!a.item.carried) - Number(!b.item.carried) ||
      a.index - b.index,
    )
    .map((x) => x.item);
}

/**
 * The nodes of the path, in drawing order (pathOrder). At most one node is `current`: the program's next item;
 * none when today is done.
 */
export function pathNodes(items: PlanItem[], nextId?: string | null): PathNode[] {
  const open = items.filter((i) => !i.done && (i.status === "planned" || i.status === "started"));
  const named = nextId && open.some((i) => i.id === nextId) ? nextId : null;
  return pathOrder(items).map((item, index) => ({
    item,
    key: item.id ?? `${item.day_index}-${index}`,
    state: nodeState(item, named),
    kind: item.mode === "simulation" ? "interview" : "practice",
    offset: zigzagOffset(index),
    carried: !!item.carried,
    dayIndex: item.day_index,
  }));
}

/**
 * The CSS the node row gets. Offsets are expressed with a logical margin, so the zig-zag mirrors by itself
 * under `dir="rtl"`: an offset of -0.9 sits near the inline start in both directions (the right edge in Hebrew).
 * `pixelOffset` gives the signed physical shift for anything that cannot use logical properties (SVG).
 */
export function nodeStyle(offset: number, amplitude: number): { marginInlineStart: string } {
  return { marginInlineStart: `${Math.round(offset * amplitude)}px` };
}

export function pixelOffset(offset: number, amplitude: number, dir: "ltr" | "rtl"): number {
  const px = Math.round(offset * amplitude);
  return dir === "rtl" ? -px || 0 : px;          // `|| 0` keeps a centred node at +0, never -0
}

/** How many of today's items are done, out of how many were due (carried items count as today's). */
export function todayProgress(program: Program | null): { done: number; total: number; fraction: number } {
  if (!program) return { done: 0, total: 0, fraction: 0 };
  const done = program.done_today ?? 0;
  const total = done + program.today.length;
  return { done, total, fraction: total ? Math.min(1, done / total) : 0 };
}

export type StrengthTone = "green" | "yellow" | "blue" | "grey";

/** Colour of a skill's bar: blue when a refresh is due, green at or above what the job needs, yellow below, grey unassessed. */
export function strengthTone(skill: Pick<SkillProgress, "level" | "required_level" | "needs_refresh" | "status">): StrengthTone {
  if (skill.level === null || skill.status === "not_assessed") return "grey";
  if (skill.needs_refresh) return "blue";
  return skill.level >= skill.required_level ? "green" : "yellow";
}

/** The five blocks of a strength bar: how many are filled for a level 1..5 (0 when unassessed). */
export function filledBlocks(level: number | null): number {
  if (level === null || level === undefined) return 0;
  return Math.max(0, Math.min(5, Math.round(level)));
}

/** The level in words for a skill (1..5 -> First steps..Expert), or "Not assessed yet". */
export function skillLevelWord(level: number | null, lang: "he" | "en"): string {
  const words = lang === "he"
    ? ["טרם הוערכה", "צעדים ראשונים", "בסיס", "שליטה", "מתקדם", "מומחה"]
    : ["Not assessed yet", "First steps", "Foundational", "Proficient", "Advanced", "Expert"];
  return words[filledBlocks(level)];
}

/** The skills worth showing in the strength card: assessed ones first by required level, then the rest; at most `limit`. */
export function strengthSkills(skills: SkillProgress[], limit = 6): SkillProgress[] {
  const assessed = skills.filter((s) => s.level !== null).sort((a, b) => b.required_level - a.required_level || a.label.localeCompare(b.label));
  return assessed.slice(0, limit);
}

/** "12 days to go" / "the interview is today" / null when no date is known. */
export function daysToGoLabel(days: number | null | undefined, lang: "he" | "en"): string | null {
  if (days === null || days === undefined) return null;
  if (days < 0) return lang === "he" ? "הראיון עבר" : "the interview has passed";
  if (days === 0) return lang === "he" ? "הראיון היום" : "the interview is today";
  if (days === 1) return lang === "he" ? "יום אחד לראיון" : "1 day to go";
  return lang === "he" ? `${days} ימים לראיון` : `${days} days to go`;
}
