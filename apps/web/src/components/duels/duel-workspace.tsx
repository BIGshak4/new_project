"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, CheckCheck, CircleHelp, Clock3, Coins, Copy, RefreshCw, Swords, Users, X } from "lucide-react";
import { BidiText } from "../bidi-text";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import type { Duel, DuelClient, DuelLanguage, DuelList, DuelWallet } from "../../lib/duel-types";
import { inviteCode, quizSecondsLeft } from "../../lib/duel-types";
import { DEFAULT_AVATAR, type AvatarConfig } from "../../lib/avatar-types";
import { LogicAvatar } from "../wardrobe/logic-avatar";
import { FeatureNav } from "../wardrobe/feature-nav";
import { DuelLooks } from "./duel-looks";
import styles from "./duels.module.css";
import avatarStyles from "./game-avatar.module.css";

function errorMessage(error: unknown, lang: DuelLanguage) {
  const e = error as { code?: string; status?: number };
  const he = lang === "he";
  if (e.status === 402) return he ? "אין מספיק מטבעות למשחק הזה." : "You do not have enough coins for this game.";
  if (e.code === "unauthenticated") return he ? "ההתחברות השתנתה. היכנסו מחדש כדי להמשיך." : "Your sign-in changed. Sign in again to continue.";
  if (e.code === "not_found") return he ? "ההזמנה לא נמצאה. בדקו את הקוד או בקשו קישור חדש." : "Invite not found. Check the code or ask for a new link.";
  if (e.code === "conflict" || e.code === "already_submitted") return he ? "מצב המשחק השתנה. רעננו את המשחק לפני ניסיון נוסף." : "The game changed. Refresh it before trying again.";
  if (e.code === "forbidden") return he ? "ההזמנה שייכת למשחק אחר, או שכבר הצטרף אליו שחקן." : "This game is unavailable to your account or another player has already joined.";
  if (e.code === "configuration" || e.status === 503) return he ? "המשחק עדיין אינו זמין בשרת. אפשר לנסות את ההדגמה בינתיים." : "The live game is not available yet. You can try the preview meanwhile.";
  return he ? "לא הצלחנו לעדכן את המשחק. רעננו כדי לבדוק מה נשמר לפני ניסיון נוסף." : "Unable to update the game. Refresh to check what was saved before trying again.";
}

export function DuelWorkspace({ client, lang, demo = false, invite = "", controls, avatar }: {
  client: DuelClient; lang: DuelLanguage; demo?: boolean; invite?: string; controls?: React.ReactNode; avatar?: AvatarConfig | null;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [list, setList] = useState<DuelList | null>(null);
  const [wallet, setWallet] = useState<DuelWallet | null>(null);
  const [duel, setDuel] = useState<Duel | null>(null);
  const [code, setCode] = useState(invite);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [tick, setTick] = useState(0);
  const clock = useRef({ seconds: 0, receivedAt: 0 });
  const mounted = useRef(false);
  const selected = useRef<string | null>(null);
  const revision = useRef(0);
  const mutating = useRef(false);
  const polling = useRef(false);
  const inviteConsumed = useRef(false);
  const questionHeading = useRef<HTMLHeadingElement>(null);
  const currentIndex = duel?.quiz?.index;

  function show(value: Duel) {
    selected.current = value.id;
    clock.current = { seconds: value.quiz?.seconds_left ?? 0, receivedAt: performance.now() };
    setDuel(value); setTick(performance.now());
  }
  function remember(id: string | null) {
    const path = demo ? "/games/preview" : "/games";
    window.history.replaceState(null, "", id ? `${path}?duel=${encodeURIComponent(id)}` : path);
  }
  const refresh = useCallback(async () => {
    if (mutating.current || polling.current) return;
    polling.current = true;
    const version = revision.current;
    const id = selected.current;
    try {
      const [rows, balance, active] = await Promise.all([client.list(), client.wallet(lang), id ? client.get(id) : Promise.resolve(null)]);
      if (!mounted.current || version !== revision.current || mutating.current) return;
      setList(rows); setWallet(balance); setLoaded(true);
      const resumed = active ?? (!selected.current && invite && !inviteConsumed.current ? rows.duels.find(d => d.code === invite) : null);
      if (resumed) { inviteConsumed.current = true; show(resumed); }
    } catch (e) { if (mounted.current && version === revision.current) { setError(errorMessage(e, lang)); setLoaded(true); } }
    finally { polling.current = false; }
  }, [client, lang, invite]);
  const latestRefresh = useRef(refresh);
  latestRefresh.current = refresh;

  useEffect(() => {
    mounted.current = true;
    selected.current = new URLSearchParams(window.location.search).get("duel");
    void latestRefresh.current();
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void latestRefresh.current(); }, 2000);
    const visible = () => { if (document.visibilityState === "visible") void latestRefresh.current(); };
    document.addEventListener("visibilitychange", visible);
    return () => { mounted.current = false; revision.current++; window.clearInterval(timer); document.removeEventListener("visibilitychange", visible); };
  }, [client, invite]);
  useEffect(() => {
    if (!duel?.quiz?.current || duel.status !== "active") return;
    const timer = window.setInterval(() => setTick(performance.now()), 250);
    return () => window.clearInterval(timer);
  }, [duel?.id, duel?.status, currentIndex, duel?.quiz?.current]);
  useEffect(() => { if (currentIndex !== undefined && duel?.quiz?.current) questionHeading.current?.focus(); }, [duel?.id, currentIndex]);

  async function act(action: () => Promise<Duel>) {
    if (mutating.current) return;
    mutating.current = true; revision.current++;
    const version = revision.current;
    setBusy(true); setError(""); setCopied(false);
    try {
      const value = await action();
      if (mounted.current && version === revision.current) { show(value); remember(value.id); }
    } catch (e) { if (mounted.current && version === revision.current) setError(errorMessage(e, lang)); }
    finally {
      mutating.current = false;
      if (mounted.current && version === revision.current) { setBusy(false); void refresh(); }
    }
  }
  async function choose(value: Duel) {
    if (mutating.current) return;
    revision.current++; show(value); remember(value.id); setError(""); setCopied(false); void refresh();
  }
  function home() { if (mutating.current) return; revision.current++; inviteConsumed.current = true; selected.current = null; setDuel(null); setError(""); remember(null); void refresh(); }
  const seconds = quizSecondsLeft(clock.current.seconds, clock.current.receivedAt, tick);

  const rules = list?.rules;
  const serverReady = rules?.readiness_required === true;
  const available = !!rules?.quiz_available && !!wallet?.enabled && serverReady;
  const enough = (wallet?.balance ?? 0) >= (rules?.stake ?? 5);
  const quiz = duel?.quiz;
  const lobby = duel?.status === "active" && !duel.deadline;
  const running = duel?.status === "active" && !!duel.deadline;
  const settled = duel?.status === "settled";
  const shareUrl = duel && !demo ? `${typeof window === "undefined" ? "" : window.location.origin}/duel/${encodeURIComponent(duel.code)}` : "";
  const Back = lang === "he" ? ArrowRight : ArrowLeft;
  const statusLabel = (d: Duel) => d.status === "open" ? t("ממתינים לחבר", "Waiting for a friend") : d.status === "cancelled" ? t("בוטל · המטבעות הוחזרו", "Cancelled · coins refunded") : d.status === "settled" ? d.won === true ? t("ניצחתם", "You won") : d.won === false ? t("החבר ניצח", "Your friend won") : t("תיקו · המטבעות הוחזרו", "Draw · coins refunded") : d.deadline ? t("במשחק", "In progress") : t("בחדר ההמתנה", "In the lobby");

  return <div className={styles.shell} dir={lang === "he" ? "rtl" : "ltr"}>
    <header className={styles.header}>
      <a className={styles.brand} href="/">JobRun<span>{t("משחקים", "Games")}</span></a>
      <FeatureNav lang={lang} avatar={duel?.me.avatar ?? avatar ?? DEFAULT_AVATAR} demo={demo} current="games" />
      <div className={styles.controls}><button type="button" aria-label={t("דיווח על בעיה", "Report a problem")} title={t("דיווח על בעיה", "Report a problem")} aria-haspopup="dialog" onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={18} aria-hidden="true" /></button>{controls}</div>
    </header>
    <main className={styles.main}>
      <div className={styles.topline}>
        {duel ? <button className={styles.textButton} onClick={home} disabled={busy}><Back size={17} />{t("לכל המשחקים", "All games")}</button> : <a className={styles.textButton} href="/"><Back size={17} />{t("בחזרה לתרגול", "Back to practice")}</a>}
        <span className={styles.wallet}><Coins size={18} aria-hidden="true" />{wallet?.enabled ? wallet.balance : "—"} {t(demo ? "מטבעות הדגמה" : "מטבעות", demo ? "demo coins" : "coins")}</span>
      </div>
      {demo && <aside className={styles.demoNotice}><strong>{t("תצוגה מקדימה", "Game preview")}</strong><span>{t("משחק מול יריב מדומה, עם שאלות בטיוטה ומטבעות הדגמה בלבד.", "A simulated opponent, draft questions and demo coins only.")}</span><a href="/games">{t("למשחקים באתר", "Live games")}</a></aside>}
      {!demo && <p className={styles.notice}>{t("שאלות המשחק בפיילוט; בדיקה מקצועית עדיין ממתינה.", "Game questions are in pilot; professional review is still pending.")}</p>}
      {error && <div className={styles.error} role="alert"><span>{error}</span><button onClick={() => { setError(""); void refresh(); }} disabled={busy}><RefreshCw size={16} />{t("רענון מצב", "Refresh status")}</button></div>}
      {!loaded && <p className={styles.loading} role="status">{t("טוענים את חדר המשחקים…", "Loading your games…")}</p>}
      {!duel && <>
        <div className={styles.intro}><Swords size={36} strokeWidth={1.5} aria-hidden="true" /><h1>{t("חמש שאלות. חבר מול חבר.", "Five questions. Friend vs friend.")}</h1><p>{t("אותן שאלות, אותו אתגר. עונים נכון, חושבים מהר ומגלים מי לקח את הסיבוב.", "The same questions, the same challenge. Answer correctly, think quickly and see who wins.")}</p></div>
        <div className={styles.rules}><span>{rules?.quiz_questions ?? 5} {t("שאלות", "questions")}</span><span>{rules?.quiz_seconds_per_question ?? 60} {t("שניות לשאלה", "seconds per question")}</span><span>{rules?.stake ?? 5} {t("מטבעות מכל צד", "coins each")}</span></div>
        {loaded && !available && <p className={styles.notice}>{!wallet?.enabled ? t("מערכת המטבעות עדיין אינה פעילה בשרת. אפשר להתרשם מהמשחק בתצוגה המקדימה.", "The coin system is not active on the server yet. Explore the game in the preview.") : !serverReady ? t("השרת ממתין לעדכון המשחק עם חדר המוכנות. בינתיים אפשר לנסות את ההדגמה.", "The server needs the game update with the ready room. You can try the preview meanwhile.") : t("מאגר המשחק ממתין לאישור השאלות. המשחק האמיתי ייפתח כשיהיו מספיק שאלות מאושרות.", "The game bank is awaiting question review. Live play opens when enough questions are approved.")} <a href="/games/preview">{t("לנסות את ההדגמה", "Try the preview")}</a></p>}
        <div className={styles.joinGrid}>
          <section className={styles.challenge}><h2>{t("מזמינים חבר לדו־קרב", "Challenge a friend")}</h2><p>{t(demo ? "היריב המדומה יצטרף אוטומטית. שניכם תתכוננו לפני שהשעון יתחיל." : "יוצרים הזמנה ושולחים את הקישור. השעון מתחיל רק אחרי ששניכם מוכנים.", demo ? "The simulated friend joins automatically. Get ready before the clock starts." : "Create an invite and share the link. The clock starts only when both of you are ready.")}</p><button className={styles.primary} disabled={busy || !available || !enough} onClick={() => void act(() => client.create(lang))}><Swords size={18} />{busy ? t("מכינים הזמנה…", "Creating invite…") : t(demo ? "להתחיל משחק הדגמה" : "אתגר חבר", demo ? "Start demo game" : "Challenge friend")}</button>{available && !enough && <p className={styles.notice}>{t("אין מספיק מטבעות. מרוויחים מטבעות מתשובות חזקות בתרגול.", "Not enough coins. Strong practice answers earn coins.")}</p>}</section>
          {!demo && <section className={styles.join}><h2>{t("קיבלתם הזמנה?", "Got an invite?")}</h2><form onSubmit={e => { e.preventDefault(); void act(() => client.accept(inviteCode(code))); }}><label htmlFor="duel-code">{t("קוד המשחק או קישור ההזמנה", "Game code or invite link")}</label><input id="duel-code" value={code} onChange={e => setCode(e.target.value)} dir="ltr" autoComplete="off" spellCheck={false} maxLength={300} placeholder="abcdefgh" /><button disabled={busy || !available || !enough || !/^[a-z0-9]{4,16}$/i.test(inviteCode(code))}>{t("להצטרף", "Join game")} · {rules?.stake ?? 5} {t("מטבעות", "coins")}</button></form></section>}
        </div>
        <section className={styles.history}><div className={styles.sectionHeading}><h2>{t("המשחקים שלי", "My games")}</h2><button className={styles.textButton} disabled={busy} onClick={() => void refresh()}><RefreshCw size={16} />{t("רענון", "Refresh")}</button></div>{list?.duels.length ? <ul>{list.duels.map(d => <li key={d.id}><button onClick={() => void choose(d)} disabled={busy}><span><strong>{statusLabel(d)}</strong><span>{new Date(d.created_at).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB")} · <bdi>{d.code}</bdi></span></span><span dir="ltr">{d.coins_delta !== null ? `${d.coins_delta > 0 ? "+" : ""}${d.coins_delta}` : d.stake} <Coins size={16} aria-hidden="true" /></span></button></li>)}</ul> : <p className={styles.muted}>{t("המשחק הראשון שלכם מתחיל בהזמנה לחבר.", "Your first game starts with an invite to a friend.")}</p>}</section>
      </>}
      {duel && <div className={styles.game}>
        {lang !== duel.language && <p className={styles.notice}>{t("שפת השאלות נקבעת בעת יצירת המשחק. החלפת שפת הממשק אינה משנה את השאלות במשחק הזה.", "Question language is fixed when the game is created. Changing the interface language does not change this game's questions.")}</p>}
        {(duel.status === "open" || lobby) && <section className={styles.lobby}><Users size={38} strokeWidth={1.4} aria-hidden="true" /><h1>{duel.status === "open" ? t("מקום שמור לחבר", "A place for your friend") : t("שניכם כאן. מוכנים?", "Both here. Ready?")}</h1><p>{duel.status === "open" ? t(demo ? "היריב המדומה בדרך לחדר שלכם…" : "שלחו את הקישור לחבר. אחרי שיצטרף, שניכם תאשרו שאתם מוכנים.", demo ? "The simulated friend is joining your room…" : "Share this link with your friend. Once they join, both of you can get ready.") : t("חמש שאלות שונות, עד דקה לכל שאלה. השעון יתחיל ברגע ששני הצדדים ילחצו על מוכנים.", "Five different questions, up to a minute each. The clock starts when both players press Ready.")}</p>
          {duel.status === "open" && !demo && <div className={styles.invite}><label htmlFor="duel-share">{t("קישור ההזמנה", "Invite link")}</label><input id="duel-share" value={shareUrl} readOnly dir="ltr" onFocus={e => e.target.select()} /><button onClick={() => { void navigator.clipboard?.writeText(shareUrl).then(() => setCopied(true)).catch(() => setCopied(false)); }}>{copied ? <Check size={17} /> : <Copy size={17} />}{copied ? t("הקישור הועתק", "Link copied") : t("העתקת קישור", "Copy invite")}</button><small>{t("אפשר גם לשלוח את הקוד:", "Or share the code:")} <bdi>{duel.code}</bdi></small></div>}
          {lobby && <><div className={styles.players}><div><LogicAvatar config={duel.me.avatar ?? avatar ?? DEFAULT_AVATAR} size={170} facing={lang === "he" ? "left" : "right"} className={avatarStyles.avatar} /><strong>{t("אתם", "You")}</strong><span>{duel.me.ready ? <CheckCheck size={20} /> : <Clock3 size={20} />}{duel.me.ready ? t("מוכנים", "Ready") : t("מתכוננים", "Getting ready")}</span></div><Swords size={24} aria-hidden="true" /><div><LogicAvatar config={duel.opponent?.avatar ?? DEFAULT_AVATAR} size={170} facing={lang === "he" ? "right" : "left"} className={avatarStyles.avatar} /><strong>{t(demo ? "יריב מדומה" : "החבר", demo ? "Demo opponent" : "Your friend")}</strong><span>{duel.opponent?.ready ? <CheckCheck size={20} /> : <Clock3 size={20} />}{duel.opponent?.ready ? t("מוכנים", "Ready") : t("מתכוננים", "Getting ready")}</span></div></div><DuelLooks me={duel.me.avatar ?? avatar ?? DEFAULT_AVATAR} opponent={duel.opponent?.avatar ?? DEFAULT_AVATAR} lang={lang}/><button className={styles.primary} disabled={busy || duel.me.ready} onClick={() => void act(() => client.ready(duel.id))}>{duel.me.ready ? t("ממתינים שהחבר יהיה מוכן…", "Waiting for your friend…") : t("מוכנים, אפשר להתחיל", "Ready to play")}</button><p className={styles.muted}>{t("אפשר לבטל ולקבל את המטבעות בחזרה עד תחילת המשחק. החדר פג אחרי עשר דקות ללא התחלה.", "Cancel for a full refund before the game starts. An unstarted lobby expires after ten minutes.")}</p></>}
          <button className={styles.textButton} disabled={busy} onClick={() => void act(() => client.cancel(duel.id))}><X size={16} />{t("ביטול והחזרת המטבעות", "Cancel and refund coins")}</button>
        </section>}
        {running && <>
          <div className={styles.scoreboard}><div><LogicAvatar config={duel.me.avatar ?? avatar ?? DEFAULT_AVATAR} size={54} facing={lang === "he" ? "left" : "right"} className={avatarStyles.avatar} /><span>{t("הניקוד שלכם", "Your score")}</span><strong dir="ltr">{quiz?.score ?? 0}<small> / {quiz?.total ?? 5}</small></strong></div><Swords size={23} aria-hidden="true" /><div><LogicAvatar config={duel.opponent?.avatar ?? DEFAULT_AVATAR} size={54} facing={lang === "he" ? "right" : "left"} className={avatarStyles.avatar} /><span>{t("התקדמות החבר", "Friend's progress")}</span><strong dir="ltr">{duel.opponent?.answered_count ?? 0}<small> / {quiz?.total ?? 5}</small></strong></div></div>
          {quiz?.current ? <section className={styles.question} aria-busy={busy} lang={duel.language} dir={duel.language === "he" ? "rtl" : "ltr"}>
            <div className={styles.questionTop}><span>{t("שאלה", "Question")} {quiz.index + 1} {t("מתוך", "of")} {quiz.total}</span><span className={`${styles.timer} ${seconds <= 10 ? styles.urgent : ""}`} role="timer" aria-live="off"><Clock3 size={18} aria-hidden="true" /><bdi>{String(Math.floor(seconds / 60)).padStart(2, "0")}:{String(seconds % 60).padStart(2, "0")}</bdi></span></div>
            <div className={styles.timeTrack} aria-hidden="true"><span style={{ transform: `scaleX(${Math.max(0, seconds / quiz.seconds_per_question)})` }} /></div>
            {quiz.answers.length > 0 && <p className={quiz.answers.at(-1)?.correct ? styles.correctNote : styles.muted} role="status">{quiz.answers.at(-1)?.correct ? t("התשובה הקודמת נכונה", "Previous answer correct") : t("התשובה הקודמת לא זיכתה בנקודה. ממשיכים!", "No point for the previous answer. Keep going!")}</p>}
            <h1 ref={questionHeading} tabIndex={-1}><BidiText>{quiz.current.prompt}</BidiText></h1>
            <div className={styles.choices}>{quiz.current.choices.map((choice, index) => <button key={`${quiz.current!.key}-${index}`} disabled={busy || seconds === 0 || !!error} onClick={() => void act(() => client.answer(duel.id, index, quiz.index))}><span className={styles.choiceNumber}>{lang === "he" ? ["א", "ב", "ג", "ד"][index] : ["A", "B", "C", "D"][index]}</span><BidiText>{choice}</BidiText></button>)}</div>
            <p className={styles.muted}>{seconds === 0 ? t("הזמן הסתיים. טוענים את השאלה הבאה…", "Time is up. Loading the next question…") : busy ? t("שומרים את הבחירה…", "Saving your choice…") : t("לחיצה על תשובה שולחת אותה מיד. אי אפשר לשנות בחירה שנשלחה.", "Selecting an answer submits it immediately. Submitted choices cannot be changed.")}</p>
          </section> : <section className={styles.waiting}><CheckCheck size={42} aria-hidden="true" /><h1>{t("סיימתם את החמש", "Your five are done")}</h1><p>{t("החבר עדיין משחק. התוצאה וההסברים יופיעו כששניכם תסיימו.", "Your friend is still playing. Results and explanations appear when both players finish.")}</p></section>}
        </>}
        {settled && <>
          <section className={`${styles.result} ${duel.won === true ? styles.won : ""}`}><Swords size={38} aria-hidden="true" /><h1>{statusLabel(duel)}</h1><p>{duel.outcome?.startsWith("forfeit_") ? t("אחד הצדדים לא השלים את המשחק בזמן.", "One player did not complete the game in time.") : duel.outcome === "no_show" ? t("אף צד לא ענה בזמן. המטבעות הוחזרו.", "Neither player answered in time. Coins were refunded.") : t("קודם תשובות נכונות, אחר כך זמן המענה הכולל.", "Correct answers first, then total answering time.")}</p><div className={styles.players}><div><LogicAvatar config={duel.me.avatar ?? avatar ?? DEFAULT_AVATAR} size={170} facing={lang === "he" ? "left" : "right"} className={avatarStyles.avatar} /><strong>{t("אתם", "You")}</strong><b dir="ltr">{duel.me.score ?? 0} / {quiz?.total ?? 5}</b><span>{(duel.me.seconds ?? 0).toFixed(1)} {t("שניות", "seconds")}</span></div><span className={styles.versus}>:</span><div><LogicAvatar config={duel.opponent?.avatar ?? DEFAULT_AVATAR} size={170} facing={lang === "he" ? "right" : "left"} className={avatarStyles.avatar} /><strong>{t("החבר", "Your friend")}</strong><b dir="ltr">{duel.opponent?.score ?? 0} / {quiz?.total ?? 5}</b><span>{(duel.opponent?.seconds ?? 0).toFixed(1)} {t("שניות", "seconds")}</span></div></div><DuelLooks me={duel.me.avatar ?? avatar ?? DEFAULT_AVATAR} opponent={duel.opponent?.avatar ?? DEFAULT_AVATAR} lang={lang}/><p className={styles.resultCoins}><Coins size={21} aria-hidden="true" /><bdi dir="ltr">{(duel.coins_delta ?? 0) > 0 ? "+" : ""}{duel.coins_delta ?? 0}</bdi> {t(demo ? "מטבעות הדגמה" : "מטבעות", demo ? "demo coins" : "coins")}</p><p className={styles.muted}>{t("המשחק אינו משנה XP או את פרופיל המיומנויות שלכם.", "This game does not change your XP or skill profile.")}</p><button className={styles.primary} onClick={home}>{t("חזרה לחדר המשחקים", "Back to games")}</button></section>
          {quiz?.review.length ? <section className={styles.review} lang={duel.language} dir={duel.language === "he" ? "rtl" : "ltr"}><h2>{t("חוזרים לשאלות", "Review the questions")}</h2>{quiz.review.map((item, index) => <article key={item.key ?? index}><div className={styles.reviewTop}><span>{t("שאלה", "Question")} {index + 1}</span><span className={item.mine_correct ? styles.correctNote : styles.muted}>{item.mine_correct ? t("עניתם נכון", "You answered correctly") : item.mine === null ? t("ללא תשובה", "No answer") : t("עניתם לא נכון", "Your answer was incorrect")}</span></div><h3><BidiText>{item.prompt}</BidiText></h3><ol>{item.choices.map((choice, i) => <li key={i} className={i === item.correct ? styles.correctChoice : undefined}><BidiText>{choice}</BidiText><span>{i === item.correct && <><Check size={15} />{t("נכון", "Correct")}</>}{i === item.mine && <span>{t("הבחירה שלכם", "Your choice")}</span>}{i === item.theirs && <span>{t("בחירת החבר", "Friend's choice")}</span>}</span></li>)}</ol><p><BidiText>{item.explanation}</BidiText></p></article>)}</section> : null}
        </>}
        {duel.status === "cancelled" && <section className={styles.waiting}><h1>{statusLabel(duel)}</h1><p>{t("אפשר לפתוח הזמנה חדשה ולשחק שוב.", "You can open a new invite and play again.")}</p><button onClick={home}>{t("למשחקים", "Back to games")}</button></section>}
      </div>}
      <footer className={styles.footer}>{t("למטבעות אין ערך כספי. אי אפשר לקנות או לפדות אותם.", "Coins have no monetary value. They cannot be bought or cashed out.")}</footer>
    </main>
  </div>;
}
