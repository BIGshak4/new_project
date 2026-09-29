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
          "שני סטודנטים להנדסה שעברו יותר מדי ראיונות, ובנו את הכלי שהיו רוצים לפני הראשון. כל שאלה במאגר נבדקת על ידי מהנדס לפני שהיא מגיעה אליכם.",
          "Two engineering students who sat through too many interviews and built the tool they wanted before the first one. An engineer checks every question before it reaches you.",
        )}
      </span>
    </footer>
  );
}
