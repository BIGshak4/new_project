import { SHORT_TOUR, tourSteps, type TourKind, type TourProgress } from "../../lib/muxi-tour";

const PUBLIC_SHORT_TOUR = SHORT_TOUR.map(step => step.id === "theme" ? {
  ...step,
  body: {
    he: "כאן משנים שפה ומצב בהיר או כהה. אפשר לפתוח את הסיור הקצר שוב דרך סיור קצר עם מוקסי. נסיים בהחלפת מצב אחת.",
    en: "Change language and appearance here. Reopen this short introduction through Short tour with Muxi. Finish by changing the theme once.",
  },
} : step);

export const tourKindForSurface = (kind: TourKind, standalone: boolean): TourKind => standalone ? "short" : kind;
export const tourStepsForSurface = (kind: TourKind, standalone: boolean) => standalone ? PUBLIC_SHORT_TOUR : tourSteps(kind);

/** A visitor's older full-tour checkpoint cannot reopen the full tour through Resume. */
export function tourProgressForSurface(progress: TourProgress, standalone: boolean): TourProgress {
  if (!standalone) return progress;
  const ids = new Set(PUBLIC_SHORT_TOUR.map(step => step.id));
  const completed = progress.completed.filter(id => ids.has(id));
  const skipped = progress.skipped.filter(id => ids.has(id) && !completed.includes(id));
  const stepId = ids.has(progress.stepId)
    ? progress.stepId
    : PUBLIC_SHORT_TOUR.find(step => !completed.includes(step.id) && !skipped.includes(step.id))?.id ?? PUBLIC_SHORT_TOUR.at(-1)!.id;
  return { ...progress, kind: "short", stepId, completed, skipped };
}
