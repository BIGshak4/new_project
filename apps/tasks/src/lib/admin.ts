import { supabase } from "./supabase";

export type PlanTier = "free" | "pro" | "team";
export type AdminUser = {
  id: string;
  email: string;
  display_name: string | null;
  created_at: string;
  last_sign_in_at: string | null;
  email_confirmed: boolean;
  plan_tier: PlanTier;
  pilot_access: boolean;
  is_founder: boolean;
};
export type Assignee = { id: string; email: string; display_name: string | null };
export type SupportStatus = "open" | "in_progress" | "waiting" | "resolved" | "closed";
export type SupportPriority = "low" | "normal" | "high";
export type SupportReport = {
  id: string;
  subject: string;
  description: string;
  category: string;
  language: string;
  page_path: string | null;
  question_key: string | null;
  status: SupportStatus;
  priority: SupportPriority;
  assigned_to: string | null;
  internal_notes: string;
  resolution: string;
  version: number;
  created_at: string;
  updated_at: string;
  reporter_email: string | null;
  reporter_name: string | null;
  file_count?: number;
};
export type SupportFile = {
  id: string;
  storage_path: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  uploaded: boolean;
};
export type SupportEvent = {
  id: string;
  actor_email: string | null;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
};
export type SupportDetail = {
  report: SupportReport;
  files: SupportFile[];
  events: SupportEvent[];
  assignees: Assignee[];
  updates?: PublicSupportUpdate[];
};
export type PublicSupportUpdate = {
  id: string;
  kind: "support";
  title: string;
  body: string;
  language: string;
  report_id: string;
  status: SupportStatus;
  created_at: string;
  read_at: string | null;
};
export type AnnouncementStatus = "draft" | "published" | "archived";
export type Announcement = {
  id: string;
  title_he: string;
  body_he: string;
  title_en: string | null;
  body_en: string | null;
  status: AnnouncementStatus;
  version: number;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};
export const announcementStatuses: Record<AnnouncementStatus, string> = {
  draft: "טיוטה", published: "פורסם למשתמשים", archived: "בארכיון",
};
export type QuestionReport = {
  id: string;
  question_id: string;
  reason: string;
  note: string | null;
  language: string;
  context: unknown;
  created_at: string;
  resolved_at: string | null;
  reporter_email: string | null;
  reporter_name: string | null;
  question_key: string | null;
  question_title_he: string | null;
  question_title_en: string | null;
};

export const supportStatuses: Record<SupportStatus, string> = {
  open: "חדש",
  in_progress: "בטיפול",
  waiting: "ממתין להמשך",
  resolved: "נפתר",
  closed: "נסגר",
};
export const supportPriorities: Record<SupportPriority, string> = {
  low: "נמוכה", normal: "רגילה", high: "גבוהה",
};
export const supportCategories: Record<string, string> = {
  bug: "תקלה טכנית", question: "תוכן או שאלה", account: "חשבון וכניסה",
  feedback: "הצעה לשיפור", other: "אחר",
};
export const planNames: Record<PlanTier, string> = { free: "Free", pro: "Pro", team: "Team" };

export async function adminRpc<T>(name: string, args: Record<string, unknown> = {}): Promise<T> {
  const { data, error } = await supabase.rpc(name, args);
  if (error) throw error;
  if (data == null) throw new Error("empty_response");
  return data as T;
}

export function isConflict(error: unknown) {
  const value = error as { code?: string; message?: string };
  return value?.code === "40001" || value?.code === "PT409" || value?.message?.includes("conflict_reload") === true;
}

export function adminError(error: unknown, fallback = "הפעולה לא הושלמה. בדקו את החיבור ונסו שוב.") {
  const value = error as { code?: string; message?: string };
  if (isConflict(error)) return "הנתונים השתנו בחלון אחר. הטיוטה נשמרה כאן; טענו את העדכון והשוו לפני שמירה נוספת.";
  if (value?.code === "42501") return "אין הרשאת ניהול לפעולה הזאת. נסו להתחבר מחדש עם חשבון מייסד.";
  if (value?.message?.includes("founder_access_protected")) return "אי אפשר להסיר גישת מייסד דרך המסך הזה.";
  if (value?.message?.includes("report_unavailable")) return "הדיווח אינו זמין. חזרו לרשימה ורעננו אותה.";
  if (value?.message?.includes("announcement_immutable")) return "אי אפשר לשנות ניסוח שכבר פורסם. אפשר להעביר אותו לארכיון וליצור עדכון חדש.";
  if (value?.code === "22023") return "הפרטים לא תקינים. בדקו את שדות החובה, אורכי הטקסט והתרגום ונסו שוב.";
  return fallback;
}

export function formatDate(value: string | null, includeTime = false) {
  if (!value) return "טרם נרשם";
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "לא זמין";
  return new Intl.DateTimeFormat("he-IL", {
    day: "numeric", month: "short", year: "numeric",
    ...(includeTime ? { hour: "2-digit", minute: "2-digit" } as const : {}),
  }).format(date);
}

export function fileSize(bytes: number) {
  return bytes < 1024 * 1024 ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function practiceLink(questionKey: string) {
  return `https://jobrun-practice.netlify.app/?question=${encodeURIComponent(questionKey)}`;
}
