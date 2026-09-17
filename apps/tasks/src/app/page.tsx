"use client";
import { useState, useEffect, useMemo } from "react";
import type { User } from "@supabase/supabase-js";
import {
  LayoutDashboard,
  Archive,
  Search,
  Plus,
  LogOut,
  ArrowUpRight,
  List,
  Columns3,
  Check,
  ArrowRight,
  X,
  MessageSquare,
  Download,
  RefreshCw,
  Link as LinkIcon,
  History,
  CalendarDays,
} from "lucide-react";
import { Auth } from "../components/auth";
import { TaskFiles } from "../components/task-files";
import { supabase } from "../lib/supabase";
type Subtask = { id: string; text: string; done: boolean };
type TaskLink = { id: string; label: string; url: string };
type Task = {
  id: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  area: string;
  phase: string;
  assignees: string[];
  due_date: string | null;
  subtasks: Subtask[];
  links: TaskLink[];
  archived: boolean;
  version: number;
  created_at: string;
  updated_at: string;
  created_by: string | null;
};
const statuses = [
  ["todo", "לביצוע"],
  ["doing", "בעבודה"],
  ["blocked", "ממתין"],
  ["done", "הושלם"],
];
const priorities: Record<string, string> = {
  high: "גבוהה",
  medium: "רגילה",
  low: "נמוכה",
};
const people: Record<string, string> = { harel: "הראל", shaked: "שקד" };
function blank(): Task {
  return {
    id: crypto.randomUUID(),
    title: "",
    description: "",
    status: "todo",
    priority: "medium",
    area: "מוצר",
    phase: "גרסה ראשונה",
    assignees: [],
    due_date: null,
    subtasks: [],
    links: [],
    archived: false,
    version: 1,
    created_at: "",
    updated_at: "",
    created_by: null,
  };
}
function safeURL(url: string) {
  try {
    return ["http:", "https:"].includes(new URL(url).protocol);
  } catch {
    return false;
  }
}
function download(name: string, data: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
export default function Page() {
  return (
    <Auth kind="tasks">
      {(user, signOut) => <Board user={user} signOut={signOut} />}
    </Auth>
  );
}
function Board({ user, signOut }: { user: User; signOut: () => void }) {
  const [tasks, setTasks] = useState<Task[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [query, setQuery] = useState(""),
    [owner, setOwner] = useState("all"),
    [area, setArea] = useState("all"),
    [priority, setPriority] = useState("all"),
    [view, setView] = useState("board"),
    [archive, setArchive] = useState(false),
    [selected, setSelected] = useState<Task | null>(null),
    [isNew, setIsNew] = useState(false),
    [notice, setNotice] = useState("");
  async function load(silent = false) {
    if (!silent) setLoading(true);
    const { data, error } = await supabase
      .from("jr_tasks")
      .select("*")
      .order("created_at", { ascending: false });
    if (error) setError("לא הצלחנו לטעון את הלוח. בדקו את החיבור ונסו שוב.");
    else {
      setTasks(data as Task[]);
      setError("");
    }
    setLoading(false);
  }
  useEffect(() => {
    void load();
    const timer = setInterval(() => void load(true), 30000);
    return () => clearInterval(timer);
  }, []);
  const filtered = useMemo(
    () =>
      tasks.filter(
        (task) =>
          task.archived === archive &&
          `${task.title} ${task.description} ${task.area} ${task.phase}`
            .toLowerCase()
            .includes(query.toLowerCase()) &&
          (owner === "all" || task.assignees.includes(owner)) &&
          (area === "all" || task.area === area) &&
          (priority === "all" || task.priority === priority),
      ),
    [tasks, query, owner, area, priority, archive],
  );
  const active = tasks.filter((t) => !t.archived);
  const counts = (status: string) =>
    active.filter((t) => t.status === status).length;
  const areas = Array.from(new Set(tasks.map((t) => t.area))).sort();
  function startTask() {
    let task = blank();
    try {
      const id = sessionStorage.getItem(`jr-new-task-${user.id}`);
      if (id) {
        const saved = sessionStorage.getItem(`jr-task-draft-${user.id}-${id}`);
        if (saved) task = JSON.parse(saved);
      }
      sessionStorage.setItem(`jr-new-task-${user.id}`, task.id);
    } catch {}
    setSelected(task);
    setIsNew(true);
  }
  function open(task: Task) {
    setSelected(task);
    setIsNew(false);
    setNotice("");
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="wordmark" href="/" dir="ltr">
          JobRun
          <span className="logo-dot" />
        </a>
        <nav>
          <button
            className={`nav-item ${!archive ? "active" : ""}`}
            onClick={() => {
              setArchive(false);
              setSelected(null);
            }}
          >
            <LayoutDashboard size={18} />
            לוח העבודה<span className="count">{active.length}</span>
          </button>
          <button
            className={`nav-item ${archive ? "active" : ""}`}
            onClick={() => {
              setArchive(true);
              setSelected(null);
            }}
          >
            <Archive size={18} />
            ארכיון
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="row">
            <span className="avatar">הא</span>
            <span className="avatar shaked">שב</span>
            <span className="small">הראל ושקד</span>
          </div>
          <a
            className="small"
            href="https://jobrun-practice.netlify.app"
            target="_blank"
            rel="noreferrer"
          >
            אתר התרגול <ArrowUpRight size={14} />
          </a>
          <p className="sidebar-note">
            מהרעיון הראשון, עד למוצר שאנשים אוהבים להשתמש בו.
          </p>
        </div>
      </aside>
      <div className="shell-main">
        <header className="topbar">
          <span className="topbar-label">סביבת העבודה של המייסדים</span>
          <div className="row">
            <span className="small muted">
              {new Intl.DateTimeFormat("he-IL", {
                day: "numeric",
                month: "long",
              }).format(new Date())}
            </span>
            <button
              className="icon-button"
              title="יציאה"
              aria-label="יציאה"
              onClick={signOut}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main className="content">
          {selected ? (
            <TaskEditor
              key={selected.id}
              initial={selected}
              isNew={isNew}
              user={user}
              onClose={() => {
                setSelected(null);
                void load(true);
              }}
              onSave={(task) => {
                if (isNew) sessionStorage.removeItem(`jr-new-task-${user.id}`);
                setTasks((old) => [
                  task,
                  ...old.filter((t) => t.id !== task.id),
                ]);
                setSelected(task);
                setIsNew(false);
                setNotice("השינויים נשמרו.");
              }}
            />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    {archive ? "החלטות שנשארות איתנו." : "עושים מקום להתקדמות."}
                  </h1>
                  <p>
                    {archive
                      ? "משימות שהועברו לארכיון, עם כל ההקשר וההיסטוריה."
                      : "מה בונים, מי מוביל, ומה הצעד הבא."}
                  </p>
                </div>
                <button className="primary" onClick={startTask}>
                  <Plus size={18} />
                  משימה חדשה
                </button>
              </div>
              <div className="summary-strip">
                <span>
                  <strong>{counts("todo")}</strong>לביצוע
                </span>
                <span>
                  <strong>{counts("doing")}</strong>בעבודה
                </span>
                <span>
                  <strong>{counts("blocked")}</strong>ממתינות להמשך
                </span>
                <span>
                  <strong>{counts("done")}</strong>הושלמו
                </span>
              </div>
              {notice && (
                <p role="status" className="status-message">
                  {notice}
                </p>
              )}
              {error && (
                <div className="notice error" role="alert">
                  {error}
                  <button onClick={() => void load()}>ניסיון נוסף</button>
                </div>
              )}
              <div className="toolbar">
                <div className="search">
                  <Search size={17} />
                  <input
                    aria-label="חיפוש משימות"
                    placeholder="חפשו משימה, החלטה או נושא…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
                <select
                  aria-label="אחראי"
                  value={owner}
                  onChange={(e) => setOwner(e.target.value)}
                >
                  <option value="all">כולם</option>
                  <option value="harel">הראל</option>
                  <option value="shaked">שקד</option>
                </select>
                <select
                  aria-label="תחום"
                  value={area}
                  onChange={(e) => setArea(e.target.value)}
                >
                  <option value="all">כל התחומים</option>
                  {areas.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
                <select
                  aria-label="עדיפות"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  <option value="all">כל העדיפויות</option>
                  {Object.entries(priorities).map(([id, name]) => (
                    <option value={id} key={id}>
                      {name}
                    </option>
                  ))}
                </select>
                <div className="segmented">
                  <button
                    className={view === "board" ? "active" : ""}
                    aria-label="תצוגת לוח"
                    aria-pressed={view === "board"}
                    onClick={() => setView("board")}
                  >
                    <Columns3 size={16} />
                  </button>
                  <button
                    className={view === "list" ? "active" : ""}
                    aria-label="תצוגת רשימה"
                    aria-pressed={view === "list"}
                    onClick={() => setView("list")}
                  >
                    <List size={16} />
                  </button>
                </div>
                <button
                  className="icon-button"
                  aria-label="רענון הלוח"
                  title="רענון הלוח"
                  onClick={() => void load()}
                >
                  <RefreshCw size={16} />
                </button>
                <button
                  className="icon-button"
                  aria-label="יצוא נתוני המשימות"
                  title="יצוא נתוני המשימות"
                  onClick={() =>
                    download("jobrun-tasks-backup.json", {
                      exportedAt: new Date().toISOString(),
                      tasks,
                    })
                  }
                >
                  <Download size={16} />
                </button>
              </div>
              {loading ? (
                <div className="loading" role="status">
                  טוענים את הלוח…
                </div>
              ) : !filtered.length ? (
                <div className="empty">
                  <LayoutDashboard size={30} />
                  <h2>
                    {archive ? "הארכיון עוד ריק." : "יש מקום למשימה הבאה."}
                  </h2>
                  <p>
                    {tasks.length
                      ? "נסו לשנות את החיפוש או הסינון."
                      : "צרו משימה ראשונה והחליטו מי מוביל אותה."}
                  </p>
                  <button
                    onClick={() => {
                      setQuery("");
                      setOwner("all");
                      setArea("all");
                      setPriority("all");
                    }}
                  >
                    איפוס סינון
                  </button>
                </div>
              ) : view === "board" ? (
                <div className="board">
                  {statuses.map(([id, label]) => (
                    <section className="column" key={id}>
                      <div className="column-head">
                        <div className={`badge ${id}`}>{label}</div>
                        <span>
                          {filtered.filter((t) => t.status === id).length}
                        </span>
                      </div>
                      {filtered
                        .filter((t) => t.status === id)
                        .map((task) => (
                          <button
                            key={task.id}
                            className="task-card"
                            onClick={() => open(task)}
                          >
                            <div className="row spread">
                              <span className="small muted">{task.area}</span>
                              {task.priority === "high" && (
                                <span className="badge high">עדיפות גבוהה</span>
                              )}
                            </div>
                            <h3>{task.title}</h3>
                            <div className="task-meta">
                              <div className="avatar-row">
                                {task.assignees.map((a) => (
                                  <span
                                    key={a}
                                    className={`avatar ${a}`}
                                    title={people[a]}
                                  >
                                    {a === "harel" ? "הא" : "שב"}
                                  </span>
                                ))}
                              </div>
                              <span>
                                {task.subtasks.length > 0 &&
                                  `${task.subtasks.filter((s) => s.done).length}/${task.subtasks.length} צעדים`}
                              </span>
                              {task.due_date && (
                                <span>
                                  <CalendarDays size={12} />{" "}
                                  {new Intl.DateTimeFormat("he-IL", {
                                    day: "numeric",
                                    month: "numeric",
                                  }).format(
                                    new Date(task.due_date + "T12:00:00"),
                                  )}
                                </span>
                              )}
                            </div>
                          </button>
                        ))}
                      {!filtered.some((t) => t.status === id) && (
                        <div className="empty-column">אין כאן משימות כרגע</div>
                      )}
                    </section>
                  ))}
                </div>
              ) : (
                <div className="task-list">
                  {filtered.map((task) => (
                    <button
                      key={task.id}
                      className="task-list-row"
                      onClick={() => open(task)}
                    >
                      <span>{task.title}</span>
                      <span className={`badge ${task.status}`}>
                        {statuses.find((s) => s[0] === task.status)?.[1]}
                      </span>
                      <span className="small muted list-secondary">
                        {task.area}
                      </span>
                      <span className="small muted list-secondary">
                        {task.assignees.map((a) => people[a]).join(", ") ||
                          "ללא אחראי"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
function TaskEditor({
  initial,
  isNew,
  user,
  onClose,
  onSave,
}: {
  initial: Task;
  isNew: boolean;
  user: User;
  onClose: () => void;
  onSave: (task: Task) => void;
}) {
  const [draft, setDraft] = useState<Task>(initial),
    [base, setBase] = useState(initial),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(""),
    [conflict, setConflict] = useState<Task | null>(null),
    [comment, setComment] = useState(""),
    [comments, setComments] = useState<
      { id: string; body: string; created_at: string; author_id: string }[]
    >([]),
    [events, setEvents] = useState<
      { id: number; version: number; created_at: string; snapshot: Task }[]
    >([]),
    [tab, setTab] = useState("comments"),
    [commentBusy, setCommentBusy] = useState(false),
    [ready, setReady] = useState(false);
  const key = `jr-task-draft-${user.id}-${draft.id}`,
    dirty = JSON.stringify(draft) !== JSON.stringify(base);
  useEffect(() => {
    try {
      const local = sessionStorage.getItem(key);
      if (local) {
        const restored = JSON.parse(local);
        setDraft(restored);
        setBase({ ...initial, version: restored.version });
        setSaved("שוחזרה טיוטה מקומית שטרם נשמרה.");
      }
    } catch {}
    setReady(true);
  }, [key]);
  useEffect(() => {
    if (ready && dirty) sessionStorage.setItem(key, JSON.stringify(draft));
    const before = (e: BeforeUnloadEvent) => {
      if (dirty) e.preventDefault();
    };
    window.addEventListener("beforeunload", before);
    return () => window.removeEventListener("beforeunload", before);
  }, [draft, dirty, ready, key]);
  async function loadDetails() {
    if (isNew) return;
    const [c, e] = await Promise.all([
      supabase
        .from("jr_comments")
        .select("*")
        .eq("task_id", draft.id)
        .order("created_at"),
      supabase
        .from("jr_task_events")
        .select("id,version,created_at,snapshot")
        .eq("task_id", draft.id)
        .order("created_at", { ascending: false })
        .limit(20),
    ]);
    if (c.error || e.error)
      setError("לא הצלחנו לטעון את ההערות או ההיסטוריה. נסו לרענן.");
    else {
      setComments(c.data);
      setEvents(e.data);
    }
  }
  useEffect(() => {
    void loadDetails();
  }, [isNew, initial.version]);
  function update<K extends keyof Task>(key: K, value: Task[K]) {
    setDraft((d) => ({ ...d, [key]: value }));
    setSaved("");
  }
  async function save(e?: React.FormEvent) {
    e?.preventDefault();
    setError("");
    setSaved("");
    if (!draft.title.trim()) {
      setError("צריך לתת למשימה כותרת.");
      return;
    }
    if (draft.links.some((l) => !safeURL(l.url))) {
      setError("כל קישור צריך להתחיל ב־https:// או http://.");
      return;
    }
    setBusy(true);
    const {
      title,
      description,
      status,
      priority,
      area,
      phase,
      assignees,
      due_date,
      subtasks,
      links,
      archived,
    } = draft;
    const payload = {
      title: title.trim(),
      description,
      status,
      priority,
      area,
      phase,
      assignees,
      due_date: due_date || null,
      subtasks,
      links,
      archived,
    };
    const result = isNew
      ? await supabase
          .from("jr_tasks")
          .insert({ ...payload, id: draft.id, created_by: user.id })
          .select()
          .single()
      : await supabase
          .from("jr_tasks")
          .update(payload)
          .eq("id", draft.id)
          .eq("version", base.version)
          .select()
          .maybeSingle();
    if (result.error)
      setError("השמירה לא הושלמה. הטיוטה נשמרה במחשב; בדקו חיבור ונסו שוב.");
    else if (!result.data) {
      const fresh = await supabase
        .from("jr_tasks")
        .select("*")
        .eq("id", draft.id)
        .single();
      setConflict(fresh.data);
      setError(
        "המשימה עודכנה בחלון אחר. הטיוטה שלכם נשמרה ולא דרסה את השינויים.",
      );
    } else {
      setDraft(result.data);
      setBase(result.data);
      setConflict(null);
      sessionStorage.removeItem(key);
      setSaved("נשמר בהצלחה.");
      onSave(result.data);
    }
    setBusy(false);
  }
  async function addComment() {
    if (!comment.trim()) return;
    setCommentBusy(true);
    const { error } = await supabase
      .from("jr_comments")
      .insert({ task_id: draft.id, body: comment.trim(), author_id: user.id });
    if (error) setError("ההערה לא נשמרה. הטקסט נשאר כאן, אפשר לנסות שוב.");
    else {
      setComment("");
      void loadDetails();
    }
    setCommentBusy(false);
  }
  function close() {
    if (
      dirty &&
      !window.confirm(
        "יש שינויים שלא נשמרו לחשבון. הטיוטה תישמר במחשב הזה. לצאת מהמשימה?",
      )
    )
      return;
    onClose();
  }
  return (
    <>
      <div className="row spread" style={{ marginBottom: 22 }}>
        <button className="text-button" onClick={close}>
          <ArrowRight size={16} />
          חזרה ללוח
        </button>
        <span className="small muted">
          {isNew ? "משימה חדשה" : `גרסה ${base.version}`} ·{" "}
          {dirty ? "טיוטה מקומית" : "נשמר בחשבון"}
        </span>
      </div>
      <div className="editor-layout">
        <form className="editor-form stack" onSubmit={save}>
          <label>
            כותרת המשימה
            <input
              className="editor-title"
              aria-label="כותרת המשימה"
              value={draft.title}
              onChange={(e) => update("title", e.target.value)}
              maxLength={240}
              required
              placeholder="מה רוצים לקדם?"
            />
          </label>
          <label>
            הקשר והחלטות
            <textarea
              value={draft.description}
              onChange={(e) => update("description", e.target.value)}
              maxLength={20000}
              rows={4}
              placeholder="מה צריך לעשות, למה זה חשוב ומה כבר הוחלט?"
            />
          </label>
          <div className="field-grid">
            <label>
              סטטוס
              <select
                value={draft.status}
                onChange={(e) => update("status", e.target.value)}
              >
                {statuses.map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              עדיפות
              <select
                value={draft.priority}
                onChange={(e) => update("priority", e.target.value)}
              >
                {Object.entries(priorities).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              תחום
              <input
                value={draft.area}
                onChange={(e) => update("area", e.target.value)}
                maxLength={100}
                list="areas"
              />
              <datalist id="areas">
                {["מוצר", "תוכן", "AI", "תשתית", "עיצוב", "שיווק"].map((a) => (
                  <option key={a}>{a}</option>
                ))}
              </datalist>
            </label>
            <label>
              שלב
              <input
                value={draft.phase}
                onChange={(e) => update("phase", e.target.value)}
                maxLength={100}
              />
            </label>
            <label>
              תאריך יעד
              <input
                type="date"
                value={draft.due_date ?? ""}
                onChange={(e) => update("due_date", e.target.value || null)}
              />
            </label>
            <div>
              <p style={{ marginBottom: 10 }}>מי מוביל?</p>
              <div className="row">
                {Object.entries(people).map(([id, name]) => (
                  <label className="check-label" key={id}>
                    <input
                      type="checkbox"
                      checked={draft.assignees.includes(id)}
                      onChange={(e) =>
                        update(
                          "assignees",
                          e.target.checked
                            ? [...draft.assignees, id]
                            : draft.assignees.filter((x) => x !== id),
                        )
                      }
                    />
                    {name}
                  </label>
                ))}
              </div>
            </div>
          </div>
          <section className="stack">
            <div className="row spread">
              <h2>צעדים בדרך</h2>
              <span className="small muted">
                {draft.subtasks.filter((s) => s.done).length} מתוך{" "}
                {draft.subtasks.length}
              </span>
            </div>
            {draft.subtasks.map((s) => (
              <div
                key={s.id}
                className={`subtask ${s.done ? "completed" : ""}`}
              >
                <input
                  type="checkbox"
                  aria-label={`הושלם: ${s.text}`}
                  checked={s.done}
                  onChange={(e) =>
                    update(
                      "subtasks",
                      draft.subtasks.map((x) =>
                        x.id === s.id ? { ...x, done: e.target.checked } : x,
                      ),
                    )
                  }
                />
                <input
                  type="text"
                  aria-label="תוכן הצעד"
                  value={s.text}
                  maxLength={1000}
                  onChange={(e) =>
                    update(
                      "subtasks",
                      draft.subtasks.map((x) =>
                        x.id === s.id ? { ...x, text: e.target.value } : x,
                      ),
                    )
                  }
                />
                <button
                  type="button"
                  className="icon-button"
                  aria-label="הסרת צעד"
                  onClick={() =>
                    update(
                      "subtasks",
                      draft.subtasks.filter((x) => x.id !== s.id),
                    )
                  }
                >
                  <X size={15} />
                </button>
              </div>
            ))}
            <button
              type="button"
              disabled={draft.subtasks.length >= 100}
              onClick={() =>
                update("subtasks", [
                  ...draft.subtasks,
                  { id: crypto.randomUUID(), text: "", done: false },
                ])
              }
            >
              <Plus size={16} />
              הוספת צעד
            </button>
          </section>
          <section className="stack">
            <h2>קישורים וחומרים</h2>
            {draft.links.map((link) => (
              <div key={link.id} className="stack">
                <div className="row">
                  <input
                    aria-label="תיאור הקישור"
                    placeholder="תיאור הקישור"
                    value={link.label}
                    maxLength={200}
                    onChange={(e) =>
                      update(
                        "links",
                        draft.links.map((l) =>
                          l.id === link.id
                            ? { ...l, label: e.target.value }
                            : l,
                        ),
                      )
                    }
                  />
                  <input
                    aria-label="כתובת הקישור"
                    type="url"
                    dir="ltr"
                    placeholder="https://…"
                    value={link.url}
                    onChange={(e) =>
                      update(
                        "links",
                        draft.links.map((l) =>
                          l.id === link.id ? { ...l, url: e.target.value } : l,
                        ),
                      )
                    }
                  />
                  <button
                    type="button"
                    className="icon-button"
                    aria-label="הסרת קישור"
                    onClick={() =>
                      update(
                        "links",
                        draft.links.filter((l) => l.id !== link.id),
                      )
                    }
                  >
                    <X size={15} />
                  </button>
                  {safeURL(link.url) && (
                    <a href={link.url} target="_blank" rel="noreferrer">
                      פתיחת הקישור <ArrowUpRight size={13} />
                    </a>
                  )}
                </div>
              </div>
            ))}
            <button
              type="button"
              disabled={draft.links.length >= 30}
              onClick={() =>
                update("links", [
                  ...draft.links,
                  { id: crypto.randomUUID(), label: "", url: "" },
                ])
              }
            >
              <LinkIcon size={16} />
              הוספת קישור
            </button>
          </section>
          {!isNew && <TaskFiles taskId={draft.id} />}
          <label className="check-label">
            <input
              type="checkbox"
              checked={draft.archived}
              onChange={(e) => update("archived", e.target.checked)}
            />
            העברה לארכיון — ההיסטוריה נשמרת
          </label>
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          {conflict && (
            <div className="notice stack">
              <p>
                הגרסה האחרונה: {conflict.title} ·{" "}
                {statuses.find((s) => s[0] === conflict.status)?.[1]}
              </p>
              <button
                type="button"
                onClick={() => download("jobrun-unsaved-task.json", draft)}
              >
                <Download size={15} />
                שמירת עותק של הטיוטה
              </button>
              <button
                type="button"
                onClick={() => {
                  if (
                    window.confirm(
                      "לטעון את הגרסה האחרונה במקום הטיוטה המקומית? אפשר להוריד את הטיוטה לפני כן.",
                    )
                  ) {
                    setDraft(conflict);
                    setBase(conflict);
                    setConflict(null);
                    setError("");
                    sessionStorage.removeItem(key);
                  }
                }}
              >
                טעינת הגרסה האחרונה
              </button>
            </div>
          )}
          <div className="save-bar">
            <button className="primary" disabled={busy || !!conflict}>
              <Check size={16} />
              {busy ? "שומרים…" : "שמירת משימה"}
            </button>
            <span className="status-message" role="status">
              {saved}
            </span>
          </div>
        </form>
        <aside className="detail-side">
          <div className="segmented" style={{ marginBottom: 18 }}>
            <button
              className={tab === "comments" ? "active" : ""}
              onClick={() => setTab("comments")}
            >
              <MessageSquare size={15} />
              הערות
            </button>
            <button
              className={tab === "history" ? "active" : ""}
              onClick={() => setTab("history")}
            >
              <History size={15} />
              היסטוריה
            </button>
          </div>
          {isNew ? (
            <p className="muted small">
              אחרי שמירת המשימה תוכלו להוסיף הערות ולעקוב אחרי שינויים.
            </p>
          ) : tab === "comments" ? (
            <>
              <label>
                הערה או החלטה
                <textarea
                  rows={4}
                  value={comment}
                  maxLength={5000}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="שומרים כאן את ההקשר להמשך…"
                />
              </label>
              <button
                className="secondary"
                style={{ marginTop: 12, width: "100%" }}
                disabled={commentBusy || !comment.trim()}
                onClick={() => void addComment()}
              >
                הוספת הערה
              </button>
              {!comments.length && (
                <p className="muted small" style={{ marginTop: 20 }}>
                  עדיין אין הערות. זה המקום לתעד החלטות.
                </p>
              )}
              {comments.map((c) => (
                <div className="comment" key={c.id}>
                  <div className="row spread">
                    <strong className="small">
                      {c.author_id === user.id ? "אני" : "חבר צוות"}
                    </strong>
                    <time>
                      {new Date(c.created_at).toLocaleString("he-IL", {
                        dateStyle: "short",
                        timeStyle: "short",
                      })}
                    </time>
                  </div>
                  <p>{c.body}</p>
                </div>
              ))}
            </>
          ) : (
            <>
              {!events.length && (
                <p className="muted small">שינויים שתשמרו יופיעו כאן.</p>
              )}
              {events.map((event) => (
                <div className="event" key={event.id}>
                  <strong>גרסה {event.version}</strong>
                  <p>{event.snapshot.title}</p>
                  <span className={`badge ${event.snapshot.status}`}>
                    {statuses.find((s) => s[0] === event.snapshot.status)?.[1]}
                  </span>
                  <p>
                    <time>
                      {new Date(event.created_at).toLocaleString("he-IL")}
                    </time>
                  </p>
                </div>
              ))}
            </>
          )}
        </aside>
      </div>
    </>
  );
}
