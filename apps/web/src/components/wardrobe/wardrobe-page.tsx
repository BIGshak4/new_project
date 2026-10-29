"use client";

import { useEffect, useMemo, useState } from "react";
import { Auth } from "../auth";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { avatarApi } from "../../lib/avatar-api";
import type { AvatarLanguage } from "../../lib/avatar-types";
import { Wardrobe } from "./wardrobe";

function LiveWardrobe({ userId, lang, controls }: { userId: string; lang: AvatarLanguage; controls: React.ReactNode }) {
  const client = useMemo(() => avatarApi(userId), [userId]);
  return <Wardrobe client={client} lang={lang} controls={controls} draftKey={userId}/>;
}

export function WardrobePage() {
  const [lang, setLang] = useState<AvatarLanguage>("he");
  useEffect(() => { try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "he" ? "rtl" : "ltr"; try { localStorage.setItem("jobrun-language", lang); } catch {} }, [lang]);
  const controls = <><ThemeToggle lang={lang}/><LanguageMenu lang={lang} onChange={setLang}/></>;
  return <Auth kind="practice" lang={lang} controls={controls}>{user => <LiveWardrobe key={user.id} userId={user.id} lang={lang} controls={controls}/>}</Auth>;
}
