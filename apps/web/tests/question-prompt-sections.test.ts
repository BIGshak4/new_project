import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { sectionQuestionPrompt } from '../src/lib/question-prompt-sections';

type Language = 'en' | 'he';
type Question = {
  key: string;
  translations: Record<Language, { prompt: string }>;
  assets: { preparation_id?: string; shared_code?: string; code_language?: string };
};
const bank = ['example', 'preparation'].flatMap(name => JSON.parse(readFileSync(
  new URL(`../../../backend/seeds/questions/${name}_bank.json`, import.meta.url), 'utf8')) as Question[]);
const entry = (id: string) => bank.find(q => q.assets.preparation_id === id)!;
const sections = (id: string, lang: Language) => sectionQuestionPrompt(entry(id).translations[lang].prompt, lang);

const fenced = (text: string) => text.match(/^ {0,3}```[^\n]*\n[\s\S]*?^ {0,3}```[ \t]*$/gm) ?? [];

test('every bilingual interview prompt retains a visible task and all fenced code, including API-appended programs', () => {
  for (const q of bank) {
    const presence: boolean[][] = [];
    for (const lang of ['he', 'en'] as const) {
      const text = q.translations[lang].prompt + (q.assets.shared_code
        ? `\n\n\`\`\`${q.assets.code_language ?? ''}\n${q.assets.shared_code.trimEnd()}\n\`\`\`` : '');
      const { main, clarifications, variations } = sectionQuestionPrompt(text, lang, q.key);
      assert.ok(main.trim(), `${q.key}/${lang}`);
      const parts = [main, clarifications, variations];
      assert.doesNotMatch(parts.join('\n'),
        /סעיפי יסוד נוספים מהצילום|הבהרות שנוספו למקור|סעיפי המקור שנשמרו|additional elementary source parts|the original screenshot is preserved|the screenshot's first part repeats/i,
        `${q.key}/${lang}: intake wording in a learner section`);
      presence.push(parts.map(Boolean));
      assert.deepEqual(parts.flatMap(fenced).sort(), fenced(text).sort(), `${q.key}/${lang}`);
      if (q.assets.shared_code) assert.ok(main.includes(q.assets.shared_code.trimEnd()));
    }
    assert.deepEqual(...presence as [boolean[], boolean[]], q.key);
  }
});

test('four-bit addition keeps the two foundational tasks visible and puts the alternative circuit in its own section', () => {
  for (const lang of ['he', 'en'] as const) {
    const { main, clarifications, variations } = sections('PREP-122', lang);
    assert.match(main, lang === 'he' ? /ארבעה ביטים/ : /four-bit numbers/i);
    assert.match(main, lang === 'he' ? /א\. ממשו מחבר למחצה \(HA\)[^\n]+\n\nב\. ממשו מחבר מלא \(FA\)/ : /A\. Implement a half adder[^\n]+\n\nB\. Implement a full adder/i);
    assert.match(main, lang === 'he' ? /ציינו מה היה משתנה/ : /State what changes/);
    assert.match(clarifications, /A\[3:0\]/);
    assert.match(clarifications, /Cin/);
    assert.match(variations, lang === 'he' ? /עם HA וגם FA/ : /both HAs and FAs/);
    assert.doesNotMatch([main, clarifications, variations].join('\n'), /מהצילום|שבצילום|screenshot|elementary source parts|source’s “2”/i);
  }
});

test('required subtasks that follow a model or a set of assumptions remain visible', () => {
  assert.match(sections('PREP-106', 'en').main, /Start with an asynchronous NOR-based SR latch/);
  assert.match(sections('PREP-106', 'he').main, /התחילו מלאץ׳ SR/);
  assert.match(sections('PREP-221', 'en').main, /Add a voltage follower/);
  assert.match(sections('PREP-353', 'en').main, /A\. Implement grid_valid/);
  assert.match(sections('PREP-353', 'he').main, /colored_grids_valid/);
  assert.match(sections('PREP-269', 'en').main, /Implement gas and brake/);
  assert.match(sections('PREP-269', 'he').main, /ממשו שתי פונקציות/);
});

test('scope changes in prose leave code examples, part-like literals and table cells intact', () => {
  const code = '```text\n### Variant: this is just code\n\nA. task. B. task.\n```';
  const table = '| x | y |\n| --- | --- |\n| A. quoted. B. label. | 1 |';
  const text = `Design a counter.\n\n${code}\n\n${table}\n\nAssumptions: edges are ideal. Explain initialization.\n\n### Variant: an enable input\nKeep the base timing and design the new logic.`;
  const result = sectionQuestionPrompt(text, 'en');
  assert.ok(result.main.includes(code));
  assert.ok(result.main.includes(table));
  assert.ok(result.main.includes('Explain initialization.'));
  assert.equal(result.clarifications, 'Assumptions: edges are ideal.');
  assert.ok(result.variations.includes('base timing'));
  const inline = 'A. Quote `A. sample. B. literal.`. B. Compute the result.';
  assert.equal(sectionQuestionPrompt(inline, 'en').main, 'A. Quote `A. sample. B. literal.`.\n\nB. Compute the result.');
});

test('an independent prompt starting with “variant” remains visible on its own', () => {
  const text = 'Variant: What is the output of this gate?';
  assert.deepEqual(sectionQuestionPrompt(text, 'en'), { main: text, clarifications: '', variations: '' });
});
