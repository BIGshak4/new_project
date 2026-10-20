"use client";

import { createContext, useCallback, useContext, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { ArrowLeft, Bell, CheckCheck, ChevronLeft, ChevronRight, Download, LoaderCircle, MessageSquareText, RefreshCw, X } from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { observeAuthUser } from "../lib/auth-access";
import { lockBodyScroll } from "../lib/body-scroll-lock";
import { SUPPORT_OPEN_EVENT } from "../lib/support-report";
import { INBOX_OPEN_EVENT, INBOX_REFRESH_EVENT, InboxRefresh, InboxRequests, supportStatus, userInboxApi, type InboxFeed, type InboxItem, type InboxLanguage, type MySupportDetail, type MySupportFile, type MySupportReports } from "../lib/user-inbox";
import { BidiText } from "./bidi-text";
import styles from "./user-inbox.module.css";

const api = userInboxApi((name, args) => supabase.rpc(name, args));
type InboxContextValue = { user: User | null; unread: number; open: (reportId?: string) => void; refreshBadge: () => Promise<void> };
const InboxContext = createContext<InboxContextValue | null>(null);

export function UserInboxProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [lang, setLang] = useState<InboxLanguage>("he");
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [requestedReport, setRequestedReport] = useState<string | undefined>();
  const requests = useRef(new InboxRequests());
  const currentOwner = useRef<string | null>(null);

  useEffect(() => observeAuthUser(supabase.auth, next => {
    const id = next?.id ?? null;
    if (currentOwner.current !== id) {
      requests.current.bind(id); setUnread(0); setOpen(false); setRequestedReport(undefined);
      currentOwner.current = id;
    }
    setUser(next); setReady(true);
  }), []);
  useEffect(() => {
    const sync = () => setLang(document.documentElement.lang.startsWith("en") ? "en" : "he");
    sync(); const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    return () => observer.disconnect();
  }, []);

  const refreshBadge = useCallback(async () => {
    if (!user || document.visibilityState !== "visible") return;
    const current = requests.current.start("badge");
    try {
      const result = await api.feed(lang);
      if (current()) setUnread(result.unread_count);
    } catch { /* Keep the last known badge; the panel provides a visible retry state. */ }
  }, [user?.id, lang]);

  useEffect(() => {
    if (!user) return;
    void refreshBadge();
    const refresh = () => { if (document.visibilityState === "visible") void refreshBadge(); };
    const timer = window.setInterval(refresh, 60_000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    window.addEventListener(INBOX_REFRESH_EVENT, refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); window.removeEventListener(INBOX_REFRESH_EVENT, refresh); };
  }, [user?.id, refreshBadge]);

  const launch = useCallback((reportId?: string) => { setRequestedReport(reportId); setOpen(true); }, []);
  useEffect(() => {
    const openInbox = (event: Event) => {
      const id = (event as CustomEvent<{ reportId?: unknown }>).detail?.reportId;
      launch(typeof id === "string" && id.length <= 100 ? id : undefined);
    };
    const closeInbox = () => setOpen(false);
    window.addEventListener(INBOX_OPEN_EVENT, openInbox);
    window.addEventListener(SUPPORT_OPEN_EVENT, closeInbox);
    return () => { window.removeEventListener(INBOX_OPEN_EVENT, openInbox); window.removeEventListener(SUPPORT_OPEN_EVENT, closeInbox); requests.current.invalidate(); };
  }, [launch]);

  return <InboxContext.Provider value={{ user, unread, open: launch, refreshBadge }}>
    {children}
    <InboxPanel key={user?.id ?? "guest"} open={open} ready={ready} user={user} lang={lang} requestedReport={requestedReport} onClose={() => setOpen(false)} refreshBadge={refreshBadge} />
  </InboxContext.Provider>;
}

export function UserInboxButton({ lang }: { lang: InboxLanguage }) {
  const inbox = useContext(InboxContext);
  const he = lang === "he";
  if (!inbox) return null;
  return <button type="button" data-jobrun-inbox-trigger className={styles.trigger} onClick={() => inbox.open()} aria-haspopup="dialog">
    <Bell size={17} aria-hidden="true" /><span>{he ? "עדכונים ופניות" : "Updates & support"}</span>
    {!!inbox.user && inbox.unread > 0 && <span className={styles.badge} aria-label={he ? `${inbox.unread} עדכונים שלא נקראו` : `${inbox.unread} unread updates`}>{inbox.unread > 99 ? "99+" : inbox.unread}</span>}
  </button>;
}

function InboxPanel({ open, ready, user, lang, requestedReport, onClose, refreshBadge }: { open: boolean; ready: boolean; user: User | null; lang: InboxLanguage; requestedReport?: string; onClose: () => void; refreshBadge: () => Promise<void> }) {
  const he = lang === "he";
  const [tab, setTab] = useState<"updates" | "reports">("updates");
  const [feed, setFeed] = useState<InboxFeed | null>(null);
  const [reports, setReports] = useState<MySupportReports | null>(null);
  const [page, setPage] = useState(1);
  const [announcement, setAnnouncement] = useState<InboxItem | null>(null);
  const [reportId, setReportId] = useState<string | null>(null);
  const [detail, setDetail] = useState<MySupportDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [marking, setMarking] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const requests = useRef(new InboxRequests());
  const viewing = useRef<Set<string>>(new Set());
  const currentRefresh = useRef(new InboxRefresh());
  const active = useRef(false); active.current = open;
  const id = useId();

  useEffect(() => { requests.current.bind(user?.id ?? null); return () => requests.current.invalidate(); }, [user?.id]);
  useEffect(() => {
    if (open && !dialog.current?.open) {
      opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      dialog.current?.showModal(); heading.current?.focus();
    } else if (!open && dialog.current?.open) dialog.current.close();
  }, [open]);
  useEffect(() => open ? lockBodyScroll() : undefined, [open]);
  useEffect(() => {
    if (!open) { requests.current.invalidate(); viewing.current.clear(); setLoading(false); setMarking(false); setDownloading(null); return; }
    setError(""); setActionError(""); setAnnouncement(null); setDetail(null); setReportId(requestedReport ?? null); setPage(1);
    if (requestedReport) setTab("reports");
  }, [open, requestedReport]);

  const load = useCallback(async () => {
    if (!user || !open || document.visibilityState !== "visible") return;
    const current = requests.current.start("content");
    setLoading(true); setError("");
    try {
      if (reportId) { const result = await api.detail(reportId); if (current()) setDetail(result); }
      else if (tab === "reports") { const result = await api.reports(page); if (current()) setReports(result); }
      else { const result = await api.feed(lang, "all", page); if (current()) setFeed(result); }
    } catch { if (current()) setError(he ? "לא הצלחנו לטעון את העדכונים. נסו לרענן." : "We could not load your updates. Please refresh and retry."); }
    finally { if (current()) setLoading(false); }
  }, [user?.id, open, reportId, tab, page, lang, he]);
  currentRefresh.current.set(load);

  useEffect(() => {
    if (!user || !open) return;
    void load();
    const refresh = () => { if (document.visibilityState === "visible") void load(); };
    const timer = window.setInterval(refresh, 60_000);
    window.addEventListener("focus", refresh); document.addEventListener("visibilitychange", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); };
  }, [load, user?.id, open]);

  async function markRead(item: InboxItem) {
    if (item.read_at || !user || !active.current || document.visibilityState !== "visible" || viewing.current.has(item.id)) return;
    viewing.current.add(item.id);
    const current = requests.current.start(`read:${item.id}`);
    try {
      const readAt = await api.markRead(item);
      if (!current() || !active.current) return;
      setFeed(previous => previous ? { ...previous, items: previous.items.map(message => message.id === item.id && message.kind === item.kind ? { ...message, read_at: readAt } : message) } : previous);
      setDetail(previous => previous ? { ...previous, updates: previous.updates.map(message => message.id === item.id ? { ...message, read_at: readAt } : message) } : previous);
      await Promise.all([currentRefresh.current.run(), refreshBadge()]);
    } catch { if (current()) { viewing.current.delete(item.id); setActionError(he ? "העדכון עדיין מסומן כלא נקרא. אפשר לרענן ולנסות שוב." : "This update is still unread. Refresh and try again."); } }
  }

  useEffect(() => {
    if (!open || !detail || loading || !dialog.current) return;
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        const message = detail.updates.find(update => update.id === (entry.target as HTMLElement).dataset.inboxUpdate);
        if (message) void markRead(message);
      }
    }, { root: dialog.current, threshold: .5 });
    dialog.current.querySelectorAll("[data-inbox-update]").forEach(element => observer.observe(element));
    return () => observer.disconnect();
  }, [detail, open, loading]);

  function close() {
    dialog.current?.close(); onClose();
    const focus = opener.current;
    if (focus?.isConnected && focus.getClientRects().length && !focus.closest("dialog:not([open])")) focus.focus();
    else document.querySelector<HTMLButtonElement>("[data-jobrun-inbox-trigger]")?.focus();
  }
  function chooseTab(next: "updates" | "reports") { setTab(next); setPage(1); setReportId(null); setDetail(null); setAnnouncement(null); setError(""); setActionError(""); }
  function view(item: InboxItem) {
    if (item.kind === "support" && item.report_id) { setTab("reports"); setReportId(item.report_id); setDetail(null); }
    else { setAnnouncement(item); void markRead(item); }
  }
  function reportProblem() { close(); window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT)); }
  async function markAll() {
    if (marking || !user) return;
    const current = requests.current.start("mark-all");
    setMarking(true); setActionError("");
    try {
      await api.markAllRead();
      if (current()) { await Promise.all([currentRefresh.current.run(), refreshBadge()]); }
    } catch { if (current()) setActionError(he ? "לא הצלחנו לסמן את העדכונים. נסו שוב." : "We could not mark updates as read. Please retry."); }
    finally { if (current()) setMarking(false); }
  }
  async function download(file: MySupportFile) {
    if (downloading || !file.uploaded) return;
    const current = requests.current.start("download");
    setDownloading(file.id); setActionError("");
    try {
      const { data, error: failure } = await supabase.storage.from("jr-support-files").download(file.storage_path);
      if (failure || !data) throw failure;
      if (!current() || !active.current) return;
      const url = URL.createObjectURL(data), link = document.createElement("a");
      link.href = url; link.download = file.name; document.body.append(link); link.click(); link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { if (current()) setActionError(he ? "לא הצלחנו להוריד את הקובץ. נסו שוב." : "We could not download the file. Please retry."); }
    finally { if (current()) setDownloading(null); }
  }
  function date(value: string) { const date = new Date(value); return Number.isNaN(date.getTime()) ? "" : new Intl.DateTimeFormat(he ? "he-IL" : "en-GB", { dateStyle: "medium", timeStyle: "short" }).format(date); }
  const total = tab === "reports" ? reports?.total ?? 0 : feed?.total ?? 0;
  const isDetail = !!reportId || !!announcement;

  return <dialog ref={dialog} data-jobrun-inbox-dialog className={styles.dialog} dir={he ? "rtl" : "ltr"} lang={lang} aria-labelledby={`${id}-title`} onCancel={close} onClose={onClose}>
    <header className={styles.header}><div><h2 ref={heading} tabIndex={-1} id={`${id}-title`}>{he ? "עדכונים ופניות" : "Updates & support"}</h2><p>{he ? "חדשות מ־JobRun והפניות שלכם, במקום אחד." : "News from JobRun and your support requests, together."}</p></div><button type="button" className={styles.icon} onClick={close} aria-label={he ? "סגירת עדכונים ופניות" : "Close updates and support"}><X size={21} aria-hidden="true" /></button></header>
    {!ready ? <p className={styles.empty} role="status">{he ? "בודקים את החשבון…" : "Checking your account…"}</p> : !user ? <section className={styles.empty}><Bell size={29} aria-hidden="true" /><h3>{he ? "העדכונים מחכים לכם בחשבון" : "Your updates live in your account"}</h3><p>{he ? "התחברו כדי לקרוא עדכונים ולעקוב אחרי הפניות שלכם. סגרו את החלון והתחברו לאתר." : "Sign in to read updates and follow your support requests. Close this window and sign in to the site."}</p><button type="button" onClick={close}>{he ? "בחזרה לאתר" : "Back to the site"}</button></section> : <>
      <nav className={styles.tabs} aria-label={he ? "תצוגות עדכונים ופניות" : "Inbox views"}><button type="button" aria-current={tab === "updates" ? "page" : undefined} onClick={() => chooseTab("updates")}><Bell size={16} aria-hidden="true" />{he ? "כל העדכונים" : "All updates"}</button><button type="button" aria-current={tab === "reports" ? "page" : undefined} onClick={() => chooseTab("reports")}><MessageSquareText size={16} aria-hidden="true" />{he ? "הפניות שלי" : "My requests"}</button></nav>
      <div className={styles.toolbar}><button type="button" onClick={() => { void load(); void refreshBadge(); }} disabled={loading}><RefreshCw size={15} aria-hidden="true" />{he ? "רענון" : "Refresh"}</button><button type="button" disabled={marking || loading} onClick={() => void markAll()}><CheckCheck size={16} aria-hidden="true" />{marking ? he ? "מסמנים…" : "Marking…" : he ? "סימון הכול כנקרא" : "Mark all as read"}</button><button type="button" onClick={reportProblem}>{he ? "דיווח על בעיה" : "Report a problem"}</button></div>
      <main className={styles.body} aria-busy={loading}>
        {actionError && <p className={styles.error} role="alert">{actionError}</p>}
        {error && <p className={styles.error} role="alert">{error}</p>}
        {loading && <p className={styles.loading} role="status"><LoaderCircle size={17} aria-hidden="true" />{he ? "טוענים…" : "Loading…"}</p>}
        {isDetail && <button type="button" className={styles.back} onClick={() => { setReportId(null); setDetail(null); setAnnouncement(null); }}><ArrowLeft size={16} aria-hidden="true" />{he ? "בחזרה לרשימה" : "Back to list"}</button>}
        {announcement && <article className={styles.article}><div className={styles.meta}><span>{he ? "עדכון מהצוות" : "Team update"}</span><time dateTime={announcement.created_at}>{date(announcement.created_at)}</time></div><h3 dir="auto"><BidiText>{announcement.title}</BidiText></h3>{announcement.language !== lang && <p className={styles.fallback}>{he ? "העדכון זמין כרגע באנגלית." : "This update is currently available in Hebrew."}</p>}<p className={styles.prose} dir="auto"><BidiText>{announcement.body}</BidiText></p></article>}
        {reportId && detail && detail.report.id === reportId && <article className={styles.article}>
          <div className={styles.meta}><span className={styles.status}>{supportStatus(detail.report.status, he)}</span><time dateTime={detail.report.created_at}>{date(detail.report.created_at)}</time></div>
          <h3 dir="auto"><BidiText>{detail.report.subject}</BidiText></h3><p className={styles.reference}>{he ? "מספר פנייה" : "Reference"}: <bdi dir="ltr">{detail.report.id}</bdi></p>
          {detail.report.resolution && <section className={styles.resolution}><h4>{he ? "סיכום הטיפול" : "Resolution"}</h4><p className={styles.prose} dir="auto"><BidiText>{detail.report.resolution}</BidiText></p></section>}
          <h4>{he ? "הדיווח ששלחתם" : "Your original report"}</h4><p className={styles.prose} dir="auto"><BidiText>{detail.report.description}</BidiText></p>
          {detail.files.length > 0 && <section className={styles.files}><h4>{he ? "הקבצים שצירפתם" : "Your attachments"}</h4><ul>{detail.files.map(file => <li key={file.id}><span dir="auto"><BidiText>{file.name}</BidiText><small>{(file.size_bytes / 1024 / 1024).toFixed(2)} MiB{!file.uploaded ? he ? " · ההעלאה לא הושלמה" : " · upload incomplete" : ""}</small></span>{file.uploaded && <button type="button" disabled={!!downloading} onClick={() => void download(file)} aria-label={`${he ? "הורדת" : "Download"} ${file.name}`}><Download size={16} aria-hidden="true" />{downloading === file.id ? he ? "מורידים…" : "Downloading…" : he ? "הורדה" : "Download"}</button>}</li>)}</ul></section>}
          <section className={styles.timeline}><h4>{he ? "עדכונים מהצוות" : "Updates from the team"}</h4>{!detail.updates.length && <p className={styles.muted}>{he ? "הפנייה התקבלה. כשיהיה עדכון, הוא יופיע כאן." : "Your request was received. Updates will appear here when available."}</p>}{[...detail.updates].reverse().map(item => <section key={item.id} className={styles.update}><div className={styles.meta}><time dateTime={item.created_at}>{date(item.created_at)}</time>{!item.read_at && <span className={styles.unread}>{he ? "חדש" : "New"}</span>}</div><h5 dir="auto" data-inbox-update={item.id}><BidiText>{item.title}</BidiText></h5><p className={styles.prose} dir="auto"><BidiText>{item.body}</BidiText></p></section>)}</section>
        </article>}
        {!isDetail && !loading && tab === "updates" && feed && (!feed.items.length ? <Empty he={he} kind="updates" /> : <ul className={styles.list}>{feed.items.map(item => <li key={`${item.kind}-${item.id}`}><button type="button" onClick={() => view(item)} className={styles.row}><div className={styles.rowTop}><span className={styles.meta}>{item.kind === "support" ? he ? "עדכון לפנייה" : "Support update" : he ? "עדכון מהצוות" : "Team update"}</span>{!item.read_at && <span className={styles.unread}>{he ? "חדש" : "New"}</span>}</div><strong dir="auto"><BidiText>{item.title}</BidiText></strong><span className={styles.preview} dir="auto"><BidiText>{item.body}</BidiText></span><time dateTime={item.created_at}>{date(item.created_at)}</time></button></li>)}</ul>)}
        {!isDetail && !loading && tab === "reports" && reports && (!reports.reports.length ? <Empty he={he} kind="reports" /> : <ul className={styles.list}>{reports.reports.map(report => <li key={report.id}><button type="button" className={styles.row} onClick={() => { setReportId(report.id); setDetail(null); }}><div className={styles.rowTop}><span className={styles.status}>{supportStatus(report.status, he)}</span>{report.unread_count > 0 && <span className={styles.unread}>{he ? `${report.unread_count} עדכונים חדשים` : `${report.unread_count} new updates`}</span>}</div><strong dir="auto"><BidiText>{report.subject}</BidiText></strong><span className={styles.preview} dir="auto"><BidiText>{report.description}</BidiText></span><time dateTime={report.updated_at}>{date(report.updated_at)}</time></button></li>)}</ul>)}
        {!isDetail && total > 20 && <nav className={styles.pagination} aria-label={he ? "עמודי עדכונים" : "Inbox pages"}><button type="button" disabled={page === 1 || loading} onClick={() => setPage(old => old - 1)}><ChevronRight size={16} aria-hidden="true" />{he ? "הקודם" : "Previous"}</button><span>{he ? `עמוד ${page} מתוך ${Math.ceil(total / 20)}` : `Page ${page} of ${Math.ceil(total / 20)}`}</span><button type="button" disabled={page * 20 >= total || loading} onClick={() => setPage(old => old + 1)}>{he ? "הבא" : "Next"}<ChevronLeft size={16} aria-hidden="true" /></button></nav>}
      </main>
    </>}
  </dialog>;
}

function Empty({ he, kind }: { he: boolean; kind: "updates" | "reports" }) {
  return <section className={styles.empty}><Bell size={27} aria-hidden="true" /><h3>{kind === "updates" ? he ? "אתם מעודכנים" : "You are up to date" : he ? "עדיין אין פניות" : "No requests yet"}</h3><p>{kind === "updates" ? he ? "עדכונים מהצוות ותשובות לפניות יופיעו כאן." : "Team announcements and replies to your requests will appear here." : he ? "אחרי שליחת דיווח על בעיה תוכלו לעקוב כאן אחרי הטיפול." : "After reporting a problem, you can follow its progress here."}</p></section>;
}
