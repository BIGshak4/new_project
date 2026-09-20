"use client";

import type { Lang } from "./auth";
import type { SubjectProgress } from "../lib/practice-api";
import { subjectLabel } from "../lib/practice-ui";
import { arc, chartSubjects, coveragePercent, donutSegments } from "../lib/charts";

/**
 * One donut per subject: the ring is the split of the candidate's answers (strong / partial /
 * weak), the centre is the average level of the subject's assessed skills, the bar underneath
 * is how much of the role plan the subject carries. Inline SVG, no chart library.
 */
export function SubjectCharts({
  subjects,
  lang,
}: {
  subjects: SubjectProgress[];
  lang: Lang;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const shown = chartSubjects(subjects);
  if (!shown.length) return null;
  const coverage = coveragePercent(shown);
  return (
    <section className="subject-charts" aria-label={t("תמונת מצב לפי נושא", "Progress by subject")}>
      <div className="subject-charts-head">
        <h3>{t("תמונת מצב לפי נושא", "By subject")}</h3>
        <span className="small muted">
          {coverage}% {t("מהמיומנויות בתוכנית כבר הוערכו", "of the plan's skills assessed")}
        </span>
      </div>
      <div className="subject-grid">
        {shown.map((s) => (
          <SubjectDonut key={s.key} subject={s} lang={lang} />
        ))}
      </div>
      <p className="chart-legend small muted">
        <span className="swatch strong" /> {t("חזקה", "Strong")}
        <span className="swatch partial" /> {t("חלקית", "Partial")}
        <span className="swatch weak" /> {t("דורשת שיפור", "Needs work")}
      </p>
    </section>
  );
}

function SubjectDonut({ subject: s, lang }: { subject: SubjectProgress; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const radius = 34;
  const segments = donutSegments(s.bands);
  const known = subjectLabel(s.key, lang);
  const label = known === s.key.replaceAll("_", " ") ? s.label : known;
  const centre =
    s.average_level !== null ? s.average_level.toFixed(1) : s.attempts ? String(s.attempts) : "—";
  const centreNote =
    s.average_level !== null ? t("רמה ממוצעת", "avg level") : s.attempts ? t("תשובות", "answers") : "";
  const weightPercent = Math.round(s.weight * 100);
  const description = `${label}: ${s.bands.STRONG} ${t("חזקות", "strong")}, ${s.bands.PARTIAL} ${t("חלקיות", "partial")}, ${s.bands.WEAK} ${t("חלשות", "weak")}`;
  return (
    <article className="subject-card">
      <svg className="donut" viewBox="0 0 88 88" role="img" aria-label={description}>
        <circle className="donut-track" cx="44" cy="44" r={radius} />
        {segments.map((segment) => {
          const { dasharray, dashoffset } = arc(segment, radius);
          return (
            <circle
              key={segment.key}
              className={`donut-seg seg-${segment.key.toLowerCase()}`}
              cx="44"
              cy="44"
              r={radius}
              strokeDasharray={dasharray}
              strokeDashoffset={dashoffset}
              transform="rotate(-90 44 44)"
            />
          );
        })}
        <text className="donut-centre" x="44" y="44" textAnchor="middle">
          {centre}
        </text>
        {centreNote && (
          <text className="donut-note" x="44" y="58" textAnchor="middle">
            {centreNote}
          </text>
        )}
      </svg>
      <div className="subject-meta">
        <h4 dir="auto">{label}</h4>
        <p className="small muted">
          {s.skills_assessed}/{s.skills_total} {t("מיומנויות הוערכו", "skills assessed")} · {s.attempts}{" "}
          {t("תשובות", "answers")}
        </p>
        <div className="level-bars" aria-hidden="true" title={t("מיומנויות לפי רמה 1-5", "skills by level 1-5")}>
          {["1", "2", "3", "4", "5"].map((level) => (
            <span key={level} style={{ height: `${6 + 9 * (s.levels[level] ?? 0)}px` }} />
          ))}
        </div>
        <div className="weight-bar" aria-hidden="true">
          <span style={{ width: `${Math.min(100, weightPercent)}%` }} />
        </div>
        <p className="small muted">
          {weightPercent}% {t("מתוכנית התפקיד", "of the role plan")} · {s.questions_available}{" "}
          {t("שאלות זמינות", "questions available")}
        </p>
      </div>
    </article>
  );
}
