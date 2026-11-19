import { parseTechnicalAnswer } from "../lib/technical-answer";
import { StudyText } from "./question-materials";
import { TruthTableView } from "./truth-table-editor";
import type { Lang } from "./auth";

export function SubmittedAnswerContent({ answer, lang }: { answer: string; lang: Lang }) {
  const { explanation, code, truthTable } = parseTechnicalAnswer(answer);
  return <>
    {explanation && <div className="question-prompt"><StudyText text={explanation} lang={lang} /></div>}
    {code && <pre className="code-block" dir="ltr"><code>{code}</code></pre>}
    {truthTable && <TruthTableView value={truthTable} lang={lang} />}
  </>;
}
