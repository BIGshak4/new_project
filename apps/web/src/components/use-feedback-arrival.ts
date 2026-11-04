"use client";

import { useEffect, useRef, type RefObject } from "react";
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

  useEffect(() => {
    if (!enabled || !attemptId) {
      tracker.current.reset();
      return;
    }
    // A route change may render once with the previous attempt before its loading effect runs.
    if (loading || !attempt || attempt.id !== attemptId) return;
    const arrival = tracker.current.observe(attempt);
    if (!arrival) return;

    const frame = requestAnimationFrame(() => {
      const feedback = feedbackRef.current;
      if (!feedback || feedback.dataset.feedbackAttempt !== arrival.attemptId) return;
      const target = feedback.dataset.feedbackRevision === String(arrival.revision)
        ? feedback
        : feedback.querySelector<HTMLElement>(`[data-feedback-revision="${arrival.revision}"]`);
      if (!target) return;
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      target.focus({ preventScroll: true });
      target.scrollIntoView({ block: "start", behavior: reduceMotion ? "instant" : "smooth" });
      // A cancelled frame (including Strict Mode replay) must not consume the arrival.
      tracker.current.acknowledge(arrival);
    });
    return () => cancelAnimationFrame(frame);
  }, [attempt, attemptId, loading, enabled, feedbackRef]);
}
