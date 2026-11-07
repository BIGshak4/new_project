const ENTRY_KEY = "jobrun-practice-entry-owner";
export const GREETING_MS = 700;
export const MAX_SPLASH_MS = 1800;

// A tab may navigate between the practice, games and shop entry points.
let currentOwner: string | null = null;

export function hasGreeted(owner: string) {
  try {
    return window.sessionStorage.getItem(ENTRY_KEY) === owner;
  } catch {
    return currentOwner === owner;
  }
}

export function recordGreeting(owner: string | null) {
  currentOwner = owner;
  try {
    if (owner === null) window.sessionStorage.removeItem(ENTRY_KEY);
    else window.sessionStorage.setItem(ENTRY_KEY, owner);
  } catch { /* Keep the greeting scoped to this document if storage is unavailable. */ }
}
