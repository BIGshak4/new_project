export type TestimonialLanguage = "he" | "en";
type LocalizedPublicCopy = Readonly<Partial<Record<TestimonialLanguage, string>>>;

/**
 * Public, already-approved copy only. Everything in this shape can be downloaded
 * by a visitor. Drafts, withdrawals and consent evidence belong outside the client
 * import graph; withdrawal means deleting the entry from the public source.
 */
export type ApprovedPublicTestimonial = Readonly<{
  id: string;
  revision: number;
  quote: LocalizedPublicCopy;
  displayName: LocalizedPublicCopy;
  context?: LocalizedPublicCopy;
  publication: Readonly<{
    state: "approved";
    consentToPublish: true;
    approvedRevision: number;
    approvedOn: string;
  }>;
}>;

export type PublishedTestimonial = Readonly<{
  id: string;
  quote: string;
  displayName: string;
  context?: string;
}>;

/** Only approval metadata crosses this helper; it never imports private quote intake. */
export function hasCurrentTestimonialApproval(revision: number, approval: Readonly<{
  state: string;
  consentToPublish?: boolean;
  approvedRevision?: number;
  approvedOn?: string;
}>): boolean {
  const date = approval.approvedOn;
  return Number.isInteger(revision) && revision > 0 &&
    approval.state === "approved" && approval.consentToPublish === true &&
    approval.approvedRevision === revision &&
    typeof date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(date) &&
    Number.isFinite(Date.parse(`${date}T00:00:00Z`)) &&
    new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date;
}

/** Locale selection is presentation, never a privacy boundary. */
export function localizePublicTestimonials(entries: readonly ApprovedPublicTestimonial[], lang: TestimonialLanguage): PublishedTestimonial[] {
  const seen = new Set<string>();
  return entries.flatMap(entry => {
    const quote = entry.quote[lang]?.trim();
    const displayName = entry.displayName[lang]?.trim();
    if (!entry.id.trim() || seen.has(entry.id) || !quote || !displayName ||
      !hasCurrentTestimonialApproval(entry.revision, entry.publication)) return [];
    seen.add(entry.id);
    return [{ id: entry.id, quote, displayName, context: entry.context?.[lang]?.trim() || undefined }];
  });
}
