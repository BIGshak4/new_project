import { hasCurrentTestimonialApproval, type PublishedTestimonial, type TestimonialLanguage } from "./public-testimonials";

/** Offline/private editorial intake only; never import raw intake records into a Client Component. */
type LocalizedCopy = Readonly<Partial<Record<TestimonialLanguage, string>>>;

/** Approval covers this exact copy revision, including the public attribution. */
export type LandingTestimonial = Readonly<{
  id: string;
  revision: number;
  quote: LocalizedCopy;
  displayName: LocalizedCopy;
  context?: LocalizedCopy;
  publication: Readonly<{
    state: "draft" | "approved" | "withdrawn";
    consentToPublish?: boolean;
    approvedRevision?: number;
    approvedOn?: string;
  }>;
}>;

/** Missing consent, changed copy and absent translations never become public testimonials. */
export function publishedTestimonials(entries: readonly LandingTestimonial[], lang: TestimonialLanguage): PublishedTestimonial[] {
  const seen = new Set<string>();
  return entries.flatMap(entry => {
    const approval = entry.publication;
    const quote = entry.quote[lang]?.trim();
    const displayName = entry.displayName[lang]?.trim();
    if (
      !entry.id.trim() || seen.has(entry.id) ||
      !hasCurrentTestimonialApproval(entry.revision, approval) ||
      !quote || !displayName
    ) return [];
    seen.add(entry.id);
    return [{ id: entry.id, quote, displayName, context: entry.context?.[lang]?.trim() || undefined }];
  });
}
