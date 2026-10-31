import type { ReactNode } from "react";
import type { Lang } from "./auth";

/** Question headings follow the UI language; technical runs keep their own BidiText isolates. */
export function QuestionTitle({ as: Heading = "h3", lang, className, children }: {
  as?: "h1" | "h2" | "h3" | "h4";
  lang: Lang;
  className?: string;
  children: ReactNode;
}) {
  return <Heading className={className} dir={lang === "he" ? "rtl" : "ltr"}>{children}</Heading>;
}
