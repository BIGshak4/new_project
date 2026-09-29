"use client";

import * as Menu from "@radix-ui/react-dropdown-menu";
import { Check } from "lucide-react";
import type { Lang } from "../auth";

/** The language switch as a menu with both languages listed and the current one ticked, instead of a toggle. */
export function LanguageMenu({ lang, onChange }: { lang: Lang; onChange: (lang: Lang) => void }) {
  const label = lang === "he" ? "שפה: עברית. החלפת שפה" : "Language: English. Change language";
  return (
    <Menu.Root dir={lang === "he" ? "rtl" : "ltr"} modal={false}>
      <Menu.Trigger asChild>
        <button type="button" className="language-switch" dir="ltr" aria-label={label} title={label}>
          {lang === "he" ? "עב" : "EN"}
        </button>
      </Menu.Trigger>
      <Menu.Portal>
        <Menu.Content className="ui-menu" sideOffset={6} align="end" collisionPadding={12}>
          <Menu.RadioGroup value={lang} onValueChange={(v) => onChange(v as Lang)}>
            <Menu.RadioItem value="he" className="ui-menu-item" dir="rtl">
              <span>עברית</span>
              <Menu.ItemIndicator className="ui-menu-tick">
                <Check size={15} aria-hidden="true" />
              </Menu.ItemIndicator>
            </Menu.RadioItem>
            <Menu.RadioItem value="en" className="ui-menu-item" dir="ltr">
              <span>English</span>
              <Menu.ItemIndicator className="ui-menu-tick">
                <Check size={15} aria-hidden="true" />
              </Menu.ItemIndicator>
            </Menu.RadioItem>
          </Menu.RadioGroup>
        </Menu.Content>
      </Menu.Portal>
    </Menu.Root>
  );
}
