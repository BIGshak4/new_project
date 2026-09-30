"use client";

import type { Lang } from "./auth";

/** The foot of every page: two names in handwriting and one true sentence. People, not a copyright line. */
export function SignOff({ lang }: { lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  return (
    <footer className="signoff" aria-label={t("מי בנה את זה", "Who built this")}>
      <span className="hand">{t("שקד והראל", "Shaked & Harel")}</span>
      <span>
        {t(
          "הראל ושקד, סטודנטים להנדסת חשמל ואלקטרוניקה, בונים כלי להכנה לראיונות. אנחנו בשלב הפיילוט: השאלות והמשובים עוברים בדיקה ושיפור.",
          "Harel and Shaked, electrical and electronics engineering students, are building an interview preparation tool. This is a pilot: questions and feedback are being reviewed and improved.",
        )}
      </span>
    </footer>
  );
}
