"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Clock3, Lightbulb, Mic, Square } from "lucide-react";
import type { Lang } from "./auth";
import { AnswerEditor } from "./answer-editor";
import {
  newIdempotencyKey,
  type Interview,
  type InterviewListItem,
  type InterviewReport,
  type InterviewTurn,
  type PracticeApi,
  type PracticeApiError,
} from "../lib/practice-api";
import { apiMessage, bandLabel, readLocal, removeLocal, subjectLabel, writeLocal } from "../lib/practice-ui";

type Props = {
  api: PracticeApi;
  lang: Lang;
  userId: string;
  interviewId?: string;
  demo: boolean;
  onStarted: (id: string) => void;
  onBack: () => void;
};

const DURATIONS = [20, 30, 45] as const;

/** The mock interview: a lobby to start one, then the timed room, then the report. */
export function InterviewSession(props: Props) {
  return props.interviewId ? <InterviewRoom {...props} interviewId={props.interviewId} /> : <InterviewLobby {...props} />;
}

function InterviewLobby({ api, lang, demo, onStarted }: Props) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [duration, setDuration] = useState<(typeof DURATIONS)[number]>(30);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [past, setPast] = useState<InterviewListItem[]>([]);
  useEffect(() => {
    api.listInterviews().then(setPast).catch(() => {});
  }, [api]);

  async function start() {
    setBusy(true);
    setError("");
    try {
      const interview = await api.startInterview({ duration_min: duration, language: lang });
      onStarted(interview.id);
    } catch (e) {
      const code = (e as PracticeApiError).code;
      setError(
        code === "no_reviewed_questions"
          ? t(
              "עדיין אין שאלות שנבדקו ואושרו לראיון. המייסדים צריכים לאשר שאלות תחילה.",
              "There are no reviewed and published questions yet for an interview. The founders need to publish questions first.",
            )
          : apiMessage(e, lang),
      );
    } finally {
      setBusy(false);
    }
  }

  const date = (s: string | null) =>
    s ? new Date(s).toLocaleString(lang === "he" ? "he-IL" : "en-GB", { dateStyle: "medium", timeStyle: "short" }) : "";

  return (
    <section className="interview-lobby">
      <div className="page-heading">
        <div>
          <h1>{t("ראיון מדומה.", "A mock interview.")}</h1>
          <p>
            {t(
              "מראיין אחד, שאלה אחת בכל פעם, נגד השעון. הוא עובר בין נושאים לפי התשובות שלכם: מחזק כשקשה, מעלה רמה כשקל. הציונים נחשפים רק בסוף, בדוח.",
              "One interviewer, one question at a time, against the clock. It moves between subjects based on your answers: easier when you struggle, harder when it is easy. Scores are revealed only at the end, in the report.",
            )}
          </p>
        </div>
      </div>
      {demo && (
        <p className="notice">
          {t(
            "עוזר התרגול עדיין אינו מחובר בסביבה הזו: הראיון ירוץ עם ציוני הדגמה.",
            "The practice assistant is not connected in this environment: the interview runs with demo scoring.",
          )}
        </p>
      )}
      <div className="interview-setup">
        <h3>{t("כמה זמן יש לכם?", "How long do you have?")}</h3>
        <div className="duration-picker" role="radiogroup">
          {DURATIONS.map((d) => (
            <button
              key={d}
              role="radio"
              aria-checked={duration === d}
              className={`duration ${duration === d ? "on" : ""}`}
              onClick={() => setDuration(d)}
            >
              <strong>{d}</strong> {t("דקות", "min")}
            </button>
          ))}
        </div>
        <ul className="small muted interview-rules">
          <li>{t("השאלות מגיעות רק ממאגר השאלות שנבדק ואושר.", "Questions come only from the reviewed, published bank.")}</li>
          <li>{t("אפשר לבקש רמז, אבל זה נרשם ומקטין את הראיה לשליטה עצמאית.", "You may ask for a hint; it is recorded and lowers the evidence of independent mastery.")}</li>
          <li>{t("אפשר לסיים מוקדם; הדוח מכסה את מה שנענה.", "You can stop early; the report covers what you answered.")}</li>
        </ul>
        {error && <p className="notice error" role="alert">{error}</p>}
        <button className="primary" disabled={busy} onClick={() => void start()}>
          <Mic size={16} /> {busy ? t("פותחים את הראיון…", "Opening the interview…") : t("להתחיל ראיון", "Start the interview")}
        </button>
      </div>
      {past.length > 0 && (
        <div className="interview-past">
          <h3>{t("ראיונות קודמים", "Previous interviews")}</h3>
          <div className="question-table">
            {past.map((p) => (
              <button className="question-row history-row" key={p.id} onClick={() => onStarted(p.id)}>
                <Mic size={18} />
                <div>
                  <h3>
                    {p.duration_min} {t("דקות", "min")} · {p.turn_count} {t("שאלות", "questions")}
                  </h3>
                  <span className="topic">{date(p.started_at)}</span>
                </div>
                <span className="badge">
                  {p.status === "completed" ? t("הדוח מוכן", "Report ready") : t("בתהליך", "In progress")}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function InterviewRoom({ api, lang, userId, interviewId, onBack }: Props & { interviewId: string }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [interview, setInterview] = useState<Interview | null>(null);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [deadline, setDeadline] = useState<number | null>(null);
  const [now, setNow] = useState(Date.now());
  const live = useRef(true);
  const draftKey = `jr-interview-draft-${userId}-${interviewId}`;

  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
    };
  }, []);

  const apply = useCallback((next: Interview) => {
    setInterview(next);
    if (next.status !== "completed") setDeadline(Date.now() + next.remaining_min * 60_000);
  }, []);

  useEffect(() => {
    api
      .getInterview(interviewId)
      .then((i) => {
        if (!live.current) return;
        apply(i);
        const draft = readLocal<{ answer?: string; turn?: number }>(draftKey);
        if (draft && draft.turn === i.current_turn?.index) setAnswer(draft.answer ?? "");
      })
      .catch((e) => live.current && setError(apiMessage(e, lang)));
  }, [api, interviewId, apply, draftKey, lang]);

  // poll while the server is still evaluating an answer (a 202 or a refresh mid-evaluation); every poll
  // replaces the interview object, which re-arms this effect until the status changes
  useEffect(() => {
    if (interview?.status !== "evaluating") return;
    const timer = setTimeout(() => {
      api.getInterview(interviewId).then((i) => live.current && apply(i)).catch(() => {});
    }, 3000);
    return () => clearTimeout(timer);
  }, [api, interviewId, interview, apply]);

  useEffect(() => {
    if (!deadline) return;
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tick);
  }, [deadline]);

  useEffect(() => {
    if (interview?.status === "completed" && !report) {
      api.interviewReport(interviewId).then((r) => live.current && setReport(r)).catch((e) => setError(apiMessage(e, lang)));
    }
  }, [api, interviewId, interview?.status, report, lang]);

  useEffect(() => {
    if (interview?.current_turn) writeLocal(draftKey, { answer, turn: interview.current_turn.index });
  }, [answer, draftKey, interview?.current_turn]);

  async function submit() {
    if (!interview?.current_turn || busy) return;
    const turn = interview.current_turn;
    const keyName = `${draftKey}-key-${turn.index}`;
    const key = readLocal<string>(keyName) ?? newIdempotencyKey();
    writeLocal(keyName, key);
    setBusy(true);
    setError("");
    try {
      const result = await api.answerInterview(interviewId, turn.index, answer, key);
      if (live.current) {
        apply(result.interview);
        if (result.turn.status === "failed") {
          setAnswer(result.turn.answer ?? answer);       // keep the text: the candidate may send it again
        } else {
          setAnswer("");
          removeLocal(draftKey);
        }
      }
    } catch (e) {
      const code = (e as PracticeApiError).code;
      if (code === "already_submitted" || code === "conflict") {
        api.getInterview(interviewId).then((i) => live.current && apply(i)).catch(() => {});
      } else if (live.current) setError(apiMessage(e, lang));
    } finally {
      if (live.current) setBusy(false);
    }
  }

  async function hint() {
    if (busy) return;
    setBusy(true);
    try {
      const result = await api.interviewHint(interviewId);
      if (live.current) apply(result.interview);
    } catch (e) {
      if (live.current) setError(apiMessage(e, lang));
    } finally {
      if (live.current) setBusy(false);
    }
  }

  async function end() {
    if (busy || !window.confirm(t("לסיים את הראיון עכשיו? הדוח יכסה את מה שנענה.", "End the interview now? The report covers what you answered."))) return;
    setBusy(true);
    try {
      apply(await api.endInterview(interviewId));
    } catch (e) {
      if (live.current) setError(apiMessage(e, lang));
    } finally {
      if (live.current) setBusy(false);
    }
  }

  if (!interview) {
    return (
      <div className="loading" role="status">
        {error || t("טוענים את הראיון…", "Loading the interview…")}
      </div>
    );
  }
  if (interview.status === "completed") {
    return (
      <InterviewReportView interview={interview} report={report} lang={lang} onBack={onBack} error={error} />
    );
  }

  const turn = interview.current_turn;
  const secondsLeft = deadline ? Math.max(0, Math.round((deadline - now) / 1000)) : interview.remaining_min * 60;
  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, "0");
  const ss = String(secondsLeft % 60).padStart(2, "0");
  const Arrow = lang === "he" ? ArrowLeft : ArrowRight;
  return (
    <section className="interview-room">
      <header className="interview-bar">
        <span className="interview-timer" dir="ltr" aria-live="off">
          <Clock3 size={16} /> {mm}:{ss}
        </span>
        <span className="small muted">
          {t("שאלה", "Question")} {interview.turn_count} · {interview.turns.length} {t("נענו", "answered")}
        </span>
        <span className="interview-plan small muted" title={interview.plan.map((p) => p.label).join(", ")}>
          {[...new Set(interview.plan.map((p) => subjectLabel(p.subject, lang)))].join(" · ")}
        </span>
        <button className="ghost" disabled={busy} onClick={() => void end()}>
          <Square size={14} /> {t("סיום מוקדם", "End early")}
        </button>
      </header>

      {turn && (
        <article className="interview-question">
          <div className="row spread">
            <span className="badge">
              {turn.skill_label}
              {turn.trial && <span className="badge trial">{t("בבדיקה חיה", "On trial")}</span>}
            </span>
            <span className="small muted">
              {t("רמת קושי", "Difficulty")} {turn.difficulty}
              {turn.subject_switch && <> · {t("נושא חדש", "new subject")}</>}
            </span>
          </div>
          <p className="interview-prompt" dir="auto">
            {turn.question}
          </p>
          {turn.hints.length > 0 && (
            <div className="interview-hints">
              {turn.hints.map((h) => (
                <p key={h.level} className="hint" dir="auto">
                  <Lightbulb size={14} /> {h.text}
                </p>
              ))}
            </div>
          )}
          {turn.status === "evaluating" || interview.status === "evaluating" ? (
            <div className="evaluation-status" role="status">
              {t("התשובה נשמרה. המראיין חושב על השאלה הבאה…", "Your answer is saved. The interviewer is preparing the next question…")}
            </div>
          ) : (
            <>
              <AnswerEditor value={answer} onChange={setAnswer} lang={lang} disabled={busy} codeLanguage={null} starterCode={null} />
              {turn.status === "failed" && (
                <p className="notice">
                  {t("ההערכה לא הושלמה. אפשר לשלוח את התשובה שוב.", "The evaluation did not finish. You can send your answer again.")}
                </p>
              )}
              {error && <p className="notice error" role="alert">{error}</p>}
              {secondsLeft === 0 && (
                <p className="notice" role="status">
                  {t(
                    "הזמן נגמר. שלחו את מה שיש לכם; המראיין יסכם אחרי התשובה הזו.",
                    "Time is up. Send what you have; the interviewer wraps up after this answer.",
                  )}
                </p>
              )}
              <div className="row interview-actions">
                <button className="primary" disabled={busy || !answer.trim()} onClick={() => void submit()}>
                  {busy ? t("שולחים…", "Sending…") : t("שליחת התשובה", "Send answer")} <Arrow size={16} />
                </button>
                {interview.can_hint && secondsLeft > 0 && (
                  <button disabled={busy} onClick={() => void hint()}>
                    <Lightbulb size={16} /> {t("רמז", "Hint")}
                  </button>
                )}
                <span className="small muted">
                  {t("כמו בראיון אמיתי: המשוב מגיע בסוף.", "As in a real interview: feedback comes at the end.")}
                </span>
              </div>
            </>
          )}
        </article>
      )}

      {interview.turns.length > 0 && (
        <details className="interview-answered">
          <summary>
            {interview.turns.length} {t("שאלות שנענו", "questions answered")}
          </summary>
          <ol>
            {interview.turns.map((x) => (
              <li key={x.index} dir="auto">
                <span className="badge">{x.skill_label}</span> {x.question.slice(0, 120)}
                {x.question.length > 120 ? "…" : ""}
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}

function InterviewReportView({
  interview,
  report,
  lang,
  onBack,
  error,
}: {
  interview: Interview;
  report: InterviewReport | null;
  lang: Lang;
  onBack: () => void;
  error: string;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const overall = report?.fit["session_overall"] ?? report?.fit["role"];
  return (
    <section className="interview-report">
      <div className="page-heading">
        <div>
          <h1>{t("הראיון הסתיים.", "The interview is over.")}</h1>
          <p>
            {interview.turns.length} {t("שאלות", "questions")} · {interview.duration_min} {t("דקות", "min")}
            {interview.ended_early && <> · {t("הסתיים מוקדם", "ended early")}</>}
          </p>
        </div>
        <button onClick={onBack}>{t("חזרה לראיונות", "Back to interviews")}</button>
      </div>
      {!report && !error && <div className="loading" role="status">{t("מכינים את הדוח…", "Preparing the report…")}</div>}
      {error && <p className="notice error">{error}</p>}
      {report && (
        <>
          <div className="fit-cards">
            {Object.entries(report.fit).map(([scope, fit]) => (
              <div className="fit-card" key={scope}>
                <span className="small muted">
                  {scope === "role"
                    ? t("התאמה לתפקיד", "Role fit")
                    : scope === "company"
                      ? t("התאמה לחברה", "Company fit")
                      : t("סך הכול", "Overall")}
                </span>
                <strong className="fit-score">{fit.fit_score === null ? "—" : `${Math.round(fit.fit_score)}%`}</strong>
                <span className="small muted">
                  {fit.skills_assessed}/{fit.skills_total} {t("מיומנויות הוערכו", "skills assessed")}
                  {fit.cap_applied !== null && <> · {t("מוגבל בגלל פער במיומנות ליבה", "capped by a core-skill gap")}</>}
                </span>
              </div>
            ))}
          </div>
          {overall && overall.core_gaps.length > 0 && (
            <p className="notice">
              {t("פערים במיומנויות ליבה:", "Core-skill gaps:")} {overall.core_gaps.join(", ")}
            </p>
          )}
          <div className="report-columns">
            <section>
              <h3>{t("מיומנות אחר מיומנות", "Skill by skill")}</h3>
              <table className="skill-table">
                <thead>
                  <tr>
                    <th>{t("מיומנות", "Skill")}</th>
                    <th>{t("רמה", "Level")}</th>
                    <th>{t("נדרש", "Required")}</th>
                  </tr>
                </thead>
                <tbody>
                  {report.skills
                    .filter((s) => s.status !== "not_assessed")
                    .map((s) => (
                      <tr key={s.key} className={s.level_gap !== null && s.level_gap < 0 ? "gap" : ""}>
                        <td dir="auto">
                          {s.label}
                          {s.status === "insufficient_evidence" && (
                            <span className="small muted"> · {t("עדות חלקית", "partial evidence")}</span>
                          )}
                        </td>
                        <td>{s.proficiency_level ?? "—"}</td>
                        <td>{s.required_level}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              {report.cover_next_time.length > 0 && (
                <p className="small muted">
                  {t("לא נבדקו הפעם:", "Not covered this time:")} {report.cover_next_time.map((s) => s.label).join(", ")}
                </p>
              )}
            </section>
            <section>
              <h3>{t("מה לתרגל הלאה", "What to practise next")}</h3>
              <ul>
                {report.recommended_next_skills.map((s) => (
                  <li key={s.key} dir="auto">{s.label}</li>
                ))}
                {report.recommended_next_skills.length === 0 && <li>{t("אין פערים מובהקים. כל הכבוד.", "No clear gaps. Well done.")}</li>}
              </ul>
              {report.top_tips.length > 0 && (
                <>
                  <h3>{t("טיפים", "Tips")}</h3>
                  <ul>
                    {report.top_tips.map((tip, i) => (
                      <li key={i} dir="auto">{tip}</li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          </div>
          <section className="report-narrative">
            <SimpleMarkdown text={report.narrative_md} />
          </section>
          <section>
            <h3>{t("השאלות והתשובות", "Questions and answers")}</h3>
            <ol className="report-turns">
              {report.turns.map((x) => (
                <TurnCard key={x.index} turn={x} lang={lang} />
              ))}
            </ol>
          </section>
        </>
      )}
    </section>
  );
}

function TurnCard({ turn: x, lang }: { turn: InterviewTurn; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  return (
    <li className="report-turn">
      <div className="row spread">
        <span className="badge">{x.skill_label}</span>
        <span className={x.band ? `badge band-${x.band.toLowerCase()}` : "badge"}>
          {x.status === "skipped" ? t("לא נענתה", "Not answered") : bandLabel(x.band, lang)}
        </span>
      </div>
      <p className="interview-prompt" dir="auto">{x.question}</p>
      {x.answer && <p className="report-answer" dir="auto">{x.answer}</p>}
      {x.summary && <p dir="auto"><strong>{t("סיכום:", "Summary:")}</strong> {x.summary}</p>}
      {x.key_points_missed.length > 0 && (
        <p className="small" dir="auto">
          {t("מה חסר:", "Missing:")} {x.key_points_missed.join(" · ")}
        </p>
      )}
      {x.check && (
        <p className="small muted" dir="auto">
          {x.check.passed === true
            ? t("הבדיקה האוטומטית עברה", "Automatic check passed")
            : x.check.passed === false
              ? t("הבדיקה האוטומטית נכשלה", "Automatic check failed")
              : t("הבדיקה האוטומטית לא הכריעה", "Automatic check inconclusive")}
          {": "}
          {x.check.detail}
        </p>
      )}
    </li>
  );
}

/** Just enough markdown for the report: headings, bullets, paragraphs. */
function SimpleMarkdown({ text }: { text: string }) {
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];
  const flush = () => {
    if (list.length) {
      blocks.push(
        <ul key={`l${blocks.length}`}>
          {list.map((item, i) => (
            <li key={i} dir="auto">{item}</li>
          ))}
        </ul>,
      );
      list = [];
    }
  };
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) {
      flush();
      continue;
    }
    if (line.startsWith("#")) {
      flush();
      blocks.push(<h3 key={`h${blocks.length}`} dir="auto">{line.replace(/^#+\s*/, "")}</h3>);
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      list.push(line.slice(2));
    } else {
      flush();
      blocks.push(<p key={`p${blocks.length}`} dir="auto">{line}</p>);
    }
  }
  flush();
  return <div className="markdown">{blocks}</div>;
}
