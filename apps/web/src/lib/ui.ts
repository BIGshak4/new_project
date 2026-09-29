/**
 * Small pure helpers behind the interactive layer (Motion, Radix, Sonner), kept free of React so they can be
 * unit-tested with the rest of `tests/`.
 */

/** Radix Select refuses an empty-string item value; the app uses "" for "all". Map it both ways. */
export const EMPTY_OPTION = "__all__";
export function toSelectValue(value: string): string {
  return value === "" ? EMPTY_OPTION : value;
}
export function fromSelectValue(value: string): string {
  return value === EMPTY_OPTION ? "" : value;
}

/**
 * Stagger for a list that reveals item by item: 45 ms apart, never more than 0.5 s in total, so a long path
 * does not keep the reader waiting. With reduced motion everything is immediate.
 */
export function revealDelay(index: number, reduced = false, step = 0.045, cap = 0.5): number {
  if (reduced || index <= 0) return 0;
  return Math.min(index * step, cap);
}

/** The grade sequence: ring, glyph, band, XP, good, missing, tip. Seconds after the panel mounts. */
export const GRADE_SEQUENCE = {
  ring: 0,
  glyph: 0.45,
  band: 0.55,
  xp: 0.85,
  good: 1.0,
  missing: 1.12,
  tip: 1.3,
} as const;

/**
 * Whether the Learn page should scroll the current node into view on open: only when the node is not already
 * fully visible, so a short path on a desktop does not jump.
 */
export function shouldScrollToNode(rect: { top: number; bottom: number }, viewportHeight: number, topBar = 90): boolean {
  return rect.top < topBar || rect.bottom > viewportHeight;
}

/** The interview timer's tone: calm, then amber for the last minute, then red for the last ten seconds. */
export function timerTone(secondsLeft: number): "calm" | "warn" | "danger" {
  if (secondsLeft <= 10) return "danger";
  if (secondsLeft <= 60) return "warn";
  return "calm";
}

/** Digits for the counting XP number: never negative, never fractional. */
export function countDisplay(value: number): number {
  return Math.max(0, Math.round(value));
}
