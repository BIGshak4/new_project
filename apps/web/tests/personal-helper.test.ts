import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { helperDestinations, helperTargets, helperTopics, type HelperAction, type HelperTopicId } from "../src/lib/personal-helper";
import { readWorkspaceRoute } from "../src/lib/workspace-route";

test("every helper topic is reachable and every branch can reach a usable action", () => {
  const ids = Object.keys(helperTopics) as HelperTopicId[];
  const reached = new Set<HelperTopicId>();
  const visit = (id: HelperTopicId) => {
    assert.ok(helperTopics[id], `Missing helper topic: ${id}`);
    if (reached.has(id)) return;
    reached.add(id);
    for (const choice of helperTopics[id].choices) if (choice.topic) visit(choice.topic);
  };
  visit("root");
  assert.deepEqual([...reached].sort(), [...ids].sort(), "No authored guidance should be stranded");
  const canAct = (id: HelperTopicId, seen = new Set<HelperTopicId>()): boolean => {
    if (seen.has(id)) return false;
    const next = new Set(seen).add(id);
    return helperTopics[id].choices.some(choice => !!choice.action || canAct(choice.topic!, next));
  };
  for (const id of ids) assert.ok(canAct(id), `${id} leads only to a navigation loop`);
});

test("choices are unambiguous, bilingual, and bounded for a conversation panel", () => {
  for (const [id, node] of Object.entries(helperTopics)) {
    assert.ok(node.messages.length > 0 && node.messages.length <= 2, `${id}: keep guidance concise`);
    assert.ok(node.choices.length >= 2 && node.choices.length <= (id === "root" ? 5 : 4), `${id}: too many choices`);
    const copy = [node.title, ...node.messages, ...node.choices.map(choice => choice.label)];
    for (const value of copy) {
      assert.match(value.he, /[א-ת]/, `${id}: missing Hebrew`);
      assert.match(value.en, /[a-z]/i, `${id}: missing English`);
      assert.equal(value.he, value.he.trim());
      assert.equal(value.en, value.en.trim());
    }
    for (const language of ["he", "en"] as const) {
      const labels = node.choices.map(choice => choice.label[language]);
      assert.equal(new Set(labels).size, labels.length, `${id}: duplicate ${language} choices`);
    }
    const contracts = node.choices.map(choice => {
      assert.equal(Number(!!choice.topic) + Number(!!choice.action), 1, `${id}: each choice must have exactly one effect`);
      return choice.topic ? `topic:${choice.topic}` : JSON.stringify(choice.action);
    });
    assert.equal(new Set(contracts).size, contracts.length, `${id}: duplicate choice effects`);
  }
});

test("the action allowlist covers all support categories without running or submitting work", () => {
  const actions = Object.values(helperTopics).flatMap(node => node.choices.flatMap(choice => choice.action ? [choice.action] : []));
  const categories = new Set(actions.filter((action): action is Extract<HelperAction, { type: "support" }> => action.type === "support").map(action => action.category));
  assert.deepEqual([...categories].sort(), ["bug", "feedback", "other", "question"]);
  const targets = new Set<string>();
  const destinations = new Set<string>();
  for (const action of actions) {
    assert.ok(["support", "inbox", "tour", "focus", "navigate"].includes(action.type));
    if (action.type === "focus") {
      assert.ok(Object.hasOwn(helperTargets, action.target));
      targets.add(action.target);
    }
    if (action.type === "navigate") {
      assert.ok(Object.hasOwn(helperDestinations, action.destination));
      destinations.add(action.destination);
    }
    const allowedKeys = action.type === "support" ? ["category", "type"] : action.type === "focus" ? ["target", "type"] : action.type === "navigate" ? ["destination", "type"] : ["type"];
    assert.deepEqual(Object.keys(action).sort(), allowedKeys, "No arbitrary payload, code or user-provided URL may become an action");
  }
  assert.deepEqual([...targets].sort(), Object.keys(helperTargets).sort());
  assert.deepEqual([...destinations].sort(), Object.keys(helperDestinations).sort());
});

test("destinations stay on known site routes and preserve cross-page practice intent", () => {
  for (const [destination, href] of Object.entries(helperDestinations)) {
    const url = new URL(href, "https://jobrun.example");
    assert.equal(url.origin, "https://jobrun.example");
    assert.ok(["/", "/games", "/games/shop"].includes(url.pathname));
    assert.equal(url.hash, "");
    if (["learn", "library", "interview"].includes(destination)) {
      assert.equal(readWorkspaceRoute(url.search, true).route.view, destination, "A category link must survive initial workspace routing");
      assert.deepEqual([...url.searchParams.keys()].sort(), ["nav", "view"]);
    } else assert.equal(url.search, "");
  }
});

test("focus selectors remain attached to real editor controls, never hint or submission actions", () => {
  const component = (name: string) => readFileSync(new URL(`../src/components/${name}.tsx`, import.meta.url), "utf8");
  const sources = ["answer-editor", "technical-code-editor", "code-execution-panel", "circuit-editor", "visual-answer", "practice-session"].map(component).join("\n");
  for (const selector of Object.values(helperTargets)) {
    assert.doesNotMatch(selector, /hint|solution-open|submit|reference/);
    for (const match of selector.matchAll(/\[data-muxi-control="([a-z-]+)"\]/g)) {
      const anchor = match[1];
      const conditionalAttribute = new RegExp(`data-muxi-control=\\{[^}]*"${anchor}"[^}]*\\}`);
      assert.ok(sources.includes(`data-muxi-control="${anchor}"`) || sources.includes(`"data-muxi-control": "${anchor}"`) || conditionalAttribute.test(sources), `Missing actual control: ${anchor}`);
    }
  }
  assert.ok(sources.includes('className="visual-answer-actions"'));
  assert.ok(sources.includes('id="feedback"'));
});
