"use client";

import { useEffect, useRef, useState } from "react";
import { ACCOUNT_GOAL_SAVED, type AccountGoalSaved } from "../../lib/goal-selection";
import { practiceApi, type ApiLang, type Goal } from "../../lib/practice-api";
import { GoalSetup } from "../goal-setup";
import { GoalSummary } from "../goal-summary";

type GoalStationProps = { userId: string; lang: ApiLang; onSaved: () => void };

export function TourAccountGoal(props: GoalStationProps) {
  return <GoalStation key={props.userId} {...props} />;
}

function GoalStation({ userId, lang, onSaved }: GoalStationProps) {
  const he = lang === "he";
  const [api] = useState(() => practiceApi());
  const [goal, setGoal] = useState<Goal | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [retry, setRetry] = useState(0);
  const [view, setView] = useState<"review" | "edit" | "confirmed">("review");
  const revision = useRef(0);
  const mounted = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    let current = true;
    const request = revision.current;
    setLoadError(false);
    void api.getGoal(lang, userId).then(saved => {
      if (current && request === revision.current) setGoal(saved);
    }).catch(() => {
      if (current && request === revision.current) setLoadError(true);
    });
    return () => { current = false; };
  }, [api, userId, lang, retry]);

  function confirm() {
    setView("confirmed");
    onSaved();
  }

  function saved(updated: Goal) {
    revision.current++;
    window.dispatchEvent(new CustomEvent<AccountGoalSaved>(ACCOUNT_GOAL_SAVED, { detail: { userId, goal: updated } }));
    if (!mounted.current) return;
    setGoal(updated);
    confirm();
  }

  if (!goal && loadError) return <div role="alert">
    <p>{he ? "לא הצלחנו לטעון את היעד מהחשבון." : "Your account’s learning goal could not be loaded."}</p>
    <button type="button" onClick={() => setRetry(value => value + 1)}>{he ? "ניסיון נוסף" : "Try again"}</button>
  </div>;
  if (!goal) return <p role="status">{he ? "טוענים את היעד שלכם…" : "Loading your learning goal…"}</p>;
  if (!goal.complete || view === "edit") return <GoalSetup api={api} userId={userId} lang={lang} goal={goal}
    onSaved={saved} onSkip={goal.complete ? () => setView("review") : undefined} />;

  return <div>
    <GoalSummary goal={goal} lang={lang} onEdit={() => setView("edit")} />
    {view === "confirmed" ? <p role="status">{he ? "היעד מוכן. אפשר להמשיך לתחנה הבאה." : "Your goal is ready. Continue to the next stop."}</p>
      : <button type="button" className="primary" data-muxi-control="goal-keep" onClick={confirm}>
        {he ? "להמשיך עם היעד הזה" : "Keep this goal"}
      </button>}
  </div>;
}
