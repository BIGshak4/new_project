/** Loaded only by /games/preview. This simulator never calls the live API. */
import data from "../components/duels/quiz-demo-data.json";
import { getDemoAvatar } from "./avatar-demo";
import type { Duel, DuelClient, DuelLanguage, QuizReview } from "./duel-types";

type Text = { he: string; en: string };
type DemoQuestion = { key: string; source_key: string; variant: number; prompt: Text; choices: Text[]; correct: number; explanation: Text };
const questions: DemoQuestion[] = data.questions;
const STORAGE = "jobrun-duel-demo-v1";
type State = { balance: number; rows: { duel: Duel; keys: string[]; opened: number; settled: boolean }[] };

export function sampleDemoQuestions(pool: DemoQuestion[], random = Math.random): DemoQuestion[] {
  const groups = new Map<string, DemoQuestion[]>();
  for (const question of pool) groups.set(question.source_key, [...(groups.get(question.source_key) ?? []), question]);
  const sources = [...groups.values()];
  for (let i = sources.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [sources[i], sources[j]] = [sources[j], sources[i]]; }
  return sources.slice(0, 5).map(group => group[Math.floor(random() * group.length)]);
}

export function demoDuelClient(now = Date.now): DuelClient {
  let state: State = { balance: 50, rows: [] };
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE) ?? "null") as State | null;
    if (saved && Array.isArray(saved.rows) && typeof saved.balance === "number" && saved.rows.every(r => r.keys.every(k => questions.some(q => q.key === k)))) state = saved;
  } catch { /* Storage is optional in the public preview. */ }
  const iso = () => new Date(now()).toISOString();
  const save = () => { try { sessionStorage.setItem(STORAGE, JSON.stringify(state)); } catch {} };
  const row = (id: string) => { const value = state.rows.find(r => r.duel.id === id); if (!value) throw new Error("Game not found"); return value; };
  function tick(value: State["rows"][number]): Duel {
    const d = value.duel;
    d.me.avatar = getDemoAvatar();
    const pool = value.keys.map(key => questions.find(q => q.key === key)!);
    const lang = d.language;
    if (d.status === "open" && now() - Date.parse(d.created_at) >= 1800) {
      d.status = "active"; d.accepted_at = iso();
      d.opponent = { avatar: { component: "xor", color: "mint", skin: "circuit" }, ready: false, answered: false, answered_count: 0, score: null, seconds: null };
      d.lobby_expires_at = new Date(now() + 600000).toISOString();
    }
    if (d.status === "active" && !d.started_at && d.me.ready && now() - Date.parse(d.accepted_at!) >= 3200) {
      d.opponent!.ready = true; d.started_at = iso(); d.deadline = new Date(now() + 300000).toISOString(); value.opened = now();
    }
    if (d.status === "active" && d.started_at && d.quiz) {
      const quiz = d.quiz;
      while (quiz.answers.length < pool.length && now() - value.opened >= 60000) {
        quiz.answers.push({ index: quiz.answers.length, choice: null, correct: false, seconds: 60 }); value.opened += 60000;
      }
      quiz.index = quiz.answers.length; quiz.finished = quiz.index >= pool.length;
      quiz.score = quiz.answers.filter(a => a.correct).length;
      d.me.answered_count = quiz.index; d.me.answered = quiz.finished; d.me.score = quiz.score;
      const otherCount = Math.min(5, Math.max(0, Math.floor((now() - Date.parse(d.started_at)) / 4000)));
      d.opponent!.answered_count = otherCount; d.opponent!.answered = otherCount >= 5;
      const q = pool[quiz.index];
      quiz.seconds_left = quiz.finished ? null : Math.max(0, Math.ceil(60 - (now() - value.opened) / 1000));
      quiz.current = q ? { index: quiz.index, key: q.key, source_key: q.source_key, variant: q.variant, prompt: q.prompt[lang], choices: q.choices.map(c => c[lang]) } : null;
      d.seconds_left = Math.max(0, Math.ceil((Date.parse(d.deadline!) - now()) / 1000));
      if (quiz.finished && otherCount >= 5) {
        d.status = "settled"; d.settled_at = iso();
        d.me.seconds = quiz.answers.reduce((sum, answer) => sum + answer.seconds, 0);
        d.opponent!.score = 4; d.opponent!.seconds = 20;
        const difference = quiz.score - 4 || 20 - d.me.seconds;
        d.won = difference === 0 ? null : difference > 0;
        d.outcome = d.won === null ? "draw" : d.won ? "challenger" : "opponent";
        d.coins_delta = d.won === null ? 0 : d.won ? 5 : -5;
        quiz.review = pool.map((item, index): QuizReview => ({ index, key: item.key, source_key: item.source_key, variant: item.variant,
          prompt: item.prompt[lang], choices: item.choices.map(c => c[lang]), correct: item.correct, explanation: item.explanation[lang],
          mine: quiz.answers[index].choice, theirs: index === 2 ? (item.correct + 1) % 4 : item.correct,
          mine_correct: quiz.answers[index].correct, theirs_correct: index !== 2 }));
        quiz.current = null; quiz.seconds_left = null;
        if (!value.settled) { state.balance += d.won === null ? 5 : d.won ? 10 : 0; value.settled = true; }
      }
    }
    d.server_now = iso(); save(); return structuredClone(d);
  }
  const rules = { stake: 5, quiz_questions: 5, quiz_seconds_per_question: 60, quiz_available: true, quiz_source_count: 10, quiz_variant_count: 50, readiness_required: true, no_monetary_value: true };
  async function create(language: DuelLanguage): Promise<Duel> {
    if (state.balance < 5) throw new Error(language === "he" ? "אין מספיק מטבעות הדגמה. רעננו את ההדגמה בהפעלה חדשה." : "Not enough demo coins.");
    const id = crypto.randomUUID(); const code = id.slice(0, 8);
    const duel: Duel = { id, code, share_path: `/games/preview`, share_url: "", status: "open", mode: "quiz", role: "challenger", stake: 5, pot: 10, language, question: null,
      me: { avatar: getDemoAvatar(), ready: false, answered: false, answered_count: 0, score: null, seconds: null }, opponent: null,
      quiz: { total: 5, seconds_per_question: 60, index: 0, current: null, seconds_left: null, answers: [], score: 0, finished: false, review: [] },
      deadline: null, seconds_left: null, started_at: null, server_now: iso(), lobby_expires_at: null,
      created_at: iso(), accepted_at: null, settled_at: null, outcome: null, won: null, coins_delta: null };
    state.balance -= 5; state.rows.unshift({ duel, keys: sampleDemoQuestions(questions).map(q => q.key), opened: 0, settled: false }); save(); return structuredClone(duel);
  }
  return {
    list: async () => ({ duels: state.rows.map(tick), rules }),
    wallet: async () => ({ balance: state.balance, enabled: true, no_monetary_value: true }),
    get: async id => tick(row(id)), create,
    accept: async () => { throw new Error("Use Challenge friend in the preview; the simulated friend joins automatically."); },
    ready: async id => { const value = row(id); value.duel.me.ready = true; return tick(value); },
    answer: async (id, choice, item) => {
      const value = row(id); tick(value);
      const quiz = value.duel.quiz!;
      if (value.duel.status !== "active" || !value.duel.started_at || item !== quiz.index || quiz.finished) throw new Error("The question changed; reload the game.");
      if (choice === null && (quiz.seconds_left ?? 0) > 0) throw new Error("The question is still open.");
      const q = questions.find(q => q.key === value.keys[item])!;
      quiz.answers.push({ index: item, choice, correct: choice === q.correct, seconds: Math.min(60, Math.max(0, (now() - value.opened) / 1000)) });
      value.opened = now(); return tick(value);
    },
    cancel: async id => { const value = row(id); const d = value.duel; if (d.status === "cancelled") return tick(value); if (d.started_at || d.status === "settled") throw new Error("This game has started."); d.status = "cancelled"; d.outcome = "cancelled"; d.coins_delta = 0; state.balance += 5; return tick(value); },
  };
}
