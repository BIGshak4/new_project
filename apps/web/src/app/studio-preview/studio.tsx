"use client";

import { useState, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronLeft, CircuitBoard, Code2, Columns2, Lightbulb, Search, SlidersHorizontal, Target, Timer } from "lucide-react";
import { studioDirections, type StudioVariant } from "./directions";
import s from "./studio.module.css";

const questions = [
  { id: "mux", title: "שני קלטים. החלטה אחת.", topic: "מרבבים", category: "חומרה", company: "Intel", alias: "אינטל", minutes: 12,
    prompt: "נתון מרבב 2:1 עם הקלטים A ו־B וקו הבחירה S. כתבו ביטוי לוגי למוצא Y, הסבירו מה קורה כאשר S משתנה, ובנו את טבלת האמת.",
    hint: "הפרידו לשני מקרים: S=0 ו־S=1. בכל מקרה רק אחד משני הקלטים צריך להגיע למוצא.", code: "assign y = s ? b : a;" },
  { id: "bits", title: "כמה ביטים דלוקים?", topic: "אריתמטיקה בינארית", category: "חומרה", company: "NVIDIA", alias: "אנבידיה נווידיה", minutes: 15,
    prompt: "הקלט הוא מילה בת 8 ביטים. תכננו מעגל קומבינטורי שסופר כמה ביטים שווים ל־1. מה רוחב המוצא הדרוש? הסבירו איך אפשר לחבר תוצאות ביניים במקביל.",
    hint: "התוצאה יכולה להיות כל מספר מ־0 עד 8. אפשר להתחיל מספירת זוגות ואז לחבר את הסכומים.", code: "// Input: 8 bits\n// Output: number of ones" },
  { id: "array", title: "האיבר שלא הגיע", topic: "מערכים", category: "תוכנה", company: "Microsoft", alias: "מיקרוסופט", minutes: 15,
    prompt: "מערך מכיל את המספרים 0 עד n, למעט מספר אחד, ללא כפילויות. מצאו את המספר החסר בזמן ליניארי ובזיכרון נוסף קבוע. הסבירו אילו הנחות הפתרון דורש.",
    hint: "מה קורה כשמבצעים XOR על כל המספרים בטווח ועל כל איברי המערך?", code: "def missing_number(values):\n    # Explain your approach\n    pass" },
  { id: "fsm", title: "לזהות רצף, גם כשהוא חופף", topic: "מכונות מצבים", category: "חומרה", company: "Apple", alias: "אפל", minutes: 20,
    prompt: "תכננו גלאי לרצף 101 בזרם ביטים. יש לזהות גם הופעות חופפות. הגדירו מצבים, מעברים ואות מוצא. בדקו את המימוש על הרצף 10101.",
    hint: "כל מצב יכול לייצג את הקידומת הארוכה ביותר של 101 שכבר ראינו ועדיין רלוונטית.", code: "// Track the matched prefix:\n// none → 1 → 10" },
  { id: "list", title: "שתי רשימות נפגשות", topic: "מבני נתונים", category: "תוכנה", company: "Google", alias: "גוגל", minutes: 20,
    prompt: "נתונות שתי רשימות מקושרות ללא מעגלים. ייתכן שיש להן זנב משותף. מצאו את הצומת הראשון המשותף בלי לשנות את הרשימות ובזיכרון נוסף קבוע.",
    hint: "חשבו איך שני מצביעים יכולים לעבור מרחק כולל זהה, גם כשאורכי הרשימות שונים.", code: "// Compare node identity,\n// not only stored values." },
  { id: "logic", title: "בדיקה אחת שמבדילה", topic: "חשיבה לוגית", category: "היגיון", company: "Intel", alias: "אינטל", minutes: 8,
    prompt: "קופסה מחשבת AND או OR של שני ביטים, ואינכם יודעים איזו פעולה הותקנה. בחרו זוג קלטים אחד שמאפשר לזהות בוודאות את הפעולה, והסבירו למה.",
    hint: "חפשו שורה שבה טבלאות האמת של AND ושל OR שונות.", code: "A = ?\nB = ?" },
];
type Question = typeof questions[number];
const topics = ["הכל", "חומרה", "תוכנה", "היגיון"];
const roles = ["תכנון דיגיטלי", "וריפיקציה", "תוכנה משובצת"];

function Mux({ a, b, select, change }: { a: number; b: number; select: number; change: (key: "a" | "b" | "select") => void }) {
  const y = select ? b : a;
  return <div className={s.mux} dir="ltr" aria-label="ניסוי מרבב 2 ל־1">
    <div className={s.muxInputs}>
      <button aria-label={`קלט A: ${a}`} aria-pressed={!!a} onClick={() => change("a")} data-active={!select}><span>A</span><b>{a}</b></button>
      <button aria-label={`קלט B: ${b}`} aria-pressed={!!b} onClick={() => change("b")} data-active={!!select}><span>B</span><b>{b}</b></button>
    </div>
    <div className={s.connections} aria-hidden="true"><i data-active={!select} /><i data-active={!!select} /></div>
    <div className={s.muxBody}><strong>MUX</strong><span>2 : 1</span><button aria-label={`קו בחירה S: ${select}`} aria-pressed={!!select} onClick={() => change("select")}>S <b>{select}</b></button></div>
    <div className={s.outputLine} aria-hidden="true" /><div className={s.muxOutput}><small>Y</small><output key={`${a}${b}${select}`} aria-live="polite">{y}</output></div>
  </div>;
}

function TruthTable({ a, b, select, choose }: { a: number; b: number; select: number; choose: (a: number, b: number, select: number) => void }) {
  return <table className={s.truth} dir="ltr"><caption>טבלת האמת — לחצו על שורה לבדיקה</caption><thead><tr><th>A</th><th>B</th><th>S</th><th>Y</th><th><span className={s.sr}>בחירת קלטים</span></th></tr></thead><tbody>{Array.from({ length: 8 }, (_, i) => {
    const av = (i >> 2) & 1, bv = (i >> 1) & 1, sv = i & 1;
    const active = a === av && b === bv && select === sv;
    return <tr key={i} data-selected={active}><td>{av}</td><td>{bv}</td><td>{sv}</td><td><b>{sv ? bv : av}</b></td><td><button aria-label={`בדיקת A=${av}, B=${bv}, S=${sv}`} aria-pressed={active} onClick={() => choose(av, bv, sv)}>{active ? <Check size={14} /> : <ChevronLeft size={14} />}</button></td></tr>;
  })}</tbody></table>;
}

function SignalPlot({ clock, tick }: { clock: number; tick: () => void }) {
  const traces = [Array.from({ length: 12 }, (_, i) => i % 2), [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1], [0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1]];
  return <div className={s.scope}><div className={s.scopeTitle}><h3>קוראים בין החזיתות.</h3><span dir="ltr">t = {clock} ns</span></div>
    <svg viewBox="0 0 600 230" role="img" aria-label={`תרשים תזמון, הסמן בזמן ${clock} ננו שניות`}>
      {Array.from({ length: 13 }, (_, i) => <g key={i}><line x1={66 + i * 40} y1="15" x2={66 + i * 40} y2="197" className={s.gridLine} /><text className={i % 2 ? s.minorTick : undefined} x={66 + i * 40} y="220" textAnchor="middle">{i}</text></g>)}
      {traces.map((values, row) => <g key={row}><text x="2" y={49 + row * 66}>{["CLK", "D", "Q"][row]}</text><path d={values.map((v, i) => `${i ? "L" : "M"}${66 + i * 40},${58 + row * 66 - v * 31}H${106 + i * 40}`).join(" ")} className={s.trace} /></g>)}
      <line x1="66" x2="66" y1="10" y2="197" style={{ transform: `translateX(${clock * 40}px)` }} className={s.cursor} />
    </svg><div className={s.scopeBottom}><p>מה נשמר במוצא אחרי חזית השעון?</p><button className={s.smallAction} onClick={tick}>צעד בזמן <ArrowLeft size={15} /></button></div></div>;
}

function Bits() {
  const [bits, setBits] = useState([1, 0, 1, 1, 0, 0, 1, 0]);
  const count = bits.reduce((sum, bit) => sum + bit, 0);
  return <div className={s.bitExperiment}><div className={s.bitLabels}><span>8 כניסות</span><span>מוצא של 4 ביטים</span></div><div className={s.bits} dir="ltr">{bits.map((bit, i) => <button key={i} aria-label={`ביט ${7 - i}: ${bit}`} aria-pressed={!!bit} onClick={() => setBits(old => old.map((v, n) => n === i ? 1 - v : v))}><small>{7 - i}</small>{bit}</button>)}</div><div className={s.bitResult}><div><span>מספר הביטים הדלוקים</span><output key={count} aria-live="polite">{count}</output></div><code dir="ltr">{count.toString(2).padStart(4, "0")}</code></div><p>החליפו ביט. עכשיו נסו לתכנן את המעגל שסופר אותם.</p></div>;
}

export function StudioPreview() {
  const params = useSearchParams();
  const variant: StudioVariant = studioDirections.find(d => d.id === params.get("variant"))?.id ?? "precision";
  const moving = params.get("motion") !== "0";
  const [view, setView] = useState("home");
  const [active, setActive] = useState<Question | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("הכל");
  const [company, setCompany] = useState("הכל");
  const [role, setRole] = useState(0);
  const [step, setStep] = useState(1);
  const [daily, setDaily] = useState(0);
  const [a, setA] = useState(1), [b, setB] = useState(0), [select, setSelect] = useState(0);
  const [clock, setClock] = useState(3);
  const [hint, setHint] = useState(false);
  const [answer, setAnswer] = useState("");
  const [saved, setSaved] = useState(false);
  const [sort, setSort] = useState(false);
  const defaultQuestion = variant === "workbench" ? questions[0] : null;
  const shown = active ?? (view === "home" ? defaultQuestion : null);
  const filtered = questions.filter(q => (category === "הכל" || q.category === category) && (company === "הכל" || q.company === company) && `${q.title} ${q.topic} ${q.category} ${q.company} ${q.alias}`.toLowerCase().includes(query.trim().toLowerCase()));
  if (sort) filtered.sort((x, y) => x.minutes - y.minutes);
  function open(q: Question) { setActive(q); setHint(false); setAnswer(""); setSaved(false); window.scrollTo({ top: 0, behavior: "instant" }); }
  function navigate(next: string) { setView(next); setActive(null); setHint(false); setSaved(false); window.scrollTo({ top: 0, behavior: "instant" }); }
  function change(key: "a" | "b" | "select") { if (key === "a") setA(1 - a); else if (key === "b") setB(1 - b); else setSelect(1 - select); }
  const mux = <Mux {...{ a, b, select, change }} />;
  const table = <TruthTable {...{ a, b, select }} choose={(av, bv, sv) => { setA(av); setB(bv); setSelect(sv); }} />;
  const plot = <SignalPlot clock={clock} tick={() => setClock(c => (c + 1) % 12)} />;
  const cta = (label = "נתחיל לתרגל", q = questions[0]) => <button className={s.primary} onClick={() => open(q)}>{label}<ArrowLeft size={18} /></button>;
  const metadata = (q: Question) => <div className={s.metadata}><span>{q.category}</span><span>{q.topic}</span><span>דיווח לדוגמה: <bdi>{q.company}</bdi></span></div>;
  const intro = (title: ReactNode, text: string, action = cta()) => <div className={s.intro}><h1>{title}</h1><p>{text}</p>{action}</div>;
  const library = <section className={s.library}><div className={s.libraryTitle}><div><h1>מוצאים את השאלה הבאה.</h1><p>לפי הנושא שמעניין אתכם, או החברה שאליה אתם מכוונים.</p></div><span>{filtered.length} שאלות בהדמיה</span></div>
    <div className={s.filterBar}><label className={s.search}><Search size={18} /><input aria-label="חיפוש שאלות בהדמיה" placeholder="נושא, שאלה או חברה…" value={query} onChange={e => setQuery(e.target.value)} /></label><button className={s.smallAction} aria-pressed={sort} onClick={() => setSort(!sort)}><SlidersHorizontal size={16} />{sort ? "זמן תרגול עולה" : "מיון לפי זמן"}</button></div>
    <div className={s.filterGroup}><div className={s.tabs} aria-label="תחום">{topics.map(t => <button key={t} aria-pressed={category === t} onClick={() => setCategory(t)}>{t}</button>)}</div><label className={s.companySelect}>חברה<select aria-label="סינון לפי חברה" value={company} onChange={e => setCompany(e.target.value)}>{["הכל", "Intel", "NVIDIA", "Apple", "Microsoft", "Google"].map(c => <option key={c}>{c}</option>)}</select></label></div>
    <div className={s.rows}>{filtered.map(q => <button className={s.questionRow} key={q.id} onClick={() => open(q)}><div><h3>{q.title}</h3>{metadata(q)}</div><span className={s.time}>{q.minutes} דק׳ <ChevronLeft size={18} /></span></button>)}{!filtered.length && <div className={s.empty}><h3>אין תוצאות לצירוף הזה.</h3><p>נסו נושא או חברה אחרים.</p><button className={s.smallAction} onClick={() => { setQuery(""); setCategory("הכל"); setCompany("הכל"); }}>ניקוי הסינון</button></div>}</div>
    <p className={s.disclosure}>השאלות ושיוכי החברות כאן הם תוכן לדוגמה לצורך בחירת העיצוב.</p></section>;
  const questionLinks = <section className={s.nextQuestions}><div className={s.sectionHead}><h2>עוד כיוון למחשבה.</h2><button className={s.linkButton} onClick={() => navigate("library")}>למאגר השאלות <ArrowLeft size={16} /></button></div><div>{questions.slice(1, 4).map(q => <button key={q.id} className={s.questionRow} onClick={() => open(q)}><div><h3>{q.title}</h3>{metadata(q)}</div><span className={s.time}>{q.minutes} דק׳ <ChevronLeft size={18} /></span></button>)}</div></section>;
  const editor = (q: Question) => <section className={s.editor}><div className={s.editorHeader}><Code2 size={18} /><h2>הפתרון שלכם</h2><span>טיוטת הדגמה</span></div><div className={s.editorTabs}><span>הסבר ודרך פתרון</span><code dir="ltr">{q.category === "תוכנה" ? "Python / C" : "Verilog / Logic"}</code></div><label className={s.sr} htmlFor="studio-answer">כתיבת הפתרון</label><textarea id="studio-answer" dir="auto" placeholder="מה ההנחות? איך ניגשים לפתרון? ואיך בודקים אותו?" value={answer} onChange={e => { setAnswer(e.target.value); setSaved(false); }} /><div className={s.editorBottom}><p>הדמיה בלבד — התשובה לא נשמרת ולא נבדקת.</p><button className={s.primary} disabled={!answer.trim()} onClick={() => setSaved(true)}>ניסיון שליחה <ArrowLeft size={17} /></button></div>{saved && <p className={s.success} role="status"><Check size={16} />השליחה הודגמה. לא בוצעה הערכה ולא נשמרה תשובה.</p>}</section>;
  const workspace = (q: Question) => <div className={s.workspace}><section className={s.questionPrompt}>{metadata(q)}<h1>{q.title}</h1><p>{q.prompt}</p><span className={s.duration}><Timer size={16} /> כ־{q.minutes} דקות</span><div className={s.promptTool}>{q.id === "mux" ? mux : q.id === "bits" ? <Bits /> : <pre dir="ltr">{q.code}</pre>}</div><button className={s.hintButton} aria-expanded={hint} onClick={() => setHint(!hint)}><Lightbulb size={17} />{hint ? "סגירת הרמז" : "אפשר רמז?"}</button>{hint && <p className={s.hint}>{q.hint}</p>}</section>{editor(q)}{variant === "workbench" && <aside className={s.workspaceAside}><h3>סדר למחשבה</h3><ol><li>מגדירים את הדרישה</li><li>מפרידים למקרים</li><li>בודקים את המוצא</li></ol><p>עוזר אישי יוכל להצטרף כאן בעתיד. בהדמיה הזו אין שיחת AI.</p></aside>}</div>;
  const brand = <a href="/design-lab" className={s.brand} aria-label="JobRun — חזרה להשוואת העיצובים" dir="ltr">jobrun<span>.</span></a>;
  const nav = <nav aria-label="ניווט בהדמיה"><button aria-current={view === "home" && !active ? "page" : undefined} onClick={() => navigate("home")}>המרחב שלי</button><button aria-current={view === "library" && !active ? "page" : undefined} onClick={() => navigate("library")}>מאגר השאלות</button></nav>;
  return <div className={`${s.root} ${s[variant]} ${moving ? s.moving : ""}`} dir="rtl">
    <div className={s.demoNotice}>הדמיית עיצוב · התוכן, החברות וההתקדמות להמחשה בלבד · ללא שמירה בחשבון</div>
    <div className={s.shell}>
      <header className={s.header}>{brand}{nav}<div className={s.profile}><span>ה</span><p>טוב שבאתם.</p></div></header>
      <main className={s.main}>
        {active && <button className={s.back} onClick={() => { setActive(null); setHint(false); setSaved(false); }}><ArrowRight size={16} />חזרה למרחב</button>}
        {shown ? workspace(shown) : view === "library" || variant === "index" ? library : <>
          {variant === "precision" && <><div className={s.precisionHero}>{intro(<>לחשוב ברור.<br /><em>להגיע מוכנים.</em></>, "תרגול ממוקד לראיונות חומרה ותוכנה. שאלה טובה, מקום לנסות, והזדמנות להבין קצת יותר.")}<section className={s.precisionStage}><div className={s.stageHeading}><h2>מה יעבור למוצא?</h2><span>מרבב 2:1</span></div>{mux}<div className={s.formula} dir="ltr">Y = S ? B : A</div><p>לחצו על הקלטים. עקבו אחרי הבחירה.</p></section></div><div className={s.topicBar}><span>בוחרים כיוון:</span>{["לוגיקה ספרתית", "מכונות מצבים", "תכנות", "חשיבה לוגית"].map((t, i) => <button key={t} onClick={() => open(questions[[0, 3, 2, 5][i]])}>{t}<ArrowLeft size={14} /></button>)}</div>{questionLinks}</>}
          {variant === "signal" && <><div className={s.signalIntro}>{intro(<>עוד רגע של הבנה.<br />עוד צעד לראיון.</>, "מסתכלים על האות, שואלים את השאלה הנכונה, ואז בודקים את הרעיון.", cta("פותחים את התרגול", questions[3]))}<aside><strong>מכונות מצבים</strong><p>מצב נוכחי · קלט · מצב הבא</p></aside></div>{plot}<div className={s.signalFooter}><span><CircuitBoard size={18} /> ניסוי תזמון אינטראקטיבי</span><button className={s.linkButton} onClick={() => open(questions[3])}>מהאות לשאלה <ArrowLeft size={16} /></button></div>{questionLinks}</>}
          {variant === "silicon" && <><div className={s.siliconIntro}>{intro(<>כל רעיון מתחיל<br />בביט אחד.</>, "מרחב לחשוב, לתכנן ולבדוק. מכאן מתחילה ההכנה לראיון הבא.")}</div><section className={s.siliconStage}><div className={s.siliconExperiment}><div><h2>הבחירה הקטנה שקובעת.</h2><p>שלוש כניסות. מוצא אחד. כל האפשרויות מולכם.</p></div>{mux}<code dir="ltr">assign y = s ? b : a;</code></div><div className={s.siliconTable}>{table}</div></section>{questionLinks}</>}
          {variant === "route" && <><div className={s.routeTitle}>{intro(<>הדרך שלכם,<br />צעד מדויק בכל פעם.</>, "לא צריך לעבור על הכל בבת אחת. מתחילים בנושא אחד ובונים עליו.", <button className={s.linkButton} onClick={() => navigate("library")}>או לבחור שאלה מהמאגר <ArrowLeft size={16} /></button>)}</div><nav className={s.routeSteps} aria-label="נושאי מסלול ההדגמה">{["ביטים ושערים", "בחירה ומרבבים", "זיכרון ומצבים", "תרגול מסכם"].map((t, i) => <button key={t} aria-pressed={step === i} onClick={() => setStep(i)}><span>{i === 0 ? <Check size={18} /> : i + 1}</span><strong>{t}</strong><small>{i === step ? "נבחר לצפייה" : "פתיחה"}</small></button>)}</nav><section className={s.routeLesson}><div><h2>{["איך בונים החלטה מביטים?", "בוחרים את הדרך למוצא.", "מה המעגל צריך לזכור?", "מחברים את כל מה שלמדנו."][step]}</h2><p>מפגש לדוגמה עם שאלה, ניסוי קטן ורמז כשצריך.</p>{cta("נכנסים למפגש", questions[[5, 0, 3, 1][step]])}</div><div>{step === 2 ? plot : mux}</div></section></>}
          {variant === "relay" && <><div className={s.relayLayout}><section className={s.relayChoice}><h1>לאן תרצו<br /><em>להגיע?</em></h1><p>בחרו תפקיד. נכוון את התרגול אל השאלות הרלוונטיות.</p><div className={s.roleList}>{roles.map((r, i) => <button key={r} aria-pressed={role === i} onClick={() => setRole(i)}><span>{r}</span><ArrowLeft size={20} /></button>)}</div><small>בחירת תפקיד להדגמה בלבד</small></section><section className={s.relayPlan}><div className={s.planTitle}><Target size={20} /><span>{roles[role]}</span></div><h2>{["מהביט הראשון\nלמעגל שלם.", "לשאול איפה\nזה יכול להישבר.", "קוד שמבין\nאת החומרה."][role]}</h2><p>{["מרבבים, חשיבה קומבינטורית ותכנון נכון של המוצא.", "מקרי קצה, כיסוי והבנת המעברים בין מצבים.", "מערכים, ביטים, זיכרון ודרך פתרון שאפשר להסביר."][role]}</p>{role === 2 ? <pre className={s.relayCode} dir="ltr">{questions[2].code}</pre> : mux}<div className={s.planActions}>{cta("מתחילים מכאן", questions[[0, 3, 2][role]])}<span>מפגש קצר, בקצב שלכם</span></div></section></div>{questionLinks}</>}
          {variant === "proof" && <><div className={s.proofHero}><div className={s.proofStatement}><h1>אל תנחשו.<br /><em>תראו למה.</em></h1><p>הדרך להסביר פתרון מתחילה ביכולת לבדוק אותו.</p>{cta("ננסח את ההסבר")}</div><div className={s.proofEquation} dir="ltr"><span>Y =</span><strong>{select ? "B" : "A"}</strong><small>when S = {select}</small></div></div><section className={s.proofLab}><div><h2>בוחרים מקרה. בודקים תוצאה.</h2>{mux}<p>הקלטים, הטבלה והביטוי מתעדכנים יחד.</p></div><div>{table}</div></section><div className={s.proofConclusion}><Lightbulb size={20} /><p>עכשיו השאלה המעניינת: איך מסבירים את זה למראיין?</p>{cta("לתרגול ההסבר")}</div></>}
          {variant === "vector" && <><div className={s.vectorHero}><section className={s.vectorTitle}><h1>יותר<br /><em>מפתרון.</em></h1><p>לדעת איך הגעתם אליו.<br />להבין למה הוא עובד.<br />להסביר אותו בביטחון.</p>{cta("חושבים על זה יחד", questions[1])}<span>תרגול לראיונות חומרה ותוכנה</span></section><section className={s.vectorExperiment}><h2>מ־8 ביטים<br />לרעיון אחד טוב.</h2><Bits /></section></div>{questionLinks}</>}
          {variant === "one" && <><section className={s.oneIntro}><h1>יש לכם רבע שעה?</h1><p>שאלה אחת. קצת ריכוז. משהו חדש לקחת להמשך היום.</p><div className={s.oneTopics}>{["מרבבים", "תכנות", "מכונות מצבים"].map((t, i) => <button key={t} aria-pressed={daily === i} onClick={() => setDaily(i)}>{t}</button>)}</div></section><section className={s.oneQuestion}><div className={s.oneHeading}><span><Timer size={16} /> {questions[[0, 2, 3][daily]].minutes} דקות</span><span>{questions[[0, 2, 3][daily]].category}</span></div><h2>{questions[[0, 2, 3][daily]].title}</h2><p>{questions[[0, 2, 3][daily]].prompt}</p>{daily === 0 ? mux : <pre dir="ltr">{questions[[0, 2, 3][daily]].code}</pre>}<div className={s.oneAction}>{cta("יש לי כיוון לפתרון", questions[[0, 2, 3][daily]])}<button className={s.linkButton} onClick={() => navigate("library")}>בא לי שאלה אחרת</button></div></section></>}
        </>}
      </main>
      <footer className={s.footer}><span>להבין. לתרגל. להגיע מוכנים.</span><a href="/design-lab">חזרה לעיצובים <Columns2 size={15} /></a></footer>
    </div>
  </div>;
}
