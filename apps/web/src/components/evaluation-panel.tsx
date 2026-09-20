"use client";

import {
  ArrowLeft,
  ArrowRight,
  Check,
  Circle,
  Cpu,
  Image as ImageIcon,
  Lightbulb,
  Sparkles,
} from "lucide-react";
import type { Lang } from "./auth";
import type { Check as CheckResult, Submission } from "../lib/practice-api";
import { bandLabel, subjectLabel } from "../lib/practice-ui";
import { bandFraction, whyLabel } from "../lib/charts";

/**
 * The evaluation a candidate sees after a real assessment: band ring, summary, automatic
 * check with the differing rows, the four-part feedback card, what went well / what to work
 * on, the coaching tip, and the next suggested question with the reason for it.
 */
export function EvaluationPanel({
  submission: s,
  lang,
  onStart,
  nextReady,
}: {
  submission: Submission;
  lang: Lang;
  /** start a new attempt on the suggested question */
  onStart: (key: string) => void;
  /** false while a follow-up is still open: the suggestion waits until the attempt is complete */
  nextReady?: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  if (s.status === "evaluating") {
    return (
      <p className="notice" role="status">
        {t(
          "התשובה נבדקת עכשיו. המשוב יופיע כאן בעוד רגע.",
          "Your answer is being assessed. Feedback appears here in a moment.",
        )}
      </p>
    );
  }
  if (s.status === "failed") {
    return (
      <p className="notice">
        {t(
          "ההערכה לא הושלמה. התשובה נשמרה ואפשר לנסות שוב.",
          "Evaluation failed. Your answer is saved and can be retried.",
        )}
      </p>
    );
  }
  const band = s.band;
  const tone = band?.toLowerCase() ?? "none";
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const glyph =
    band === "STRONG" ? "✓" : band === "PARTIAL" ? "~" : band === "WEAK" ? "!" : "?";
  const flags = new Set(s.flags);
  const photosNotAssessed =
    flags.has("images_not_assessed") || flags.has("images_unavailable");
  const evidenceText =
    s.evidence === "none"
      ? t(
          "התשובה אינה מוסיפה ראיה לשליטה עצמאית.",
          "This answer adds no independent skill evidence.",
        )
      : s.evidence === "reduced"
        ? t(
            "משקל ההערכה הופחת לפי תנאי התרגול והחשיפה לשאלה.",
            "Evidence weight is reduced based on practice conditions and question exposure.",
          )
        : t("התשובה נכללת בהערכת המיומנות.", "This answer contributes skill evidence.");
  const card = s.card
    ? [
        [t("מה קרה בתשובה", "What happened"), s.card.what_happened],
        [t("למה זה חשוב בראיון", "Why it matters"), s.card.why_it_matters],
        [t("מה כדאי לעשות בהמשך", "Next step"), s.card.next_step],
        [
          t("הדרך שלכם מול הפתרון", "Your reasoning and the reference"),
          s.card.your_reasoning_vs_reference,
        ],
      ]
    : [];
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  return (
    <div className={`evaluation tone-${tone}`}>
      <header className="evaluation-head">
        <svg className="band-ring" viewBox="0 0 64 64" aria-hidden="true">
          <circle className="ring-track" cx="32" cy="32" r={radius} />
          <circle
            className="ring-fill"
            cx="32"
            cy="32"
            r={radius}
            strokeDasharray={`${bandFraction(band) * circumference} ${circumference}`}
            transform="rotate(-90 32 32)"
          />
          <text className="ring-glyph" x="32" y="38" textAnchor="middle">
            {glyph}
          </text>
        </svg>
        <div className="evaluation-title">
          <span className={`badge band-${tone}`}>{bandLabel(band, lang)}</span>
          {s.summary && (
            <p className="evaluation-summary" dir="auto">
              {s.summary}
            </p>
          )}
        </div>
      </header>

      <div className="evaluation-chips" aria-label={t("פרטי ההערכה", "Assessment details")}>
        {s.check && (
          <span className={`chip check-${s.check.passed === null ? "none" : s.check.passed}`}>
            {s.check.passed === true
              ? t("בדיקה אוטומטית עברה", "Automatic check passed")
              : s.check.passed === false
                ? t("בדיקה אוטומטית נכשלה", "Automatic check failed")
                : t("בדיקה אוטומטית לא הכריעה", "Automatic check inconclusive")}
          </span>
        )}
        {flags.has("circuit_assessed") && (
          <span className="chip">
            <Cpu size={14} /> {t("המעגל שציירתם נבדק", "Your circuit was assessed")}
          </span>
        )}
        {flags.has("images_assessed") && (
          <span className="chip">
            <ImageIcon size={14} /> {t("התמונות נבדקו", "Your photos were assessed")}
          </span>
        )}
        {photosNotAssessed && (
          <span className="chip chip-warn">
            <ImageIcon size={14} /> {t("התמונות לא נבדקו", "Photos not assessed")}
          </span>
        )}
        <span className="chip chip-quiet">
          {s.evidence === "full"
            ? t("ראיה מלאה", "Full evidence")
            : s.evidence === "reduced"
              ? t("ראיה מופחתת", "Reduced evidence")
              : t("ללא ראיה", "No evidence")}
        </span>
        {s.assessed_by === "model" && s.model && (
          <span className="chip chip-quiet" title={s.model}>
            {t("נבדק על ידי", "Judged by")} {modelName(s.model)}
          </span>
        )}
      </div>

      {s.check && <CheckBlock check={s.check} lang={lang} />}

      {card.length > 0 && (
        <div className="evaluation-card-grid">
          {card.map(([label, value]) => (
            <section className="evaluation-tile" key={label}>
              <h4>{label}</h4>
              <p dir="auto">{value}</p>
            </section>
          ))}
        </div>
      )}

      {(s.key_points_hit.length > 0 || s.key_points_missed.length > 0) && (
        <div className="evaluation-points">
          {s.key_points_hit.length > 0 && (
            <section>
              <h4>{t("מה עשיתם היטב", "What went well")}</h4>
              <ul>
                {s.key_points_hit.map((p, i) => (
                  <li dir="auto" key={i}>
                    <Check size={16} aria-hidden="true" /> <span>{p}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          {s.key_points_missed.length > 0 && (
            <section>
              <h4>{t("מה כדאי לחזק", "What to work on")}</h4>
              <ul>
                {s.key_points_missed.map((p, i) => (
                  <li dir="auto" key={i}>
                    <Circle size={14} aria-hidden="true" /> <span>{p}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      {s.tip && (
        <aside className="evaluation-tip" dir="auto">
          <Lightbulb size={18} aria-hidden="true" />
          <span>{s.tip.text}</span>
        </aside>
      )}

      {s.next_question && nextReady !== false && (
        <section className="next-up" aria-labelledby="next-up-title">
          <div className="next-up-head">
            <Sparkles size={18} aria-hidden="true" />
            <span id="next-up-title">
              {t("השאלה הבאה המומלצת", "Suggested next question")}
            </span>
            <span className={`badge why-${s.next_question.why}`}>
              {whyLabel(s.next_question.why, lang)}
            </span>
          </div>
          <h4 dir="auto">{s.next_question.title}</h4>
          <p className="small muted">
            {subjectLabel(s.next_question.subject, lang)} ·{" "}
            {t("רמת קושי", "Difficulty")} {s.next_question.difficulty}
            <span className="difficulty-dots" aria-hidden="true">
              {Array.from({ length: 5 }, (_, i) => (
                <i key={i} className={i < Math.min(5, s.next_question!.difficulty) ? "on" : ""} />
              ))}
            </span>
          </p>
          <p dir="auto">{s.next_question.reason}</p>
          <button type="button" onClick={() => onStart(s.next_question!.key)}>
            {t("להתחיל את השאלה הבאה", "Start the next question")} <Arrow size={16} />
          </button>
        </section>
      )}

      <p className="small muted">{evidenceText}</p>
    </div>
  );
}

function modelName(model: string) {
  // "claude-opus-5" -> "Claude Opus 5"
  return model
    .split("-")
    .filter((part) => part && !/^\d{8}$/.test(part))
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function CheckBlock({ check, lang }: { check: CheckResult; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const rows = check.mismatches ?? [];
  return (
    <div className={`check-result check-${check.passed === null ? "none" : check.passed}`}>
      <strong>
        {check.type === "code_tests"
          ? t("הרצת הקוד מול מקרי בדיקה", "Your code against the test cases")
          : check.type === "truth_table"
            ? t("טבלת האמת של התשובה", "Truth table of your answer")
            : t("בדיקה אוטומטית", "Automatic check")}
      </strong>
      <p dir="auto">{check.detail}</p>
      {rows.length > 0 && (
        <table className="mismatch-table">
          <thead>
            <tr>
              <th>{t("קלט", "Input")}</th>
              <th>{t("צפוי", "Expected")}</th>
              <th>{t("התקבל", "Got")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((row, i) => (
              <tr key={i}>
                <td>{formatInputs(row.inputs)}</td>
                <td>{formatValue(row.expected)}</td>
                <td className={"error" in row ? "error" : ""}>
                  {"error" in row ? String(row.error) : formatValue(row.got)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function formatInputs(inputs: unknown) {
  if (inputs && typeof inputs === "object" && !Array.isArray(inputs)) {
    return Object.entries(inputs as Record<string, unknown>)
      .map(([k, v]) => `${k}=${formatValue(v)}`)
      .join(", ");
  }
  if (Array.isArray(inputs)) return inputs.map(formatValue).join(", ");
  return formatValue(inputs);
}

function formatValue(value: unknown) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}
