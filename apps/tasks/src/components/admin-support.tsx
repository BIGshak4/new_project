"use client";
import { useEffect, useRef, useState } from "react";
import { Search, RefreshCw, Paperclip, Download, ArrowRight, Check, ExternalLink } from "lucide-react";
import { supabase } from "../lib/supabase";
import {
  adminError, adminRpc, fileSize, formatDate, isConflict, practiceLink, supportCategories, supportPriorities, supportStatuses,
  type Assignee, type QuestionReport, type SupportDetail, type SupportFile, type SupportPriority, type SupportReport, type SupportStatus,
} from "../lib/admin";
import { AdminError, AdminLoading, Pagination } from "./admin-shared";

type SupportList = { reports: SupportReport[]; total: number; assignees: Assignee[] };
type LegacyList = { reports: QuestionReport[]; total: number };
type Handling = Pick<SupportReport, "status" | "priority" | "assigned_to" | "internal_notes" | "resolution">;

function handling(report: SupportReport): Handling {
  return { status: report.status, priority: report.priority, assigned_to: report.assigned_to, internal_notes: report.internal_notes || "", resolution: report.resolution || "" };
}

export function AdminSupport({ active }: { active: boolean }) {
  const [tab, setTab] = useState<"support" | "questions">("support");
  return <section aria-labelledby="admin-support-title" className="admin-section">
    <div className="page-heading"><div><h1 id="admin-support-title">דיווחי תקלות</h1><p>מה המשתמשים חוו, מי מטפל ומה כבר נפתר.</p></div></div>
    <div className="admin-tabs" aria-label="סוג הדיווחים">
      <button type="button" aria-pressed={tab === "support"} className={tab === "support" ? "active" : ""} onClick={() => setTab("support")}>פניות ותקלות באתר</button>
      <button type="button" aria-pressed={tab === "questions"} className={tab === "questions" ? "active" : ""} onClick={() => setTab("questions")}>דיווחים על שאלות</button>
    </div>
    <div hidden={tab !== "support"}><SupportQueue active={active && tab === "support"} /></div>
    <div hidden={tab !== "questions"}><QuestionReports active={active && tab === "questions"} /></div>
  </section>;
}

function SupportQueue({ active }: { active: boolean }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [result, setResult] = useState<SupportList>({ reports: [], total: 0, assignees: [] });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editorDirty, setEditorDirty] = useState(false);
  const requestRef = useRef(0);

  useEffect(() => {
    if (!active) return;
    const request = ++requestRef.current;
    setBusy(true); setError("");
    void adminRpc<SupportList>("jr_admin_support_list", { p_query: query, p_status: status, p_page: page, p_page_size: 25 }).then(
      (data) => { if (requestRef.current === request) setResult(data); },
      (err: unknown) => { if (requestRef.current === request) setError(adminError(err, "לא הצלחנו לטעון את הפניות. נסו שוב.")); },
    ).finally(() => { if (requestRef.current === request) setBusy(false); });
    return () => { requestRef.current += 1; };
  }, [active, query, status, page, reload]);

  return <>
    <form className="toolbar" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); setReload((v) => v + 1); }}>
      <div className="search"><Search size={17} /><input aria-label="חיפוש דיווחי תקלות" placeholder="נושא, תיאור או אימייל של המדווח…" value={search} onChange={(event) => setSearch(event.target.value)} maxLength={200} /></div>
      <select aria-label="סינון פניות לפי מצב" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="all">כל המצבים</option>{Object.entries(supportStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      <button type="submit" disabled={busy}>חיפוש</button>
      <button type="button" disabled={busy} onClick={() => setReload((v) => v + 1)}><RefreshCw size={16} />רענון</button>
      {(query || status !== "all") && <button type="button" onClick={() => { setQuery(""); setSearch(""); setStatus("all"); setPage(1); }}>איפוס סינון</button>}
    </form>
    {error && <AdminError message={error} retry={() => setReload((v) => v + 1)} />}
    <div className={`admin-support-layout ${selectedId ? "has-detail" : ""}`}>
      <div className="admin-queue">
        {busy ? <AdminLoading label="טוענים פניות…" /> : !error && !result.reports.length ? <div className="empty"><h2>{query || status !== "all" ? "לא נמצאו פניות בסינון הזה." : "אין עדיין פניות לטיפול."}</h2><p>{query || status !== "all" ? "שנו את החיפוש או בחרו מצב אחר." : "דיווחים שנשלחים מאתר התרגול ירוכזו כאן, עם ההקשר והקבצים."}</p></div> : <div className="admin-report-list" aria-label="פניות המשתמשים">{result.reports.map((report) => <button type="button" key={report.id} className={`admin-report-row ${selectedId === report.id ? "selected" : ""}`} aria-expanded={selectedId === report.id} onClick={() => {
          if (selectedId !== report.id && editorDirty && !window.confirm("יש שינויים בטיפול שטרם נשמרו. לעבור לפנייה אחרת ולוותר עליהם?")) return;
          setSelectedId(report.id);
        }}>
          <div className="row spread"><span className={`badge support-${report.status}`}>{supportStatuses[report.status]}</span><time className="small muted">{formatDate(report.created_at)}</time></div>
          <h2 dir="auto">{report.subject}</h2>
          <p className="admin-report-preview" dir="auto">{report.description}</p>
          <div className="admin-report-meta"><bdi dir="ltr">{report.reporter_email || "חשבון ללא אימייל"}</bdi><span>עדיפות {supportPriorities[report.priority]}</span>{!!report.file_count && <span><Paperclip size={13} />{report.file_count} קבצים</span>}</div>
        </button>)}</div>}
        <Pagination page={page} total={result.total} busy={busy} onChange={setPage} />
      </div>
      {selectedId && <SupportEditor key={selectedId} reportId={selectedId} onDirty={setEditorDirty} onClose={() => setSelectedId(null)} onSaved={(report) => setResult((old) => ({ ...old, reports: old.reports.map((row) => row.id === report.id ? { ...row, ...report } : row) }))} />}
    </div>
  </>;
}

function SupportEditor({ reportId, onClose, onSaved, onDirty }: { reportId: string; onClose: () => void; onSaved: (report: SupportReport) => void; onDirty: (dirty: boolean) => void }) {
  const [detail, setDetail] = useState<SupportDetail | null>(null);
  const [draft, setDraft] = useState<Handling | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [conflict, setConflict] = useState(false);
  const [latest, setLatest] = useState<SupportDetail | null>(null);
  const [reload, setReload] = useState(0);
  const [fileBusy, setFileBusy] = useState<string | null>(null);
  const dirty = !!detail && !!draft && JSON.stringify(handling(detail.report)) !== JSON.stringify(draft);
  const detailRef = useRef<HTMLElement>(null);
  useEffect(() => { onDirty(dirty); return () => onDirty(false); }, [dirty, onDirty]);
  useEffect(() => { if (!loading) detailRef.current?.scrollIntoView({ block: "nearest" }); }, [loading]);

  useEffect(() => {
    let live = true;
    setLoading(true); setError("");
    void adminRpc<SupportDetail>("jr_admin_support_detail", { p_id: reportId }).then((data) => {
      if (live) { setDetail(data); setDraft(handling(data.report)); }
    }, (err: unknown) => { if (live) setError(adminError(err)); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [reportId, reload]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function update<K extends keyof Handling>(key: K, value: Handling[K]) {
    setDraft((old) => old ? { ...old, [key]: value } : old); setSaved("");
  }
  async function save(event: React.FormEvent) {
    event.preventDefault(); if (!detail || !draft) return;
    setBusy(true); setError(""); setSaved("");
    try {
      const report = await adminRpc<SupportReport>("jr_admin_update_support", {
        p_id: reportId, p_expected_version: detail.report.version, p_status: draft.status, p_priority: draft.priority,
        p_assigned_to: draft.assigned_to, p_internal_notes: draft.internal_notes, p_resolution: draft.resolution,
      });
      setDetail((old) => old ? { ...old, report: { ...old.report, ...report } } : old); setDraft(handling(report)); setConflict(false); setLatest(null);
      setSaved("הטיפול בפנייה נשמר."); onSaved(report);
      // Fetch audit context separately; a failed refresh must not undo a successful save.
      void adminRpc<SupportDetail>("jr_admin_support_detail", { p_id: reportId }).then((data) => setDetail((old) => old ? { ...old, events: data.events, files: data.files, assignees: data.assignees } : old), () => undefined);
    } catch (err) { setConflict(isConflict(err)); setError(adminError(err)); }
    finally { setBusy(false); }
  }
  async function compare() {
    setBusy(true);
    try { setLatest(await adminRpc<SupportDetail>("jr_admin_support_detail", { p_id: reportId })); }
    catch (err) { setError(adminError(err)); }
    finally { setBusy(false); }
  }
  async function download(file: SupportFile) {
    setFileBusy(file.id); setError("");
    try {
      const result = await supabase.storage.from("jr-support-files").createSignedUrl(file.storage_path, 60, { download: file.name });
      if (result.error) throw result.error;
      const link = document.createElement("a");
      link.href = result.data.signedUrl; link.rel = "noopener"; link.download = file.name; link.click();
    } catch { setError("לא הצלחנו להוריד את הקובץ. נסו שוב; קישורי הורדה תקפים לדקה בלבד."); }
    finally { setFileBusy(null); }
  }
  function close() { if (!dirty || window.confirm("יש שינויים בטיפול שטרם נשמרו. לסגור את הפנייה ולוותר עליהם?")) onClose(); }

  return <section ref={detailRef} className="admin-report-detail" aria-labelledby="support-detail-title">
    <button type="button" className="text-button" disabled={busy} onClick={close}><ArrowRight size={16} />סגירת פרטי הפנייה</button>
    {loading ? <AdminLoading label="טוענים את פרטי הפנייה…" /> : !detail || !draft ? <AdminError message={error || "הפנייה לא זמינה."} retry={() => setReload((v) => v + 1)} /> : <>
      <div className="admin-detail-heading"><h2 id="support-detail-title" dir="auto">{detail.report.subject}</h2><span className={`badge support-${detail.report.status}`}>{supportStatuses[detail.report.status]}</span></div>
      <dl className="admin-facts">
        <div><dt>נשלח על ידי</dt><dd>{detail.report.reporter_name || "ללא שם"}<bdi dir="ltr" className="admin-email">{detail.report.reporter_email || "ללא אימייל"}</bdi></dd></div>
        <div><dt>תאריך</dt><dd>{formatDate(detail.report.created_at, true)}</dd></div>
        <div><dt>סוג פנייה</dt><dd>{supportCategories[detail.report.category] || detail.report.category}</dd></div>
        <div><dt>שפת האתר</dt><dd>{detail.report.language === "he" ? "עברית" : detail.report.language === "en" ? "אנגלית" : detail.report.language}</dd></div>
        {detail.report.page_path && <div><dt>מיקום באתר</dt><dd><bdi dir="ltr">{detail.report.page_path}</bdi></dd></div>}
        {detail.report.question_key && <div><dt>שאלה קשורה</dt><dd><a className="admin-inline-link" href={practiceLink(detail.report.question_key)} target="_blank" rel="noreferrer">פתיחת השאלה<ExternalLink size={13} /></a></dd></div>}
      </dl>
      <section className="admin-original"><h3>תיאור הבעיה</h3><p dir="auto">{detail.report.description}</p></section>
      <section className="admin-attachments"><h3><Paperclip size={16} />קבצים מצורפים</h3>{!detail.files.some((file) => file.uploaded) ? <p className="small muted">אין קבצים שהועלו לפנייה.</p> : <ul>{detail.files.filter((file) => file.uploaded).map((file) => <li key={file.id}><button type="button" className="text-button" disabled={fileBusy !== null} onClick={() => void download(file)}><Download size={15} /><span dir="auto">{file.name}</span></button><bdi dir="ltr" className="small muted">{fileSize(file.size_bytes)}</bdi></li>)}</ul>}<p className="small muted">קבצים פרטיים · קישור הורדה תקף לדקה.</p></section>
      <form className="admin-handling" onSubmit={(event) => void save(event)}>
        <h3>טיפול בפנייה</h3>
        <div className="field-grid"><label>מצב<select value={draft.status} disabled={busy} onChange={(event) => update("status", event.target.value as SupportStatus)}>{Object.entries(supportStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>עדיפות<select value={draft.priority} disabled={busy} onChange={(event) => update("priority", event.target.value as SupportPriority)}>{Object.entries(supportPriorities).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div>
        <label>אחראי לטיפול<select value={draft.assigned_to || ""} disabled={busy} onChange={(event) => update("assigned_to", event.target.value || null)}><option value="">ללא אחראי</option>{detail.assignees.map((person) => <option key={person.id} value={person.id}>{person.display_name || person.email}</option>)}</select></label>
        <label>הערות פנימיות<textarea dir="auto" rows={5} maxLength={10000} value={draft.internal_notes} disabled={busy} onChange={(event) => update("internal_notes", event.target.value)} placeholder="מה בדקנו, מה שחזרנו ומה נותר לעשות…" /></label>
        <p className="small muted">ההערות מיועדות לצוות בלבד. לא נשלחת הודעה אוטומטית למשתמש.</p>
        <label>סיכום הטיפול<textarea dir="auto" rows={3} maxLength={5000} value={draft.resolution} disabled={busy} onChange={(event) => update("resolution", event.target.value)} placeholder="מה תוקן או מדוע הפנייה נסגרה?" /></label>
        {error && <AdminError message={error} />}{saved && <p className="status-message" role="status">{saved}</p>}
        {conflict && <div className="admin-conflict"><p>הטיוטה שלכם לא נדרסה. השוו לגרסה שנשמרה בחלון האחר לפני שממשיכים.</p><button type="button" disabled={busy} onClick={() => void compare()}>הצגת הגרסה העדכנית</button>{latest && <><dl className="admin-facts"><div><dt>מצב עדכני</dt><dd>{supportStatuses[latest.report.status]}</dd></div><div><dt>הערות שנשמרו</dt><dd className="admin-preserve" dir="auto">{latest.report.internal_notes || "אין הערות"}</dd></div><div><dt>סיכום שנשמר</dt><dd className="admin-preserve" dir="auto">{latest.report.resolution || "אין סיכום"}</dd></div></dl><button type="button" onClick={() => { setDetail(latest); setLatest(null); setConflict(false); setError(""); setSaved("הגרסה העדכנית נטענה והטיוטה שלכם נשמרה בטופס. מזגו את השינויים ובדקו לפני שמירה."); }}>להמשיך לערוך את הטיוטה שלי על בסיס העדכון</button></>}</div>}
        <div className="row spread"><span className="small muted">גרסה {detail.report.version} · {dirty ? "יש שינויים שלא נשמרו" : "הטיפול מעודכן"}</span><button type="submit" className="primary" disabled={busy || !dirty || conflict}><Check size={16} />{busy ? "שומרים…" : "שמירת הטיפול"}</button></div>
      </form>
      <section className="admin-history"><h3>היסטוריית טיפול</h3>{!detail.events.length ? <p className="small muted">עדיין לא נרשמו פעולות טיפול.</p> : <ol>{detail.events.map((event) => <li key={event.id}><div className="row spread"><strong>{event.action === "report_created" ? "הפנייה נפתחה" : event.action === "report_updated" ? "הטיפול עודכן" : event.action === "file_added" ? "נוסף קובץ" : "עודכן רישום הפנייה"}</strong><time className="small muted">{formatDate(event.created_at, true)}</time></div>{event.actor_email && <bdi dir="ltr" className="small muted">{event.actor_email}</bdi>}<AuditDetails details={event.details} /></li>)}</ol>}</section>
    </>}
  </section>;
}

function AuditDetails({ details }: { details: Record<string, unknown> }) {
  if (!details || !Object.keys(details).length) return null;
  const labels: Record<string, string> = { status_before: "מצב קודם", status_after: "מצב חדש", priority_before: "עדיפות קודמת", priority_after: "עדיפות חדשה", assigned_before: "אחראי קודם", assigned_after: "אחראי חדש", internal_notes_changed: "ההערות הפנימיות השתנו", resolution_changed: "סיכום הטיפול השתנה", version: "גרסה", name: "שם קובץ" };
  return <details className="admin-audit-details"><summary>פרטי השינוי</summary><dl>{Object.entries(details).map(([key, value]) => <div key={key}><dt>{labels[key] || key}</dt><dd dir="auto">{typeof value === "string" ? (supportStatuses[value as SupportStatus] || supportPriorities[value as SupportPriority] || value) : typeof value === "boolean" ? value ? "כן" : "לא" : value == null ? "ללא" : JSON.stringify(value)}</dd></div>)}</dl></details>;
}

function QuestionReports({ active }: { active: boolean }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [resolved, setResolved] = useState(false);
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [result, setResult] = useState<LegacyList>({ reports: [], total: 0 });
  const [busy, setBusy] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const requestRef = useRef(0);
  useEffect(() => {
    if (!active) return;
    const request = ++requestRef.current;
    setBusy(true); setError("");
    void adminRpc<LegacyList>("jr_admin_question_reports", { p_query: query, p_resolved: resolved, p_page: page, p_page_size: 25 }).then((data) => {
      if (requestRef.current === request) setResult(data);
    }, (err: unknown) => { if (requestRef.current === request) setError(adminError(err, "לא הצלחנו לטעון את הדיווחים על שאלות. נסו שוב.")); }).finally(() => { if (requestRef.current === request) setBusy(false); });
    return () => { requestRef.current += 1; };
  }, [active, query, resolved, page, reload]);
  async function resolve(report: QuestionReport) {
    setSaving(report.id); setError(""); setNotice("");
    try { await adminRpc("jr_admin_resolve_question_report", { p_id: report.id, p_resolved: !resolved }); setNotice(resolved ? "הדיווח חזר לטיפול." : "הדיווח סומן כטופל."); setReload((v) => v + 1); }
    catch (err) { setError(adminError(err)); }
    finally { setSaving(null); }
  }
  return <>
    <p className="admin-policy-note">כאן מרוכזים גם הדיווחים שנשלחו דרך האפשרות ״השאלה לא ברורה״. סימון כטופל אינו משנה את תוכן השאלה.</p>
    <form className="toolbar" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); setReload((v) => v + 1); }}><div className="search"><Search size={17} /><input aria-label="חיפוש דיווחים על שאלות" placeholder="חיפוש שאלה, הערה או מדווח…" maxLength={200} value={search} onChange={(event) => setSearch(event.target.value)} /></div><select aria-label="מצב דיווחי שאלות" value={resolved ? "resolved" : "open"} onChange={(event) => { setResolved(event.target.value === "resolved"); setPage(1); }}><option value="open">ממתינים לטיפול</option><option value="resolved">טופלו</option></select><button type="submit" disabled={busy}>חיפוש</button><button type="button" disabled={busy} onClick={() => setReload((v) => v + 1)}><RefreshCw size={16} />רענון</button></form>
    {notice && <p role="status" className="status-message">{notice}</p>}{error && <AdminError message={error} retry={() => setReload((v) => v + 1)} />}
    {busy ? <AdminLoading label="טוענים דיווחים על שאלות…" /> : !error && !result.reports.length ? <div className="empty"><h2>אין דיווחי שאלות בסינון הזה.</h2><p>דיווחים חדשים על ניסוח או הבנה של שאלה יופיעו כאן.</p></div> : <div className="admin-legacy-list">{result.reports.map((report) => <article key={report.id} className="admin-legacy-report"><div className="row spread"><h2 dir="auto">{report.question_title_he || report.question_title_en || report.question_key || "דיווח על שאלה"}</h2><span className="badge">{report.resolved_at ? "טופל" : "ממתין לטיפול"}</span></div><div className="admin-report-meta"><bdi dir="ltr">{report.reporter_email || "ללא אימייל"}</bdi><time>{formatDate(report.created_at, true)}</time></div><p dir="auto">{{ unclear: "השאלה לא ברורה", wrong: "טעות בשאלה או בפתרון", other: "דיווח אחר" }[report.reason] || report.reason}</p><p className="small muted">נשלח מתוך: {typeof report.context === "string" ? ({ practice: "תרגול", interview: "ראיון", library: "מאגר השאלות" }[report.context] || report.context) : "לא צוין"} · {report.language === "he" ? "עברית" : "אנגלית"}</p>{report.note && <p className="admin-preserve" dir="auto">{report.note}</p>}<div className="row spread">{report.question_key ? <a href={practiceLink(report.question_key)} target="_blank" rel="noreferrer" className="admin-inline-link">פתיחת השאלה<ExternalLink size={14} /></a> : <span className="small muted">קישור לשאלה אינו זמין</span>}<button type="button" disabled={saving !== null} onClick={() => void resolve(report)}>{saving === report.id ? "מעדכנים…" : resolved ? "החזרה לטיפול" : "סימון כטופל"}</button></div></article>)}</div>}
    <Pagination page={page} total={result.total} busy={busy} onChange={setPage} />
  </>;
}
