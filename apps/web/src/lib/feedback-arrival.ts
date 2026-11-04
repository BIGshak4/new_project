import type { Attempt, Submission } from "./practice-api";

export type FeedbackArrival = { attemptId: string; revision: number };

function latestFeedback(attempt: Attempt): Submission | undefined {
  return [attempt.submission, ...attempt.follow_ups.map((followUp) => followUp.submission)]
    .filter((submission): submission is Submission => !!submission)
    .reduce<Submission | undefined>((latest, submission) =>
      !latest || submission.revision > latest.revision ? submission : latest, undefined);
}

function isReady(attempt: Attempt, submission: Submission | undefined): submission is Submission {
  return !!submission && submission.status === "done" && submission.assessed_by === "model" &&
    attempt.status !== "evaluating" && !submission.feedback_pending && !attempt.feedback_pending;
}

/** Tracks arrivals in the currently open attempt, without jumping on a historical report visit. */
export class FeedbackArrivalTracker {
  private attemptId: string | null = null;
  private highestRevision = 0;
  private delivered = new Set<number>();

  reset() {
    this.attemptId = null;
    this.highestRevision = 0;
    this.delivered.clear();
  }

  observe(attempt: Attempt): FeedbackArrival | null {
    const submission = latestFeedback(attempt);
    if (this.attemptId !== attempt.id) {
      this.attemptId = attempt.id;
      this.highestRevision = submission?.revision ?? 0;
      this.delivered.clear();
      // A completed answer on first load is history; an in-flight answer should still announce arrival.
      if (isReady(attempt, submission)) this.delivered.add(submission.revision);
      return null;
    }
    // An older response must not pull the reader back to a previous answer.
    if (submission && submission.revision < this.highestRevision) return null;
    this.highestRevision = submission?.revision ?? this.highestRevision;
    if (!isReady(attempt, submission) || this.delivered.has(submission.revision)) return null;
    return { attemptId: attempt.id, revision: submission.revision };
  }

  acknowledge(arrival: FeedbackArrival) {
    if (arrival.attemptId === this.attemptId) this.delivered.add(arrival.revision);
  }
}
