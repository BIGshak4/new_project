import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { learnerCopy } from '../src/lib/learner-copy';
import { sectionQuestionPrompt } from '../src/lib/question-prompt-sections';

type Language = 'he' | 'en';
type Question = {
  key: string;
  assets: { preparation_id?: string };
  translations: Record<Language, { prompt: string }>;
};

const bank = ['example', 'preparation'].flatMap(name =>
  JSON.parse(readFileSync(new URL(`../../../backend/seeds/questions/${name}_bank.json`, import.meta.url), 'utf8')) as Question[]);

function shown(id: string, lang: Language) {
  const question = bank.find(row => row.assets.preparation_id === id || row.key === id);
  assert.ok(question, id);
  return Object.values(sectionQuestionPrompt(question.translations[lang].prompt, lang, question.key)).join('\n');
}

test('learner wording stays stable across both locales, including text exposed in disclosures', () => {
  for (const question of bank) {
    for (const lang of ['he', 'en'] as const) {
      const prompt = question.translations[lang].prompt;
      const once = learnerCopy(prompt);
      assert.equal(learnerCopy(once), once, `${question.key}/${lang}/complete`);
      const sections = sectionQuestionPrompt(prompt, lang, question.key);
      for (const [section, text] of Object.entries(sections)) {
        const at = `${question.key}/${lang}/${section}`;
        assert.equal(learnerCopy(text), text, at);
        assert.doesNotMatch(text, /not requested by the source|preserve the source opcode names|clarifications added to the (?:terse )?source|לא הוגדרה במקור|שלא הופיע במקור|הנחות אלה נוספו במפורש|ההיתרים האלה נוספו במפורש/i, at);
      }
    }
  }
});

test('edition notes become precise requirements and keep technical distinctions intact', () => {
  const opcodes = shown('PREP-035', 'en');
  assert.match(opcodes, /ADD R increments by 1, SUM R decrements by 1, and JNZ R, label branches/);
  assert.match(shown('PREP-064', 'he'), /איפוס סינכרוני פעיל בגבוה קובע את המצב ההתחלתי ל־0 וגובר על e/);
  assert.match(shown('PREP-095', 'he'), /שבע דגימות אחרי reset.+ריפוד באפסים/);
  assert.match(shown('PREP-114', 'he'), /ארבעה בדיוק/);
  assert.match(shown('PREP-117', 'he'), /כ־2gb/);
  assert.match(shown('PREP-256', 'he'), /1000 גבר יוצא, 0100 גבר נכנס, 0010 אישה יוצאת, 0001 אישה נכנסת\. 0000 משאיר את המצב ללא שינוי/);
  assert.match(shown('PREP-085', 'en'), /added moment about the center/);
  assert.match(shown('PREP-115', 'en'), /source, drain, gate and insulator/);
  assert.match(shown('example-asynchronous-pulse-transfer', 'en'), /source clock is 100 MHz/);
});
