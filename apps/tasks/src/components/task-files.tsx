"use client";
import { useEffect, useState } from "react";
import { Paperclip, Download, Trash2 } from "lucide-react";
import { supabase } from "../lib/supabase";
function encodeName(name: string) {
  return btoa(String.fromCharCode(...new TextEncoder().encode(name)))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}
function decodeName(name: string) {
  try {
    return new TextDecoder().decode(
      Uint8Array.from(
        atob(name.slice(37).replaceAll("-", "+").replaceAll("_", "/")),
        (c) => c.charCodeAt(0),
      ),
    );
  } catch {
    return name.slice(37);
  }
}
export function TaskFiles({ taskId }: { taskId: string }) {
  const [files, setFiles] = useState<{ name: string; id: string }[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const bucket = supabase.storage.from("jobrun-task-files");
  async function load() {
    const result = await bucket.list(taskId, {
      limit: 100,
      sortBy: { column: "created_at", order: "desc" },
    });
    if (result.error) setError("לא ניתן לטעון קבצים. נסו שוב.");
    else
      setFiles(
        result.data
          .filter((f) => f.id)
          .map((f) => ({ name: f.name, id: f.id! })),
      );
  }
  useEffect(() => {
    void load();
  }, [taskId]);
  async function upload(file?: File) {
    if (!file) return;
    setError("");
    if (
      file.size > 10 * 1024 * 1024 ||
      !["application/pdf", "image/png", "image/jpeg", "text/plain"].includes(
        file.type,
      )
    ) {
      setError("אפשר להעלות PDF, תמונה מסוג PNG/JPEG או קובץ טקסט עד 10MB.");
      return;
    }
    setBusy(true);
    const name = `${crypto.randomUUID()}_${encodeName(file.name)}`;
    const result = await bucket.upload(`${taskId}/${name}`, file, {
      contentType: file.type,
      upsert: false,
    });
    if (result.error) setError("הקובץ לא הועלה. בדקו חיבור ונסו שוב.");
    else await load();
    setBusy(false);
  }
  async function open(name: string) {
    setError("");
    const result = await bucket.createSignedUrl(`${taskId}/${name}`, 60, {
      download: decodeName(name),
    });
    if (result.error) {
      setError("לא ניתן לפתוח את הקובץ. נסו שוב.");
      return;
    }
    window.location.assign(result.data.signedUrl);
  }
  async function remove(name: string) {
    if (!window.confirm("למחוק את הקובץ המצורף?")) return;
    setBusy(true);
    setError("");
    const result = await bucket.remove([`${taskId}/${name}`]);
    if (result.error) setError("הקובץ לא נמחק. נסו שוב.");
    else await load();
    setBusy(false);
  }
  return (
    <section className="stack">
      <h2>
        <Paperclip size={18} /> קבצים מצורפים
      </h2>
      <p className="small muted">
        גישה למייסדים בלבד · PDF, תמונות או טקסט · עד 10MB לקובץ.
      </p>
      <label>
        העלאת קובץ
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.txt"
          disabled={busy || files.length >= 100}
          onChange={(e) => {
            void upload(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </label>
      {files.map((file) => (
        <div className="row spread" key={file.id}>
          <button
            type="button"
            className="text-button"
            disabled={busy}
            onClick={() => void open(file.name)}
          >
            <Download size={15} />
            <span style={{ overflowWrap: "anywhere" }}>
              {decodeName(file.name)}
            </span>
          </button>
          <button
            type="button"
            className="icon-button"
            disabled={busy}
            aria-label={`מחיקת ${decodeName(file.name)}`}
            onClick={() => void remove(file.name)}
          >
            <Trash2 size={15} />
          </button>
        </div>
      ))}
      {busy && <p role="status">מעדכנים קבצים…</p>}
      {error && (
        <p role="alert" className="notice error">
          {error}
          <button type="button" onClick={() => void load()}>
            ניסיון נוסף
          </button>
        </p>
      )}
    </section>
  );
}
