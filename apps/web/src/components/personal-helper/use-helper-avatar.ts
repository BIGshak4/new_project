"use client";

import { useEffect, useState } from "react";
import { avatarApi } from "../../lib/avatar-api";
import { getDemoAvatar } from "../../lib/avatar-demo";
import { AVATAR_UPDATED_EVENT, AvatarRefreshGuard, isAvatarConfig, readAvatarUpdate } from "../../lib/avatar-events";
import { DEFAULT_AVATAR, type AvatarConfig } from "../../lib/avatar-types";

export type HelperAvatarState = { avatar: AvatarConfig; status: "loading" | "ready" | "fallback" };
type OwnedAvatarState = HelperAvatarState & { owner: string };

export function useHelperAvatar(userId: string, demo: boolean): HelperAvatarState {
  const owner = demo ? "preview" : `user:${userId}`;
  const [state, setState] = useState<OwnedAvatarState>({ owner: "", avatar: DEFAULT_AVATAR, status: "fallback" });

  useEffect(() => {
    const guard = new AvatarRefreshGuard();
    setState({ owner, avatar: DEFAULT_AVATAR, status: "loading" });

    async function refresh() {
      const current = guard.start();
      try {
        const avatar = demo ? getDemoAvatar() : (await avatarApi(userId).get()).avatar;
        if (!isAvatarConfig(avatar)) throw new Error("Invalid avatar");
        if (current()) setState({ owner, avatar: { ...avatar }, status: "ready" });
      } catch {
        if (current()) setState(previous => previous.owner === owner && previous.status === "ready"
          ? previous : { owner, avatar: DEFAULT_AVATAR, status: "fallback" });
      }
    }
    const update = (event: Event) => {
      const avatar = readAvatarUpdate((event as CustomEvent<unknown>).detail, userId, demo);
      if (!avatar) return;
      guard.invalidate();
      setState({ owner, avatar, status: "ready" });
    };
    const focus = () => { if (document.visibilityState === "visible") void refresh(); };
    window.addEventListener(AVATAR_UPDATED_EVENT, update);
    window.addEventListener("focus", focus);
    document.addEventListener("visibilitychange", focus);
    void refresh();
    return () => {
      guard.invalidate();
      window.removeEventListener(AVATAR_UPDATED_EVENT, update);
      window.removeEventListener("focus", focus);
      document.removeEventListener("visibilitychange", focus);
    };
  }, [userId, demo, owner]);

  // Do not briefly render the previous account's outfit before the new owner's effect runs.
  return state.owner === owner ? { avatar: state.avatar, status: state.status }
    : { avatar: DEFAULT_AVATAR, status: "loading" };
}
