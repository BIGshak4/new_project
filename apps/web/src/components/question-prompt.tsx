import { useMemo, type ReactNode, type Ref } from "react";
import type { Lang } from "./auth";
import { BidiText } from "./bidi-text";
import { StudyText } from "./question-materials";
import { sectionQuestionPrompt } from "../lib/question-prompt-sections";
import { learnerCopy } from "../lib/learner-copy";

type Props = {
  text: string;
  lang: Lang;
  contentLang?: Lang;
  questionKey?: string | null;
  additionalWordings?: string[];
  compact?: boolean;
  mainClassName?: string;
  heading?: "h1" | "h3";
  headingRef?: Ref<HTMLHeadingElement>;
  children?: ReactNode;
};

/** The statement is always visible. Native disclosures keep their state while a learner types. */
export function QuestionPrompt({ text, lang, contentLang = lang, questionKey, additionalWordings, compact = false, mainClassName, heading: Heading, headingRef, children }: Props) {
  const { main, clarifications, variations } = useMemo(
    () => (compact || Heading) && !text.includes("\n")
      ? { main: learnerCopy(text), clarifications: "", variations: "" }
      : sectionQuestionPrompt(text, contentLang, questionKey ?? undefined), [text, contentLang, questionKey, compact, Heading]);
  const alternatives = useMemo(() => {
    const identity = (value: string) => value.replace(/^\s*(?:[-*+] |\d+[.)] )/gm, "").replace(/\s+/g, " ").trim();
    const seen = new Set([main, variations, ...variations.split("\n")].map(identity));
    const extra: string[] = [];
    for (const raw of additionalWordings ?? []) {
      const wording = learnerCopy(raw).trim();
      const key = identity(wording);
      if (key && !seen.has(key)) {
        extra.push(wording);
        seen.add(key);
      }
    }
    return [variations, ...extra].filter(Boolean);
  }, [additionalWordings, main, variations]);
  const statement = Heading
    ? <Heading ref={headingRef} tabIndex={headingRef ? -1 : undefined} lang={contentLang}><BidiText>{main}</BidiText></Heading>
    : <StudyText text={main} lang={contentLang} />;

  return <>
    {mainClassName ? <div className={`${mainClassName} question-statement`} lang={contentLang}>{statement}</div> : statement}
    {children}
    {(clarifications || alternatives.length > 0) && <div className="question-disclosures" key={`${questionKey ?? text}:${contentLang}:${lang}`} lang={lang} dir={lang === "he" ? "rtl" : "ltr"}>
      {clarifications && <details>
        <summary>{lang === "he" ? "הבהרות" : "Clarifications"}</summary>
        <div lang={contentLang}><StudyText text={clarifications} lang={contentLang} /></div>
      </details>}
      {alternatives.length > 0 && <details>
        <summary>{lang === "he" ? "ניסוחים נוספים (וריאציות)" : "Alternative wordings (variations)"}</summary>
        <div lang={contentLang}>{alternatives.map(wording => <StudyText key={wording} text={wording} lang={contentLang} />)}</div>
      </details>}
    </div>}
  </>;
}
