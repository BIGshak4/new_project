export type SupportLanguage = "he" | "en";
export const SUPPORT_OPEN_EVENT = "jobrun:report-problem";
export type SupportCategory = "bug" | "question" | "feedback" | "other";
export const SUPPORT_LIMITS = { files: 5, fileBytes: 5 * 1024 * 1024, totalBytes: 15 * 1024 * 1024 } as const;
export const SUPPORT_ACCEPT = ".png,.jpg,.jpeg,.webp,.pdf,.txt";

const extensions: Record<string, string> = {
  png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", webp: "image/webp",
  pdf: "application/pdf", txt: "text/plain",
};
export type SupportValidationCode = "file_count" | "file_size" | "total_size" | "file_name" | "file_type" | "file_contents" | "subject" | "description";
export class SupportValidationError extends Error {
  constructor(public code: SupportValidationCode) { super(code); }
}
export type SupportFile = { id: string; file: File; mimeType: string; uploaded: boolean; storagePath?: string };
type InspectableFile = Pick<File, "name" | "size" | "type" | "slice" | "arrayBuffer">;

/** Reject extension/MIME mismatches and misleading binary files before any upload. Storage enforces its own limits too. */
export async function inspectSupportFile(file: InspectableFile): Promise<string> {
  if (!file.name.trim() || file.name.length > 180 || /[\u0000-\u001f\u007f/\\\u202a-\u202e\u2066-\u2069]/.test(file.name)) throw new SupportValidationError("file_name");
  if (!file.size || file.size > SUPPORT_LIMITS.fileBytes) throw new SupportValidationError("file_size");
  const extension = file.name.split(".").at(-1)?.toLowerCase() ?? "";
  const mime = extensions[extension];
  if (!mime || (file.type && file.type !== mime)) throw new SupportValidationError("file_type");
  const bytes = new Uint8Array(await file.slice(0, 16).arrayBuffer());
  const ascii = (start: number, value: string) => [...value].every((letter, index) => bytes[start + index] === letter.charCodeAt(0));
  const matches = mime === "image/png" ? [137, 80, 78, 71, 13, 10, 26, 10].every((byte, index) => bytes[index] === byte)
    : mime === "image/jpeg" ? bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255
    : mime === "image/webp" ? ascii(0, "RIFF") && ascii(8, "WEBP")
    : mime === "application/pdf" ? ascii(0, "%PDF-")
    : true;
  if (!matches) throw new SupportValidationError("file_contents");
  if (mime === "text/plain") {
    const all = new Uint8Array(await file.arrayBuffer());
    try {
      if (all.includes(0)) throw new Error("binary");
      new TextDecoder("utf-8", { fatal: true }).decode(all);
    } catch { throw new SupportValidationError("file_contents"); }
  }
  return mime;
}

export async function inspectSupportFiles(files: InspectableFile[]): Promise<string[]> {
  if (files.length > SUPPORT_LIMITS.files) throw new SupportValidationError("file_count");
  if (files.reduce((total, file) => total + file.size, 0) > SUPPORT_LIMITS.totalBytes) throw new SupportValidationError("total_size");
  return Promise.all(files.map(inspectSupportFile));
}

export function validateSupportDetails(subject: string, description: string) {
  if (subject.trim().length < 3 || subject.trim().length > 160) throw new SupportValidationError("subject");
  if (description.trim().length < 20 || description.trim().length > 6000) throw new SupportValidationError("description");
}

/** Only known public route names and a bounded question identifier are collected. Never forward the complete URL. */
export function supportPageContext(href: string): { pagePath: string; questionKey: string | null } {
  try {
    const url = new URL(href);
    const routes = ["/", "/tour", "/design-lab", "/support", "/privacy"];
    const question = url.searchParams.get("question");
    return {
      pagePath: routes.includes(url.pathname) ? url.pathname : "/",
      questionKey: question && /^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,199}$/.test(question) ? question : null,
    };
  } catch { return { pagePath: "/", questionKey: null }; }
}

export type SupportSubmission = { id: string; subject: string; description: string; category: SupportCategory; language: SupportLanguage; pagePath: string; questionKey: string | null };
export type SupportTransport = {
  saveReport(input: SupportSubmission): Promise<void>;
  reserveFile(reportId: string, item: SupportFile): Promise<string>;
  uploadFile(path: string, item: SupportFile): Promise<void>;
  removeReservation(fileId: string): Promise<void>;
};
export type SupportSubmissionResult = { reportSaved: boolean; files: SupportFile[]; failedFiles: number; error?: unknown };

/** A successful RPC response is not enough: false means the server refused to remove the file reservation. */
export async function removeSupportReservation(remove: () => PromiseLike<{ data: unknown; error: unknown }>): Promise<void> {
  const { data, error } = await remove();
  if (error) throw error;
  if (data !== true) throw new Error("Support attachment removal was not confirmed");
}

/** A stable report ID makes an uncertain network response retryable. Successful files are never uploaded twice. */
export async function sendSupportReport(
  transport: SupportTransport, input: SupportSubmission, items: SupportFile[],
  options: { alreadySaved?: boolean; isCurrent?: () => boolean; onProgress?: (items: SupportFile[]) => void } = {},
): Promise<SupportSubmissionResult> {
  const files = items.map(item => ({ ...item }));
  const current = options.isCurrent ?? (() => true);
  let reportSaved = !!options.alreadySaved;
  try {
    if (!current()) return { reportSaved, files, failedFiles: files.filter(item => !item.uploaded).length };
    if (!reportSaved) { await transport.saveReport(input); reportSaved = true; }
    for (const item of files) {
      if (!current()) break;
      if (item.uploaded) continue;
      try {
        item.storagePath = await transport.reserveFile(input.id, item);
        if (!current()) break;
        await transport.uploadFile(item.storagePath, item);
        item.uploaded = true;
      } catch {
        // Removal is server-guarded: an existing object can never lose its reservation here.
        if (current()) {
          try { await transport.removeReservation(item.id); } catch { /* Preserve the stable ID for retry. */ }
        }
      }
      if (current()) options.onProgress?.(files.map(file => ({ ...file })));
    }
    return { reportSaved, files, failedFiles: files.filter(item => !item.uploaded).length };
  } catch (error) { return { reportSaved, files, failedFiles: files.filter(item => !item.uploaded).length, error }; }
}

export function supportErrorMessage(error: unknown, he: boolean): string {
  const code = error instanceof SupportValidationError ? error.code : "";
  const copy: Record<string, [string, string]> = {
    file_count: ["אפשר לצרף עד 5 קבצים.", "Attach up to 5 files."],
    file_size: ["כל קובץ צריך להיות בגודל של עד 5 מגה־בייט ולא ריק.", "Each file must be non-empty and no larger than 5 MiB."],
    total_size: ["אפשר לצרף עד 15 מגה־בייט בסך הכול.", "Attachments may total up to 15 MiB."],
    file_name: ["שם הקובץ צריך להיות באורך של עד 180 תווים, בלי קווים נטויים או תווי בקרה. שנו את השם ונסו שוב.", "Use a file name of up to 180 characters without slashes or control characters. Rename it and retry."],
    file_type: ["אפשר לצרף תמונות PNG, JPG או WebP, מסמכי PDF וקובצי טקסט. סוג הקובץ חייב להתאים לסיומת.", "Use PNG, JPG, WebP, PDF or plain text. The file type must match its extension."],
    file_contents: ["אחד הקבצים אינו תואם לסוג שלו או אינו תקין. נסו לייצא אותו מחדש.", "A file does not match its type or is invalid. Export it again and retry."],
    subject: ["כתבו כותרת באורך של 3 עד 160 תווים.", "Write a subject of 3 to 160 characters."],
    description: ["פרטו את הבעיה ב־20 עד 6,000 תווים כדי שנוכל לבדוק אותה.", "Describe the issue in 20 to 6,000 characters so we can investigate."],
  };
  if (copy[code]) return copy[code][he ? 0 : 1];
  const message = typeof error === "object" && error && "message" in error ? String(error.message) : "";
  if (/daily|rate.limit|too.many|5 reports/i.test(message)) return he ? "הגעתם למכסת 5 הדיווחים היומית. נסו שוב מחר." : "You reached the daily limit of 5 reports. Try again tomorrow.";
  if (/quota|storage.limit/i.test(message)) return he ? "מכסת הקבצים בחשבון מלאה. אפשר לשלוח את הדיווח בלי קבצים נוספים." : "Your attachment storage is full. You can submit the report without more files.";
  return he ? "הדיווח לא נשלח. הטיוטה נשמרה בחלון הזה; בדקו את החיבור ונסו שוב." : "The report was not sent. Your draft is kept in this window; check your connection and retry.";
}
