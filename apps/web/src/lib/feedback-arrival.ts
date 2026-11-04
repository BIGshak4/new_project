import type { Attempt, Submission } from "./practice-api";

export type FeedbackArrival = { attemptId: string; revision: number };
export type FeedbackTarget = { key: string } | { revision: number };

function feedbackSubmissions(attempt: Attempt): Submission[] {
  return [attempt.submission, ...attempt.follow_ups.map((followUp) => followUp.submission)]
    .filter((submission): submission is Submission => !!submission);
}

function isReady(submission: Submission | undefined): submission is Submission {
  return !!submission && submission.status === "done" && submission.assessed_by === "model" &&
    !submission.feedback_pending;
}

/** Tracks arrivals in the currently open attempt, without jumping on a historical report visit. */
export class FeedbackArrivalTracker {
  private attemptId: string | null = null;
  private highestRevision = 0;
  private delivered = new Set<number>();
  private requested: { attemptId: string; target: FeedbackTarget; seenRevision?: number } | null = null;

  /** A submit/retry is explicit intent, even if its first observable response is already complete. */
  request(attemptId: string, target: FeedbackTarget) {
    this.requested = { attemptId, target };
  }

  reset() {
    this.attemptId = null;
    this.highestRevision = 0;
    this.delivered.clear();
    this.requested = null;
  }

  observe(attempt: Attempt): FeedbackArrival | null {
    const submissions = feedbackSubmissions(attempt);
    const latest = submissions.reduce<Submission | undefined>((previous, submission) =>
      !previous || submission.revision > previous.revision ? submission : previous, undefined);
    const firstObservation = this.attemptId !== attempt.id;
    if (firstObservation) {
      this.attemptId = attempt.id;
      this.highestRevision = 0;
      this.delivered.clear();
      if (this.requested?.attemptId !== attempt.id) this.requested = null;
    }
    // An older response must not pull the reader back to a previous answer.
    if (latest && latest.revision < this.highestRevision) return null;
    this.highestRevision = latest?.revision ?? this.highestRevision;

    if (this.requested) {
      const target = this.requested.target;
      const selected = submissions.find(submission => "key" in target
        ? submission.key === target.key : submission.revision === target.revision);
      if (selected) this.requested.seenRevision = selected.revision;
      // Existing completed feedback must not stand in for the answer currently being submitted.
      if (firstObservation && isReady(latest) && latest !== selected) this.delivered.add(latest.revision);
      if (!isReady(selected) || selected.revision < this.highestRevision) return null;
      return { attemptId: attempt.id, revision: selected.revision };
    }

    if (firstObservation) {
      // A completed answer on first load is history; an in-flight answer should still announce arrival.
      if (isReady(latest)) this.delivered.add(latest.revision);
      return null;
    }
    if (!isReady(latest) || this.delivered.has(latest.revision)) return null;
    return { attemptId: attempt.id, revision: latest.revision };
  }

  acknowledge(arrival: FeedbackArrival) {
    if (arrival.attemptId !== this.attemptId) return;
    this.delivered.add(arrival.revision);
    if (this.requested?.attemptId === arrival.attemptId && this.requested.seenRevision === arrival.revision)
      this.requested = null;
  }
}
