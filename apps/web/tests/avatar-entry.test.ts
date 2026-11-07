import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { demoAvatarClient } from "../src/lib/avatar-demo";

const require = createRequire(import.meta.url);
require.extensions[".css"] = module => { module.exports = {}; };

test("account entry renders the personal area while optional avatar data is still pending", async () => {
  const { DashboardAvatarSetup } = await import("../src/components/wardrobe/avatar-onboarding");
  const { PracticeEntry } = await import("../src/components/practice-entry-splash");
  const workspace = createElement("main", null,
    createElement("h1", null, "האזור האישי שלכם"),
    createElement(DashboardAvatarSetup, { userId: "new-member", lang: "he" }),
  );
  const markup = renderToStaticMarkup(createElement(PracticeEntry, { owner: "new-member", lang: "he", children: workspace }));
  assert.match(markup, /נתחיל בשאלה טובה/);
  assert.match(markup, /<h1>האזור האישי שלכם<\/h1>/);
  assert.doesNotMatch(markup, /מכינים את סביבת העבודה|איזה רכיב אתם/u);
});

test("the dashboard picker still offers a free choice or skip inside the personal area", async () => {
  const { AvatarWelcome } = await import("../src/components/wardrobe/avatar-onboarding");
  const client = demoAvatarClient();
  const markup = renderToStaticMarkup(createElement(AvatarWelcome, { inline: true, client, data: await client.get(), lang: "he", onContinue() {} }));
  assert.match(markup, /<h3>נעים להכיר. איזה רכיב אתם\?<\/h3>/);
  assert.match(markup, /זאת הדמות שלי, ממשיכים/u);
  assert.match(markup, /אעשה את זה אחר כך/u);
  assert.doesNotMatch(markup, /<main|<header/);
});
