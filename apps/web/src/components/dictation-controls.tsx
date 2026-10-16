"use client";

import { Mic, Square } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import type { Lang } from "./auth";
import { DictationController, recognitionFactory, type DictationError, type DictationState } from "../lib/speech-dictation";

export function dictationHelpMessage(support: "checking" | "supported" | "unsupported", lang: Lang) {
  const index = lang === "he" ? 0 : 1;
  return {
    unsupported: ["הכתבה קולית אינה זמינה בדפדפן הזה. אפשר להקליד כרגיל או להשתמש במיקרופון שבמקלדת הטלפון.", "Voice dictation is unavailable in this browser. You can keep typing or use your phone keyboard's microphone."],
    checking: ["בודקים אם הדפדפן תומך בהכתבה…", "Checking browser dictation support…"],
    supported: ["הדפדפן ממיר את הדיבור לטקסט ועשוי לשלוח אודיו לספק שירות ההכתבה שלו. אפשר לערוך את הטקסט לפני שליחה; התשובה לא נשלחת אוטומטית.", "Your browser converts speech to text and may send audio to its dictation provider. You can edit the text before sending; the answer is never submitted automatically."],
  }[support][index];
}

export function dictationErrorMessage(error: DictationError, lang: Lang) {
  const messages: Record<DictationError, [string, string]> = {
    permission: ["לא התקבל אישור להפעלת ההכתבה. בדקו את הרשאת המיקרופון באתר או באפליקציה. אם אתם באייפון ופתחתם את האתר מתוך אפליקציית Google או אפליקציה אחרת, נסו לפתוח את כתובת האתר ישירות ב־Safari. בהגדרות האייפון אפשר לבדוק: פרטיות ואבטחה ← מיקרופון ← האפליקציה או הדפדפן, אם הם מופיעים ברשימה. אפשר גם להשתמש במיקרופון שבמקלדת או להקליד.", "Dictation was not allowed to start. Check microphone permission for the site or app. If you are on iPhone and opened the site inside the Google app or another app, try opening the site address directly in Safari. In iPhone Settings, check Privacy & Security → Microphone → the app or browser, if it is listed. You can also use the keyboard microphone or type."],
    service: ["שירות ההכתבה בדפדפן לא זמין כרגע. אם אתם באייפון, בדקו ש־Siri והכתבה מופעלות בהגדרות המכשיר ונסו שוב. אפשר גם ללחוץ על שדה התשובה ולהשתמש במיקרופון שבמקלדת, או להקליד.", "The browser's dictation service is unavailable. If you are on iPhone, check that Siri and Dictation are enabled in device settings and try again. You can also tap the answer field and use the keyboard microphone, or type."],
    timeout: ["ההכתבה לא התחילה בתוך 15 שניות וההפעלה בוטלה. הטקסט שלכם לא השתנה. נסו שוב; אם אתם באייפון, בדקו ש־Siri והכתבה מופעלות בהגדרות המכשיר. אפשר גם ללחוץ על שדה התשובה ולהשתמש במיקרופון שבמקלדת, או להקליד.", "Dictation did not start within 15 seconds and was cancelled. Your text is unchanged. Try again; if you are on iPhone, check that Siri and Dictation are enabled in device settings. You can also tap the answer field and use the keyboard microphone, or type."],
    microphone: ["לא נמצא מיקרופון זמין. בדקו שהוא מחובר ושהוא אינו בשימוש באפליקציה אחרת, או המשיכו להקליד.", "No microphone is available. Check that it is connected and not in use by another app, or keep typing."],
    network: ["שירות ההכתבה לא הצליח להתחבר. בדקו את החיבור ונסו שוב. הטקסט שכבר נוסף נשמר בתשובה.", "The dictation service could not connect. Check your connection and try again. Text already added remains in your answer."],
    "no-speech": ["לא זוהה דיבור ברור. נסו שוב ודברו קרוב למיקרופון, או המשיכו להקליד.", "No clear speech was detected. Try again closer to the microphone, or keep typing."],
    language: ["שירות ההכתבה בדפדפן לא תומך בשפה שנבחרה. נסו שפה אחרת או המשיכו להקליד.", "Your browser's dictation service does not support this language. Try another language or keep typing."],
    unavailable: ["ההכתבה לא זמינה כרגע. אפשר לנסות שוב או להמשיך להקליד; הטקסט שלכם לא נמחק.", "Dictation is unavailable right now. Try again or keep typing; your text has not been deleted."],
    limit: ["אין מספיק מקום בתשובה למשפט האחרון, ולכן הוא לא נוסף. קצרו את הטקסט ונסו שוב, או ערכו אותו ידנית.", "There is not enough room in the answer for the last phrase, so it was not added. Shorten the text and try again, or edit it manually."],
  };
  return messages[error][lang === "he" ? 0 : 1];
}

/** Final phrases are appended to the latest draft; interim text never overwrites manual edits. */
export function DictationControls({ value, onChange, lang, disabled, maxLength = 20000 }: {
  value: string;
  onChange: (value: string) => void;
  lang: Lang;
  disabled: boolean;
  maxLength?: number;
}) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const id = useId();
  const [languageChoice, setLanguageChoice] = useState({ ui: lang, speech: lang });
  // Changing the site's language immediately changes the default, including before effects run.
  const speechLanguage = languageChoice.ui === lang ? languageChoice.speech : lang;
  const [support, setSupport] = useState<"checking" | "supported" | "unsupported">("checking");
  const [state, setState] = useState<DictationState>({ phase: "idle", interim: "", error: null });
  const controller = useRef<DictationController | null>(null);
  const latest = useRef({ value, onChange, disabled, maxLength, lang });
  latest.current = { value, onChange, disabled, maxLength, lang };
  useEffect(() => {
    const create = recognitionFactory(window);
    setSupport(create ? "supported" : "unsupported");
    setState({ phase: "idle", interim: "", error: null });
    if (!create) return;
    const instance = new DictationController({
      create,
      language: speechLanguage === "he" ? "he-IL" : "en-US",
      disabled: () => latest.current.disabled || latest.current.lang !== lang,
      getText: () => latest.current.value,
      maxLength: () => latest.current.maxLength,
      onText: (text) => {
        latest.current.value = text;
        latest.current.onChange(text);
      },
      onState: setState,
    });
    controller.current = instance;
    const onVisibility = () => { if (document.hidden) instance.cancel(); };
    const onPageHide = () => instance.cancel();
    document.addEventListener("visibilitychange", onVisibility);
    window.addEventListener("pagehide", onPageHide);
    return () => {
      document.removeEventListener("visibilitychange", onVisibility);
      window.removeEventListener("pagehide", onPageHide);
      instance.dispose();
      if (controller.current === instance) controller.current = null;
    };
  }, [speechLanguage, lang]);
  useEffect(() => { if (disabled) controller.current?.cancel(); }, [disabled]);
  const active = state.phase !== "idle";
  const buttonLabel = state.phase === "starting"
    ? t("ביטול הפעלת המיקרופון", "Cancel microphone start")
    : state.phase === "stopping"
      ? t("מסיימים את ההכתבה…", "Finishing dictation…")
      : active
        ? t("עצירת ההכתבה", "Stop dictation")
        : t("הכתבה קולית", "Dictate answer");

  return (
    <div className="dictation-controls" style={{ display: "grid", gap: 8, minWidth: 0 }}>
      <div className="row" style={{ flexWrap: "wrap", gap: 10 }}>
        <button
          type="button"
          disabled={disabled || support !== "supported" || state.phase === "stopping"}
          aria-pressed={active}
          aria-describedby={`${id}-help ${id}-status`}
          onClick={() => {
            if (state.phase === "starting") controller.current?.cancel();
            else if (active) controller.current?.stop();
            else controller.current?.start();
          }}
        >
          {active ? <Square size={16} aria-hidden="true" /> : <Mic size={17} aria-hidden="true" />}
          {buttonLabel}
        </button>
        {support === "supported" && (
          <label className="small" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
            {t("שפת ההכתבה", "Dictation language")}
            <select
              aria-label={t("שפת ההכתבה", "Dictation language")}
              value={speechLanguage}
              disabled={disabled || active}
              onChange={(event) => setLanguageChoice({ ui: lang, speech: event.target.value as Lang })}
              style={{ width: "auto", minHeight: 44 }}
            >
              <option value="he">עברית</option>
              <option value="en">English</option>
            </select>
          </label>
        )}
      </div>
      <p className="small muted" id={`${id}-help`} style={{ margin: 0 }}>
        {dictationHelpMessage(support, lang)}
      </p>
      <p className="small" id={`${id}-status`} role="status" aria-live="polite" style={{ margin: 0 }}>
        {state.error ? dictationErrorMessage(state.error, lang)
          : state.phase === "starting" ? t("מפעילים את ההכתבה בדפדפן… אם תופיע בקשת גישה למיקרופון, אשרו אותה כדי להכתיב.", "Starting browser dictation… If a microphone access request appears, allow it to dictate.")
          : state.phase === "listening" ? t("מקשיבים… משפטים שזוהו נוספים לסוף ההסבר.", "Listening… Recognized phrases are added to the end of your explanation.")
          : state.phase === "stopping" ? t("מסיימים את המשפט האחרון…", "Finishing the last phrase…")
          : ""}
      </p>
      {state.interim && (
        <p className="small muted" dir="auto" style={{ margin: 0, overflowWrap: "anywhere" }}>
          {t("בתהליך זיהוי: ", "Recognizing: ")}{state.interim}
        </p>
      )}
    </div>
  );
}
