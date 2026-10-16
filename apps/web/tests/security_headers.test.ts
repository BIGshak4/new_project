import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import practice from "../next.config";
import tasks from "../../tasks/next.config";

for (const [name, config] of [["practice", practice], ["tasks", tasks]] as const) {
  test(`${name}: every route blocks cross-origin framing but permits the same-origin design gallery`, async () => {
    const rules = await config.headers!();
    const catchAll = rules.find((rule) => rule.source === "/:path*");
    assert.ok(catchAll);
    const headers = new Map(catchAll.headers.map(({ key, value }) => [key.toLowerCase(), value]));
    const directives = new Map(headers.get("content-security-policy")!.split(";").map((value) => {
      const [key, ...parts] = value.trim().split(/\s+/);
      return [key, parts.join(" ")];
    }));
    assert.equal(directives.get("frame-ancestors"), "'self'");
    assert.equal(headers.get("x-frame-options"), "SAMEORIGIN");
    assert.equal(directives.get("base-uri"), "'self'");
    assert.equal(directives.get("object-src"), "'none'");
    assert.equal(directives.get("form-action"), "'self'");
    assert.equal(headers.get("x-content-type-options"), "nosniff");
    // This bounded policy does not disable Next's inline hydration, the theme bootstrap,
    // CodeMirror styling or private signed Supabase image URLs.
    assert.equal(directives.has("default-src"), false);
    assert.equal(directives.has("script-src"), false);
    assert.match(headers.get("permissions-policy")!, /camera=\(\)/);
    assert.match(headers.get("permissions-policy")!, /geolocation=\(\)/);
    assert.match(headers.get("permissions-policy")!, name === "practice" ? /microphone=\(self\)/ : /microphone=\(\)/);
  });

  test(`${name}: Netlify static and fallback responses enforce the same security headers as Next routes`, async () => {
    const file = name === "practice" ? "../netlify.toml" : "../../tasks/netlify.toml";
    const toml = readFileSync(new URL(file, import.meta.url), "utf8");
    assert.match(toml, /\[\[headers\]\]\s*for = "\/\*"\s*\[headers.values\]/);
    const headerSection = toml.split("[headers.values]")[1].split(/\r?\n\[/)[0];
    const deployedHeaders = new Map([...headerSection.matchAll(/^([A-Za-z-]+)\s*=\s*("[^"\r\n]*")\s*$/gm)]
      .map((match) => [match[1].toLowerCase(), JSON.parse(match[2]) as string]));
    const rules = await config.headers!();
    const applicationHeaders = rules.find((rule) => rule.source === "/:path*")!.headers;
    for (const { key, value } of applicationHeaders)
      assert.equal(deployedHeaders.get(key.toLowerCase()), value, `${key} must be enforced by both delivery paths`);
  });
}
