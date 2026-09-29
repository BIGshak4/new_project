"use client";

import { Flame, RefreshCw, Sparkles } from "lucide-react";
import type { Lang } from "./auth";
import type { SkillProgress } from "../lib/practice-api";
import { filledBlocks, skillLevelWord, strengthSkills, strengthTone } from "../lib/path";
import { revealDelay } from "../lib/ui";
import { motion, spring, useReducedMotion } from "./ui/motion";

/** Five-block bars per skill, the level word and the XP earned on it; blue "needs a refresh" when the evidence is old. */
export function SkillStrength({
  skills,
  lang,
  limit = 6,
  title,
  ordered = false,
  hotKey,
}: {
  skills: SkillProgress[];
  lang: Lang;
  limit?: number;
  title?: string;
  /** the list is already in the order to show (the job's focus skills), unassessed ones included */
  ordered?: boolean;
  /** the skill being trained today: its next block is drawn in copper */
  hotKey?: string;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const reduced = useReducedMotion();
  const shown = ordered ? skills.slice(0, limit) : strengthSkills(skills, limit);
  return (
    <section className="side-card skill-strength" aria-labelledby="strength-title">
      <h2 id="strength-title">
        {title ?? t("חוזק", "Strength")}
        <small>{t("המיומנויות שהתפקיד בודק", "the skills the job tests")}</small>
      </h2>
      {shown.length === 0 ? (
        <p className="muted small">{t("אחרי התשובה הראשונה המיומנויות מתחילות להתמלא כאן.", "After your first answer the skills start filling up here.")}</p>
      ) : (
        <ul className="strength-list">
          {shown.map((s) => {
            const tone = strengthTone(s);
            const filled = filledBlocks(s.level);
            return (
              <li key={s.key} className={`strength tone-${tone} ${s.key === hotKey ? "hot" : ""}`}>
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
                    <motion.i
                      key={i}
                      className={i < filled ? "on" : s.key === hotKey && i === filled ? "next" : ""}
                      style={{ originX: lang === "he" ? 1 : 0 }}
                      initial={reduced || i >= filled ? false : { scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ ...spring, delay: revealDelay(i, !!reduced, 0.07, 0.35) }}
                    />
                  ))}
                </div>
                {(s.xp ?? 0) > 0 && (
                  <span className="strength-xp small muted">
                    <Sparkles size={12} aria-hidden="true" /> <bdi dir="ltr">{s.xp} XP</bdi>
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
        ? t(`${days === 1 ? "יום אחד" : `${days} ימים`} שלא ויתרתם. מחר בשעה הזאת זה ${days + 1}.`, `${days} ${days === 1 ? "day" : "days"} without giving up. Same time tomorrow makes it ${days + 1}.`)
        : t("תשובה אחת היום שומרת עליו.", "One answer today keeps it going.");
  return (
    <section className={`side-card streak-card ${days > 0 ? "lit" : ""}`} aria-label={t("רצף", "Streak")}>
      {days > 0 ? (
        <div className="streak-number" aria-hidden="true">{days}</div>
      ) : (
        <Flame size={34} aria-hidden="true" className="streak-flame" />
      )}
      <div>
        <div className="streak-headline">{headline}</div>
        <div className="streak-line">{line}</div>
      </div>
    </section>
  );
}
