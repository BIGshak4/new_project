"use client";

import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { CheckCircle2, CircleHelp, FileText, LoaderCircle, Paperclip, Send, X } from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { observeAuthUser } from "../lib/auth-access";
import { lockBodyScroll } from "../lib/body-scroll-lock";
import {
  SUPPORT_ACCEPT, SUPPORT_LIMITS, SUPPORT_OPEN_EVENT, inspectSupportFiles, removeSupportReservation, sendSupportReport, supportErrorMessage,
  supportPageContext, validateSupportDetails, type SupportCategory, type SupportFile, type SupportLanguage,
  type SupportSubmission, type SupportTransport,
} from "../lib/support-report";
import { BidiText } from "./bidi-text";
import styles from "./support-reporter.module.css";

function uuid() { return crypto.randomUUID(); }

const transport: SupportTransport = {
  async saveReport(input) {
    const { error } = await supabase.rpc("jr_submit_support_report", {
      p_id: input.id, p_subject: input.subject.trim(), p_description: input.description.trim(),
      p_category: input.category, p_language: input.language, p_page_path: input.pagePath, p_question_key: input.questionKey,
    });
    if (error) throw error;
  },
  async reserveFile(reportId, item) {
    const { data, error } = await supabase.rpc("jr_reserve_support_file", {
      p_id: item.id, p_report_id: reportId, p_name: item.file.name, p_mime_type: item.mimeType, p_size_bytes: item.file.size,
    });
    if (error) throw error;
    if (!data || typeof data.storage_path !== "string") throw new Error("Missing attachment reservation");
    return data.storage_path as string;
  },
  async uploadFile(path, item) {
    const storage = supabase.storage.from("jr-support-files");
    const { error } = await storage.upload(path, item.file, { contentType: item.mimeType, upsert: false });
    if (!error) return;
    // A dropped response can hide a completed upload. A UUID path is immutable, so checking that exact object safely recovers it.
    const separator = path.lastIndexOf("/");
    const name = path.slice(separator + 1);
    const { data, error: lookupError } = await storage.list(path.slice(0, separator), { search: name, limit: 10 });
    if (!lookupError && data?.some(object => object.name === name && Number(object.metadata?.size) === item.file.size)) return;
    throw error;
  },
  async removeReservation(fileId) {
    await removeSupportReservation(() => supabase.rpc("jr_remove_support_file", { p_id: fileId }));
  },
};

/** The report stays above the current page so opening help never discards an answer or circuit draft. */
export function SupportReporter() {
  const [lang, setLang] = useState<SupportLanguage>("he");
  const [open, setOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<SupportCategory>("bug");
  const [files, setFiles] = useState<SupportFile[]>([]);
  const [busy, setBusy] = useState(false);
  const [checkingFiles, setCheckingFiles] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [context, setContext] = useState({ pagePath: "/", questionKey: null as string | null });
  const [reportId, setReportId] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const userId = useRef<string | null>(null);
  const draftOwner = useRef<string | null>(null);
  const generation = useRef(0);
  const working = useRef(false);
  const reportSnapshot = useRef<SupportSubmission | null>(null);
  const ids = useId();
  const he = lang === "he";
  const pending = files.filter(file => !file.uploaded).length;
  const totalBytes = files.reduce((total, item) => total + item.file.size, 0);

  function reset() {
    setSubject(""); setDescription(""); setCategory("bug"); setFiles([]); setError(""); setSaved(false); setSubmitted(false);
    setReportId(""); setConfirmReset(false); reportSnapshot.current = null;
    if (input.current) input.current.value = "";
  }

  useEffect(() => {
    const update = () => setLang(document.documentElement.lang.startsWith("en") ? "en" : "he");
    update();
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => observeAuthUser(supabase.auth, next => {
    const nextId = next?.id ?? null;
    if (nextId !== userId.current) {
      generation.current += 1;
      working.current = false;
      setBusy(false); setCheckingFiles(false); setError("");
      if (nextId && draftOwner.current && nextId !== draftOwner.current) reset();
      if (nextId) draftOwner.current = nextId;
      userId.current = nextId;
    }
    setUser(next); setAuthReady(true);
  }), []);

  useEffect(() => {
    if (!dialog.current) return;
    if (open && !dialog.current.open) {
      dialog.current.showModal();
      heading.current?.focus();
    } else if (!open && dialog.current.open) dialog.current.close();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    return lockBodyScroll();
  }, [open]);

  useEffect(() => {
    window.addEventListener(SUPPORT_OPEN_EVENT, launch);
    return () => window.removeEventListener(SUPPORT_OPEN_EVENT, launch);
  }, []);

  function launch() {
    opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : trigger.current;
    setContext(supportPageContext(window.location.href));
    setOpen(true);
  }

  function close() {
    setOpen(false);
    (opener.current ?? trigger.current)?.focus();
  }

  async function selectFiles(selected: FileList | null) {
    if (!selected?.length || working.current || checkingFiles) return;
    const epoch = generation.current;
    const additions = Array.from(selected);
    setCheckingFiles(true); setError("");
    try {
      const candidates = [...files.map(item => item.file), ...additions];
      const types = await inspectSupportFiles(candidates);
      if (generation.current !== epoch) return;
      setFiles(previous => [...previous, ...additions.map((file, index) => ({ id: uuid(), file, mimeType: types[files.length + index], uploaded: false }))]);
    } catch (failure) { if (generation.current === epoch) setError(supportErrorMessage(failure, he)); }
    finally {
      if (generation.current === epoch) setCheckingFiles(false);
      if (input.current) input.current.value = "";
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (working.current || checkingFiles || !userId.current) return;
    const owner = userId.current;
    const epoch = generation.current;
    const isCurrent = () => generation.current === epoch && userId.current === owner;
    working.current = true; setBusy(true); setError("");
    try {
      if (!saved) validateSupportDetails(subject, description);
      const { data, error: authError } = await supabase.auth.getUser();
      if (authError || data.user?.id !== owner) throw new Error("Session changed");
      if (!isCurrent()) return;
      if (!reportSnapshot.current) {
        const id = reportId || uuid();
        setReportId(id);
        reportSnapshot.current = { id, subject, description, category, language: lang, ...context };
      }
      const result = await sendSupportReport(transport, reportSnapshot.current, files, {
        alreadySaved: saved, isCurrent, onProgress: setFiles,
      });
      if (!isCurrent()) return;
      setSaved(result.reportSaved); setFiles(result.files);
      if (result.error) setError(supportErrorMessage(result.error, he));
      else if (result.failedFiles) setError(he ? "הדיווח נשמר, אבל חלק מהקבצים לא עלו. נסו שוב להעלות אותם; לא יישלח דיווח כפול." : "Your report was saved, but some files were not uploaded. Retry those files; no duplicate report will be created.");
      else setSubmitted(true);
    } catch (failure) { if (isCurrent()) setError(supportErrorMessage(failure, he)); }
    finally { if (isCurrent()) { working.current = false; setBusy(false); } }
  }

  async function omitFile(item: SupportFile) {
    if (working.current || item.uploaded) return;
    if (!saved) { setFiles(previous => previous.filter(file => file.id !== item.id)); return; }
    const epoch = generation.current;
    working.current = true; setBusy(true); setError("");
    try {
      await transport.removeReservation(item.id);
      if (generation.current === epoch) setFiles(previous => previous.filter(file => file.id !== item.id));
    } catch {
      if (generation.current === epoch) setError(he ? "לא הצלחנו לוותר על הקובץ. ייתכן שכבר עלה; נסו שוב את ההעלאה כדי לבדוק זאת." : "We could not omit the file. It may already be uploaded; retry the upload to check.");
    } finally { if (generation.current === epoch) { working.current = false; setBusy(false); } }
  }

  return <>
    <button ref={trigger} type="button" className={styles.launcher} onClick={launch} aria-haspopup="dialog" aria-controls={`${ids}-dialog`}>
      <CircleHelp size={18} aria-hidden="true" /><span>{he ? "נתקלתם בבעיה?" : "Report a problem"}</span>
    </button>
    <dialog ref={dialog} data-jobrun-support-dialog id={`${ids}-dialog`} className={styles.dialog} dir={he ? "rtl" : "ltr"} lang={lang}
      aria-labelledby={`${ids}-title`} aria-describedby={`${ids}-intro`} onCancel={event => { event.preventDefault(); close(); }}>
      <div className={styles.header}>
        <div><h2 ref={heading} tabIndex={-1} id={`${ids}-title`}>{he ? "ספרו לנו מה קרה" : "Tell us what happened"}</h2>
          <p id={`${ids}-intro`}>{he ? "הדיווח יגיע ישירות להראל ולשקד. נבדוק ונטפל בהקדם." : "Your report goes directly to Harel and Shaked. We will investigate as soon as we can."}</p></div>
        <button type="button" className={styles.close} onClick={close} aria-label={he ? "סגירה ושמירת הטיוטה בלשונית" : "Close and keep the draft in this tab"}><X size={21} aria-hidden="true" /></button>
      </div>
      {!authReady ? <p className={styles.auth} role="status">{he ? "בודקים את החיבור לחשבון…" : "Checking your account…"}</p>
        : !user ? <div className={styles.auth}>
          <CircleHelp size={30} aria-hidden="true" /><h3>{he ? "התחברו כדי לשלוח דיווח" : "Sign in to submit a report"}</h3>
          <p>{he ? "כך נוכל לקשר את הפנייה לחשבון שלכם ולשמור על הקבצים פרטיים. סגרו את החלון, התחברו ואז פתחו אותו שוב." : "This links the report to your account and keeps your attachments private. Close this window, sign in, then open it again."}</p>
          <button type="button" onClick={close}>{he ? "בחזרה לאתר" : "Back to the site"}</button>
        </div> : submitted ? <div className={styles.receipt} role="status">
          <CheckCircle2 size={36} aria-hidden="true" /><h3>{he ? "הדיווח הגיע אלינו" : "Your report is with us"}</h3>
          <p>{he ? "תודה שעזרתם לנו לשפר את חוויית התרגול. הפנייה מופיעה כעת במרכז הניהול של הצוות." : "Thank you for helping us improve practice. Your report is now in the team's support inbox."}</p>
          <p className={styles.reference}>{he ? "מספר פנייה" : "Report reference"}<bdi dir="ltr">{reportId}</bdi></p>
          {files.length > 0 && <p>{he ? `צורפו ${files.length} קבצים.` : `${files.length} attachments received.`}</p>}
          <div className={styles.actions}><button type="button" className={styles.primary} onClick={close}>{he ? "בחזרה לתרגול" : "Back to practice"}</button><button type="button" onClick={reset}>{he ? "דיווח נוסף" : "Report another issue"}</button></div>
        </div> : <form className={styles.form} onSubmit={submit}>
          <p className={styles.account}>{he ? "שולחים מהחשבון" : "Reporting as"} <bdi dir="ltr">{user.email}</bdi></p>
          {saved && <p className={styles.saved} role="status"><CheckCircle2 size={18} aria-hidden="true" />{pending ? he ? "הדיווח כבר נשמר. נותר להעלות את הקבצים המסומנים, או לוותר עליהם." : "The report is saved. Retry the marked attachments or omit them." : he ? "הדיווח נשמר. אפשר לסיים." : "The report is saved. You can finish now."}</p>}
          {!!reportId && !saved && <p className={styles.draft}>{he ? "פרטי הדיווח נשמרים ללא שינוי לניסיון נוסף, כדי למנוע שליחה כפולה." : "Report details are kept unchanged for a safe retry without duplicates."}</p>}
          <fieldset disabled={busy || checkingFiles || !!reportId} className={styles.fields}>
            <label htmlFor={`${ids}-subject`}>{he ? "כותרת קצרה" : "Short subject"}<input id={`${ids}-subject`} dir="auto" value={subject} onChange={event => setSubject(event.target.value)} required minLength={3} maxLength={160} autoComplete="off" placeholder={he ? "למשל: השרטוט לא נשמר" : "For example: my circuit did not save"} /></label>
            <label htmlFor={`${ids}-category`}>{he ? "במה מדובר?" : "What is this about?"}<select id={`${ids}-category`} value={category} onChange={event => setCategory(event.target.value as SupportCategory)}>
              <option value="bug">{he ? "תקלה באתר" : "Something is broken"}</option><option value="question">{he ? "בעיה בשאלה או בפתרון" : "A question or solution"}</option><option value="feedback">{he ? "הצעה לשיפור" : "An improvement idea"}</option><option value="other">{he ? "משהו אחר" : "Something else"}</option>
            </select></label>
            <label htmlFor={`${ids}-description`}>{he ? "תיאור הבעיה" : "Describe the issue"}<textarea id={`${ids}-description`} dir="auto" value={description} onChange={event => setDescription(event.target.value)} required minLength={20} maxLength={6000} rows={5} placeholder={he ? "מה ניסיתם לעשות? מה ציפיתם שיקרה, ומה קרה בפועל?" : "What were you trying to do? What did you expect, and what happened instead?"} aria-describedby={`${ids}-privacy`} /></label>
          </fieldset>
          <section className={styles.attachments} aria-labelledby={`${ids}-attachments`}>
            <h3 id={`${ids}-attachments`}><Paperclip size={17} aria-hidden="true" />{he ? "קבצים לצירוף" : "Attachments"}<span>{he ? "לא חובה" : "optional"}</span></h3>
            <p id={`${ids}-file-limits`}>{he ? "עד 5 קבצים, עד 5 מגה־בייט לקובץ ו־15 מגה־בייט בסך הכול. תמונות PNG, JPG ו־WebP, מסמכי PDF או טקסט." : "Up to 5 files, 5 MiB each and 15 MiB in total. PNG, JPG, WebP, PDF or plain text."}</p>
            {!reportId && <label className={styles.filePicker} htmlFor={`${ids}-files`}><Paperclip size={17} aria-hidden="true" /><span>{checkingFiles ? he ? "בודקים קבצים…" : "Checking files…" : he ? "בחירת תמונות או מסמכים" : "Choose images or documents"}</span><input ref={input} id={`${ids}-files`} type="file" accept={SUPPORT_ACCEPT} multiple disabled={busy || checkingFiles} onChange={event => void selectFiles(event.target.files)} aria-describedby={`${ids}-file-limits`} /></label>}
            {files.length > 0 && <><ul className={styles.fileList}>{files.map(item => <li key={item.id}>
              <FileText size={18} aria-hidden="true" /><span className={styles.fileName}><BidiText>{item.file.name}</BidiText><small>{(item.file.size / 1024 / 1024).toFixed(2)} {he ? "מגה־בייט" : "MiB"}{item.uploaded ? he ? " · צורף" : " · uploaded" : saved ? he ? " · ההעלאה לא הושלמה" : " · not uploaded" : ""}</small></span>
              {item.uploaded ? <CheckCircle2 size={18} className={styles.uploaded} aria-hidden="true" /> : (!reportId || saved) && <button type="button" className={styles.remove} disabled={busy || checkingFiles} onClick={() => void omitFile(item)} aria-label={`${he ? "ויתור על הקובץ" : "Omit file"} ${item.file.name}`}>{saved ? he ? "ויתור" : "Omit" : <X size={17} aria-hidden="true" />}</button>}
            </li>)}</ul><p className={styles.total}>{he ? "סה״כ" : "Total"}: {(totalBytes / 1024 / 1024).toFixed(2)} / {SUPPORT_LIMITS.totalBytes / 1024 / 1024} {he ? "מגה־בייט" : "MiB"}</p></>}
          </section>
          <p id={`${ids}-privacy`} className={styles.privacy}>{he ? "אל תצרפו סיסמאות, מפתחות גישה או מידע אישי רגיש. הקבצים פרטיים וזמינים רק לכם ולמנהלי האתר. נצרף את מסלול העמוד ומזהה השאלה בלבד, בלי התשובה שלכם או פרטי ההתחברות." : "Do not include passwords, access keys or sensitive personal information. Attachments are private to you and the site administrators. We include only the page route and question ID, never your answer or sign-in details."}</p>
          {context.questionKey && <p className={styles.context}>{he ? "משויך לשאלה" : "Related question"}: <bdi dir="ltr">{context.questionKey}</bdi></p>}
          {error && <p className={styles.error} role="alert">{error}</p>}
          <div className={styles.actions}><button type="submit" className={styles.primary} disabled={busy || checkingFiles}>
            {busy ? <LoaderCircle size={18} className={styles.spinner} aria-hidden="true" /> : <Send size={17} aria-hidden="true" />}
            {busy ? he ? "שולחים…" : "Sending…" : saved ? pending ? he ? `ניסיון נוסף להעלאת ${pending} קבצים` : `Retry ${pending} attachments` : he ? "סיום הדיווח" : "Finish report" : he ? "שליחת דיווח" : "Send report"}
          </button><button type="button" onClick={close}>{he ? "סגירה ושמירת הטיוטה" : "Close and keep draft"}</button></div>
          <p className={styles.draft}>{he ? "הטיוטה נשמרת כל עוד הלשונית פתוחה. ניתן לשלוח עד 5 דיווחים ביום." : "Your draft stays in this tab until it is closed or reloaded. You can send up to 5 reports per day."}</p>
          {!!reportId && !saved && !busy && <div className={styles.recovery}>
            {!confirmReset ? <button type="button" onClick={() => setConfirmReset(true)}>{he ? "פתיחת טיוטה חדשה במקום ניסיון נוסף" : "Start a new draft instead of retrying"}</button> : <>
              <p>{he ? "ייתכן שהפנייה כבר נשמרה בשרת. פתיחת טיוטה חדשה תמחק את הטיוטה מהחלון הזה בלבד. מספר הפנייה הנוכחית:" : "The report may already be saved on the server. Starting again clears only the draft in this window. Current report reference:"} <bdi dir="ltr">{reportId}</bdi></p>
              <button type="button" onClick={reset}>{he ? "הבנתי, לפתוח טיוטה חדשה" : "Understood, start a new draft"}</button><button type="button" onClick={() => setConfirmReset(false)}>{he ? "להישאר עם הטיוטה" : "Keep this draft"}</button>
            </>}
          </div>}
        </form>}
    </dialog>
  </>;
}
