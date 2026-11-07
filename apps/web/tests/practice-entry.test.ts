import assert from "node:assert/strict";
import { afterEach, before, test } from "node:test";
import { createRequire } from "node:module";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { hasGreeted, recordGreeting } from "../src/lib/practice-entry";

const require = createRequire(import.meta.url);
require.extensions[".css"] = module => { module.exports = {}; };
let Entry: typeof import("../src/components/practice-entry-splash").PracticeEntry;
before(async () => { ({ PracticeEntry: Entry } = await import("../src/components/practice-entry-splash")); });
const previousWindow = Object.getOwnPropertyDescriptor(globalThis, "window");
afterEach(() => {
  recordGreeting(null);
  if (previousWindow) Object.defineProperty(globalThis, "window", previousWindow);
  else Reflect.deleteProperty(globalThis, "window");
});

test("the initial workspace prepares under Muxi's greeting; section navigation skips it until the account signs out", () => {
  const data = new Map<string, string>();
  Object.defineProperty(globalThis, "window", { configurable: true, value: { sessionStorage: {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => data.set(key, value),
    removeItem: (key: string) => data.delete(key),
  } } });
  const draw = (owner: string, lang: "he" | "en") => renderToStaticMarkup(createElement(Entry, {
    owner, lang, children: createElement("main", null, "workspace"),
  }));
  const first = draw("alice", "he");
  assert.match(first, /נתחיל בשאלה טובה/);
  assert.match(first, /data-pose="wave"/);
  assert.match(first, /inert=""[^>]*><main>workspace<\/main>/);
  recordGreeting("alice");
  const navigation = draw("alice", "en");
  assert.doesNotMatch(navigation, /data-pose|inert=/);
  assert.match(navigation, /<main>workspace<\/main>/);
  assert.match(draw("bob", "en"), /Let’s start with a good question/);
  recordGreeting(null);
  assert.match(draw("alice", "en"), /Let’s start with a good question/);
});

test("storage restrictions preserve account-specific greeting behavior in the current document", () => {
  Object.defineProperty(globalThis, "window", { configurable: true, value: {
    get sessionStorage() { throw new Error("Storage blocked"); },
  } });
  recordGreeting("alice");
  assert.equal(hasGreeted("alice"), true);
  assert.equal(hasGreeted("bob"), false);
  recordGreeting(null);
  assert.equal(hasGreeted("alice"), false);
});
