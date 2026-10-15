import type { ApprovedPublicTestimonial } from "../lib/public-testimonials";

/**
 * PUBLIC APPROVED COPY ONLY: this file is included in visitors' JavaScript.
 * Never put drafts, pending/withdrawn quotes or private consent evidence here,
 * even if they would be hidden by a UI condition. Keep them in a private store
 * outside the client import graph. Withdraw publication by removing the entry.
 *
 * No approved quotes have been supplied. Keep this empty until a real user has
 * approved the exact quote, public name and every published translation. Content
 * edits require renewed consent before replacing the published revision here.
 */
export const landingTestimonials: readonly ApprovedPublicTestimonial[] = [];
