"use client";

import { useEffect, useState } from "react";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { demoDuelClient } from "../../lib/duel-demo";
import { getDemoAvatar } from "../../lib/avatar-demo";
import type { DuelClient, DuelLanguage } from "../../lib/duel-types";
import { DuelWorkspace } from "./duel-workspace";

/** This route alone includes answer-bearing draft demo content. */
export function DuelPreview() {
  const [client, setClient] = useState<DuelClient | null>(null);
  const [lang, setLang] = useState<DuelLanguage>("he");
  useEffect(() => { setClient(demoDuelClient()); try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "he" ? "rtl" : "ltr"; try { localStorage.setItem("jobrun-language", lang); } catch {} }, [lang]);
  if (!client) return <main style={{ padding: "40px 5%", color: "var(--ink)" }} role="status">טוענים את ההדגמה… / Loading preview…</main>;
  return <DuelWorkspace client={client} lang={lang} demo avatar={getDemoAvatar()} controls={<><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>} />;
}
