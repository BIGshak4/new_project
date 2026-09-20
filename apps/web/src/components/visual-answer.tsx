"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { CircuitBoard, ImagePlus, X, ExternalLink } from "lucide-react";
import { supabase } from "../lib/supabase";
import {
  emptyCircuit,
  type VisualAnswer as Visual,
  type AnswerImage,
} from "../lib/circuit";
import type { Lang } from "./auth";

const CircuitEditor = dynamic(() => import("./circuit-editor"), { ssr: false });
export const ANSWER_BUCKET = "practice-answer-images";

/** Decode and re-encode locally: rejects non-images and removes camera metadata. */
export async function prepareAnswerImage(file: File): Promise<Blob> {
  if (
    !["image/png", "image/jpeg", "image/webp"].includes(file.type) ||
    file.size > 10 * 1024 * 1024 ||
    !file.size
  )
    throw new Error("file");
  const bitmap = await createImageBitmap(file, {
    imageOrientation: "from-image",
  });
  try {
    if (
      bitmap.width * bitmap.height > 40_000_000 ||
      !bitmap.width ||
      !bitmap.height
    )
      throw new Error("dimensions");
    const scale = Math.min(1, 3000 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("canvas");
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.94),
    );
    if (!blob || blob.size > 5 * 1024 * 1024) throw new Error("size");
    return blob;
  } finally {
    bitmap.close();
  }
}

function PrivateImage({
  image,
  lang,
  remove,
  disabled,
}: {
  image: AnswerImage;
  lang: Lang;
  remove?: () => void;
  disabled?: boolean;
}) {
  const [url, setUrl] = useState(""),
    [error, setError] = useState(false),
    [retry, setRetry] = useState(0);
  useEffect(() => {
    let cancelled = false;
    async function load() {
      const { data, error } = await supabase.storage
        .from(ANSWER_BUCKET)
        .createSignedUrl(image.path, 900);
      if (!cancelled) {
        setUrl(data?.signedUrl ?? "");
        setError(!!error);
      }
    }
    void load();
    const timer = setInterval(() => void load(), 12 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [image.path, retry]);
  return (
    <figure className="answer-image">
      {url ? (
        <a href={url} target="_blank" rel="noopener noreferrer">
          <img src={url} alt={image.name} onError={() => setError(true)} />
          <span>
            <ExternalLink size={14} />
            {lang === "he" ? "פתיחת התמונה" : "Open image"}
          </span>
        </a>
      ) : (
        <span className="muted small">
          {lang === "he" ? "טוענים תמונה…" : "Loading image…"}
        </span>
      )}
      {error && (
        <button
          type="button"
          onClick={() => {
            setError(false);
            setRetry((r) => r + 1);
          }}
        >
          {lang === "he" ? "טעינת התמונה מחדש" : "Reload image"}
        </button>
      )}
      <figcaption dir="auto">{image.name}</figcaption>
      {remove && (
        <button
          type="button"
          className="remove-image"
          disabled={disabled}
          onClick={remove}
          aria-label={`${lang === "he" ? "הסרת" : "Remove"} ${image.name}`}
        >
          <X size={15} />
        </button>
      )}
    </figure>
  );
}

export function VisualAnswer({
  value,
  onChange,
  lang,
  attemptId,
  userId,
  disabled,
  onUploading,
}: {
  value: Visual;
  onChange?: (v: Visual) => void;
  lang: Lang;
  attemptId?: string;
  userId?: string;
  disabled?: boolean;
  onUploading?: (busy: boolean) => void;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [open, setOpen] = useState(!!value.circuit?.parts.length),
    [uploading, setUploading] = useState(false),
    [error, setError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null),
    uploadGuard = useRef(false),
    current = useRef(value);
  current.current = value;
  const readonly = !onChange;
  async function upload(files: File[]) {
    if (!onChange || !attemptId || !userId || uploadGuard.current || disabled)
      return;
    const room = 4 - current.current.images.length;
    if (files.length > room) {
      setError(
        t(
          "אפשר לצרף עד 4 תמונות לתשובה. בחרו פחות תמונות.",
          "Attach up to 4 images per answer. Select fewer files.",
        ),
      );
      return;
    }
    uploadGuard.current = true;
    setUploading(true);
    onUploading?.(true);
    setError("");
    try {
      for (const file of files) {
        const blob = await prepareAnswerImage(file);
        const path = `${userId}/${attemptId}/${crypto.randomUUID()}.jpg`;
        const { error } = await supabase.storage
          .from(ANSWER_BUCKET)
          .upload(path, blob, { contentType: "image/jpeg", upsert: false });
        if (error) throw error;
        const next = {
          ...current.current,
          images: [
            ...current.current.images,
            {
              path,
              name: file.name.slice(0, 160),
              mime: "image/jpeg" as const,
              size: blob.size,
            },
          ],
        };
        current.current = next;
        onChange(next);
      }
    } catch {
      setError(
        t(
          "התמונה לא עלתה. בחרו קובץ תקין עד 10 מגה־בייט, בדקו חיבור ונסו שוב. תמונות שכבר עלו נשמרו בטיוטה.",
          "Image upload failed. Choose a valid image up to 10 MB, check your connection and retry. Images already uploaded remain in the draft.",
        ),
      );
    } finally {
      uploadGuard.current = false;
      setUploading(false);
      onUploading?.(false);
    }
  }
  return (
    <section
      className="visual-answer"
      aria-label={t("שרטוטים ותמונות לתשובה", "Answer diagrams and images")}
    >
      {!readonly && (
        <>
          <div className="visual-answer-actions">
            <button
              type="button"
              disabled={disabled}
              aria-expanded={open}
              onClick={() => {
                if (!open && !value.circuit)
                  onChange?.({ ...value, circuit: emptyCircuit() });
                setOpen(!open);
              }}
            >
              <CircuitBoard size={18} />
              {open
                ? t("קיפול השרטוט", "Collapse circuit")
                : value.circuit?.parts.length
                  ? t("עריכת המעגל", "Edit circuit")
                  : t("שרטוט מעגל לוגי", "Draw a logic circuit")}
            </button>
            <button
              type="button"
              disabled={disabled || uploading || value.images.length >= 4}
              onClick={() => fileInput.current?.click()}
            >
              <ImagePlus size={18} />
              {uploading
                ? t("מעלים תמונה…", "Uploading image…")
                : t("צירוף תמונת פתרון", "Attach answer image")}
            </button>
            <input
              ref={fileInput}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              hidden
              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                e.target.value = "";
                void upload(files);
              }}
            />
          </div>
          <p className="small muted">
            {t(
              "אפשר לשלב הסבר, קוד, מעגל ותמונות — או לשלוח רק שרטוט. עד 4 תמונות, כל אחת עד 10 מגה־בייט לפני התאמה. קבצים נתמכים:",
              "Combine explanation, code, a circuit and images — or submit a drawing on its own. Up to 4 images, 10 MB each before resizing. Formats:",
            )}{" "}
            <bdi>JPG, PNG, WebP</bdi>.
          </p>
        </>
      )}
      {((readonly && value.circuit?.parts.length) || open) && value.circuit && (
        <CircuitEditor
          value={value.circuit}
          lang={lang}
          readOnly={readonly || disabled}
          onChange={(circuit) => onChange?.({ ...current.current, circuit })}
        />
      )}
      {!!value.images.length && (
        <div className="answer-images">
          {value.images.map((image) => (
            <PrivateImage
              key={image.path}
              image={image}
              lang={lang}
              disabled={disabled || uploading}
              remove={
                readonly
                  ? undefined
                  : () =>
                      onChange?.({
                        ...value,
                        images: value.images.filter(
                          (i) => i.path !== image.path,
                        ),
                      })
              }
            />
          ))}
        </div>
      )}
      {uploading && (
        <p role="status" className="small muted">
          {t(
            "מעבדים ומעלים את התמונות לפני שליחת התשובה…",
            "Processing and uploading images before submission…",
          )}
        </p>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {(!!value.images.length || !!value.circuit?.parts.length) && (
        <p className="visual-review-note">
          {t(
            "השרטוט נבדק כחלק מהתשובה: העוזר מקבל את רשימת הרכיבים והחיבורים ואת הפונקציה הלוגית שנגזרה ממנו. תמונות נבדקות רק כשהשרת מורשה לקרוא אותן; אחרת הן נשמרות לבדיקה אנושית.",
            "Your circuit is assessed as part of the answer: the assistant reads its components, wires and the logic function derived from it. Photos are assessed only when the server is allowed to read them; otherwise they are kept for human review.",
          )}
        </p>
      )}
    </section>
  );
}
