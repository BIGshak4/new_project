"use client";

import { Flame, RefreshCw, Sparkles } from "lucide-react";
import type { Lang } from "./auth";
import type { SkillProgress } from "../lib/practice-api";
import { filledBlocks, skillLevelWord, strengthSkills, strengthTone } from "../lib/path";

/** Five-block bars per skill, the level word and the XP earned on it; blue "needs a refresh" when the evidence is old. */
export function SkillStrength({ skills, lang, limit = 6, title }: { skills: SkillProgress[]; lang: Lang; limit?: number; title?: string }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const shown = strengthSkills(skills, limit);
  return (
    <section className="side-card skill-strength" aria-labelledby="strength-title">
      <h2 id="strength-title">{title ?? t("חוזק המיומנויות", "Skill strength")}</h2>
      {shown.length === 0 ? (
        <p className="muted small">{t("אחרי התשובה הראשונה המיומנויות מתחילות להתמלא כאן.", "After your first answer the skills start filling up here.")}</p>
      ) : (
        <ul className="strength-list">
          {shown.map((s) => {
            const tone = strengthTone(s);
            const filled = filledBlocks(s.level);
            return (
              <li key={s.key} className={`strength tone-${tone}`}>
                <div className="strength-head">
                  <span className="strength-name" dir="auto">
                    {s.label}
                  </span>
                  <span className="strength-word">
                    {tone === "blue" ? (
                      <>
                        <RefreshCw size={13} aria-hidden="true" /> {t("צריך רענון", "Needs a refresh")}
                      </>
                    ) : (
                      skillLevelWord(s.level, lang)
                    )}
                  </span>
                </div>
                <div className="blocks" role="img" aria-label={`${s.label}: ${skillLevelWord(s.level, lang)}`}>
                  {Array.from({ length: 5 }, (_, i) => (
                    <i key={i} className={i < filled ? "on" : ""} />
                  ))}
                </div>
                {(s.xp ?? 0) > 0 && (
                  <span className="strength-xp small muted">
                    <Sparkles size={12} aria-hidden="true" /> {s.xp} XP
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

/** The streak card: days in a row with a scored answer, and a line that says what keeps it. */
export function StreakCard({ days, todayDone, lang }: { days: number; todayDone: boolean; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const headline =
    days === 0
      ? t("עוד אין רצף", "No streak yet")
      : days === 1
        ? t("יום אחד ברצף", "1 day in a row")
        : `${days} ${t("ימים ברצף", "days in a row")}`;
  const line =
    days === 0
      ? t("תשובה אחת היום פותחת רצף.", "One answer today starts a streak.")
      : todayDone
        ? t("היום כבר נספר. נתראה מחר.", "Today is counted. See you tomorrow.")
        : t("תשובה אחת היום שומרת עליו.", "One answer today keeps it going.");
  return (
    <section className={`side-card streak-card ${days > 0 ? "lit" : ""}`} aria-label={t("רצף", "Streak")}>
      <Flame size={38} aria-hidden="true" className="streak-flame" />
      <div>
        <div className="streak-headline">{headline}</div>
        <div className="streak-line">{line}</div>
      </div>
    </section>
  );
}
