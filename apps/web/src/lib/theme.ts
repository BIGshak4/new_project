export type Theme = "dark" | "light";
export const THEME_KEY = "jobrun-theme";
export function resolveTheme(value: string | null): Theme {
  return value === "light" ? "light" : "dark";
}
// Runs before paint. First visits are dark, regardless of the OS preference.
// Keep storage optional: private browsing must not prevent using the site.
export const themeBootstrap = `(()=>{let t="dark";try{t=localStorage.getItem("${THEME_KEY}")==="light"?"light":"dark"}catch{}document.documentElement.dataset.theme=t})()`;
