import type { AvatarConfig } from "./avatar-types";

export type IdentityLanguage = "he" | "en";
export type AccountIdentityData = { username: string | null; friend_code: string; can_claim_username: boolean };
export type UsernameAvailability = { available: boolean; reason: "invalid" | "offensive" | "taken" | null };
export type FriendPerson = { user_id: string; username: string | null; friend_code: string; avatar: AvatarConfig | null };
export type FriendRequest = { id: string; person: FriendPerson; created_at: string };
export type FriendsData = { friends: FriendPerson[]; incoming: FriendRequest[]; outgoing: FriendRequest[] };
export type IdentityClient = {
  identity(): Promise<AccountIdentityData>;
  claimUsername(username: string): Promise<AccountIdentityData>;
  friends(): Promise<FriendsData>;
  requestFriend(friendCode: string): Promise<FriendsData>;
  acceptRequest(id: string): Promise<FriendsData>;
  declineRequest(id: string): Promise<FriendsData>;
  cancelRequest(id: string): Promise<FriendsData>;
  removeFriend(userId: string): Promise<FriendsData>;
};

export const IDENTITY_UPDATED_EVENT = "jobrun:identity-updated";

export function normalizeUsername(value: string): string { return value.normalize("NFKC").trim(); }
export function validUsernameFormat(value: string): boolean {
  return /^(?=.{3,24}$)(?=.*[A-Za-z\u05d0-\u05ea])[A-Za-z\u05d0-\u05ea0-9_]+$/u.test(normalizeUsername(value));
}
export function normalizeFriendCode(value: string): string { return value.trim().toUpperCase(); }
export function validFriendCode(value: string): boolean { return /^[A-F0-9]{8}$/.test(normalizeFriendCode(value)); }
export function friendName(person: Pick<FriendPerson, "username" | "friend_code">, lang: IdentityLanguage): string {
  return person.username ?? `${lang === "he" ? "משתמש/ת" : "User"} ${person.friend_code}`;
}

export class IdentityApiError extends Error {
  constructor(public code: string, message: string, public status = 0) { super(message); this.name = "IdentityApiError"; }
}

export function identityErrorMessage(error: unknown, lang: IdentityLanguage): string {
  const he = lang === "he", code = (error as { code?: string } | null)?.code;
  const messages: Record<string, [string, string]> = {
    username_invalid: ["בחרו שם בן 3–24 תווים: אותיות בעברית או באנגלית, ספרות וקו תחתון. חייבת להיות בו לפחות אות אחת.", "Choose 3–24 characters: Hebrew or English letters, digits and underscores, including at least one letter."],
    username_offensive: ["השם הזה אינו מתאים. בחרו שם אחר.", "This name is not allowed. Choose another one."],
    username_taken: ["שם המשתמש כבר תפוס. בחרו שם אחר.", "This username is already taken. Choose another one."],
    username_immutable: ["שם המשתמש כבר נבחר ולא ניתן לשנותו.", "Your username has already been chosen and cannot be changed."],
    username_required: ["בחרו שם משתמש באזור האישי כדי להמשיך.", "Choose your username in Personal area to continue."],
    friend_invalid_code: ["הזינו קוד חבר בן 8 תווים, עם ספרות והאותיות A–F.", "Enter an 8-character friend code using digits and A–F."],
    friend_not_found: ["לא מצאנו משתמש עם הקוד הזה. בדקו את הקוד ונסו שוב.", "We could not find a user with this code. Check it and try again."],
    friend_self: ["זה הקוד שלכם. הזינו קוד של חבר או חברה.", "This is your own code. Enter a friend’s code."],
    friend_request_conflict: ["כבר קיימת בקשה או חברות עם המשתמש הזה. רעננו את הרשימה.", "A request or friendship already exists with this user. Refresh the list."],
    friend_request_received: ["כבר קיבלתם בקשה מהמשתמש הזה. אפשר לאשר אותה ברשימת הבקשות שקיבלתם.", "This user has already sent you a request. Accept it under incoming requests."],
    friend_limit: ["הגעתם למספר המרבי של חברים או בקשות. הסירו בקשה ישנה ונסו שוב.", "You have reached the friend or request limit. Remove an old request and try again."],
    not_found: ["הבקשה כבר אינה זמינה. רעננו את הרשימה.", "This request is no longer available. Refresh the list."],
    unauthenticated: ["החיבור לחשבון הסתיים. התחברו שוב כדי להמשיך.", "Your session has ended. Sign in again to continue."],
    account_changed: ["החשבון השתנה. טענו מחדש כדי להמשיך.", "The account changed. Reload to continue."],
    rate_limited: ["בוצעו יותר מדי ניסיונות. המתינו מעט ונסו שוב.", "There have been too many attempts. Wait a little and try again."],
    network: ["לא הצלחנו להגיע לשרת. נסו שוב.", "We could not reach the server. Please try again."],
  };
  return messages[code ?? ""]?.[he ? 0 : 1] ?? (he ? "הפעולה לא הושלמה. נסו לרענן ולנסות שוב." : "The action did not complete. Refresh and try again.");
}

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new IdentityApiError("invalid_response", "Incomplete identity response");
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== "string" || !value) throw new IdentityApiError("invalid_response", "Missing identity value");
  return value;
}
function code(value: unknown): string {
  const result = text(value);
  if (!/^[A-F0-9]{8}$/.test(result)) throw new IdentityApiError("invalid_response", "Invalid friend code");
  return result;
}
export function readIdentity(value: unknown): AccountIdentityData {
  const data = object(value);
  if (!(data.username === null || typeof data.username === "string") || typeof data.can_claim_username !== "boolean") throw new IdentityApiError("invalid_response", "Incomplete account identity");
  return { username: data.username, friend_code: code(data.friend_code), can_claim_username: data.can_claim_username };
}
export function readUsernameAvailability(value: unknown): UsernameAvailability {
  const data = object(value);
  if (typeof data.available !== "boolean" || ![null, "invalid", "offensive", "taken"].includes(data.reason as null | string) || (data.available && data.reason !== null) || (!data.available && data.reason === null)) throw new IdentityApiError("invalid_response", "Incomplete username check");
  return { available: data.available, reason: data.reason as UsernameAvailability["reason"] };
}
function person(value: unknown): FriendPerson {
  const data = object(value);
  if (!(data.username === null || typeof data.username === "string")) throw new IdentityApiError("invalid_response", "Invalid friend name");
  let avatar: AvatarConfig | null = null;
  if (data.avatar !== null) {
    const config = object(data.avatar);
    avatar = { component: text(config.component), color: text(config.color), skin: text(config.skin) };
  }
  return { user_id: text(data.user_id), username: data.username, friend_code: code(data.friend_code), avatar };
}
function request(value: unknown): FriendRequest {
  const data = object(value);
  return { id: text(data.id), person: person(data.person), created_at: text(data.created_at) };
}
export function readFriends(value: unknown): FriendsData {
  const data = object(value);
  if (!Array.isArray(data.friends) || !Array.isArray(data.incoming) || !Array.isArray(data.outgoing)) throw new IdentityApiError("invalid_response", "Incomplete friends list");
  const result = { friends: data.friends.map(person), incoming: data.incoming.map(request), outgoing: data.outgoing.map(request) };
  if (new Set(result.friends.map(friend => friend.user_id)).size !== result.friends.length || new Set([...result.incoming, ...result.outgoing].map(item => item.id)).size !== result.incoming.length + result.outgoing.length) throw new IdentityApiError("invalid_response", "Duplicate friendship records");
  return result;
}
