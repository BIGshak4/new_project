export const INBOX_OPEN_EVENT = "jobrun:open-inbox";
export const INBOX_REFRESH_EVENT = "jobrun:refresh-inbox";
export type InboxLanguage = "he" | "en";
export type InboxKind = "announcement" | "support";
export type InboxItem = {
  id: string; kind: InboxKind; title: string; body: string; language: InboxLanguage;
  report_id?: string; status?: string; created_at: string; read_at: string | null;
};
export type InboxFeed = { items: InboxItem[]; total: number; unread_count: number };
export type MySupportReport = {
  id: string; subject: string; description: string; category: string; language: InboxLanguage;
  page_path: string; question_key: string | null; status: string; resolution: string | null;
  created_at: string; updated_at: string; unread_count: number;
};
export type MySupportFile = { id: string; report_id: string; storage_path: string; name: string; mime_type: string; size_bytes: number; created_at: string; uploaded: boolean };
export type MySupportDetail = { report: MySupportReport; files: MySupportFile[]; updates: InboxItem[] };
export type MySupportReports = { reports: MySupportReport[]; total: number };
export type InboxRpc = (name: string, args?: Record<string, unknown>) => PromiseLike<{ data: unknown; error: unknown }>;

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid inbox response");
  return value as Record<string, unknown>;
}
function count(value: unknown) { if (typeof value !== "number" || !Number.isFinite(value) || value < 0) throw new Error("Invalid inbox count"); return value; }
async function call(rpc: InboxRpc, name: string, args?: Record<string, unknown>) {
  const { data, error } = await rpc(name, args);
  if (error) throw error;
  return object(data);
}
export function userInboxApi(rpc: InboxRpc) {
  return {
    async feed(language: InboxLanguage, kind: InboxKind | "all" = "all", page = 1): Promise<InboxFeed> {
      const data = await call(rpc, "jr_user_inbox", { p_kind: kind, p_page: page, p_page_size: 20, p_language: language });
      if (!Array.isArray(data.items)) throw new Error("Invalid inbox items");
      return { items: data.items as InboxItem[], total: count(data.total), unread_count: count(data.unread_count) };
    },
    async reports(page = 1): Promise<MySupportReports> {
      const data = await call(rpc, "jr_my_support_reports", { p_page: page, p_page_size: 20 });
      if (!Array.isArray(data.reports)) throw new Error("Invalid support reports");
      return { reports: data.reports as MySupportReport[], total: count(data.total) };
    },
    async detail(id: string): Promise<MySupportDetail> {
      const data = await call(rpc, "jr_my_support_detail", { p_id: id });
      if (!data.report || !Array.isArray(data.files) || !Array.isArray(data.updates)) throw new Error("Invalid support detail");
      return data as MySupportDetail;
    },
    async markRead(item: Pick<InboxItem, "kind" | "id">) {
      const data = await call(rpc, "jr_mark_inbox_read", { p_kind: item.kind, p_id: item.id });
      if (data.kind !== item.kind || data.id !== item.id || typeof data.read_at !== "string") throw new Error("Read state was not confirmed");
      return data.read_at;
    },
    async markAllRead() { const data = await call(rpc, "jr_mark_all_inbox_read"); return count(data.marked); },
  };
}

/** Every response belongs to an account and the latest request for that specific channel. */
export class InboxRequests {
  private owner: string | null = null;
  private revision = 0;
  private channels = new Map<string, number>();
  bind(owner: string | null) {
    if (owner !== this.owner) { this.owner = owner; this.revision++; this.channels.clear(); }
  }
  start(channel: string) {
    const owner = this.owner, revision = this.revision;
    const sequence = (this.channels.get(channel) ?? 0) + 1;
    this.channels.set(channel, sequence);
    return () => !!owner && this.owner === owner && this.revision === revision && this.channels.get(channel) === sequence;
  }
  invalidate() { this.revision++; this.channels.clear(); }
}

/** Write acknowledgements may arrive after navigation. Always refresh the current view, never the captured old one. */
export class InboxRefresh {
  private latest: () => Promise<void> = async () => {};
  set(refresh: () => Promise<void>) { this.latest = refresh; }
  async run() { await this.latest(); }
}

export function openUserInbox(reportId?: string) {
  window.dispatchEvent(new CustomEvent(INBOX_OPEN_EVENT, { detail: { reportId } }));
}

export function supportStatus(status: string, he: boolean) {
  const labels: Record<string, [string, string]> = {
    new: ["התקבלה", "Received"], open: ["פתוחה", "Open"], in_progress: ["בטיפול", "In progress"],
    waiting: ["ממתינה לפרטים", "Waiting for details"], waiting_for_user: ["ממתינה לפרטים", "Waiting for details"],
    resolved: ["טופלה", "Resolved"], closed: ["נסגרה", "Closed"],
  };
  return labels[status]?.[he ? 0 : 1] ?? (he ? "בבדיקה" : "Under review");
}
