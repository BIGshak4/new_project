"use client";

import { useEffect, useState } from "react";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { demoAvatarClient } from "../../lib/avatar-demo";
import type { AvatarClient, AvatarLanguage } from "../../lib/avatar-types";
import { Wardrobe } from "./wardrobe";

export function WardrobePreview() {
  const [client, setClient] = useState<AvatarClient | null>(null);
  const [lang, setLang] = useState<AvatarLanguage>("he");
  useEffect(() => { setClient(demoAvatarClient()); try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "he" ? "rtl" : "ltr"; try { localStorage.setItem("jobrun-language", lang); } catch {} }, [lang]);
  if (!client) return <main role="status">טוענים את החנות… / Loading shop…</main>;
  return <Wardrobe client={client} lang={lang} demo controls={<><ThemeToggle lang={lang}/><LanguageMenu lang={lang} onChange={setLang}/></>}/>;
}
