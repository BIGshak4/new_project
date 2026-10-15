import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { DictationController, appendDictatedText, dictationExplanationLimit, recognitionError, recognitionFactory, type DictationState, type Recognition } from "../src/lib/speech-dictation";
import { DictationControls, dictationErrorMessage, dictationHelpMessage } from "../src/components/dictation-controls";
import { formatTechnicalAnswer, parseTechnicalAnswer } from "../src/lib/technical-answer";

class MockRecognition implements Recognition {
  lang = "";
  continuous = false;
  interimResults = false;
  maxAlternatives = 0;
  onstart: Recognition["onstart"] = null;
  onend: Recognition["onend"] = null;
  onresult: Recognition["onresult"] = null;
  onerror: Recognition["onerror"] = null;
  onnomatch: Recognition["onnomatch"] = null;
  starts = 0; stops = 0; aborts = 0;
  start() { this.starts += 1; }
  stop() { this.stops += 1; }
  abort() { this.aborts += 1; }
  results(values: Array<[string, boolean]>, resultIndex = 0) {
    this.onresult?.({ resultIndex, results: values.map(([transcript, isFinal]) => ({ isFinal, 0: { transcript } })) });
  }
}

function setup(language = "he-IL", maxLength = 20000) {
  let text = "התחלה";
  let disabled = false;
  const sessions: MockRecognition[] = [];
  const states: DictationState[] = [];
  const updates: string[] = [];
  const controller = new DictationController({
    create: () => { const session = new MockRecognition(); sessions.push(session); return session; },
    language, disabled: () => disabled, maxLength: () => maxLength,
    getText: () => text,
    onText: (next) => { text = next; updates.push(next); },
    onState: (state) => states.push(state),
  });
  return {
    controller, sessions, states, updates,
    text: () => text,
    edit: (next: string) => { text = next; },
    disable: () => { disabled = true; },
    current: () => sessions.at(-1)!,
    state: () => states.at(-1)!,
  };
}

test("dictation never captures on initialization and sets the explicit session language", () => {
  for (const language of ["he-IL", "en-US"]) {
    const context = setup(language);
    assert.equal(context.sessions.length, 0);
    context.controller.start();
    assert.equal(context.current().starts, 1);
    assert.equal(context.current().lang, language);
    assert.equal(context.current().continuous, true);
    assert.equal(context.current().interimResults, true);
    assert.equal(context.state().phase, "starting");
    context.current().onstart?.();
    assert.equal(context.state().phase, "listening");
    context.controller.dispose();
  }
});

test("interim revisions remain previews; finalized phrases append exactly once", () => {
  const context = setup();
  context.controller.start();
  const session = context.current();
  session.results([["אחד", false]]);
  session.results([["אחד שתיים", false]]);
  assert.equal(context.text(), "התחלה");
  assert.equal(context.state().interim, "אחד שתיים");
  session.results([["אחד שתיים", true]]);
  session.results([["אחד שתיים", true], ["שלוש", false]], 1);
  session.results([["אחד שתיים", true], ["שלוש", true]], 1);
  session.results([["אחד שתיים", true], ["שלוש", true]], 1);
  assert.equal(context.text(), "התחלה אחד שתיים שלוש");
  assert.equal(context.updates.length, 2);
  assert.equal(context.state().interim, "");
  context.controller.dispose();
});

test("dictation appends to the latest manual edit rather than the value at recording start", () => {
  const context = setup();
  context.controller.start();
  context.current().results([["ראשון", true]]);
  context.edit("ערכתי ידנית\n");
  context.current().results([["ראשון", true], ["שני", true]], 1);
  assert.equal(context.text(), "ערכתי ידנית\nשני");
  context.controller.dispose();
});

test("stop waits for the browser's final phrase and end; natural end does not restart capture", () => {
  const context = setup();
  context.controller.start();
  const session = context.current();
  session.onstart?.();
  context.controller.stop();
  assert.equal(session.stops, 1);
  assert.equal(context.state().phase, "stopping");
  session.results([["סיום", true]]);
  session.onend?.();
  assert.equal(context.text(), "התחלה סיום");
  assert.equal(context.state().phase, "idle");
  assert.equal(context.sessions.length, 1);
  context.controller.dispose();
});

test("cancel and unmount abort capture and discard even already-queued callbacks", () => {
  for (const action of ["cancel", "dispose"] as const) {
    const context = setup();
    context.controller.start();
    const session = context.current();
    const lateResult = session.onresult;
    const lateEnd = session.onend;
    context.controller[action]();
    const count = context.states.length;
    lateResult?.({ resultIndex: 0, results: [{ isFinal: true, 0: { transcript: "מאוחר" } }] });
    lateEnd?.();
    assert.equal(session.aborts, 1);
    assert.equal(context.text(), "התחלה");
    assert.equal(context.states.length, count);
    assert.equal(session.onresult, null);
  }
});

test("disabled submission rejects queued speech before its cleanup effect runs", () => {
  const context = setup();
  context.controller.start();
  context.disable();
  context.current().results([["אסור לשלוח", true]]);
  assert.equal(context.text(), "התחלה");
  context.controller.cancel();
  context.controller.start();
  assert.equal(context.sessions.length, 1);
});

test("an old delayed start cannot cancel the user's next recording", () => {
  const context = setup();
  context.controller.start();
  const oldStart = context.current().onstart;
  const oldResult = context.current().onresult;
  context.controller.cancel();
  context.controller.start();
  oldStart?.();
  oldResult?.({ resultIndex: 0, results: [{ isFinal: true, 0: { transcript: "ישן" } }] });
  assert.equal(context.current().aborts, 0);
  context.current().results([["חדש", true]]);
  assert.equal(context.text(), "התחלה חדש");
  context.controller.dispose();
});

test("new sessions have a fresh final index and duplicate start clicks create no second microphone", () => {
  const context = setup();
  context.controller.start();
  context.controller.start();
  assert.equal(context.sessions.length, 1);
  context.current().results([["אחד", true]]);
  context.current().onend?.();
  context.controller.start();
  context.current().results([["שתיים", true]]);
  assert.equal(context.text(), "התחלה אחד שתיים");
  context.controller.dispose();
});

test("recognition errors abort, preserve the existing draft and offer recoverable explanations", () => {
  for (const [browserError, expected] of [
    ["not-allowed", "permission"], ["service-not-allowed", "permission"],
    ["audio-capture", "microphone"], ["network", "network"],
    ["no-speech", "no-speech"], ["language-not-supported", "language"], ["unknown", "unavailable"],
  ] as const) {
    const context = setup();
    context.controller.start();
    const session = context.current();
    session.onerror?.({ error: browserError });
    assert.equal(context.state().error, expected);
    assert.equal(context.state().phase, "idle");
    assert.equal(context.text(), "התחלה");
    assert.equal(session.aborts, 1);
    assert.equal(recognitionError(browserError), expected);
    assert.ok(dictationErrorMessage(expected, "he").length > 20);
    assert.ok(dictationErrorMessage(expected, "en").length > 20);
    context.controller.dispose();
  }
});

test("silence and a no-match event do not invent an answer", () => {
  for (const event of ["onend", "onnomatch"] as const) {
    const context = setup();
    context.controller.start();
    context.current()[event]?.();
    assert.equal(context.state().error, "no-speech");
    assert.equal(context.updates.length, 0);
    context.controller.dispose();
  }
});

test("limit errors do not truncate a draft or silently insert only half a phrase", () => {
  const context = setup("he-IL", 8);
  context.controller.start();
  context.current().results([["הרבה יותר מדי מילים", true]]);
  assert.equal(context.text(), "התחלה");
  assert.equal(context.state().error, "limit");
  assert.equal(context.current().aborts, 1);
  assert.equal(appendDictatedText("one", " two ", 7), "one two");
  assert.equal(appendDictatedText("one", "two", 6), null);
  assert.equal(appendDictatedText("one\n", "two", 7), "one\ntwo");
  context.controller.dispose();
});

test("dictating an explanation preserves code fences, language and the combined answer limit", () => {
  const original = formatTechnicalAnswer("הסבר", "if (a) { return 1; }", "c");
  const parts = parseTechnicalAnswer(original);
  const limit = dictationExplanationLimit(original);
  const explanation = appendDictatedText(parts.explanation, "המשך ההסבר", limit)!;
  const answer = formatTechnicalAnswer(explanation, parts.code, parts.language!);
  assert.equal(parseTechnicalAnswer(answer).code, parts.code);
  assert.equal(parseTechnicalAnswer(answer).language, "c");
  assert.equal(parseTechnicalAnswer(answer).explanation, "הסבר המשך ההסבר");
  assert.ok(answer.length <= 20000);
  assert.equal(appendDictatedText("x".repeat(limit), "extra", limit), null);
  const codeOnly = formatTechnicalAnswer("", parts.code, "c");
  const firstExplanationLimit = dictationExplanationLimit(codeOnly);
  assert.equal(formatTechnicalAnswer("x".repeat(firstExplanationLimit), parts.code, "c").length, 20000);
  assert.equal(appendDictatedText("", "x".repeat(firstExplanationLimit + 1), firstExplanationLimit), null);
});

test("unsupported, insecure and prefixed browser detection does not request a microphone", () => {
  assert.equal(recognitionFactory(undefined), null);
  assert.equal(recognitionFactory({}), null);
  assert.equal(recognitionFactory({ isSecureContext: false, SpeechRecognition: MockRecognition }), null);
  const standard = recognitionFactory({ isSecureContext: true, SpeechRecognition: MockRecognition });
  const prefixed = recognitionFactory({ isSecureContext: true, webkitSpeechRecognition: MockRecognition });
  assert.ok(standard?.() instanceof MockRecognition);
  assert.ok(prefixed?.() instanceof MockRecognition);
  assert.match(dictationHelpMessage("unsupported", "he"), /להקליד כרגיל/);
  assert.match(dictationHelpMessage("unsupported", "en"), /keep typing/);
  assert.match(dictationHelpMessage("supported", "en"), /may send audio/);
  assert.match(dictationHelpMessage("supported", "he"), /לא נשלחת אוטומטית/);
});

test("server rendering is inert, names the microphone button, and keeps it disabled until support detection", () => {
  for (const lang of ["he", "en"] as const) {
    let changed = false;
    const html = renderToStaticMarkup(createElement(DictationControls, {
      value: "draft", onChange: () => { changed = true; }, disabled: false, lang,
    }));
    assert.match(html, /type="button" disabled="" aria-pressed="false"/);
    assert.match(html, /role="status" aria-live="polite"/);
    assert.match(html, lang === "he" ? /הכתבה קולית/ : /Dictate answer/);
    assert.equal(changed, false);
  }
});

test("a browser start exception returns to an editable idle state", () => {
  let state: DictationState | undefined;
  const controller = new DictationController({
    create: () => { throw new Error("Browser service unavailable"); },
    language: "en-US", disabled: () => false, getText: () => "draft",
    onText: () => assert.fail("must not write"), maxLength: () => 20000,
    onState: (next) => { state = next; },
  });
  controller.start();
  assert.equal(state?.phase, "idle");
  assert.equal(state?.error, "unavailable");
  controller.dispose();
});
