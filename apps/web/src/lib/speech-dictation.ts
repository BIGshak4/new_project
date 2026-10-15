import { parseTechnicalAnswer } from "./technical-answer";

/** Browser speech recognition is optional. Keep capture separate from answer submission. */
export type DictationPhase = "idle" | "starting" | "listening" | "stopping";
export type DictationError =
  | "permission" | "microphone" | "network" | "no-speech"
  | "language" | "unavailable" | "limit";
export type DictationState = {
  phase: DictationPhase;
  interim: string;
  error: DictationError | null;
};

export type RecognitionResult = {
  isFinal: boolean;
  0: { transcript: string };
};
export type RecognitionEvent = {
  resultIndex: number;
  results: ArrayLike<RecognitionResult>;
};
export type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onnomatch: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
export type RecognitionFactory = () => Recognition;

export function recognitionFactory(scope: unknown): RecognitionFactory | null {
  if (!scope || typeof scope !== "object") return null;
  const browser = scope as {
    isSecureContext?: boolean;
    SpeechRecognition?: new () => Recognition;
    webkitSpeechRecognition?: new () => Recognition;
  };
  if (browser.isSecureContext === false) return null;
  const Constructor = browser.SpeechRecognition ?? browser.webkitSpeechRecognition;
  return Constructor ? () => new Constructor() : null;
}

export function appendDictatedText(current: string, transcript: string, maxLength: number) {
  const phrase = transcript.trim();
  if (!phrase) return current;
  const next = `${current}${current && !/\s$/.test(current) ? " " : ""}${phrase}`;
  // Leave the existing draft intact instead of silently dropping part of a spoken phrase.
  return next.length <= maxLength ? next : null;
}

export function dictationExplanationLimit(answer: string) {
  const parts = parseTechnicalAnswer(answer);
  // A code-only answer gains a blank line when its first explanation is added.
  const separator = parts.code && !parts.explanation ? 2 : 0;
  return Math.max(0, 20000 - (answer.length - parts.explanation.length) - separator);
}

export function recognitionError(error: string): DictationError {
  switch (error) {
    case "not-allowed":
    case "service-not-allowed": return "permission";
    case "audio-capture": return "microphone";
    case "network": return "network";
    case "no-speech": return "no-speech";
    case "language-not-supported": return "language";
    default: return "unavailable";
  }
}

/** An event-driven controller also lets lifecycle and late-event races be tested without a mic. */
export class DictationController {
  private recognition: Recognition | null = null;
  private generation = 0;
  private disposed = false;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private state: DictationState = { phase: "idle", interim: "", error: null };

  constructor(private readonly options: {
    create: RecognitionFactory;
    language: string;
    disabled: () => boolean;
    getText: () => string;
    onText: (text: string) => void;
    maxLength: () => number;
    onState: (state: DictationState) => void;
  }) {}

  private publish(next: Partial<DictationState>) {
    this.state = { ...this.state, ...next };
    if (!this.disposed) this.options.onState(this.state);
  }

  private detach() {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
    const recognition = this.recognition;
    this.recognition = null;
    this.generation += 1;
    if (recognition) {
      recognition.onstart = recognition.onend = recognition.onnomatch = null;
      recognition.onresult = recognition.onerror = null;
    }
    return recognition;
  }

  private fail(error: DictationError) {
    const recognition = this.detach();
    try { recognition?.abort(); } catch { /* Already stopped by the browser. */ }
    this.publish({ phase: "idle", interim: "", error });
  }

  start() {
    if (this.disposed || this.options.disabled() || this.recognition) return;
    const generation = ++this.generation;
    let recognition: Recognition;
    try { recognition = this.options.create(); } catch { this.fail("unavailable"); return; }
    this.recognition = recognition;
    const current = () => !this.disposed && this.generation === generation && !this.options.disabled();
    const finalIndexes = new Set<number>();
    let hasFinal = false;
    recognition.lang = this.options.language;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => {
      if (this.disposed || this.generation !== generation) return;
      if (!current()) { this.cancel(); return; }
      // A quick second click can stop capture before the browser emits its start event.
      if (this.state.phase !== "stopping") this.publish({ phase: "listening" });
    };
    recognition.onresult = (event) => {
      if (!current()) return;
      const phrases: string[] = [];
      const interim: string[] = [];
      for (let index = 0; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result[0]?.transcript?.trim() ?? "";
        if (result.isFinal) {
          if (index >= event.resultIndex && !finalIndexes.has(index)) {
            finalIndexes.add(index);
            if (transcript) phrases.push(transcript);
          }
        } else if (transcript) interim.push(transcript);
      }
      if (phrases.length) {
        const next = appendDictatedText(this.options.getText(), phrases.join(" "), this.options.maxLength());
        if (next === null) { this.fail("limit"); return; }
        hasFinal = true;
        this.options.onText(next);
      }
      this.publish({ interim: interim.join(" ") });
    };
    recognition.onerror = (event) => {
      if (current()) this.fail(recognitionError(event.error));
    };
    recognition.onnomatch = () => { if (current()) this.fail("no-speech"); };
    recognition.onend = () => {
      if (!current()) return;
      this.detach();
      this.publish({ phase: "idle", interim: "", error: hasFinal ? null : "no-speech" });
    };
    this.publish({ phase: "starting", interim: "", error: null });
    try { recognition.start(); } catch (error) {
      this.fail(error instanceof DOMException && error.name === "NotAllowedError" ? "permission" : "unavailable");
    }
  }

  stop() {
    if (!this.recognition || this.state.phase === "stopping") return;
    this.publish({ phase: "stopping" });
    // stop(), unlike abort(), lets the browser finalize the phrase already captured.
    try { this.recognition.stop(); } catch { this.cancel(); return; }
    // Some browser services never emit end after disconnecting. Do not leave capture stuck.
    if (this.recognition) this.timer = setTimeout(() => this.cancel(), 5000);
  }

  cancel() {
    const recognition = this.detach();
    try { recognition?.abort(); } catch { /* No active browser session. */ }
    this.publish({ phase: "idle", interim: "", error: null });
  }

  dispose() {
    this.disposed = true;
    this.cancel();
  }
}
