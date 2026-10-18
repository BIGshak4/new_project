import test from "node:test";
import assert from "node:assert/strict";
import { lockBodyScroll } from "../src/lib/body-scroll-lock";
import {
  FULL_TOUR,
  SHORT_TOUR,
  checkpoint,
  initialTourProgress,
  parseTourProgress,
  stationReady,
  tourKey,
  tourSteps,
  type TourKind,
  type TourProgress,
  type TourStep,
} from "../src/lib/muxi-tour";

const station = (id: string): TourStep => {
  const found = FULL_TOUR.find((step) => step.id === id);
  assert.ok(found, `Missing required tour station: ${id}`);
  return found;
};
const stored = (patch: Record<string, unknown> = {}) => JSON.stringify({
  ...initialTourProgress(),
  offered: true,
  updatedAt: 123,
  ...patch,
});

test("both tours have unique, bilingual stations with a concrete action requirement", () => {
  for (const kind of ["short", "full"] as const) {
    const steps = tourSteps(kind);
    assert.ok(steps.length > 0);
    assert.equal(new Set(steps.map((step) => step.id)).size, steps.length);
    for (const step of steps) {
      assert.match(step.id, /^[a-z][a-z0-9-]*$/);
      for (const field of [step.chapter, step.title, step.body, step.task]) {
        assert.ok(field.he.trim().length > 0, `${step.id} needs Hebrew copy`);
        assert.ok(field.en.trim().length > 0, `${step.id} needs English copy`);
      }
      assert.ok(step.actions.length > 0, `${step.id} cannot be a passive next-button step`);
      assert.equal(new Set(step.actions).size, step.actions.length);
      for (const action of step.actions) assert.match(action, /^[a-z][a-z0-9-]*$/);
      assert.equal(stationReady(step, []), false, `${step.id} must wait for an action`);
    }
  }
});

test("the short route is substantially shorter and still hands-on across the main areas", () => {
  assert.equal(tourSteps("short"), SHORT_TOUR);
  assert.equal(tourSteps("full"), FULL_TOUR);
  assert.equal(SHORT_TOUR.length, 10, "The quick route includes one consolidated topics overview");
  assert.equal(FULL_TOUR.length, 39, "The full route keeps the tools without separate per-topic question stations");
  assert.ok(FULL_TOUR.length >= SHORT_TOUR.length * 3);
  const exercises = new Set(SHORT_TOUR.map((step) => step.exercise));
  for (const exercise of ["goal", "library", "topics", "code", "circuit", "hints", "feedback", "interview", "progress", "settings"]) {
    assert.ok(exercises.has(exercise as TourStep["exercise"]), `Quick tour must include ${exercise}`);
  }
  for (const step of SHORT_TOUR) {
    assert.ok(FULL_TOUR.some((full) => full.id === step.id));
    assert.ok(step.actions.length > 0);
  }
});

test("both routes share one interactive topics overview while the full route retains every learning tool", () => {
  const overview = station("topics");
  assert.equal(overview.exercise, "topics");
  for (const steps of [FULL_TOUR, SHORT_TOUR]) {
    assert.equal(steps.filter((step) => step.id === "topics").length, 1);
    assert.deepEqual(steps.find((step) => step.id === "topics")?.actions, ["topics-explored"]);
    for (const oldTopic of ["digital", "fsm", "programming", "algorithms", "reasoning-topic", "behavioral", "design-topic", "communication"]) {
      assert.ok(!steps.some((step) => step.id === oldTopic), `The consolidated overview replaces the old ${oldTopic} station`);
    }
  }
  for (const tool of ["code", "languages", "wire", "simulate", "inputs", "truth", "palette", "configure", "undo", "expand", "export-circuit", "mux", "clock-start", "clock", "reset", "hint", "solution", "materials", "photo", "remove-photo", "feedback", "feedback-details", "followup", "reports", "interview", "interview-answer", "interview-report", "saved", "history", "progress", "readiness", "plan", "theme", "language"]) {
    assert.ok(station(tool).actions.length > 0, `${tool} needs a hands-on requirement`);
  }
});

test("unrelated actions and actions from neighboring stations cannot satisfy a task", () => {
  for (const step of FULL_TOUR) {
    const unrelated = FULL_TOUR.flatMap((other) => other.actions).filter((action) => !step.actions.includes(action));
    assert.equal(stationReady(step, ["next-clicked", "panel-seen", ...unrelated]), false, step.id);
    assert.equal(stationReady(step, [...step.actions, "unrelated-event"]), true, step.id);
  }
});

test("a station requiring several actions waits for all concrete actions", () => {
  const combined: TourStep = { ...station("wire"), actions: ["circuit-edited", "circuit-simulated"] };
  assert.equal(stationReady(combined, ["circuit-edited"]), false);
  assert.equal(stationReady(combined, ["circuit-simulated"]), false);
  assert.equal(stationReady(combined, ["circuit-edited", "circuit-edited"]), false);
  assert.equal(stationReady(combined, ["circuit-simulated", "circuit-edited"]), true);
});

test("initial progress does not pretend the tour was offered or completed", () => {
  const a = initialTourProgress();
  assert.equal(a.offered, false);
  assert.equal(a.status, "paused");
  assert.equal(a.kind, "full");
  assert.equal(a.stepId, FULL_TOUR[0].id);
  assert.equal(a.completed.length, 0);
  assert.equal(a.skipped.length, 0);
  a.completed.push("goal");
  assert.deepEqual(initialTourProgress().completed, [], "Fresh sessions must not share mutable arrays");
});

test("corrupt, missing, unsupported and oversized storage restarts safely", () => {
  const corrupt: (string | null)[] = [null, "", "{", "null", "false", "[]", "1", '"old-data"'];
  for (const value of corrupt) assert.deepEqual(parseTourProgress(value), initialTourProgress());
  for (const patch of [{ version: 2 }, { version: "1" }, { kind: "unknown" }, { status: "running" }, { status: null }]) {
    assert.deepEqual(parseTourProgress(stored(patch)), initialTourProgress());
  }
  assert.deepEqual(parseTourProgress(stored().padEnd(20_001, " ")), initialTourProgress());
});

test("storage accepts only station IDs belonging to the chosen tour and deduplicates them", () => {
  const parsed = parseTourProgress(stored({
    kind: "short",
    stepId: "clock",
    completed: ["goal", "goal", "search", "clock", "not-a-station", 7, null, { id: "code" }],
    skipped: ["hint", "hint", "truth", false, "photo"],
  }));
  assert.equal(parsed.kind, "short");
  assert.equal(parsed.stepId, SHORT_TOUR[0].id);
  assert.deepEqual(parsed.completed, ["goal", "search"]);
  assert.deepEqual(parsed.skipped, ["hint"]);
});

test("an older per-topic checkpoint resumes at the topics overview without losing completed tool stations", () => {
  const parsed = parseTourProgress(stored({
    kind: "full",
    stepId: "fsm",
    completed: ["goal", "digital", "code", "truth", "languages", "code"],
    skipped: ["programming", "photo", "clock"],
    status: "paused",
  }));
  assert.equal(parsed.stepId, "topics");
  assert.equal(parsed.kind, "full");
  assert.equal(parsed.status, "paused");
  assert.equal(parsed.offered, true);
  assert.equal(parsed.updatedAt, 123);
  assert.deepEqual(parsed.completed, ["goal", "code", "truth", "languages"]);
  assert.deepEqual(parsed.skipped, ["photo", "clock"]);
  assert.ok(!parsed.completed.includes("topics"), "Migrating a location must not pretend the new overview was completed");
});

test("storage normalizes optional scalar fields and malformed ID collections", () => {
  const parsed = parseTourProgress(stored({
    offered: "true",
    completed: "goal",
    skipped: { goal: true },
    updatedAt: "123",
    stepId: { id: "goal" },
  }));
  assert.equal(parsed.offered, false);
  assert.equal(parsed.updatedAt, 0);
  assert.equal(parsed.stepId, FULL_TOUR[0].id);
  assert.deepEqual(parsed.completed, []);
  assert.deepEqual(parsed.skipped, []);
  for (const value of [null, "Infinity", {}, []]) {
    assert.equal(parseTourProgress(stored({ updatedAt: value })).updatedAt, 0);
  }
});

test("stored completion takes precedence over a contradictory skipped mark", () => {
  const parsed = parseTourProgress(stored({
    completed: ["goal", "search", "goal"],
    skipped: ["goal", "hint", "search", "hint"],
  }));
  assert.deepEqual(parsed.completed, ["goal", "search"]);
  assert.deepEqual(parsed.skipped, ["hint"]);
  assert.equal(new Set([...parsed.completed, ...parsed.skipped]).size, parsed.completed.length + parsed.skipped.length);
});

test("each supported status and route round-trips without dropping a valid checkpoint", () => {
  for (const kind of ["short", "full"] as TourKind[]) {
    for (const status of ["paused", "completed", "dismissed"] as TourProgress["status"][]) {
      const ids = tourSteps(kind).map((step) => step.id);
      const progress: TourProgress = {
        version: 1, offered: true, kind, status, stepId: ids.at(-1)!,
        completed: ids.slice(0, 2), skipped: ids.slice(2, 3), updatedAt: 123,
      };
      assert.deepEqual(parseTourProgress(JSON.stringify(progress)), progress);
    }
  }
});

test("checkpoint distinguishes completed work from an explicitly skipped station", () => {
  const before = initialTourProgress();
  const skipped = checkpoint(before, station("goal"), "skipped", station("search"));
  assert.deepEqual(before, initialTourProgress(), "Checkpoint must not mutate the source progress");
  assert.equal(skipped.offered, true);
  assert.equal(skipped.status, "paused");
  assert.equal(skipped.stepId, "search");
  assert.deepEqual(skipped.completed, []);
  assert.deepEqual(skipped.skipped, ["goal"]);
  assert.ok(skipped.updatedAt > 0);
  const completed = checkpoint(skipped, station("goal"), "completed", station("search"));
  assert.deepEqual(completed.completed, ["goal"]);
  assert.deepEqual(completed.skipped, [], "Finishing a previously skipped station resolves its skipped mark");
  const repeated = checkpoint(completed, station("goal"), "completed", station("search"));
  assert.deepEqual(repeated.completed, ["goal"]);
});

test("revisiting and skipping completed work does not erase the user's achievement", () => {
  const completed = checkpoint(initialTourProgress(), station("goal"), "completed", station("search"));
  const revisited = checkpoint(completed, station("goal"), "skipped", station("search"));
  assert.deepEqual(revisited.completed, ["goal"]);
  assert.deepEqual(revisited.skipped, []);
});

test("the final checkpoint ends either route, including a tour with explicit skips", () => {
  for (const kind of ["short", "full"] as const) {
    const steps = tourSteps(kind);
    let progress: TourProgress = { ...initialTourProgress(), kind, stepId: steps[0].id };
    for (let index = 0; index < steps.length; index++) {
      progress = checkpoint(progress, steps[index], index % 2 === 0 ? "completed" : "skipped", steps[index + 1]);
    }
    assert.equal(progress.status, "completed");
    assert.equal(progress.stepId, steps.at(-1)!.id);
    assert.equal(progress.completed.length + progress.skipped.length, steps.length);
    assert.equal(new Set([...progress.completed, ...progress.skipped]).size, steps.length);
    assert.deepEqual(parseTourProgress(JSON.stringify(progress)), progress);
  }
});

test("tour storage is scoped per user and strips all answer or attachment payloads", () => {
  assert.notEqual(tourKey("user-one"), tourKey("user-two"));
  assert.notEqual(tourKey("user-one"), tourKey());
  assert.equal(tourKey("user-one"), tourKey("user-one"));
  assert.match(tourKey("user-one"), /v1/);
  assert.ok(!tourKey("user-one").startsWith("jr-attempt-draft"));
  const parsed = parseTourProgress(stored({
    answer: "private handwritten response",
    code: "secret implementation",
    images: [{ path: "private/storage/path" }],
    circuit: { parts: ["personal-work"] },
    userId: "other-user",
    token: "private-token",
  }));
  assert.deepEqual(Object.keys(parsed).sort(), Object.keys(initialTourProgress()).sort());
  const serialized = JSON.stringify(parsed);
  for (const privateValue of ["private handwritten response", "secret implementation", "private/storage/path", "personal-work", "other-user", "private-token"]) {
    assert.ok(!serialized.includes(privateValue));
  }
});

const fakeDocument = (overflow = "") => ({ body: { style: { overflow } } }) as unknown as Document;

test("nested tour and expanded-circuit scroll locks release correctly in either cleanup order", () => {
  for (const original of ["", "auto", "scroll", "hidden"]) {
    for (const parentFirst of [true, false]) {
      const document = fakeDocument(original);
      const releaseTour = lockBodyScroll(document);
      assert.equal(document.body.style.overflow, "hidden");
      const releaseCircuit = lockBodyScroll(document);
      const [first, last] = parentFirst ? [releaseTour, releaseCircuit] : [releaseCircuit, releaseTour];
      first();
      assert.equal(document.body.style.overflow, "hidden", "A still-open nested surface must retain the lock");
      last();
      assert.equal(document.body.style.overflow, original, "The last cleanup must restore the original page overflow");
    }
  }
});

test("scroll-lock cleanup is idempotent and cannot release another active surface's lock", () => {
  const document = fakeDocument("auto");
  const releaseTour = lockBodyScroll(document);
  const releaseCircuit = lockBodyScroll(document);
  releaseTour();
  releaseTour();
  releaseTour();
  assert.equal(document.body.style.overflow, "hidden");
  releaseCircuit();
  assert.equal(document.body.style.overflow, "auto");
  releaseCircuit();
  assert.equal(document.body.style.overflow, "auto");
  document.body.style.overflow = "scroll";
  const releaseNextTour = lockBodyScroll(document);
  releaseTour();
  assert.equal(document.body.style.overflow, "hidden", "Old cleanup callbacks must not unlock a later tour");
  releaseNextTour();
  assert.equal(document.body.style.overflow, "scroll", "A new lock cycle must capture its own current overflow");
});

test("scroll locks are isolated per document rather than leaking across independent windows", () => {
  const one = fakeDocument("auto"), two = fakeDocument("scroll");
  const releaseOne = lockBodyScroll(one), releaseTwo = lockBodyScroll(two);
  releaseOne();
  assert.equal(one.body.style.overflow, "auto");
  assert.equal(two.body.style.overflow, "hidden");
  releaseTwo();
  assert.equal(two.body.style.overflow, "scroll");
});
