import test from "node:test";
import assert from "node:assert/strict";
import { colorPalettes, paletteById } from "../src/app/color-preview/palettes";

function luminance(hex: string): number {
  const channels = hex.slice(1).match(/.{2}/g)!.map((channel) => {
    const value = parseInt(channel, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function contrast(a: string, b: string): number {
  const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("the comparison offers ten stable, individually named treatments", () => {
  assert.deepEqual(colorPalettes.map((palette) => palette.id), [
    "fog", "sage", "celadon", "olive", "mineral", "paper", "split", "graphite", "forest", "fern",
  ]);
  assert.equal(new Set(colorPalettes.map((palette) => palette.treatment)).size, 10);
  assert.equal(new Set(colorPalettes.map((palette) => palette.tokens.bg)).size, 10);
  assert.equal(new Set(colorPalettes.map((palette) => palette.name)).size, 10);
  assert.deepEqual(colorPalettes.filter((palette) => palette.theme === "dark").map((palette) => palette.id), ["graphite", "forest"]);
  for (const palette of colorPalettes) {
    assert.equal(palette.treatment, palette.id);
    assert.ok(palette.nameEn && palette.description);
    assert.deepEqual(palette.swatches, [palette.tokens.bg, palette.tokens.surface2, palette.tokens.ink, palette.tokens.accent]);
    for (const value of Object.values(palette.tokens)) assert.match(value, /^#[0-9a-f]{6}$/i);
  }
});

test("shareable palette IDs resolve deterministically with a stable default", () => {
  for (const palette of colorPalettes) assert.equal(paletteById(palette.id), palette);
  for (const invalid of [null, "", "unknown", "FOG", "__proto__", "constructor"])
    assert.equal(paletteById(invalid), colorPalettes[0]);
});

test("all reading, secondary-action and focus pairs meet their contrast roles", () => {
  const failures: string[] = [];
  const check = (ratio: number, minimum: number, role: string) => {
    if (ratio < minimum) failures.push(`${role}: ${ratio.toFixed(3)} < ${minimum}`);
  };
  for (const palette of colorPalettes) {
    const { tokens } = palette;
    for (const surface of ["bg", "surface", "surface2", "soft"] as const) {
      for (const foreground of ["ink", "muted", "link"] as const) {
        const ratio = contrast(tokens[foreground], tokens[surface]);
        check(ratio, 4.5, `${palette.id} ${foreground}/${surface}`);
      }
      const focusRatio = contrast(tokens.link, tokens[surface]);
      check(focusRatio, 3, `${palette.id} focus/${surface}`);
    }
    const actionRatio = contrast(tokens.accentInk, tokens.accent);
    check(actionRatio, 4.5, `${palette.id} action`);
    for (const surface of ["bg", "surface", "surface2"] as const) {
      const boundaryRatio = contrast(tokens.line, tokens[surface]);
      check(boundaryRatio, 3, `${palette.id} boundary/${surface}`);
    }
  }
  assert.deepEqual(failures, []);
});
