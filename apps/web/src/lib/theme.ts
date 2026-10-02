export type Theme = "dark" | "light";
export const THEME_KEY = "jobrun-theme";
export function resolveTheme(value: string | null): Theme {
  return value === "dark" ? "dark" : "light";
}
// Runs before paint. First visits are light, regardless of the OS preference.
// Keep storage optional: private browsing must not prevent using the site.
export const themeBootstrap = `(()=>{let t="light";try{t=localStorage.getItem("${THEME_KEY}")==="dark"?"dark":"light"}catch{}document.documentElement.dataset.theme=t})()`;
