"use client";

import { useId, useMemo, useState } from "react";
import { Table2 } from "lucide-react";
import {
  truthTable,
  truthTablePlan,
  type Circuit,
  type Signal,
  type TruthTable,
  type TruthTableIssue,
} from "../lib/circuit";
import type { Lang } from "./auth";
import styles from "./circuit-truth-table.module.css";

const messages: Record<TruthTableIssue, [string, string]> = {
  empty: [
    "הוסיפו רכיבים וחברו אותם לרכיב OUTPUT כדי ליצור טבלת אמת.",
    "Add components and connect an OUTPUT component to create a truth table.",
  ],
  invalid: [
    "יש במעגל רכיב או חיבור לא תקין. בדקו רוחבי קווים, חיבורים חסרים או כמה חוטים לאותה כניסה, ואז נסו שוב.",
    "The circuit has an invalid component or wire. Check bus widths, wire endpoints and multiple drivers on the same input, then try again.",
  ],
  sequential: [
    "המעגל כולל זיכרון. הפלט תלוי גם במצב הקודם, ולכן טבלת אמת צירופית אינה מספיקה. השתמשו בסימולציה ובצעד שעון לבדיקת המעברים.",
    "This circuit includes memory. Its output also depends on the previous state, so a combinational truth table is not enough. Use simulation and clock steps to check transitions.",
  ],
  clock: [
    "המעגל כולל שעון. לטבלת אמת צירופית החליפו אותו ברכיב INPUT או CONSTANT; לבדיקת תזמון השתמשו בסימולציה ובצעד שעון.",
    "This circuit includes a clock. Replace it with an INPUT or CONSTANT for a combinational truth table, or use simulation and clock steps to check timing.",
  ],
  "no-output": [
    "חברו את הפלטים שתרצו לבדוק לרכיבי OUTPUT מתוך ״קלט ופלט״. כל OUTPUT יופיע בעמודה נפרדת.",
    "Connect the signals you want to inspect to OUTPUT components under Input & output. Each OUTPUT becomes a separate column.",
  ],
  "too-many-inputs": [
    "אפשר להציג עד 6 ביטים משתנים של INPUT, כלומר עד 64 צירופים. צמצמו את רוחב הכניסות או החליפו חלק מהן ב־CONSTANT.",
    "Truth tables support up to 6 variable INPUT bits, or 64 combinations. Reduce input widths or replace some inputs with CONSTANT components.",
  ],
  feedback: [
    "יש במעגל מסלול משוב שחוזר לרכיב קודם. נתקו את הלולאה כדי לבדוק מעגל צירופי; טבלה כזאת אינה מתארת מעגל עם משוב.",
    "A feedback path returns to an earlier component. Remove the loop to check combinational logic; this truth table does not describe circuits with feedback.",
  ],
};

export const truthTableSignal = (value: Signal, bits: number) =>
  value === null ? "?" : value.toString(2).padStart(bits, "0");

export function CircuitTruthTable({
  circuit,
  lang,
  onGenerate,
}: {
  circuit: Circuit;
  lang: Lang;
  onGenerate?: () => void;
}) {
  const he = lang === "he";
  const t = (heText: string, enText: string) => (he ? heText : enText);
  const headingId = useId(),
    tableId = useId(),
    helpId = useId();
  const plan = useMemo(() => truthTablePlan(circuit), [circuit]);
  const signature = useMemo(() => JSON.stringify(circuit), [circuit]);
  const [snapshot, setSnapshot] = useState<{
    signature: string;
    table: TruthTable;
  } | null>(null);
  // Hide old data during the render that receives an edit, without running
  // enumeration in an effect or altering the canvas / current input values.
  const table = snapshot?.signature === signature ? snapshot.table : null;
  return (
    <section className={styles.root} aria-labelledby={headingId}>
      <div className={styles.toolbar}>
        <strong id={headingId}>
          <Table2 size={18} aria-hidden="true" />
          {t("טבלת אמת", "Truth table")}
        </strong>
        <button
          type="button"
          disabled={!plan.ok}
          aria-expanded={!!table}
          aria-controls={tableId}
          aria-describedby={helpId}
          onClick={() => {
            if (table) setSnapshot(null);
            else {
              const result = truthTable(circuit);
              if (result.ok) { setSnapshot({ signature, table: result }); onGenerate?.(); }
            }
          }}
        >
          {table
            ? t("הסתרת הטבלה", "Hide table")
            : t("יצירת טבלת אמת", "Generate truth table")}
        </button>
      </div>
      <p
        id={helpId}
        className={styles.help}
        role={!plan.ok || (!!snapshot && !table) ? "status" : undefined}
      >
        {!plan.ok
          ? messages[plan.issue][he ? 0 : 1]
          : snapshot && !table
            ? t(
                "המעגל השתנה. צרו את הטבלה מחדש כדי לראות את התוצאה העדכנית.",
                "The circuit changed. Generate the table again to see current results.",
              )
            : t(
                "הטבלה בודקת את כל צירופי ה־INPUT. ערכי CONSTANT נשארים קבועים; השרטוט וערכי הכניסות שלכם לא משתנים.",
                "The table checks every INPUT combination. CONSTANT values stay fixed; your drawing and current input values do not change.",
              )}
      </p>
      <div id={tableId}>
        {table && (
          <>
            <div
              className={styles.scroll}
              role="region"
              aria-labelledby={headingId}
              tabIndex={0}
            >
              <table className={styles.table} dir="ltr">
                <caption dir={he ? "rtl" : "ltr"}>
                  {table.rows.length} {t("צירופים", "combinations")}
                  {!table.inputs.length &&
                    t(" · מעגל עם קבועים בלבד", " · constants-only circuit")}
                  {t(" · ערכים בינאריים", " · binary values")}
                </caption>
                <thead>
                  <tr>
                    {table.inputs.map((p) => (
                      <th key={p.id} scope="col">
                        <bdi>{p.label || "INPUT"}</bdi>
                        <small>
                          {t("קלט", "Input")}
                          {p.bits > 1 ? ` · ${p.bits} bit` : ""}
                        </small>
                      </th>
                    ))}
                    {table.outputs.map((p, index) => (
                      <th
                        key={p.id}
                        scope="col"
                        data-first-output={index === 0 ? "true" : undefined}
                      >
                        <bdi>{p.label || "OUTPUT"}</bdi>
                        <small>
                          {t("פלט", "Output")}
                          {p.bits > 1 ? ` · ${p.bits} bit` : ""}
                        </small>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {table.rows.map((row, index) => (
                    <tr key={index}>
                      {row.inputs.map((v, i) => (
                        <td key={table.inputs[i].id}>
                          {truthTableSignal(v, table.inputs[i].bits)}
                        </td>
                      ))}
                      {row.outputs.map((v, i) => (
                        <td
                          key={table.outputs[i].id}
                          data-first-output={i === 0 ? "true" : undefined}
                          data-unknown={v === null ? "true" : undefined}
                          aria-label={
                            v === null
                              ? t("ערך לא ידוע", "Unknown value")
                              : undefined
                          }
                        >
                          {truthTableSignal(v, table.outputs[i].bits)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {table.hasUnknown && (
              <p className={styles.warning} role="status">
                {t(
                  "? מסמן פלט שלא ניתן לקבוע: למשל חיבור חסר או צירוף לא מוגדר ברכיב. בדקו את החיבורים ואת סוג הרכיב; זה אינו הערך 0.",
                  "? means the output cannot be determined, for example a missing connection or an undefined component input combination. Check connections and component behavior; ? does not mean 0.",
                )}
              </p>
            )}
            <p className={styles.help}>
              {t(
                "זו סימולציה לוגית ללא זמני השהיה. הטבלה אינה קובעת אם השרטוט פותר את השאלה.",
                "This is zero-delay logic simulation. The table does not assess whether your drawing answers the question.",
              )}
            </p>
          </>
        )}
      </div>
    </section>
  );
}
