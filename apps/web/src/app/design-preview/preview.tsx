"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, BookOpen, Check, ChevronLeft, Code2, Lightbulb, Search, SlidersHorizontal, Target } from "lucide-react";
import styles from "./preview.module.css";

const questions = [
  { id: 1, title: "איך בונים XOR משני MUX?", category: "חומרה", topic: "לוגיקה קומבינטורית", company: "Intel", alias: "אינטל", minutes: 15, description: "לרשותכם שני מרבבים מסוג 2:1 והקבוע 0 בלבד. איך תממשו את הפעולה XOR בין שתי כניסות? נסחו את הבחירה בכל מרבב והסבירו את דרך החשיבה." },
  { id: 2, title: "המקום שבו שתי רשימות נפגשות", category: "תוכנה", topic: "מבני נתונים", company: "Microsoft", alias: "מיקרוסופט", minutes: 20, description: "שתי רשימות מקושרות עשויות לחלוק זנב משותף. מצאו את הצומת הראשון שמשותף לשתיהן בזיכרון נוסף קבוע. מה קורה כשאין חיתוך?" },
  { id: 3, title: "מאה מתגים, שאלה אחת", category: "היגיון", topic: "פתרון בעיות", company: "Google", alias: "גוגל", minutes: 10, description: "מאה נורות כבויות עומדות בשורה. בסיבוב k מחליפים את מצבה של כל נורה שמספרה מתחלק ב־k. אילו נורות יישארו דולקות אחרי מאה סיבובים, ולמה?" },
  { id: 4, title: "סופרים ביטים בלי לולאה", category: "חומרה", topic: "מחברים ומעגלים", company: "NVIDIA", alias: "אנבידיה נווידיה", minutes: 15, description: "תכננו מעגל שמקבל מילה בת שמונה ביטים ומחזיר את מספר הביטים שערכם 1. הציעו מימוש בעזרת מחברים והסבירו את רוחב המוצא." },
];
type Question = typeof questions[number];

export function Preview() {
  const params = useSearchParams();
  const variant = ["studio", "play", "index", "focus", "trail"].includes(params.get("variant") ?? "") ? params.get("variant")! : "studio";
  const moving = params.get("motion") !== "0";
  const [view, setView] = useState("today");
  const [active, setActive] = useState<Question | null>(null);
  const [filter, setFilter] = useState("הכל");
  const [query, setQuery] = useState("");
  const [a, setA] = useState(false);
  const [b, setB] = useState(true);
  const [answer, setAnswer] = useState("");
  const [hint, setHint] = useState(false);
  const [saved, setSaved] = useState(false);
  const filtered = questions.filter(q => (filter === "הכל" || q.category === filter) && `${q.title} ${q.company} ${q.alias} ${q.topic} ${q.category}`.toLowerCase().includes(query.trim().toLowerCase()));
  function open(q: Question) { setActive(q); setHint(false); setAnswer(""); setSaved(false); window.scrollTo({ top: 0, behavior: "instant" }); }
  function home(next: string) { setView(next); setActive(null); setHint(false); setSaved(false); }
  const cta = (label = "נתחיל לתרגל", q = questions[0]) => <button className={styles.primary} onClick={() => open(q)}>{label}<ArrowLeft size={18} /></button>;
  const tags = (q: Question) => <div className={styles.tags}><span>{q.category}</span><span>{q.topic}</span><span>נשאלה ב־<bdi>{q.company}</bdi></span></div>;
  const circuit = <div className={styles.circuit} aria-label="ניסוי שער XOR"><div className={styles.inputs}>
    <button aria-label={`כניסה A: ${Number(a)}`} aria-pressed={a} onClick={() => setA(!a)}><bdi>A</bdi><strong>{Number(a)}</strong></button>
    <button aria-label={`כניסה B: ${Number(b)}`} aria-pressed={b} onClick={() => setB(!b)}><bdi>B</bdi><strong>{Number(b)}</strong></button>
  </div><div className={styles.wires} aria-hidden="true"><i /><i /></div><div className={styles.gate}><span>XOR</span><small>A ⊕ B</small></div><div className={styles.wire} aria-hidden="true" /><output key={`${a}-${b}`} className={styles.output} aria-live="polite">{Number(a !== b)}</output></div>;
  const search = <div className={styles.filters}><label className={styles.search}><Search size={18} /><input aria-label="חיפוש שאלות בהדמיה" value={query} onChange={e => setQuery(e.target.value)} placeholder="שאלה, נושא או חברה…" /></label><div className={styles.categories}>{["הכל", "חומרה", "תוכנה", "היגיון"].map(item => <button key={item} aria-pressed={filter === item} onClick={() => setFilter(item)}>{item}</button>)}</div></div>;
  const list = <div className={styles.questionList}>{filtered.map(q => <button className={styles.questionRow} key={q.id} onClick={() => open(q)}><div><h3>{q.title}</h3>{tags(q)}</div><span className={styles.duration}>{q.minutes} דקות <ChevronLeft size={19} /></span></button>)}{!filtered.length && <p className={styles.empty}>לא מצאנו שאלה מתאימה. נסו חברה או נושא אחר.</p>}</div>;
  const workspace = (q: Question, isFocus = false) => <div className={styles.workspace}><section className={styles.prompt}>
    <div className={styles.meta}><span>{q.category} / {q.topic}</span><span>{q.minutes} דקות</span></div><h1>{q.title}</h1><p>{q.description}</p>{tags(q)}
    {q.id === 1 && <div className={styles.experiment}>{circuit}<p>לחצו על הכניסות כדי לבדוק את טבלת האמת.</p></div>}
    <button className={styles.quiet} onClick={() => setHint(!hint)} aria-expanded={hint}><Lightbulb size={18} />{hint ? "סגירת הרמז" : "כיוון קטן למחשבה"}</button>
    {hint && <p className={styles.hint}>{q.id === 1 ? "התחילו משתי האפשרויות של A. כשהוא 0, מה צריך להופיע במוצא? וכשהוא 1?" : "נסו מקרה קטן שאפשר לבדוק ביד. מה נשאר נכון כשמגדילים אותו?"}</p>}
  </section><section className={styles.answer}><div className={styles.answerTitle}><Code2 size={20} /><h2>המקום לחשוב בקול</h2></div><p>הנחות, דרך הפתרון ובדיקה קצרה.</p><label htmlFor="demo-answer">הפתרון שלכם</label><textarea id="demo-answer" dir="auto" value={answer} onChange={e => { setAnswer(e.target.value); setSaved(false); }} placeholder="הייתי מתחיל/ה מ…" />
    <button className={styles.primary} disabled={!answer.trim()} onClick={() => setSaved(true)}><Check size={18} />בדיקת חוויית השליחה</button><p className={styles.saved} role="status">{saved ? "כך תיראה הודעת הצלחה. זו הדמיה: לא נשמרה תשובה ולא בוצעה הערכה." : "הדמיה בלבד — אין שמירה או הפעלה של עוזר AI."}</p>
    {isFocus && <span className={styles.focusHint}>כל מה שצריך, באותו מקום.</span>}
  </section></div>;

  return <div className={`${styles.preview} ${styles[variant]} ${moving ? styles.moving : ""}`} dir="rtl">
    <div className={styles.demoNotice}>הדמיית עיצוב · השאלות, שיוכי החברות וההתקדמות להמחשה בלבד</div>
    <header className={styles.nav}><a className={styles.brand} href="/design-lab" target="_top">jobrun<span>.</span></a><nav aria-label="ניווט בהדמיה"><button aria-current={view === "today" && !active ? "page" : undefined} onClick={() => home("today")}>היום שלי</button><button aria-current={view === "library" && !active ? "page" : undefined} onClick={() => home("library")}>מאגר השאלות</button></nav><span className={styles.avatar} aria-label="משתמש לדוגמה">ה</span></header>
    <main className={styles.main}>
      {active ? <><button className={styles.back} onClick={() => setActive(null)}>חזרה לתצוגה <ArrowLeft size={17} /></button>{workspace(active)}</>
      : view === "library" ? <section className={styles.library}><h1>שאלה טובה. התחלה טובה.</h1><p>בחרו משהו שמסקרן אתכם, ותנו למחשבה מקום.</p>{search}{list}<p className={styles.sourceNote}>במוצר, שיוך חברות מבוסס על דיווחי אנשים ומקורות הכנה. השיוכים כאן הם להמחשת העיצוב.</p></section>
      : variant === "studio" ? <><div className={styles.studioHero}><section><h1>קצת תרגול.<br />הרבה יותר ביטחון.</h1><p>לא צריך לדעת הכל היום. נתחיל משאלה אחת, נבין את הדרך ונמשיך משם.</p>{cta()}<p className={styles.softNote}>רבע שעה של ריכוז, בקצב שלכם.</p></section><section className={styles.studioFeature}><div className={styles.featureTitle}><BookOpen size={20} /><span>על שולחן העבודה</span></div><h2>מתי שני ביטים<br />מספרים סיפור אחר?</h2>{circuit}<p>ניסוי קטן בלוגיקה. החליפו את ערכי הכניסות.</p><button className={styles.textLink} onClick={() => open(questions[0])}>מהניסוי לשאלת ראיון <ArrowLeft size={17} /></button></section></div><section className={styles.below}><div className={styles.sectionHead}><h2>לאן הסקרנות לוקחת אתכם?</h2><button className={styles.textLink} onClick={() => home("library")}>לכל השאלות <ArrowLeft size={17} /></button></div>{list}</section></>
      : variant === "play" ? <><div className={styles.playHero}><section><h1>בואו נדליק<br />משהו בראש.</h1><p>אתגר קטן להתחלה. נסו להדליק את המוצא — בכמה דרכים אפשר לעשות את זה?</p>{circuit}<p className={styles.signalStatus} role="status">{a !== b ? "בדיוק. כניסות שונות, מוצא דולק." : "כרגע הכניסות זהות. נסו לשנות אחת מהן."}</p>{cta("מוכנים לאתגר הבא?")}</section><aside className={styles.playAside}><span className={styles.bigGate} aria-hidden="true">⊕</span><h2>לטעות.<br />להבין.<br /><em>להצליח.</em></h2><p>כאן מותר לנסות שוב.</p></aside></div><div className={styles.playFooter}><span><Target size={19} /> בוחרים שאלה</span><span><Lightbulb size={19} /> מקבלים כיוון כשצריך</span><span><Check size={19} /> מבינים את הדרך</span></div></>
      : variant === "index" ? <div className={styles.indexLayout}><aside className={styles.indexAside}><h2>מקום לשאלות<br />שפותחות דלתות.</h2><p>הכנה לראיונות חומרה ותוכנה, מסודרת סביב מה שחשוב לכם עכשיו.</p><SlidersHorizontal size={25} /><p>בחרו תחום או חפשו חברה. כל שאלה שומרת את ההקשר שלה.</p></aside><section className={styles.indexContent}><div className={styles.indexTitle}><h1>הספרייה</h1><BookOpen size={38} /></div>{search}{list}<p className={styles.sourceNote}>השאלות והחברות כאן הן נתוני הדגמה. במאגר המלא יוצגו הדיווחים שנאספו.</p></section></div>
      : variant === "focus" ? <><div className={styles.focusTop}><span><Target size={16} /> זמן לחשוב לעומק</span><span>שאלת הדגמה · לוגיקה ספרתית</span></div>{workspace(questions[0], true)}</>
      : <div className={styles.trailLayout}><section className={styles.trailIntro}><h1>את הדרך לראיון<br />בונים בצעדים.</h1><p>קצת הבנה בכל פעם. היום מחברים בין מה שכבר יודעים לבין האתגר הבא.</p><div className={styles.planNote}><Target size={23} /><h2>הכיוון שלכם</h2><p>תכנון דיגיטלי<br />יסודות → חשיבה → תרגול</p></div><p className={styles.softNote}>מסלול לדוגמה. התוכנית האמיתית תתבסס על הלמידה שלכם.</p></section><section className={styles.path} aria-label="מסלול למידה לדוגמה"><div className={styles.pathLine} aria-hidden="true" />{[{ title: "מתחילים מהיסודות", sub: "לוגיקה קומבינטורית", icon: Check, q: questions[0] }, { title: "חושבים כמו מתכננים", sub: "מרבבים ודרך הפתרון", icon: Lightbulb, q: questions[0] }, { title: "מחברים את החלקים", sub: "מחברים וספירת ביטים", icon: Code2, q: questions[3] }].map((step, i) => <button className={`${styles.pathStep} ${i === 1 ? styles.currentStep : ""}`} key={step.title} onClick={() => open(step.q)}><span className={styles.node}><step.icon size={24} /></span><span><small>{i === 0 ? "חוזרים ומחזקים" : i === 1 ? "הצעד הבא" : "בהמשך הדרך"}</small><strong>{step.title}</strong><span>{step.sub}</span>{i === 1 && <span className={styles.pathAction}>נתחיל? <ArrowLeft size={18} /></span>}</span></button>)}</section></div>}
    </main><footer className={styles.footer}><span>לומדים איך לחשוב, לא רק מה לענות.</span><span>JobRun · הנדסה פוגשת סקרנות</span></footer>
  </div>;
}
