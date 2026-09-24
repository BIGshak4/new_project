"use client";

import { CalendarDays, Check, Circle, Flame, RefreshCw, Target, TrendingUp } from "lucide-react";
import type { Lang } from "./auth";
import type { Goal, Plan, ProgressOverview, TimelinePoint } from "../lib/practice-api";
import { dayLabel, levelSteps, modeLabel, planByDay, tickDays, timelineLayout } from "../lib/timeline";

/**
 * The progress page is three things and nothing else (Shaked, 2026-09-23): a card that says how far the
 * user has come in words and counts, a graph of the road so far, and the plan from today until the interview.
 */

export function OverviewCard({
  overview,
  goal,
  lang,
  onEditGoal,
}: {
  overview: ProgressOverview;
  goal: Goal | null;
  lang: Lang;
  onEditGoal: () => void;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const steps = levelSteps(lang);
  return (
    <section className="overview-card" aria-labelledby="overview-title">
      <div className="overview-main">
        <span className="overview-kicker">
          <Flame size={16} aria-hidden="true" /> {t("איפה אתם עומדים", "Where you stand")}
        </span>
        <h2 id="overview-title" className="overview-level" dir="auto">
          {overview.level}
        </h2>
        <p className="overview-message" dir="auto">
          {overview.message}
        </p>
        <ol className="level-meter" aria-label={t("סולם הרמות", "Level scale")}>
          {steps.map((step, i) => (
            <li key={step} className={`level-step ${i <= overview.level_rank ? "on" : ""} ${i === overview.level_rank ? "now" : ""}`}>
              <i aria-hidden="true" />
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
      <div className="stat-tiles">
        <div className="stat">
          <strong>{overview.answered}</strong>
          <span>{t("תשובות שנענו", "answers given")}</span>
        </div>
        <div className="stat stat-strong">
          <strong>{overview.strong}</strong>
          <span>{t("חזקות", "strong")}</span>
        </div>
        <div className="stat stat-partial">
          <strong>{overview.partial}</strong>
          <span>{t("חלקיות", "partial")}</span>
        </div>
        <div className="stat stat-weak">
          <strong>{overview.weak}</strong>
          <span>{t("לחיזוק", "to strengthen")}</span>
        </div>
        <div className="stat">
          <strong>
            {overview.skills_assessed}
            <small> / {overview.skills_total}</small>
          </strong>
          <span>{t("מיומנויות שהוערכו", "skills assessed")}</span>
        </div>
      </div>
      {(overview.skills_to_refresh ?? 0) > 0 && (
        <p className="overview-refresh small" dir="auto">
          <RefreshCw size={14} aria-hidden="true" />{" "}
          {overview.skills_to_refresh === 1
            ? t("מיומנות אחת לא נבדקה כבר זמן מה; רענון שלה מתוכנן לפני חומר חדש.", "One skill has not been checked for a while; a refresh of it is planned before new material.")
            : `${overview.skills_to_refresh} ${t("מיומנויות לא נבדקו כבר זמן מה; רענון שלהן מתוכנן לפני חומר חדש.", "skills have not been checked for a while; a refresh of them is planned before new material.")}`}
        </p>
      )}
      <footer className="overview-goal">
        <Target size={16} aria-hidden="true" />
        <span dir="auto">
          {goal?.job_type_label
            ? goal.job_type_label
            : t("עוד לא בחרתם סוג תפקיד", "No job type chosen yet")}
          {goal?.days_to_interview !== null && goal?.days_to_interview !== undefined && (
            <>
              {" · "}
              {goal.days_to_interview < 0
                ? t("הראיון עבר", "the interview has passed")
                : goal.days_to_interview === 0
                  ? t("הראיון היום", "the interview is today")
                  : `${goal.days_to_interview} ${t("ימים לראיון", "days to the interview")}`}
            </>
          )}
          {goal?.minutes_per_day ? ` · ${goal.minutes_per_day} ${t("דק׳ ביום", "min a day")}` : ""}
        </span>
        <button type="button" className="text-button" onClick={onEditGoal}>
          {t("עריכת היעד", "Edit goal")}
        </button>
      </footer>
    </section>
  );
}

export function ProgressGraph({ timeline, lang }: { timeline: TimelinePoint[]; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const width = 680,
    height = 220;
  const layout = timelineLayout(timeline, width, height);
  const ticks = tickDays(timeline);
  const baseline = height - layout.padding.bottom;
  const shortDate = (day: string) => {
    const d = new Date(`${day}T12:00:00`);
    return Number.isNaN(d.getTime()) ? day : d.toLocaleDateString(lang === "he" ? "he-IL" : "en-GB", { day: "numeric", month: "short" });
  };
  return (
    <section className="progress-graph" aria-labelledby="graph-title">
      <header className="board-head">
        <h3 id="graph-title">
          <TrendingUp size={18} aria-hidden="true" /> {t("הדרך עד כאן", "The road so far")}
        </h3>
        <span className="small muted">
          {t("עמודות: תשובות בכל יום · קו: הרמה הממוצעת", "Bars: answers per day · line: average level")}
        </span>
      </header>
      {timeline.length === 0 ? (
        <p className="empty-column">
          {t("הגרף מתחיל לצייר את עצמו אחרי התשובה הראשונה.", "The graph starts drawing itself after your first answer.")}
        </p>
      ) : (
        <div className="graph-wrap" dir="ltr">
        <svg className="graph-svg" viewBox={`0 0 ${width} ${height}`} role="img"
             aria-label={t("תשובות לפי יום ורמה ממוצעת", "Answers per day and average level")}>
          <line className="graph-axis" x1={layout.padding.left} x2={width - layout.padding.right} y1={baseline} y2={baseline} />
          <text className="graph-label" x={layout.padding.left - 6} y={layout.padding.top + 4} textAnchor="end">
            {layout.maxAnswers}
          </text>
          <text className="graph-label" x={layout.padding.left - 6} y={baseline} textAnchor="end">
            0
          </text>
          {layout.bars.map((bar) => (
            <g key={bar.day}>
              {bar.segments.map(([key, y, h]) => (
                <rect key={key} className={`bar-seg bar-${key.toLowerCase()}`} x={bar.x} y={y} width={bar.width} height={h} rx={2}>
                  <title>{`${shortDate(bar.day)}: ${bar.answered} ${t("תשובות", "answers")}`}</title>
                </rect>
              ))}
              {ticks.has(bar.day) && (
                <text className="graph-label" x={bar.x + bar.width / 2} y={height - 8} textAnchor="middle">
                  {shortDate(bar.day)}
                </text>
              )}
            </g>
          ))}
          {layout.levelPath && <path className="level-line" d={layout.levelPath} />}
          {layout.levelPoints.map((pt) => (
            <circle key={pt.day} className="level-dot" cx={pt.x} cy={pt.y} r={4}>
              <title>{`${shortDate(pt.day)}: ${t("רמה", "level")} ${pt.level.toFixed(1)}`}</title>
            </circle>
          ))}
          <text className="graph-label level-label" x={width - layout.padding.right + 2} y={layout.padding.top + 4} textAnchor="start">
            5
          </text>
          <text className="graph-label level-label" x={width - layout.padding.right + 2} y={baseline} textAnchor="start">
            1
          </text>
        </svg>
        </div>
      )}
      <p className="chart-legend small muted">
        <span className="swatch strong" /> {t("חזקה", "Strong")}
        <span className="swatch partial" /> {t("חלקית", "Partial")}
        <span className="swatch weak" /> {t("לחיזוק", "Needs work")}
        <span className="swatch line" /> {t("רמה ממוצעת (1-5)", "Average level (1-5)")}
      </p>
    </section>
  );
}

export function PlanTable({ plan, lang, onEditGoal }: { plan: Plan | null; lang: Lang; onEditGoal: () => void }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const days = planByDay(plan?.items ?? []);
  const passed = plan?.days_to_interview !== null && plan?.days_to_interview !== undefined && plan.days_to_interview < 0;
  return (
    <section className="plan-table" aria-labelledby="plan-title">
      <header className="board-head">
        <h3 id="plan-title">
          <CalendarDays size={18} aria-hidden="true" /> {t("התוכנית עד הראיון", "The plan until the interview")}
        </h3>
        {plan && (
          <span className="small muted">
            {plan.days_to_interview === null || plan.days_to_interview === undefined
              ? t("שבוע קדימה", "A week ahead")
              : plan.days_to_interview >= 0
                ? `${plan.days_to_interview} ${t("ימים לראיון", "days to go")}`
                : t("הראיון עבר", "the interview has passed")}
            {" · "}
            {plan.minutes_per_day} {t("דק׳ ביום", "min a day")}
          </span>
        )}
      </header>
      {passed ? (
        <p className="empty-column">
          {t("תאריך הראיון עבר. ", "The interview date has passed. ")}
          <button type="button" className="text-button" onClick={onEditGoal}>
            {t("עדכנו את היעד", "Update your goal")}
          </button>
          {t(" ונבנה תוכנית חדשה.", " and a new plan will be built.")}
        </p>
      ) : days.length === 0 ? (
        <p className="empty-column">
          {t(
            "עדיין אין שאלות מאושרות לבנות מהן תוכנית. כשהמאגר יאושר התוכנית תופיע כאן.",
            "There are no approved questions to build a plan from yet. The plan appears here once the bank is approved.",
          )}
        </p>
      ) : (
        <table className="plan-grid">
          <thead>
            <tr>
              <th>{t("יום", "Day")}</th>
              <th>{t("מה עושים", "What to do")}</th>
              <th>{t("על מה", "On what")}</th>
              <th>{t("זמן", "Time")}</th>
              <th>{t("למה", "Why")}</th>
            </tr>
          </thead>
          <tbody>
            {days.map((day) =>
              day.items.map((item, i) => (
                <tr key={`${day.day_index}-${i}`} className={`plan-row ${item.done ? "done" : ""} ${i === 0 ? "first" : ""}`}>
                  {i === 0 ? (
                    <th scope="rowgroup" rowSpan={day.items.length} className="plan-day">
                      <strong>{dayLabel(item.date, day.day_index, lang)}</strong>
                      <span className="small muted">
                        {day.minutes} {t("דק׳", "min")}
                      </span>
                    </th>
                  ) : null}
                  <td>
                    <span className="plan-mode">
                      {item.done ? <Check size={15} aria-hidden="true" /> : <Circle size={13} aria-hidden="true" />}
                      {modeLabel(item.mode, lang)}
                    </span>
                  </td>
                  <td dir="auto">{item.skills.map((s) => s.label).join(", ")}</td>
                  <td className="plan-minutes">
                    {item.minutes} {t("דק׳", "min")}
                  </td>
                  <td className="plan-reason small" dir="auto">
                    {item.reason}
                  </td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      )}
    </section>
  );
}
