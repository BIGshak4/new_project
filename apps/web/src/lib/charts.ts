/** Pure helpers behind the progress donuts and the evaluation ring. No DOM, so they are unit-testable with tsx. */

import type { NextQuestion, SubjectProgress } from "./practice-api";

export type Segment = {
  key: "STRONG" | "PARTIAL" | "WEAK";
  count: number;
  /** share of the ring, 0-1 */
  fraction: number;
  /** where this segment starts on the ring, 0-1 */
  offset: number;
};

/** Ring segments for one subject's answers, strongest first. Empty when nothing was answered. */
export function donutSegments(
  bands: Partial<Record<"STRONG" | "PARTIAL" | "WEAK", number>>,
): Segment[] {
  const order = ["STRONG", "PARTIAL", "WEAK"] as const;
  const total = order.reduce((sum, k) => sum + (bands[k] ?? 0), 0);
  if (!total) return [];
  let offset = 0;
  return order
    .filter((k) => (bands[k] ?? 0) > 0)
    .map((k) => {
      const count = bands[k] ?? 0;
      const seg = { key: k, count, fraction: count / total, offset };
      offset += seg.fraction;
      return seg;
    });
}

/** SVG stroke-dasharray / dashoffset for a segment on a circle of the given radius. */
export function arc(segment: { fraction: number; offset: number }, radius: number) {
  const circumference = 2 * Math.PI * radius;
  const length = Math.max(0, segment.fraction * circumference - 1.5); // a hairline gap between segments
  return {
    dasharray: `${length} ${circumference - length}`,
    dashoffset: -(segment.offset * circumference),
  };
}

/** How much of the ring the band lights up: one third, two thirds, all. */
export function bandFraction(band: string | null | undefined) {
  return band === "STRONG" ? 1 : band === "PARTIAL" ? 2 / 3 : band === "WEAK" ? 1 / 3 : 0;
}

/** Subjects worth drawing: in the role plan or already practised, heaviest first. */
export function chartSubjects(subjects: SubjectProgress[]) {
  return [...subjects]
    .filter((s) => s.skills_total > 0 || s.attempts > 0)
    .sort((a, b) => b.weight - a.weight || a.label.localeCompare(b.label));
}

/** Percent of the plan's skills that already have a level, across the subjects shown. */
export function coveragePercent(subjects: SubjectProgress[]) {
  const total = subjects.reduce((n, s) => n + s.skills_total, 0);
  if (!total) return 0;
  return Math.round(
    (100 * subjects.reduce((n, s) => n + s.skills_assessed, 0)) / total,
  );
}

export function whyLabel(why: NextQuestion["why"], lang: "he" | "en") {
  const labels: Record<NextQuestion["why"], [string, string]> = {
    reinforce: ["חיזוק", "Reinforce"],
    consolidate: ["ביסוס", "Consolidate"],
    advance: ["התקדמות", "Advance"],
    explore: ["נושא חדש", "Explore"],
  };
  return (labels[why] ?? [why, why])[lang === "he" ? 0 : 1];
}
