// Browser actions shared by the visitor preview and authenticated walkthrough checks.
import assert from "node:assert/strict";

export const previewStations = ["guest-library", "guest-hardware", "guest-explain", "guest-code", "guest-interview"];
export const memberStations = ["goal", "library", "circuit", "code", "feedback", "quiz", "interview", "community", "helper"];

export function tourControl(page, name) {
  return page.locator(`[data-muxi-stage] [data-muxi-control="${name}"]`).first();
}

export async function exerciseStation(page, id) {
  const click = name => tourControl(page, name).click();
  switch (id) {
    case "guest-library": {
      await click("guest-library-interview");
      const reveal = page.locator('[data-muxi-control="guest-library-reveal"]').filter({ visible: true });
      await reveal.click();
      await click("guest-library-short");
      await reveal.click();
      assert.equal(await page.locator('[data-muxi-stage] p:visible').filter({ hasText: /12/ }).count(), 1);
      break;
    }
    case "guest-hardware":
      await click("guest-hardware-open");
      await click("circuit-wire-open");
      await tourControl(page, "circuit-wire-source").selectOption("ab:Y");
      await tourControl(page, "circuit-wire-target").selectOption("vote:A0");
      await click("circuit-wire-connect");
      await tourControl(page, "circuit-component").selectOption("b");
      await click("circuit-input-toggle");
      await click("circuit-truth-table");
      await page.locator("[data-guest-hardware]").getByText(/כל שמונת הצירופים|All eight combinations/).waitFor();
      break;
    case "guest-explain": {
      await click("guest-explain-fill");
      assert.ok((await tourControl(page, "guest-explain-input").inputValue()).includes("O(n)"));
      await click("guest-explain-submit");
      await tourControl(page, "guest-software-feedback").locator(".evaluation.tone-partial").waitFor();
      break;
    }
    case "guest-code": {
      await page.locator("[data-muxi-stage] details summary").click();
      assert.ok((await page.locator("[data-muxi-stage] blockquote").innerText()).includes("O(n)"));
      await click("guest-code-open");
      await page.locator("[data-muxi-stage] .cm-content").waitFor();
      await click("guest-code-submit");
      const next = page.locator("[data-muxi-next]").filter({ visible: true }).first();
      assert.equal(await next.isDisabled(), true, "The starter code fails for negative arrays");
      await click("guest-code-fix");
      await click("guest-code-submit");
      await tourControl(page, "guest-software-feedback").locator(".evaluation.tone-strong").waitFor();
      break;
    }
    case "guest-interview":
      await click("guest-interview-start");
      await click("guest-interview-example");
      await click("guest-interview-finish");
      await page.locator("[data-muxi-stage]").getByText(/הדוח הוכן מראש על התשובה של מוקסי|This report was prepared in advance for Muxi’s answer/).waitFor();
      break;
    case "library":
      await click("library-question");
      break;
    case "circuit": {
      const output = tourControl(page, "xor-output");
      const before = await output.innerText();
      await click("xor-input-a");
      assert.notEqual(await output.innerText(), before, "Toggling A must change the XOR output");
      break;
    }
    case "code":
      await click("code-fix");
      break;
    case "feedback": {
      await click("feedback-answer");
      await click("feedback-review");
      const stage = page.locator("[data-muxi-stage]");
      await stage.getByRole("textbox").fill("1, 1");
      await stage.getByRole("button", { name: /השוואה לתשובה לדוגמה|Compare with a sample answer/ }).click();
      const first = await stage.getByRole("textbox").inputValue();
      assert.equal(first, "1, 1");
      await stage.locator('[data-muxi-control="feedback-answer"]').nth(1).click();
      await click("feedback-review");
      assert.equal(await stage.getByRole("textbox").inputValue(), "", "A different sample answer has its own follow-up");
      break;
    }
    case "quiz": {
      await click("quiz-open");
      const modal = page.locator("dialog:modal");
      const all = modal.getByRole("checkbox", { name: /בחר הכול|Select all/ });
      await all.check();
      await all.uncheck();
      assert.equal(await modal.locator('button[type="submit"]').isDisabled(), true, "An empty pool cannot start a quiz");
      await modal.getByRole("checkbox").nth(1).check();
      await modal.locator('button[type="submit"]').click();
      const reveal = page.locator("[data-muxi-stage]").getByRole("button", { name: /הצגת פתרון קצר|Show short solution/ });
      await reveal.first().waitFor();
      assert.equal(await reveal.count(), 10, "The selected topics produce ten questions together");
      await reveal.first().click();
      assert.equal(await reveal.count(), 9, "Each solution can be revealed independently");
      break;
    }
    case "interview":
      await click("interview-start");
      await click("interview-example");
      await click("interview-finish");
      break;
    case "community":
      await click("friend-preview");
      await click("friend-add");
      break;
    case "helper":
      await click("helper-question");
      break;
    default: throw Error(`Unknown demonstration station: ${id}`);
  }
}

export async function nextStation(page) {
  await page.locator("[data-muxi-next]").filter({visible: true}).first().click();
}
