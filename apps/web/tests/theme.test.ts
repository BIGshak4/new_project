import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import { resolveTheme, themeBootstrap, THEME_KEY } from "../src/lib/theme";

test("first visit and invalid preferences are dark; an explicit light preference wins", () => {
  for (const value of [null, "", "system", "invalid", "dark"])
    assert.equal(resolveTheme(value), "dark");
  assert.equal(resolveTheme("light"), "light");
});

test("the pre-paint script restores the saved preference before React renders", () => {
  for (const saved of [null, "dark", "light", "malformed"]) {
    const document = {
      documentElement: { dataset: {} as Record<string, string> },
    };
    vm.runInNewContext(themeBootstrap, {
      document,
      localStorage: {
        getItem(key: string) {
          assert.equal(key, THEME_KEY);
          return saved;
        },
      },
    });
    assert.equal(document.documentElement.dataset.theme, resolveTheme(saved));
  }
});

test("unavailable browser storage cannot break the page or its dark default", () => {
  const document = {
    documentElement: { dataset: {} as Record<string, string> },
  };
  vm.runInNewContext(themeBootstrap, {
    document,
    localStorage: {
      getItem() {
        throw new Error("Storage blocked");
      },
    },
  });
  assert.equal(document.documentElement.dataset.theme, "dark");
});
