"use client";

import { useEffect, useState, type ReactNode } from "react";
import { CircleHelp } from "lucide-react";
import type { DuelLanguage } from "../../lib/duel-types";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { FeatureNav } from "../wardrobe/feature-nav";
import headerStyles from "../wardrobe/workspace-header.module.css";
import styles from "./duels.module.css";

export function useDuelLanguage() {
  const [lang, setLang] = useState<DuelLanguage>("he");
  useEffect(() => { try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "he" ? "rtl" : "ltr"; try { localStorage.setItem("jobrun-language", lang); } catch {} }, [lang]);
  return [lang, setLang] as const;
}

export function GamesNavigation({ lang, demo = false, controls }: { lang: DuelLanguage; demo?: boolean; controls: ReactNode }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  return <>
    <header className={`topnav ${headerStyles.header}`}>
      <a className="wordmark" href="/" dir="ltr"><span>.</span>jobrun</a>
      <FeatureNav className="tabs" lang={lang} demo={demo} current="games" />
      <div className={`topnav-actions ${headerStyles.toolbar} ${styles.controls}`}><button type="button" aria-label={t("דיווח על בעיה", "Report a problem")} title={t("דיווח על בעיה", "Report a problem")} aria-haspopup="dialog" onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={18} aria-hidden="true" /></button>{controls}</div>
    </header>
    <FeatureNav className="tabbar" variant="bottom" lang={lang} demo={demo} current="games" />
  </>;
}
