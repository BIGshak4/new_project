"use client";
import { useEffect, useRef, useState } from "react";
import { Archive, Check, Plus, RefreshCw, Search, Send, X } from "lucide-react";
import { adminError, adminRpc, announcementStatuses, formatDate, isConflict, type Announcement, type AnnouncementStatus } from "../lib/admin";
import { AdminError, AdminLoading, Pagination } from "./admin-shared";

type AnnouncementList = { announcements: Announcement[]; total: number };
type Wording = Pick<Announcement, "title_he" | "body_he" | "title_en" | "body_en">;
function wording(row: Announcement): Wording {
  return { title_he: row.title_he, body_he: row.body_he, title_en: row.title_en || "", body_en: row.body_en || "" };
}
function newAnnouncement(copy?: Wording): Announcement {
  return { id: crypto.randomUUID(), title_he: copy?.title_he || "", body_he: copy?.body_he || "", title_en: copy?.title_en || "", body_en: copy?.body_en || "", status: "draft", version: 0, created_at: "", updated_at: "", published_at: null };
}

export function AdminAnnouncements({ active }: { active: boolean }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [result, setResult] = useState<AnnouncementList>({ announcements: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Announcement | null>(null);
  const [dirty, setDirty] = useState(false);
  const requestRef = useRef(0);
  useEffect(() => {
    if (!active) return;
    const request = ++requestRef.current;
    setLoading(true); setError("");
    void adminRpc<AnnouncementList>("jr_admin_announcements", { p_query: query, p_status: status, p_page: page, p_page_size: 25 }).then((data) => {
      if (requestRef.current === request) setResult(data);
    }, (err: unknown) => { if (requestRef.current === request) setError(adminError(err, "לא הצלחנו לטעון עדכונים למשתמשים. נסו שוב.")); }).finally(() => { if (requestRef.current === request) setLoading(false); });
    return () => { requestRef.current += 1; };
  }, [active, query, status, page, reload]);

  function open(row: Announcement) {
    if (row.id !== selected?.id && dirty && !window.confirm("יש ניסוח שלא נשמר. לעבור לעדכון אחר ולוותר על הטיוטה הזאת?")) return;
    setSelected(row);
  }
  return <section className="admin-section" aria-labelledby="admin-announcements-title">
    <div className="page-heading"><div><h1 id="admin-announcements-title">עדכונים למשתמשים</h1><p>כותבים, בודקים ומפרסמים הודעות באזור העדכונים באתר.</p></div><button type="button" className="primary" onClick={() => open(newAnnouncement())}><Plus size={17} />עדכון חדש</button></div>
    <p className="admin-policy-note">טיוטה נשארת לצוות בלבד. פרסום חושף את העדכון לכל המשתמשים באתר; לא נשלח מייל. ניסוח שפורסם נשמר כפי שנשלח, וניתן להעבירו לארכיון.</p>
    <form className="toolbar" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); setReload((old) => old + 1); }}>
      <div className="search"><Search size={17} /><input aria-label="חיפוש עדכונים למשתמשים" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="חיפוש לפי כותרת או תוכן…" maxLength={200} /></div>
      <select aria-label="סינון עדכונים לפי מצב" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}><option value="all">כל המצבים</option>{Object.entries(announcementStatuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      <button type="submit" disabled={loading}>חיפוש</button><button type="button" disabled={loading} onClick={() => setReload((old) => old + 1)}><RefreshCw size={16} />רענון</button>
      {(query || status !== "all") && <button type="button" onClick={() => { setSearch(""); setQuery(""); setStatus("all"); setPage(1); }}>איפוס סינון</button>}
    </form>
    {error && <AdminError message={error} retry={() => setReload((old) => old + 1)} />}
    <div className={`admin-announcement-layout ${selected ? "has-editor" : ""}`}>
      <div>
        {loading ? <AdminLoading label="טוענים את העדכונים…" /> : !error && !result.announcements.length ? <div className="empty"><h2>{query || status !== "all" ? "לא נמצאו עדכונים בסינון הזה." : "העדכון הראשון מתחיל בטיוטה."}</h2><p>צרו עדכון, עברו על הניסוח ושמרו אותו לפני הפרסום.</p></div> : <div className="admin-report-list" aria-label="רשימת העדכונים">{result.announcements.map((row) => <button type="button" key={row.id} className={`admin-report-row ${selected?.id === row.id ? "selected" : ""}`} aria-expanded={selected?.id === row.id} onClick={() => open(row)}><div className="row spread"><span className={`badge announcement-${row.status}`}>{announcementStatuses[row.status]}</span><time className="small muted">{formatDate(row.updated_at)}</time></div><h2 dir="auto">{row.title_he}</h2><p className="admin-report-preview" dir="auto">{row.body_he}</p><span className="small muted">{row.title_en && row.body_en ? "כולל תרגום לאנגלית" : "עברית · מוצגת גם כשאין תרגום לאנגלית"}</span></button>)}</div>}
        <Pagination page={page} total={result.total} busy={loading} onChange={setPage} />
      </div>
      {selected && <AnnouncementEditor key={selected.id} initial={selected} onDirty={setDirty} onClose={() => setSelected(null)} onCopy={(copy) => setSelected(newAnnouncement(copy))} onSaved={(row) => {
        setSelected(row); setReload((old) => old + 1);
      }} />}
    </div>
  </section>;
}

function AnnouncementEditor({ initial, onDirty, onClose, onSaved, onCopy }: {
  initial: Announcement; onDirty: (dirty: boolean) => void; onClose: () => void; onSaved: (row: Announcement) => void; onCopy: (copy: Wording) => void;
}) {
  const [base, setBase] = useState(initial);
  const [draft, setDraft] = useState<Wording>(() => wording(initial));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [conflict, setConflict] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [comparison, setComparison] = useState<Announcement | null>(null);
  const [preservedDraft, setPreservedDraft] = useState<Wording | null>(null);
  const dirty = JSON.stringify(draft) !== JSON.stringify(wording(base));
  const editable = base.status === "draft";
  const locked = busy || uncertain;
  const sectionRef = useRef<HTMLElement>(null);
  useEffect(() => { onDirty(dirty || uncertain); return () => onDirty(false); }, [dirty, uncertain, onDirty]);
  useEffect(() => { sectionRef.current?.scrollIntoView({ block: "nearest" }); }, []);
  useEffect(() => {
    if (!dirty && !uncertain) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, uncertain]);

  function update(key: keyof Wording, value: string) { setDraft((old) => ({ ...old, [key]: value })); setNotice(""); }
  async function perform(action: "save" | "publish" | "archive") {
    if (locked) return;
    setError(""); setNotice("");
    if (action !== "archive") {
      if (!draft.title_he.trim() || !draft.body_he.trim()) { setError("צריך למלא כותרת ותוכן בעברית."); return; }
      if (!!draft.title_en?.trim() !== !!draft.body_en?.trim()) { setError("תרגום לאנגלית צריך לכלול גם כותרת וגם תוכן, או להשאיר את שניהם ריקים."); return; }
    }
    if (action === "publish") {
      if (dirty || !base.version) { setError("שמרו קודם את הטיוטה ובדקו את הניסוח לפני הפרסום."); return; }
      if (!window.confirm(`לפרסם את ״${base.title_he}״ לכל המשתמשים באתר? הניסוח לא יהיה ניתן לעריכה לאחר הפרסום. לא יישלח מייל.`)) return;
    }
    if (action === "archive" && !window.confirm("להעביר את העדכון לארכיון? הוא יוסר מרשימת העדכונים הפעילים של המשתמשים.")) return;
    setBusy(true);
    try {
      const row = await adminRpc<Announcement>("jr_admin_save_announcement", {
        p_id: base.id, p_expected_version: base.version, p_action: action,
        ...(action !== "archive" ? { p_title_he: draft.title_he.trim(), p_body_he: draft.body_he.trim(), p_title_en: draft.title_en?.trim() || null, p_body_en: draft.body_en?.trim() || null } : {}),
      });
      setBase(row); setDraft(wording(row)); setConflict(false); setUncertain(false); setComparison(null); setPreservedDraft(null);
      setNotice(action === "publish" ? "העדכון פורסם באזור העדכונים של המשתמשים." : action === "archive" ? "העדכון הועבר לארכיון." : "הטיוטה נשמרה לצוות בלבד."); onSaved(row);
    } catch (err) {
      const known = isConflict(err) || ["22023", "42501"].includes((err as { code?: string })?.code || "");
      setConflict(isConflict(err)); setUncertain(!known);
      setError(known ? adminError(err) : "לא התקבל אישור חד־משמעי מהשרת. הניסוח נשמר כאן. בדקו את מצב העדכון לפני פעולה נוספת כדי להימנע מפרסום כפול.");
    } finally { setBusy(false); }
  }
  async function recover() {
    setBusy(true);
    try {
      const result = await adminRpc<AnnouncementList>("jr_admin_announcements", { p_query: base.id, p_status: "all", p_page: 1, p_page_size: 25 });
      const latest = result.announcements.find((row) => row.id === base.id);
      if (!latest) {
        setUncertain(false); setConflict(false); setError(""); setNotice("לא נמצא עדכון שמור עם המספר הזה. הטיוטה נשמרה כאן; אפשר לנסות לשמור אותה שוב."); return;
      }
      setComparison(latest); setUncertain(false); setError("");
      if (latest.status !== "draft") {
        if (JSON.stringify(draft) !== JSON.stringify(wording(latest))) setPreservedDraft(draft);
        setBase(latest); setDraft(wording(latest)); setConflict(false);
        setNotice(latest.status === "published" ? "השרת אישר שהעדכון כבר פורסם. הנוסח שפורסם מוצג כאן." : "העדכון נמצא בארכיון. הנוסח השמור מוצג כאן.");
      } else {
        setConflict(true); setNotice("הגרסה שנשמרה בשרת מוצגת להשוואה. הניסוח שלכם נשאר בטופס.");
      }
    } catch (err) { setError(adminError(err, "בדיקת מצב העדכון לא הושלמה. הטיוטה נשמרה; נסו שוב.")); }
    finally { setBusy(false); }
  }

  return <section ref={sectionRef} className="admin-announcement-editor" aria-labelledby="announcement-editor-title">
    <div className="row spread"><h2 id="announcement-editor-title">{base.version ? "פרטי העדכון" : "עדכון חדש"}</h2><button type="button" className="icon-button" aria-label="סגירת עריכת העדכון" disabled={busy} onClick={() => { if ((!dirty && !uncertain) || window.confirm("יש טיוטה שלא נשמרה או פעולה שטרם אושרה. לסגור ולוותר על העריכה המקומית?")) onClose(); }}><X size={17} /></button></div>
    <div className="row spread"><span className={`badge announcement-${base.status}`}>{announcementStatuses[base.status]}</span><span className="small muted">{base.version ? `גרסה ${base.version}` : "טרם נשמר"}</span></div>
    {!editable && <p className="admin-public-note">הניסוח שפורסם נעול לעריכה. לתיקון או המשך, צרו עדכון חדש.</p>}
    <form onSubmit={(event) => { event.preventDefault(); void perform("save"); }} className="admin-announcement-form">
      <label>כותרת בעברית<input required maxLength={160} dir="rtl" value={draft.title_he} readOnly={!editable} disabled={locked} onChange={(event) => update("title_he", event.target.value)} /></label>
      <label>תוכן בעברית<textarea required rows={7} maxLength={10000} dir="rtl" value={draft.body_he} readOnly={!editable} disabled={locked} onChange={(event) => update("body_he", event.target.value)} /></label>
      <details className="admin-translation" open={!!draft.title_en || !!draft.body_en}><summary>תרגום לאנגלית — אופציונלי</summary><p className="small muted">מלאו כותרת ותוכן יחד. בלי תרגום, משתמשי הממשק באנגלית יקבלו את הנוסח בעברית עם ציון שפת ההודעה.</p><label>כותרת באנגלית<input maxLength={160} dir="ltr" value={draft.title_en || ""} readOnly={!editable} disabled={locked} onChange={(event) => update("title_en", event.target.value)} /></label><label>תוכן באנגלית<textarea rows={6} maxLength={10000} dir="ltr" value={draft.body_en || ""} readOnly={!editable} disabled={locked} onChange={(event) => update("body_en", event.target.value)} /></label></details>
      {error && <AdminError message={error} />}{notice && <p role="status" className="status-message">{notice}</p>}
      {(conflict || uncertain) && <button type="button" disabled={busy} onClick={() => void recover()}><RefreshCw size={15} />בדיקת הגרסה השמורה</button>}
      {comparison && <div className="admin-conflict"><h3>הנוסח השמור בשרת</h3><span className="small">{announcementStatuses[comparison.status]} · גרסה {comparison.version}</span><strong dir="auto">{comparison.title_he}</strong><p dir="auto" className="admin-preserve">{comparison.body_he}</p>{comparison.title_en && <><strong dir="ltr">{comparison.title_en}</strong><p dir="ltr" className="admin-preserve">{comparison.body_en}</p></>}{comparison.status === "draft" && conflict && <button type="button" onClick={() => { setBase(comparison); setConflict(false); setComparison(null); setError(""); setNotice("בסיס השמירה עודכן. הטיוטה שלכם נשארה בטופס; בדקו אותה לפני שמירה."); }}>להמשיך עם הטיוטה שלי לאחר ההשוואה</button>}</div>}
      {preservedDraft && <div className="admin-conflict"><p>העריכה המקומית לא אבדה. אפשר לפתוח ממנה טיוטה חדשה בלי לשנות את העדכון שפורסם.</p><details><summary>הצגת הטיוטה שלי</summary><strong>{preservedDraft.title_he}</strong><p className="admin-preserve">{preservedDraft.body_he}</p></details><button type="button" onClick={() => onCopy(preservedDraft)}>טיוטה חדשה מהעריכה שלי</button></div>}
      <div className="admin-announcement-actions">
        {editable && <button type="submit" className="primary" disabled={locked || conflict || (!dirty && base.version > 0)}><Check size={16} />שמירת טיוטה</button>}
        {editable && <button type="button" disabled={locked || conflict || dirty || !base.version} onClick={() => void perform("publish")}><Send size={16} />פרסום לכל המשתמשים</button>}
        {base.version > 0 && base.status !== "archived" && <button type="button" disabled={locked || conflict || dirty} onClick={() => void perform("archive")}><Archive size={16} />העברה לארכיון</button>}
      </div>
      {editable && <p className="small muted">שמירת טיוטה אינה מפרסמת. כדי לפרסם, שמרו קודם את הניסוח ואז בחרו בפרסום ואשרו אותו.</p>}
    </form>
  </section>;
}
