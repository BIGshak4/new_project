"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState, type FormEvent } from "react";
import { Check, RefreshCw, UserPlus, Users, X } from "lucide-react";
import { identityApi } from "../lib/identity-api";
import { DEFAULT_AVATAR } from "../lib/avatar-types";
import { IdentityApiError, friendName, identityErrorMessage, normalizeFriendCode, validFriendCode, type AccountIdentityData, type FriendPerson, type FriendRequest, type FriendsData, type IdentityLanguage } from "../lib/identity-types";
import { LogicAvatar } from "./wardrobe/logic-avatar";
import { FriendCode } from "./account-identity";
import styles from "./account-social.module.css";

export function FriendsPanel({ userId, lang }: { userId: string; lang: IdentityLanguage }) {
  const api = useMemo(() => identityApi(userId), [userId]);
  const id = useId(), he = lang === "he";
  const [saved, setSaved] = useState<{ owner: string; data: FriendsData } | null>(null);
  const [profile, setProfile] = useState<{ owner: string; data: AccountIdentityData } | null>(null);
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null), [identityError, setIdentityError] = useState<unknown>(null), [actionError, setActionError] = useState<unknown>(null);
  const [code, setCode] = useState(""), [sent, setSent] = useState(false), [uncertain, setUncertain] = useState(false);
  const owner = useRef(userId); owner.current = userId;
  const sequence = useRef(0), live = useRef(true), writing = useRef(false);
  const friends = saved?.owner === userId ? saved.data : null;
  const identity = profile?.owner === userId ? profile.data : null;
  const load = useCallback(async () => {
    const request = ++sequence.current;
    const current = () => live.current && owner.current === userId && sequence.current === request;
    setLoading(true); setError(null); setIdentityError(null);
    const results = await Promise.allSettled([api.friends(), api.identity()]);
    if (!current()) return;
    if (results[0].status === "fulfilled") { setSaved({ owner: userId, data: results[0].value }); setUncertain(false); }
    else setError(results[0].reason);
    if (results[1].status === "fulfilled") setProfile({ owner: userId, data: results[1].value });
    else setIdentityError(results[1].reason);
    setLoading(false);
  }, [api, userId]);
  useEffect(() => {
    live.current = true; setCode(""); setSent(false); setActionError(null); setBusy(null); setUncertain(false); writing.current = false;
    void load();
    return () => { live.current = false; sequence.current++; };
  }, [load]);

  async function act(key: string, operation: () => Promise<FriendsData>) {
    if (writing.current || loading || uncertain || !friends) return;
    writing.current = true; setBusy(key); setActionError(null); setSent(false);
    const request = ++sequence.current;
    const current = () => live.current && owner.current === userId && sequence.current === request;
    try {
      const data = await operation();
      if (current()) { setSaved({ owner: userId, data }); if (key === "add") { setCode(""); setSent(true); } }
    } catch (reason) {
      if (current()) {
        setActionError(reason);
        if (!(reason instanceof IdentityApiError) || ["network", "invalid_response"].includes(reason.code) || reason.status >= 500) setUncertain(true);
      }
    } finally { if (current()) { writing.current = false; setBusy(null); } }
  }
  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validFriendCode(code)) { setActionError(new IdentityApiError("friend_invalid_code", "Invalid friend code")); return; }
    void act("add", () => api.requestFriend(code));
  }
  const disabled = loading || !!busy || uncertain;
  const person = (value: FriendPerson, size: number) => <LogicAvatar config={value.avatar ?? DEFAULT_AVATAR} size={size} label={he ? `הדמות של ${friendName(value, lang)}` : `${friendName(value, lang)}’s avatar`} />;
  const requests = (values: FriendRequest[], incoming: boolean) => <ul className={styles.requests}>
    {values.map(request => <li key={request.id} className={styles.request}>
      {person(request.person, 64)}<div className={styles.requestName}><strong><bdi>{friendName(request.person, lang)}</bdi></strong>{!incoming && <span>{he ? "ממתינה לאישור" : "Waiting for acceptance"}</span>}</div>
      <div className={styles.requestActions}>{incoming ? <><button type="button" disabled={disabled || !identity?.username} onClick={() => void act(request.id, () => api.acceptRequest(request.id))} aria-label={he ? `אישור בקשת החברות של ${friendName(request.person, lang)}` : `Accept ${friendName(request.person, lang)}’s friend request`}><Check size={16} aria-hidden="true" />{busy === request.id ? he ? "מאשרים…" : "Accepting…" : he ? "אישור" : "Accept"}</button><button type="button" disabled={disabled} onClick={() => void act(`decline-${request.id}`, () => api.declineRequest(request.id))} aria-label={he ? `דחיית בקשת החברות של ${friendName(request.person, lang)}` : `Decline ${friendName(request.person, lang)}’s friend request`}><X size={16} aria-hidden="true" />{he ? "דחייה" : "Decline"}</button></> : <button type="button" disabled={disabled} onClick={() => void act(request.id, () => api.cancelRequest(request.id))}>{busy === request.id ? he ? "מבטלים…" : "Cancelling…" : he ? "ביטול הבקשה" : "Cancel request"}</button>}</div>
    </li>)}
  </ul>;

  return <section className={styles.friends} aria-labelledby={`${id}-title`} aria-busy={loading || !!busy} data-friends-panel>
    <div className={styles.friendsTop}><div className={styles.sectionHeading}><Users size={22} aria-hidden="true" /><h2 id={`${id}-title`}>{he ? "חברים" : "Friends"}</h2></div><button type="button" disabled={loading || !!busy} className={styles.refresh} onClick={() => void load()}><RefreshCw size={16} aria-hidden="true" />{he ? "רענון" : "Refresh"}</button></div>
    {identity && <div data-member-tour="friends-code"><FriendCode key={identity.friend_code} code={identity.friend_code} lang={lang} /></div>}
    {identityError != null && <p className={styles.error} role="alert">{he ? "לא הצלחנו לטעון את הקוד שלכם. לחצו על רענון כדי לנסות שוב." : "We couldn’t load your code. Refresh to try again."}</p>}
    {identity && !identity.username && <p className={styles.message}>{he ? "כדי לשלוח ולאשר בקשות חברות, בחרו שם משתמש בפרופיל. " : "Choose a username in your profile to send and accept friend requests. "}<a href="/#account-identity">{he ? "לבחירת שם משתמש" : "Choose a username"}</a></p>}
    <form className={styles.addFriend} onSubmit={add}>
      <label htmlFor={`${id}-code`}>{he ? "הוספת חבר לפי קוד" : "Add a friend by code"}</label>
      <div className={styles.addFriendRow}><input data-member-tour="friends-input" id={`${id}-code`} name="friend_code" dir="ltr" spellCheck={false} autoComplete="off" autoCapitalize="characters" maxLength={8} required value={code} placeholder="A1B2C3D4" disabled={!!busy} aria-describedby={`${id}-code-help`} onChange={event => { setCode(normalizeFriendCode(event.target.value)); setSent(false); setActionError(null); }} /><button type="submit" className="primary" disabled={disabled || !friends || !identity?.username || !validFriendCode(code)}><UserPlus size={17} aria-hidden="true" />{busy === "add" ? he ? "שולחים…" : "Sending…" : he ? "שליחת בקשת חברות" : "Send friend request"}</button></div>
      <p className={styles.message} id={`${id}-code-help`}>{he ? "בקשו מחבר או חברה את הקוד בן 8 התווים שלהם. החברות תתווסף אחרי אישור הבקשה." : "Ask your friend for their 8-character code. They’ll appear as a friend once they accept."}</p>
    </form>
    {loading && !friends && <p className={styles.message} role="status">{he ? "טוענים את החברים…" : "Loading friends…"}</p>}
    {error != null && <p className={styles.error} role="alert">{identityErrorMessage(error, lang)}</p>}
    {actionError != null && <p className={styles.error} role="alert">{uncertain ? he ? "לא קיבלנו אישור שהפעולה נשמרה. רעננו את הרשימה לפני ניסיון נוסף." : "We couldn’t confirm whether the action was saved. Refresh the list before trying again." : identityErrorMessage(actionError, lang)}</p>}
    {sent && <p className={styles.success} role="status">{he ? "בקשת החברות נשלחה. אפשר לראות אותה בבקשות ששלחתם." : "Friend request sent. You can see it under sent requests."}</p>}
    {friends && <>
      {friends.incoming.length > 0 && <section className={styles.requestSection} aria-labelledby={`${id}-incoming`}><h3 id={`${id}-incoming`}>{he ? "בקשות שקיבלתם" : "Incoming requests"} <span>({friends.incoming.length})</span></h3>{requests(friends.incoming, true)}</section>}
      <div className={styles.friendListHeading}><h3>{he ? "החברים שלכם" : "Your friends"} <span>({friends.friends.length})</span></h3></div>
      {friends.friends.length ? <ul className={styles.friendGrid}>{friends.friends.map(friend => <li className={styles.friend} key={friend.user_id} data-friend-code={friend.friend_code}>{person(friend, 112)}<strong><bdi>{friendName(friend, lang)}</bdi></strong><button type="button" className={styles.remove} disabled={disabled} onClick={() => void act(friend.user_id, () => api.removeFriend(friend.user_id))} aria-label={he ? `הסרת ${friendName(friend, lang)} מהחברים` : `Remove ${friendName(friend, lang)} from friends`}>{busy === friend.user_id ? he ? "מסירים…" : "Removing…" : he ? "הסרה" : "Remove"}</button></li>)}</ul> : <p className={styles.empty}>{he ? "עדיין אין חברים ברשימה. שלחו בקשה באמצעות הקוד של חבר או חברה." : "No friends yet. Send a request using a friend’s code."}</p>}
      {friends.outgoing.length > 0 && <section className={styles.requestSection} aria-labelledby={`${id}-outgoing`}><h3 id={`${id}-outgoing`}>{he ? "בקשות ששלחתם" : "Sent requests"} <span>({friends.outgoing.length})</span></h3>{requests(friends.outgoing, false)}</section>}
    </>}
  </section>;
}
