/** Pure helpers behind the progress graph and the plan table. No DOM, so they are unit-testable with tsx. */

import type { PlanItem, TimelinePoint } from "./practice-api";

export type Bar = {
  day: string;
  x: number;
  width: number;
  /** stacked segments from the baseline up: [key, y, height] */
  segments: ["STRONG" | "PARTIAL" | "WEAK", number, number][];
  answered: number;
};

export type Layout = {
  bars: Bar[];
  /** the level line, one point per day that has a level; null when no level is known yet */
  levelPath: string | null;
  levelPoints: { x: number; y: number; day: string; level: number }[];
  maxAnswers: number;
  width: number;
  height: number;
  padding: { top: number; right: number; bottom: number; left: number };
};

const PADDING = { top: 14, right: 12, bottom: 26, left: 28 };

/** Bars per practice day (answers by band) and a line for the average level (1-5). */
export function timelineLayout(points: TimelinePoint[], width = 640, height = 200): Layout {
  const p = PADDING;
  const innerW = Math.max(1, width - p.left - p.right);
  const innerH = Math.max(1, height - p.top - p.bottom);
  const maxAnswers = Math.max(1, ...points.map((pt) => pt.answered));
  const slot = points.length ? innerW / points.length : innerW;
  const barW = Math.max(4, Math.min(28, slot * 0.6));
  const yFor = (n: number) => p.top + innerH - (n / maxAnswers) * innerH;
  const bars: Bar[] = points.map((pt, i) => {
    const x = p.left + slot * i + (slot - barW) / 2;
    let stack = 0;
    const segments: Bar["segments"] = [];
    for (const key of ["WEAK", "PARTIAL", "STRONG"] as const) {
      const n = pt[key.toLowerCase() as "weak" | "partial" | "strong"];
      if (!n) continue;
      const top = yFor(stack + n);
      const bottom = yFor(stack);
      segments.push([key, top, Math.max(1, bottom - top)]);
      stack += n;
    }
    return { day: pt.day, x, width: barW, segments, answered: pt.answered };
  });
  const levelPoints = points
    .map((pt, i) =>
      pt.level === null || pt.level === undefined
        ? null
        : {
            x: p.left + slot * i + slot / 2,
            y: p.top + innerH - ((Math.min(5, Math.max(1, pt.level)) - 1) / 4) * innerH,
            day: pt.day,
            level: pt.level,
          },
    )
    .filter((v): v is NonNullable<typeof v> => v !== null);
  const levelPath = levelPoints.length
    ? levelPoints.map((pt, i) => `${i ? "L" : "M"}${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`).join(" ")
    : null;
  return { bars, levelPath, levelPoints, maxAnswers, width, height, padding: p };
}

/** Which day labels to print under the bars so they never overlap: first, last and every n-th. */
export function tickDays(points: TimelinePoint[], maxTicks = 6): Set<string> {
  if (!points.length) return new Set();
  const step = Math.max(1, Math.ceil(points.length / maxTicks));
  const out = new Set<string>();
  points.forEach((pt, i) => {
    if (i % step === 0 || i === points.length - 1) out.add(pt.day);
  });
  return out;
}

/** The plan grouped by day, in order, with the minutes used per day. */
export function planByDay(items: PlanItem[]): { day_index: number; date: string; minutes: number; items: PlanItem[] }[] {
  const days = new Map<number, { day_index: number; date: string; minutes: number; items: PlanItem[] }>();
  for (const item of items) {
    const day = days.get(item.day_index) ?? { day_index: item.day_index, date: item.date, minutes: 0, items: [] };
    day.items.push(item);
    day.minutes += item.minutes;
    days.set(item.day_index, day);
  }
  return [...days.values()].sort((a, b) => a.day_index - b.day_index);
}

/** How the day is named: today, tomorrow, or the weekday and date. */
export function dayLabel(date: string, dayIndex: number, lang: "he" | "en", today = new Date()): string {
  if (dayIndex === 0) return lang === "he" ? "היום" : "Today";
  if (dayIndex === 1) return lang === "he" ? "מחר" : "Tomorrow";
  const d = new Date(`${date}T12:00:00`);
  if (Number.isNaN(d.getTime())) return date;
  void today;
  return d.toLocaleDateString(lang === "he" ? "he-IL" : "en-GB", { weekday: "short", day: "numeric", month: "short" });
}

export function modeLabel(mode: string, lang: "he" | "en"): string {
  const labels: Record<string, [string, string]> = {
    quick: ["שאלה קצרה", "Quick question"],
    deep: ["תרגול מעמיק", "Deep practice"],
    simulation: ["ראיון מדומה", "Mock interview"],
    diagnostic: ["אבחון", "Diagnostic"],
    retention_check: ["בדיקת זיכרון", "Retention check"],
  };
  return labels[mode]?.[lang === "he" ? 0 : 1] ?? mode;
}

/** The six words of the level meter, in the app's language (the server sends the current one already localised). */
export function levelSteps(lang: "he" | "en"): string[] {
  return lang === "he"
    ? ["בתחילת הדרך", "צעדים ראשונים", "בסיס", "שליטה", "מתקדם", "מומחה"]
    : ["Getting started", "First steps", "Foundational", "Proficient", "Advanced", "Expert"];
}
