"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Swords } from "lucide-react";
import { duelApi } from "../../lib/duel-api";
import type { DuelInvitation, DuelLanguage } from "../../lib/duel-types";
import styles from "./duels.module.css";

const Invitations = createContext<{ owner: string; items: DuelInvitation[] } | null>(null);
const empty: DuelInvitation[] = [];
export function useFriendInvitations(userId: string) {
  const snapshot = useContext(Invitations);
  return snapshot?.owner === userId ? snapshot.items : empty;
}

export function FriendDuelActivity({ userId, lang, children }: { userId: string | null; lang: DuelLanguage; children: ReactNode }) {
  const client = useMemo(() => userId ? duelApi(userId) : null, [userId]);
  const [snapshot, setSnapshot] = useState<{ owner: string; items: DuelInvitation[] } | null>(null);
  const path = usePathname();

  useEffect(() => {
    if (!client || !userId) { setSnapshot(null); return; }
    let live = true, reading = false, lastPresence = -Infinity;
    async function refresh() {
      if (document.visibilityState !== "visible" || !client || !userId) return;
      const now = performance.now();
      if (now - lastPresence >= 45_000) {
        lastPresence = now;
        void client.presence().catch(() => { lastPresence = -Infinity; });
      }
      if (reading) return;
      reading = true;
      try {
        const result = await client.invitations();
        if (live) setSnapshot({ owner: userId, items: result.invitations });
      } catch { /* Retry on the next foreground refresh. */ }
      finally { reading = false; }
    }
    void refresh();
    const timer = window.setInterval(refresh, 15_000);
    document.addEventListener("visibilitychange", refresh);
    return () => { live = false; window.clearInterval(timer); document.removeEventListener("visibilitychange", refresh); };
  }, [client, userId]);

  const active = snapshot?.owner === userId ? snapshot : null;
  const first = active?.items[0];
  const inGames = path === "/games" || path.startsWith("/duel/") || path.startsWith("/games/preview");
  return <Invitations.Provider value={active}>
    {first && !inGames && <aside className={styles.invitationNotice} dir={lang === "he" ? "rtl" : "ltr"}>
      <Swords size={18} aria-hidden="true" />
      <span role="status">{lang === "he" ? <>קיבלתם הזמנה לדו־קרב{first.username && <> מאת <bdi>{first.username}</bdi></>}.</> : <><bdi>{first.username ?? "A friend"}</bdi> invited you to a duel.</>}</span>
      <a href="/games#duel-invitations">{lang === "he" ? "לצפייה בהזמנה" : "View invitation"}</a>
    </aside>}
    {children}
  </Invitations.Provider>;
}
