import { AVATAR_COLORS, type AvatarConfig } from "./avatar-types";

export const AVATAR_UPDATED_EVENT = "jobrun:avatar-updated";
export type AvatarUpdate = { userId: string | null; avatar: AvatarConfig; demo: boolean };

export function isAvatarConfig(value: unknown): value is AvatarConfig {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AvatarConfig>;
  return typeof candidate.component === "string" && ["and", "or", "xor", "mux", "dff"].includes(candidate.component)
    && typeof candidate.color === "string" && Object.hasOwn(AVATAR_COLORS, candidate.color)
    && typeof candidate.skin === "string" && /^[a-z0-9_-]{1,80}$/.test(candidate.skin);
}

/** Preview updates and another account's responses must never change the current user's helper. */
export function readAvatarUpdate(value: unknown, userId: string | undefined, demo: boolean): AvatarConfig | null {
  if (!value || typeof value !== "object") return null;
  const update = value as Partial<AvatarUpdate>;
  if (update.demo !== demo || (demo ? update.userId !== null : !userId || update.userId !== userId) || !isAvatarConfig(update.avatar)) return null;
  return { ...update.avatar };
}

export function publishAvatarUpdate(update: AvatarUpdate): void {
  if (typeof window === "undefined" || !readAvatarUpdate(update, update.userId ?? undefined, update.demo)) return;
  window.dispatchEvent(new CustomEvent<AvatarUpdate>(AVATAR_UPDATED_EVENT, { detail: { ...update, avatar: { ...update.avatar } } }));
}

/** A saved outfit supersedes every older read, including a read still awaiting its first response. */
export class AvatarRefreshGuard {
  private revision = 0;
  start(): () => boolean {
    const revision = ++this.revision;
    return () => revision === this.revision;
  }
  invalidate(): void { this.revision++; }
}
