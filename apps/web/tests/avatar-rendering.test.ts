import assert from "node:assert/strict";
import { before, test } from "node:test";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { createElement, Fragment } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { ShirtArtwork, ShirtPrint } from "../src/components/wardrobe/shirt-print";
import catalog from "../src/lib/avatar-catalog.json";

const require = createRequire(import.meta.url);
require.extensions[".css"] = (module) => { module.exports = { avatar: "avatar" }; };
let LogicAvatar: typeof import("../src/components/wardrobe/logic-avatar").LogicAvatar;
before(async () => { ({ LogicAvatar } = await import("../src/components/wardrobe/logic-avatar")); });

test("every catalog component and skin renders a branded, self-contained avatar in both directions", () => {
  for (const component of catalog.components) for (const skin of catalog.skins) for (const facing of ["left", "right"] as const) {
    const html = renderToStaticMarkup(createElement(LogicAvatar, { config: { component: component.key, color: "mint", skin: skin.key }, facing, label: "My character" }));
    assert.ok(html.includes("Job_Run"), `${component.key}/${skin.key}`);
    assert.ok(html.includes('aria-label="My character"'));
    assert.ok(!html.includes("NaN") && !html.includes("undefined"));
    const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
    for (const reference of html.matchAll(/url\(#([^\)]+)\)/g)) assert.ok(ids.has(reference[1]), `unresolved paint ${reference[1]}`);
    // Readable print/brand lives after the reflected anatomy group.
    if (facing === "left") assert.ok(html.indexOf("scale(-1 1)") < html.indexOf("Job_Run"));
  }
});

test("multiple gradient shirts keep unique paint IDs in a single rendered shelf", () => {
  const html = renderToStaticMarkup(createElement(Fragment, null,
    ...["gold", "aurora", "gold", "aurora"].map((skin, index) => createElement(ShirtArtwork, { skin, key: index }))));
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length);
  const targets = new Set(ids);
  for (const reference of html.matchAll(/url\(#([^\)]+)\)/g)) assert.ok(targets.has(reference[1]));
});

test("the six technical meme prints retain readable slogans in merchandise and close-up views", () => {
  const slogans: Record<string, string> = {
    negative_feedback: "NEGATIVE FEEDBACK", works_on_my_machine: "MY MACHINE", binary_people: "TYPES OF PEOPLE",
    gate_keeper: "AND GATE ON", sleep_not_found: "SLEEP NOT FOUND", resistance_futile: "IS FUTILE",
  };
  for (const [skin, slogan] of Object.entries(slogans)) {
    const shirt = renderToStaticMarkup(createElement(ShirtArtwork, { skin, label: slogan }));
    const print = renderToStaticMarkup(createElement(ShirtPrint, { skin, label: slogan }));
    assert.ok(shirt.includes(slogan) && shirt.includes("Job_Run"));
    assert.ok(print.includes(slogan));
    assert.ok(!shirt.includes("<image") && !print.includes("<image"), "runtime vectors do not depend on remote image assets");
  }
});

test("header and duel avatars use large identifying emblems while merchandise keeps the full joke", () => {
  const prints = {
    negative_feedback: ["negative-feedback", "NEGATIVE FEEDBACK"], works_on_my_machine: ["terminal", "MY MACHINE"],
    binary_people: ["binary", "TYPES OF PEOPLE"], gate_keeper: ["and", "AND GATE ON"],
    sleep_not_found: ["404", "SLEEP NOT FOUND"], resistance_futile: ["resistance", "IS FUTILE"],
  };
  for (const [skin, [symbol, slogan]] of Object.entries(prints)) {
    for (const size of [56, 170]) {
      const avatar = renderToStaticMarkup(createElement(LogicAvatar, { config: { component: "mux", color: "mint", skin }, size }));
      assert.ok(avatar.includes('data-avatar-print="compact"'));
      assert.ok(avatar.includes(`data-print-symbol="${symbol}"`));
      assert.ok(!avatar.includes(slogan), `small ${skin} avoids the unreadable full slogan`);
    }
    const full = renderToStaticMarkup(createElement(LogicAvatar, { config: { component: "mux", color: "mint", skin }, size: 280 }));
    const merchandise = renderToStaticMarkup(createElement(ShirtArtwork, { skin }));
    assert.ok(full.includes(slogan) && merchandise.includes(slogan));
  }
  const fullOverride = renderToStaticMarkup(createElement(LogicAvatar, { config: { component: "mux", color: "mint", skin: "negative_feedback" }, size: 170, compact: false }));
  assert.ok(fullOverride.includes('data-avatar-print="full"') && fullOverride.includes("NEGATIVE FEEDBACK"));
});

test("theme-aware silhouette separation is independent of the original face ink", () => {
  const avatar = renderToStaticMarkup(createElement(LogicAvatar, { config: { component: "mux", color: "mint", skin: "negative_feedback" } }));
  assert.match(avatar, /stroke="var\(--avatar-edge, transparent\)"[^>]+data-avatar-edge="silhouette"/);
  assert.match(avatar, /<ellipse cx="117" cy="91" rx="6" ry="8" fill="#35204f"/);
  const css = readFileSync(new URL("../src/components/wardrobe/logic-avatar.module.css", import.meta.url), "utf8");
  assert.ok(css.includes("--avatar-edge: color-mix") && css.includes("var(--link"));
  assert.match(css, /:root\[data-theme="light"\][^}]+--avatar-edge: transparent/);
});
