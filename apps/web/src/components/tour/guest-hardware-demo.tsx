"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowDown, CircuitBoard, RotateCcw } from "lucide-react";
import { type Circuit, type Kind, type Part, signalKey, simulate, truthTable } from "../../lib/circuit";
import { BidiText } from "../bidi-text";
import styles from "./guest-hardware-demo.module.css";

const CircuitEditor = dynamic(() => import("../circuit-editor"), { ssr: false });
type Lang = "he" | "en";

// A partial answer to the bank's example-sensor-majority interview question.
function sensorCircuit(): Circuit {
  const part = (id: string, kind: Kind, x: number, y: number, value = 0, count = 2): Part =>
    ({ id, label: id.toUpperCase(), kind, x, y, bits: 1, value, count });
  const wire = (source: string, sourcePort: string, target: string, targetPort: string) =>
    ({ id: `${source}-${target}-${targetPort}`, source, sourcePort, target, targetPort });
  return {
    version: 1,
    parts: [
      part("a", "input", 0, 0, 1), part("b", "input", 0, 155), part("c", "input", 0, 310),
      part("ab", "and", 260, 0), part("ac", "and", 260, 155), part("bc", "and", 260, 310),
      part("vote", "or", 510, 150, 0, 3), part("alarm", "output", 760, 150),
    ],
    wires: [
      wire("a", "Q", "ab", "A0"), wire("b", "Q", "ab", "A1"),
      wire("a", "Q", "ac", "A0"), wire("c", "Q", "ac", "A1"),
      wire("b", "Q", "bc", "A0"), wire("c", "Q", "bc", "A1"),
      wire("ac", "Y", "vote", "A1"), wire("bc", "Y", "vote", "A2"), wire("vote", "Y", "alarm", "D"),
    ],
  };
}

function hasLastWire(circuit: Circuit) {
  return circuit.wires.some(w => w.source === "ab" && w.sourcePort === "Y" && w.target === "vote" && w.targetPort === "A0");
}

function showsFirstPair(circuit: Circuit) {
  const bits = ["a", "b", "c"].map(id => circuit.parts.find(p => p.id === id)?.value);
  return bits[0] === 1 && bits[1] === 1 && bits[2] === 0 && simulate(circuit).signals[signalKey("alarm", "display")] === 1;
}

function isMajorityTable(circuit: Circuit) {
  const table = truthTable(circuit);
  if (!table.ok || table.rows.length !== 8 || table.inputs.length !== 3) return false;
  const alarm = table.outputs.findIndex(column => column.id === "alarm");
  return alarm >= 0 && table.rows.every(row => row.outputs[alarm] === Number(row.inputs.filter(Boolean).length >= 2));
}

type GuideTarget = "wire-open" | "wire-source" | "wire-target" | "wire-connect" | "component" | "input-toggle" | "truth-table";
function Cue({ target, children }: { target: GuideTarget; children: ReactNode }) {
  const ref = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    const element = ref.current;
    if (!element || target === "wire-open") return;
    const bounds = element.getBoundingClientRect();
    if (bounds.top < 85 || bounds.bottom > window.innerHeight - 140) {
      element.scrollIntoView({ block: "center", behavior: "instant" });
    }
  }, [target]);
  return <p ref={ref} className={styles.cue} data-guest-hardware-cue={target} role="status">
    <ArrowDown size={19} aria-hidden="true" /><span><BidiText>{children}</BidiText></span>
  </p>;
}

export function GuestHardwareDemo({ lang, onAction, guide }: {
  lang: Lang; onAction: (action: string) => void; guide?: ReactNode;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [open, setOpen] = useState(false);
  const [generation, setGeneration] = useState(0);
  const [circuit, setCircuit] = useState(sensorCircuit);
  const [wireOpen, setWireOpen] = useState(false);
  const [tested, setTested] = useState(false);
  const [done, setDone] = useState(false);
  const [invalidTable, setInvalidTable] = useState(false);
  const root = useRef<HTMLElement>(null);
  const wired = hasLastWire(circuit);
  const alarm = simulate(circuit).signals[signalKey("alarm", "display")];
  const title = t("הכרעת רוב בין שלושה חיישנים", "Two-out-of-three sensor vote");
  const question = t("שלושה חיישנים בשם A, B ו־C שולחים 1 כשיש תקלה. תכננו מעגל שמפעיל אזעקה אם לפחות שני חיישנים מדווחים על תקלה, ובדקו את כל צירופי הכניסות.",
    "Sensors A, B and C send 1 when they detect a fault. Design a circuit that raises an alarm when at least two sensors detect a fault, and check every input combination.");

  useEffect(() => {
    const owner = root.current;
    if (!owner) return;
    function readWirePanel(event: Event) {
      const details = event.target;
      if (details instanceof HTMLDetailsElement && details.dataset.muxiControl === "circuit-wire-details") setWireOpen(details.open);
    }
    owner.addEventListener("toggle", readWirePanel, true);
    return () => owner.removeEventListener("toggle", readWirePanel, true);
  }, []);

  useEffect(() => {
    const owner = root.current;
    if (!open || !owner) return;
    const observer = new MutationObserver(showCanvas);
    function showCanvas() {
      const canvas = owner?.querySelector<HTMLElement>(".circuit-canvas");
      if (!canvas) return;
      canvas.scrollIntoView({ block: "center", behavior: "instant" });
      observer.disconnect();
    }
    observer.observe(owner, { childList: true, subtree: true });
    showCanvas();
    return () => observer.disconnect();
  }, [open, generation]);

  function update(next: Circuit) {
    setDone(false);
    if (!hasLastWire(next)) setTested(false);
    if (wired && circuit.parts.find(p => p.id === "b")?.value === 0 && hasLastWire(next) && showsFirstPair(next)) setTested(true);
    setInvalidTable(false);
    setCircuit(next);
  }

  function reset() {
    setCircuit(sensorCircuit()); setWireOpen(false); setTested(false); setDone(false); setInvalidTable(false);
    setGeneration(n => n + 1);
  }

  function checkTable() {
    if (!wired || !tested) return;
    if (!isMajorityTable(circuit)) { setInvalidTable(true); return; }
    setDone(true);
    onAction("drawing-tried");
  }

  function observeDiagram() {
    const canvas = root.current?.querySelector<HTMLElement>(".circuit-canvas");
    canvas?.scrollIntoView({ block: "center", behavior: "instant" });
  }

  function showWirePanel() {
    const details = root.current?.querySelector<HTMLDetailsElement>("[data-muxi-control='circuit-wire-details']");
    if (!details) return;
    details.open = true;
    details.querySelector<HTMLSelectElement>("select")?.focus({ preventScroll: true });
    details.scrollIntoView({ block: "center", behavior: "instant" });
  }

  function wiringCue(source: string, target: string, at: "open" | "source" | "target" | "connect") {
    if (wired || done) return null;
    if (!wireOpen) return at === "open" && <Cue target="wire-open">{t("פתחו „חיבור חוט בלי גרירה”. אפשר גם לגרור על הלוח מהיציאה Y של AB אל הכניסה A0 של VOTE.",
      "Open “Connect pins without dragging”. You can also drag on the canvas from AB’s Y output to VOTE’s A0 input.")}</Cue>;
    if (source !== "ab:Y") return at === "source" && <Cue target="wire-source">{t("בשדה „יציאה” בחרו AB · Y. זהו האות שעולה כששני החיישנים A ו־B מדווחים על תקלה.",
      "Under Output, choose AB · Y. This signal is high when sensors A and B both detect a fault.")}</Cue>;
    if (target !== "vote:A0") return at === "target" && <Cue target="wire-target">{t("בשדה „כניסה” בחרו VOTE · A0. זו הכניסה הפנויה בשער OR שמרכז את שלושת הזוגות.",
      "Under Input, choose VOTE · A0, the free input on the OR gate that combines the three pairs.")}</Cue>;
    return at === "connect" && <Cue target="wire-connect">{t("לחצו על „חיבור” כדי להוסיף את החוט לשרטוט.", "Choose Connect to add that wire to your drawing.")}</Cue>;
  }

  function inputCue(selected: string | null, at: "select" | "toggle") {
    if (!wired || tested || done) return null;
    if (selected !== "b") return at === "select" && <Cue target="component">{t("ב„בחירת רכיב להגדרה” בחרו B, או לחצו על B בלוח. נבדוק מה משתנה כאשר גם הוא מדווח על תקלה.",
      "Choose B under Select component to configure, or click B on the canvas. Let’s see what happens when it detects a fault too.")}</Cue>;
    return at === "toggle" && <Cue target="input-toggle">{t("הפעילו את B בעזרת „החלפת 0 / 1”. כאשר A ו־B הם 1 ו־C הוא 0, גם ALARM צריך לעלות ל־1.",
      "Use Toggle 0 / 1 to turn B on. With A and B at 1 and C at 0, ALARM should rise to 1.")}</Cue>;
  }

  return <section ref={root} className={styles.demo} data-guest-hardware aria-label={title}>
    <div className={styles.question}><h3>{title}</h3><p><BidiText>{question}</BidiText></p></div>
    <p className={styles.lead}>{t("הכנו שלושה שערי AND, אחד לכל זוג חיישנים. שער OR אוסף את התוצאות. נשלים חוט אחד, נפעיל חיישן ונבדוק את טבלת האמת.",
      "We’ve drawn an AND gate for each pair of sensors. An OR gate combines their outputs. Complete one wire, switch a sensor on and inspect the truth table.")}</p>
    {!open ? <div className={styles.entry}>
      <p><ArrowDown size={19} aria-hidden="true" />{t("פתחו את כלי השרטוט של השאלה.", "Open the question’s drawing tool.")}</p>
      <button type="button" className="primary" data-muxi-control="guest-hardware-open" onClick={() => setOpen(true)}>
        <CircuitBoard size={18} aria-hidden="true" />{t("שרטוט מעגל לוגי", "Draw a logic circuit")}
      </button>
    </div> : <>
      <div className={styles.tools}><button type="button" onClick={observeDiagram}>{t("הצגת השרטוט", "Show drawing")}</button>
        {!done && <button type="button" onClick={() => root.current?.querySelector<HTMLElement>("[data-guest-hardware-cue]")?.scrollIntoView({ block: "center", behavior: "instant" })}>{t("לפעולה הבאה בעורך", "Find the next control")}</button>}
        <button type="button" onClick={reset}><RotateCcw size={15} />{t("איפוס הדוגמה", "Reset sample")}</button></div>
      <CircuitEditor key={generation} value={circuit} onChange={update} lang={lang} guide={guide}
        question={{ title, content: <BidiText>{question}</BidiText> }}
        onActivity={activity => { if (activity === "truth-table-generated") checkTable(); }}
        instructions={{ drawing: !wired && !done && <div className={styles.canvasCue}>
          <p><BidiText>{t("על הלוח רואים את שלושת זוגות החיישנים. חברו את היציאה Y של AB לכניסה A0 של VOTE בגרירה, או פתחו את רשימת החיבורים כאן.", "The canvas shows the three sensor pairs. Drag AB’s Y output to VOTE’s A0 input, or open the pin selectors here.")}</BidiText></p>
          <button type="button" onClick={showWirePanel}><ArrowDown size={16} />{t("חיבור בלי גרירה", "Connect without dragging")}</button>
        </div>, wiring: wiringCue, input: inputCue, truthTable: wired && tested && !done ?
          <Cue target="truth-table">{invalidTable ? t("בדקו מחדש את החיבורים. האזעקה צריכה לפעול בכל שורה עם שניים או שלושה חיישנים פעילים.",
            "Check the wiring again. Every row with two or three active sensors should trigger the alarm.")
            : t("הפלט ALARM דלק ב־110. לחצו „יצירת טבלת אמת” כדי לבדוק את כל שמונת הצירופים.",
            "ALARM turned on at 110. Choose Generate truth table to check all eight combinations.")}</Cue> : null }}
      />
      {wired && <p className={styles.result} role="status"><bdi dir="ltr">ALARM = {alarm ?? "?"}</bdi> · {done
        ? t("כל שמונת הצירופים נבדקו. האזעקה פועלת בדיוק כאשר שניים או שלושה חיישנים פעילים.", "All eight combinations match. The alarm is on exactly when two or three sensors detect a fault.")
        : t("הפלט מתעדכן מיד כשמשנים כניסה.", "The output updates immediately when an input changes.")}</p>}
      <details className={styles.more}><summary>{t("מה עוד אפשר לעשות בעורך?", "What else can I do in the editor?")}</summary>
        <ul>
          <li>{t("הוסיפו רכיב מספריית השערים וגררו אותו למקום. לחצו עליו כדי לערוך את שמו, מספר הכניסות או רוחב הנתונים, לפי סוג הרכיב.", "Add a part from the palette and drag it into place. Select it to edit its label, input count or bus width when supported.")}</li>
          <li>{t("בחרו חוט ולחצו על כפתור המחיקה כדי לחבר אותו מחדש. „ביטול שינוי” מחזיר את הפעולה האחרונה.", "Select a wire and use Delete to reconnect it. Undo restores the previous drawing.")}</li>
          <li>{t("„כל המעגל” מכניס את השרטוט לתצוגה. „הרחבת הלוח” ו„מסך מלא” נותנים יותר מקום לעבודה.", "Whole circuit fits the drawing to the view. Expand drawing and Full screen provide more workspace.")}</li>
          <li>{t("בתרגיל הזה הפלט מתעדכן מיד. כשמוסיפים פליפ־פלופ, רגיסטר או מונה, מופיעה „הרצת סימולציה”. אחריה אפשר לקדם את השעון ולבדוק שינויי מצב.", "Here the output updates live. Add a flip-flop, register or counter to enable Run simulation, then step the clock to inspect changes of state.")}</li>
        </ul>
      </details>
    </>}
  </section>;
}
