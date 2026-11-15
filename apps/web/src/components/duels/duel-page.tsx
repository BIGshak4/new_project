"use client";

import { useEffect, useMemo, useState } from "react";
import { useDuelLanguage } from "./games-navigation";
import { Auth } from "../auth";
import { LanguageMenu } from "../ui/language-menu";
import { ThemeToggle } from "../ui/theme-toggle";
import { duelApi } from "../../lib/duel-api";
import { avatarApi } from "../../lib/avatar-api";
import type { AvatarConfig } from "../../lib/avatar-types";
import type { DuelLanguage } from "../../lib/duel-types";
import { DuelWorkspace } from "./duel-workspace";
import { FriendsPanel } from "../friends-panel";
import { useFriendInvitations } from "./friend-duel-activity";

function LiveWorkspace({ userId, lang, invite, controls }: { userId: string; lang: DuelLanguage; invite: string; controls: React.ReactNode }) {
  const client = useMemo(() => duelApi(userId), [userId]);
  const invitations = useFriendInvitations(userId);
  const [avatar, setAvatar] = useState<AvatarConfig | null>(null);
  useEffect(() => {
    let current = true;
    void avatarApi(userId).get().then(value => { if (current) setAvatar(value.avatar); }).catch(() => {});
    return () => { current = false; };
  }, [userId]);
  return <DuelWorkspace client={client} lang={lang} invite={invite} controls={controls} avatar={avatar} invitations={invitations}
    renderFriends={(onChallenge, disabled, stake) => <FriendsPanel key={userId} userId={userId} lang={lang} onChallenge={onChallenge} challengeDisabled={disabled} stake={stake} />} />;
}

export function DuelPage({ invite = "" }: { invite?: string }) {
  const [lang, setLang] = useDuelLanguage();
  const controls = <><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>;
  return <Auth kind="practice" lang={lang} controls={controls}>{user => <LiveWorkspace key={user.id} userId={user.id} lang={lang} invite={invite} controls={controls} />}</Auth>;
}
