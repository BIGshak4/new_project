"use client";

import { useCallback, useEffect, useRef, type RefObject } from "react";
import type { Attempt } from "../lib/practice-api";
import { FeedbackArrivalTracker } from "../lib/feedback-arrival";

/** Run after React has committed the completed feedback, never from the polling callback. */
export function useFeedbackArrival({
  attempt,
  attemptId,
  loading,
  enabled = true,
  feedbackRef,
}: {
  attempt: Attempt | null;
  attemptId?: string;
  loading: boolean;
  enabled?: boolean;
  feedbackRef: RefObject<HTMLElement | null>;
}) {
  const tracker = useRef(new FeedbackArrivalTracker());
  const requestFeedback = useCallback((target: { key: string } | { revision: number }) => {
    if (attemptId) tracker.current.request(attemptId, target);
  }, [attemptId]);

  useEffect(() => {
    if (!attemptId) {
      tracker.current.reset();
      return;
    }
    // A route change may render once with the previous attempt before its loading effect runs.
    // Temporary health/loading gates must not erase the user's explicit submit request.
    if (!enabled || loading || !attempt || attempt.id !== attemptId) return;
    const arrival = tracker.current.observe(attempt);
    if (!arrival) return;

    const frame = requestAnimationFrame(() => {
      const feedback = feedbackRef.current;
      if (!feedback || feedback.dataset.feedbackAttempt !== arrival.attemptId) return;
      const target = feedback.querySelector<HTMLElement>(`[data-feedback-revision="${arrival.revision}"]`);
      if (!target) return;
      target.focus({ preventScroll: true });
      // Land directly on the completed card; a smooth trip can be interrupted by
      // scrolling or late layout changes elsewhere in the saved-answer area.
      target.scrollIntoView({ block: "start", behavior: "instant" });
      // A cancelled frame (including Strict Mode replay) must not consume the arrival.
      tracker.current.acknowledge(arrival);
    });
    return () => cancelAnimationFrame(frame);
  }, [attempt, attemptId, loading, enabled, feedbackRef]);

  return requestFeedback;
}
