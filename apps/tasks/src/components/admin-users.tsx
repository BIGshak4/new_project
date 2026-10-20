"use client";
import { useEffect, useRef, useState } from "react";
import { Search, RefreshCw, ShieldCheck, X, Check } from "lucide-react";
import { adminError, adminRpc, formatDate, isConflict, planNames, type AdminUser, type PlanTier } from "../lib/admin";
import { AdminError, AdminLoading, Pagination } from "./admin-shared";

type UserList = { users: AdminUser[]; total: number };

export function AdminUsers({ active }: { active: boolean }) {
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [result, setResult] = useState<UserList>({ users: [], total: 0 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<AdminUser | null>(null);
  const [editorDirty, setEditorDirty] = useState(false);
  const [notice, setNotice] = useState("");
  const revision = useRef(0);

  useEffect(() => {
    if (!active) return;
    const request = ++revision.current;
    setBusy(true);
    setError("");
    void adminRpc<UserList>("jr_admin_users", { p_query: query, p_page: page, p_page_size: 25 }).then(
      (data) => { if (request === revision.current) setResult(data); },
      (err: unknown) => { if (request === revision.current) setError(adminError(err, "לא הצלחנו לטעון משתמשים. נסו שוב.")); },
    ).finally(() => { if (request === revision.current) setBusy(false); });
    return () => { revision.current += 1; };
  }, [active, query, page, reload]);

  return <section aria-labelledby="admin-users-title" className="admin-section">
    <div className="page-heading">
      <div><h1 id="admin-users-title">משתמשים</h1><p>חשבונות, הרשאות גישה ומסלולים — במקום אחד.</p></div>
      <button type="button" disabled={busy} onClick={() => setReload((v) => v + 1)}><RefreshCw size={16} />רענון</button>
    </div>
    <p className="admin-policy-note">המסלולים הם הרשאות ידניות בשלב הזה. שינוי מסלול אינו גובה תשלום ואינו יוצר מנוי בתשלום.</p>
    <form className="toolbar" onSubmit={(event) => { event.preventDefault(); setQuery(search.trim()); setPage(1); setReload((v) => v + 1); }}>
      <div className="search"><Search size={17} /><input aria-label="חיפוש משתמשים לפי שם או אימייל" placeholder="חיפוש לפי שם או אימייל…" value={search} onChange={(event) => setSearch(event.target.value)} maxLength={200} /></div>
      <button type="submit" disabled={busy}>חיפוש</button>
      {query && <button type="button" onClick={() => { setSearch(""); setQuery(""); setPage(1); }}>ניקוי חיפוש</button>}
    </form>
    {notice && <p role="status" className="status-message">{notice}</p>}
    {error && <AdminError message={error} retry={() => setReload((v) => v + 1)} />}
    {busy ? <AdminLoading label="טוענים את רשימת המשתמשים…" /> : !error && !result.users.length ? <div className="empty"><h2>{query ? "לא נמצאו משתמשים בחיפוש." : "אין עדיין חשבונות להצגה."}</h2><p>{query ? "נסו שם אחר או חלק מכתובת האימייל." : "משתמשים שנרשמו לאתר יופיעו כאן."}</p></div> : <div className="admin-table-scroll">
      <table className="admin-table"><caption className="sr-only">רשימת המשתמשים ופרטי הגישה שלהם</caption>
        <thead><tr><th scope="col">משתמש</th><th scope="col">הצטרפות</th><th scope="col">כניסה אחרונה</th><th scope="col">אימות אימייל</th><th scope="col">גישה לפיילוט</th><th scope="col">מסלול</th><th scope="col"><span className="sr-only">פעולה</span></th></tr></thead>
        <tbody>{result.users.map((user) => <tr key={user.id} className={selected?.id === user.id ? "selected" : ""}>
          <td><strong>{user.display_name || "ללא שם תצוגה"}</strong><bdi dir="ltr" className="admin-email">{user.email}</bdi>{user.is_founder && <span className="admin-founder"><ShieldCheck size={13} />מייסד · גישה מוגנת</span>}</td>
          <td>{formatDate(user.created_at)}</td><td>{formatDate(user.last_sign_in_at, true)}</td>
          <td>{user.email_confirmed ? "מאומת" : "ממתין לאימות"}</td><td>{user.pilot_access ? "מאושרת" : "ללא גישה"}</td>
          <td><bdi dir="ltr" className="badge">{planNames[user.plan_tier]}</bdi></td>
          <td><button type="button" onClick={() => {
            if (selected?.id !== user.id && editorDirty && !window.confirm("יש בחירות שלא נשמרו. לעבור למשתמש אחר ולוותר עליהן?")) return;
            setSelected(user); setNotice("");
          }} aria-expanded={selected?.id === user.id}>ניהול</button></td>
        </tr>)}</tbody>
      </table>
    </div>}
    <Pagination page={page} total={result.total} busy={busy} onChange={setPage} />
    {selected && <UserEditor key={selected.id} initial={selected} onDirty={setEditorDirty} onClose={() => setSelected(null)} onSaved={(user) => {
      setSelected(user);
      setResult((old) => ({ ...old, users: old.users.map((row) => row.id === user.id ? user : row) }));
      setNotice("המסלול והרשאת הגישה נשמרו. לא נגבה תשלום.");
    }} />}
  </section>;
}

function UserEditor({ initial, onClose, onSaved, onDirty }: { initial: AdminUser; onClose: () => void; onSaved: (user: AdminUser) => void; onDirty: (dirty: boolean) => void }) {
  const [base, setBase] = useState(initial);
  const [plan, setPlan] = useState<PlanTier>(initial.plan_tier);
  const [access, setAccess] = useState(initial.pilot_access);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const dirty = plan !== base.plan_tier || access !== base.pilot_access;
  const formRef = useRef<HTMLFormElement>(null);
  useEffect(() => { onDirty(dirty); return () => onDirty(false); }, [dirty, onDirty]);
  useEffect(() => { formRef.current?.scrollIntoView({ block: "nearest" }); }, []);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      const user = await adminRpc<AdminUser>("jr_admin_update_user", {
        p_user_id: base.id, p_plan_tier: plan, p_pilot_access: base.is_founder ? true : access,
        p_expected_plan: base.plan_tier, p_expected_access: base.pilot_access,
      });
      setBase(user); setPlan(user.plan_tier); setAccess(user.pilot_access); setConflict(false); onSaved(user);
    } catch (err) { setConflict(isConflict(err)); setError(adminError(err)); }
    finally { setBusy(false); }
  }
  async function reloadBase() {
    setBusy(true);
    try {
      const result = await adminRpc<UserList>("jr_admin_users", { p_query: base.email, p_page: 1, p_page_size: 25 });
      const fresh = result.users.find((user) => user.id === base.id);
      if (!fresh) throw new Error("missing_user");
      setBase(fresh); setConflict(false);
      setError(`הגרסה העדכנית: מסלול ${planNames[fresh.plan_tier]}, ${fresh.pilot_access ? "עם גישה לפיילוט" : "ללא גישה לפיילוט"}. הבחירה שלכם נשמרה בטופס. בדקו אותה לפני שמירה.`);
    } catch (err) { setError(adminError(err)); }
    finally { setBusy(false); }
  }
  return <form ref={formRef} className="admin-user-editor" onSubmit={(event) => void save(event)} aria-labelledby="admin-user-edit-title">
    <div className="row spread"><div><h2 id="admin-user-edit-title">ניהול משתמש</h2><bdi dir="ltr" className="small muted">{base.email}</bdi></div><button type="button" className="icon-button" aria-label="סגירת ניהול המשתמש" disabled={busy} onClick={() => { if (!dirty || window.confirm("יש בחירות שלא נשמרו. לסגור את ניהול המשתמש?")) onClose(); }}><X size={18} /></button></div>
    <div className="admin-user-fields">
      <label>מסלול<select value={plan} onChange={(event) => setPlan(event.target.value as PlanTier)} disabled={busy}>{Object.entries(planNames).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="check-label"><input type="checkbox" checked={base.is_founder || access} disabled={busy || base.is_founder} onChange={(event) => setAccess(event.target.checked)} />גישה לפיילוט</label>
      <button type="submit" className="primary" disabled={busy || !dirty || conflict}><Check size={16} />{busy ? "שומרים…" : "שמירת מסלול וגישה"}</button>
    </div>
    {base.is_founder && <p className="small muted">גישת מייסדים מוגנת ואי אפשר להסיר אותה מכאן.</p>}
    <p className="small muted">זהו עדכון הרשאה ידני בלבד. אין חיבור לסליקה ואין חיוב כספי.</p>
    {error && <AdminError message={error} />}
    {conflict && <button type="button" disabled={busy} onClick={() => void reloadBase()}>טעינת גרסה עדכנית והשוואה לבחירה שלי</button>}
  </form>;
}
