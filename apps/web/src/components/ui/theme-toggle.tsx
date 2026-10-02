"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { resolveTheme, THEME_KEY, type Theme } from "../../lib/theme";

const EVENT = "jobrun-theme-change";
function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  window.dispatchEvent(new Event(EVENT));
}
function subscribe(listener: () => void) {
  const storage = (event: StorageEvent) => {
    if (event.key === THEME_KEY || event.key === null)
      applyTheme(resolveTheme(event.newValue));
  };
  window.addEventListener(EVENT, listener);
  window.addEventListener("storage", storage);
  return () => {
    window.removeEventListener(EVENT, listener);
    window.removeEventListener("storage", storage);
  };
}
const snapshot = () =>
  resolveTheme(document.documentElement.dataset.theme ?? null);
const serverSnapshot = (): Theme => "light";

/** CSS changes in place; editors, API requests and unsent answers are never remounted. */
export function ThemeToggle({ lang }: { lang: "he" | "en" }) {
  const theme = useSyncExternalStore(subscribe, snapshot, serverSnapshot);
  const light = theme === "light";
  const label =
    lang === "he"
      ? light
        ? "מעבר למצב כהה"
        : "מעבר למצב בהיר"
      : light
        ? "Switch to dark mode"
        : "Switch to light mode";
  return (
    <button
      type="button"
      className="icon-button theme-toggle"
      aria-label={label}
      title={label}
      onClick={() => {
        const next = light ? "dark" : "light";
        applyTheme(next);
        try {
          localStorage.setItem(THEME_KEY, next);
        } catch {
          /* The current visit still works. */
        }
      }}
    >
      {light ? (
        <Moon size={18} aria-hidden="true" />
      ) : (
        <Sun size={18} aria-hidden="true" />
      )}
    </button>
  );
}
