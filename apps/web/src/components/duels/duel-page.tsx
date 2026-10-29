"use client";

import { useEffect, useMemo, useState } from "react";
import { Auth } from "../auth";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { duelApi } from "../../lib/duel-api";
import { avatarApi } from "../../lib/avatar-api";
import type { AvatarConfig } from "../../lib/avatar-types";
import type { DuelLanguage } from "../../lib/duel-types";
import { DuelWorkspace } from "./duel-workspace";

export function useDuelLanguage() {
  const [lang, setLang] = useState<DuelLanguage>("he");
  useEffect(() => { try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "he" ? "rtl" : "ltr"; try { localStorage.setItem("jobrun-language", lang); } catch {} }, [lang]);
  return [lang, setLang] as const;
}

function LiveWorkspace({ userId, lang, invite, controls }: { userId: string; lang: DuelLanguage; invite: string; controls: React.ReactNode }) {
  const client = useMemo(() => duelApi(userId), [userId]);
  const [avatar, setAvatar] = useState<AvatarConfig | null>(null);
  useEffect(() => {
    let current = true;
    void avatarApi(userId).get().then(value => { if (current) setAvatar(value.avatar); }).catch(() => {});
    return () => { current = false; };
  }, [userId]);
  return <DuelWorkspace client={client} lang={lang} invite={invite} controls={controls} avatar={avatar} />;
}

export function DuelPage({ invite = "" }: { invite?: string }) {
  const [lang, setLang] = useDuelLanguage();
  const controls = <><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>;
  return <Auth kind="practice" lang={lang} controls={controls}>{user => <LiveWorkspace key={user.id} userId={user.id} lang={lang} invite={invite} controls={controls} />}</Auth>;
}
