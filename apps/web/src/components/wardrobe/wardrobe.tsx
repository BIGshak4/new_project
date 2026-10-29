"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, CircleHelp, Coins, MessagesSquare, RefreshCw, Shirt, ShoppingBag, ZoomIn } from "lucide-react";
import { MuxiMascot } from "../tour/muxi-mascot";
import { LogicAvatar } from "./logic-avatar";
import { ShirtArtwork, ShirtPrint, shirtPalette } from "./shirt-print";
import { FeatureNav } from "./feature-nav";
import { MEME_SKINS, muxiShopLine } from "./muxi-shop-copy";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { DEFAULT_AVATAR, sameAvatar, type AvatarClient, type AvatarConfig, type AvatarLanguage, type AvatarPayload } from "../../lib/avatar-types";
import styles from "./wardrobe.module.css";

function errorText(error: unknown, lang: AvatarLanguage) {
  const e = error as { code?: string; status?: number };
  const he = lang === "he";
  if (e.code === "unauthenticated") return he ? "ההתחברות השתנתה. היכנסו מחדש כדי לשמור." : "Your sign-in changed. Sign in again to save.";
  if (e.status === 402) return he ? "אין מספיק מטבעות לסקין הזה. הרכישה לא בוצעה." : "You do not have enough coins for this skin. The purchase was not made.";
  if (e.status === 503 || e.code === "configuration") return he ? "החנות עדיין אינה זמינה בשרת. אפשר להתרשם ממנה בהדגמה." : "The shop is not available on the server yet. Explore the preview meanwhile.";
  if (e.status === 422 || e.code === "validation") return he ? "לא ניתן לשמור את הבחירה הזאת. רעננו ובחרו פריט מהמאגר." : "This selection could not be saved. Refresh and choose a catalog item.";
  return he ? "לא הצלחנו לאשר את הפעולה. רעננו את החנות כדי לבדוק מה נשמר לפני ניסיון נוסף." : "We could not confirm the action. Refresh the shop to check what was saved before trying again.";
}

function validDraft(value: unknown, data: AvatarPayload): value is AvatarConfig {
  if (!value || typeof value !== "object") return false;
  const candidate = value as AvatarConfig;
  return data.components.some(item => item.key === candidate.component) && data.colors.some(item => item.key === candidate.color) && data.skins.some(item => item.key === candidate.skin);
}

export function Wardrobe({ client, lang, controls, demo = false, draftKey }: { client: AvatarClient; lang: AvatarLanguage; controls?: React.ReactNode; demo?: boolean; draftKey?: string }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [data, setData] = useState<AvatarPayload | null>(null);
  const [draft, setDraft] = useState<AvatarConfig>(DEFAULT_AVATAR);
  const [featuredKey, setFeaturedKey] = useState("negative_feedback");
  const [printExpanded, setPrintExpanded] = useState(false);
  const [filter, setFilter] = useState<"memes" | "classics" | "owned">("memes");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [notice, setNotice] = useState<"" | "saved" | "bought">("");
  const [joke, setJoke] = useState(0);
  const mounted = useRef(false);
  const generation = useRef(0);
  const working = useRef(false);
  const draftRef = useRef(draft);
  const dataRef = useRef(data);
  const featureHeading = useRef<HTMLHeadingElement>(null);
  const printHeading = useRef<HTMLHeadingElement>(null);
  const editorHeading = useRef<HTMLHeadingElement>(null);
  const storageKey = draftKey ? `jobrun-wardrobe-draft-v2:${draftKey}` : null;
  const Back = lang === "he" ? ArrowRight : ArrowLeft;
  draftRef.current = draft;
  dataRef.current = data;

  async function refresh() {
    if (working.current) return;
    const version = ++generation.current;
    setBusy("refresh"); setError(null);
    try {
      const next = await client.get();
      if (mounted.current && generation.current === version) {
        let restored: AvatarConfig = next.avatar;
        if (dataRef.current && !sameAvatar(draftRef.current, dataRef.current.avatar) && validDraft(draftRef.current, next)) restored = draftRef.current;
        else if (storageKey) {
          try { const value: unknown = JSON.parse(sessionStorage.getItem(storageKey) ?? "null"); if (validDraft(value, next)) restored = value; } catch {}
        }
        setData(next); setDraft(restored);
      }
    } catch (e) { if (mounted.current && generation.current === version) setError(e); }
    finally { if (mounted.current && generation.current === version) setBusy(""); }
  }
  useEffect(() => { mounted.current = true; void refresh(); return () => { mounted.current = false; generation.current++; }; }, [client]);
  const changed = data ? !sameAvatar(data.avatar, draft) : false;
  useEffect(() => {
    if (!data || !storageKey) return;
    try { if (changed) sessionStorage.setItem(storageKey, JSON.stringify(draft)); else sessionStorage.removeItem(storageKey); } catch {}
  }, [data, draft, changed, storageKey]);
  async function change(action: "save" | "buy", skin?: string, selection?: AvatarConfig) {
    if (working.current || !data) return;
    working.current = true;
    const version = ++generation.current;
    setBusy(skin ?? action); setError(null); setNotice("");
    try {
      const next = action === "buy" ? await client.buy(skin!) : await client.save(selection ?? draft);
      if (mounted.current && generation.current === version) {
        setData(next);
        if (action === "save") setDraft(next.avatar);
        setNotice(action === "buy" ? "bought" : "saved");
      }
    } catch (e) { if (mounted.current && generation.current === version) setError(e); }
    finally { working.current = false; if (mounted.current && generation.current === version) setBusy(""); }
  }
  function select(next: Partial<AvatarConfig>) { setDraft(current => ({ ...current, ...next })); setNotice(""); }
  function showPrint(key: string) {
    setFeaturedKey(key); setPrintExpanded(true); setNotice(""); setJoke(value => value + 1);
    requestAnimationFrame(() => { printHeading.current?.scrollIntoView({ block: "center", behavior: "instant" }); printHeading.current?.focus({ preventScroll: true }); });
  }
  function tryOn(key: string) {
    select({ skin: key });
    requestAnimationFrame(() => { editorHeading.current?.scrollIntoView({ block: "start", behavior: "instant" }); editorHeading.current?.focus({ preventScroll: true }); });
  }
  const ownsDraft = data?.owned_skins.includes(draft.skin) ?? false;
  const featured = data?.skins.find(skin => skin.key === featuredKey) ?? data?.skins[0];
  const featuredOwned = featured ? data?.owned_skins.includes(featured.key) : false;
  const lowBalance = !!(data && featured && !featuredOwned && data.balance < featured.price);
  const context = notice || (joke === 0 && ((error as { status?: number } | null)?.status === 402 || lowBalance) ? "short" : undefined);
  const catalog = data?.skins.filter(skin => filter === "owned" ? data.owned_skins.includes(skin.key) : filter === "memes" ? MEME_SKINS.has(skin.key) : !MEME_SKINS.has(skin.key)) ?? [];

  return <div className={styles.shell} dir={lang === "he" ? "rtl" : "ltr"}>
    <header className={styles.header}>
      <a href="/" className={styles.brand}>JobRun<span>{t("הדוכן של מוקסי", "Muxi's booth")}</span></a>
      <FeatureNav lang={lang} avatar={data?.avatar} demo={demo} current="shop"/>
      <div className={styles.controls}><button type="button" aria-haspopup="dialog" aria-label={t("דיווח על בעיה", "Report a problem")} title={t("דיווח על בעיה", "Report a problem")} onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={18} aria-hidden="true"/></button>{controls}</div>
    </header>
    <main className={styles.main}>
      <div className={styles.topline}><a href={demo ? "/games/preview" : "/games"}><Back size={17} aria-hidden="true"/>{t("לחדר המשחקים", "Back to games")}</a><span className={styles.wallet}><Coins size={20} aria-hidden="true"/>{data ? data.balance : "—"} {t(demo ? "מטבעות הדגמה" : "מטבעות", demo ? "demo coins" : "coins")}</span></div>
      {demo && <aside className={styles.demo}><strong>{t("חנות לדוגמה", "Shop preview")}</strong><span>{t("מודדים וקונים במטבעות הדגמה בלבד. החשבון שלכם אינו משתנה.", "Try and buy with demo coins only. Your account is unchanged.")}</span><a href="/games/shop">{t("לחנות האמיתית", "Open your real shop")}</a></aside>}
      {!!error && <div className={styles.error} role="alert"><span>{errorText(error, lang)}</span><button disabled={!!busy} onClick={() => void refresh()}><RefreshCw size={16} aria-hidden="true"/>{t("רענון החנות", "Refresh shop")}</button></div>}
      {!data && !error && <p className={styles.loading} role="status">{t("מוקסי פותח את הדוכן…", "Muxi is opening the booth…")}</p>}
      {data && <>
        {!data.enabled && <p className={styles.warning}>{t("שמירת הדמויות ממתינה להפעלה בשרת. אפשר לנסות את הבחירות כאן או לפתוח את ההדגמה.", "Character saving is awaiting server activation. Explore here or open the preview.")} <a href="/games/preview/shop">{t("להדגמה", "Try preview")}</a></p>}
        <section className={styles.booth} aria-labelledby="muxi-shop-title">
          <div className={styles.awning} aria-hidden="true"><span>Job_Run</span><span>{t("פתוח לרעיונות", "Open for ideas")}</span></div>
          <div className={styles.boothInside}>
            <div className={styles.merchant}>
              <h1 id="muxi-shop-title">{t("תפור עליכם.", "Your kind of thread.")}</h1>
              <div className={styles.speech}><p>{muxiShopLine(lang, joke, context)}</p><button type="button" onClick={() => { setJoke(value => value + 1); setNotice(""); }}><MessagesSquare size={15} aria-hidden="true"/>{t("עוד משהו, מוקסי?", "Anything else, Muxi?")}</button></div>
              <div className={styles.seller}><MuxiMascot pose={notice === "bought" || notice === "saved" ? "celebrate" : "wave"} className={styles.muxi} label={t("מוקסי, המוכר בדוכן", "Muxi, your shopkeeper")}/><span className={styles.sellerTag}>{t("מוקסי · תפור עליכם", "MUXI · AT YOUR SERVICE")}</span></div>
            </div>
            {featured && <div className={styles.featured}>
              <div className={styles.featuredShirt}><span className={styles.hanger} aria-hidden="true"/><ShirtArtwork skin={featured.key} size={310} label={featured.label[lang]}/></div>
              <div className={styles.featuredInfo}><h2 ref={featureHeading} tabIndex={-1}>{featured.label[lang]}</h2><p>{featured.description[lang]}</p><span className={styles.featuredPrice}>{featuredOwned ? <><Check size={17} aria-hidden="true"/>{t("כבר בארון שלכם", "Already in your wardrobe")}</> : <><Coins size={20} aria-hidden="true"/>{featured.price} {t("מטבעות", "coins")}</>}</span>
                {featuredOwned ? <button className={styles.primary} disabled={!!busy || !data.enabled || sameAvatar(data.avatar, { ...draft, skin: featured.key })} onClick={() => void change("save", undefined, { ...draft, skin: featured.key })}><Shirt size={17} aria-hidden="true"/>{busy === "save" ? t("שומרים…", "Saving…") : sameAvatar(data.avatar, { ...draft, skin: featured.key }) ? t("כבר לבוש", "You're wearing it") : t("ללבוש ולשמור", "Wear and save")}</button> : <button className={styles.primary} disabled={!!busy || !data.shop_enabled || lowBalance} onClick={() => void change("buy", featured.key)}><ShoppingBag size={17} aria-hidden="true"/>{busy === featured.key ? t("רוכשים…", "Buying…") : lowBalance ? t("חסרים מטבעות", "Need more coins") : t(`לקנות ב־${featured.price}`, `Buy for ${featured.price}`)}</button>}
                <button className={styles.textButton} disabled={!!busy} onClick={() => tryOn(featured.key)}>{t("למדוד על הדמות שלי", "Try on my character")}<Back size={16} aria-hidden="true"/></button>
                <button className={styles.textButton} aria-expanded={printExpanded} aria-controls="shirt-detail" onClick={() => { if (printExpanded) setPrintExpanded(false); else showPrint(featured.key); }}><ZoomIn size={16} aria-hidden="true"/>{printExpanded ? t("לסגור את התקריב", "Close print detail") : t("להגדיל את ההדפס", "Enlarge the print")}</button>
              </div>
            </div>}
          </div>
          {featured && printExpanded && <div className={styles.printDetail} id="shirt-detail"><div><h3 ref={printHeading} tabIndex={-1}>{featured.label[lang]}</h3><p>{t("הדפס קטן, בדיחה גדולה.", "Small print. Big personality.")}</p><button onClick={() => { setPrintExpanded(false); featureHeading.current?.focus({ preventScroll: true }); }}>{t("סגירת התקריב", "Close detail")}</button></div><div className={styles.printCanvas} style={{ backgroundColor: shirtPalette(featured.key).fabric }}><ShirtPrint skin={featured.key} label={t(`ההדפס של ${featured.label.he}`, `Print of ${featured.label.en}`)}/></div></div>}
          <div className={styles.counter}><span><ShoppingBag size={21} aria-hidden="true"/>{t("קצת הומור. הרבה אופי.", "A little humor. A lot of character.")}</span><small>{t("סקינים שנשארים אצלכם · רק בשביל הסטייל", "Yours to keep · strictly for the style")}</small></div>
        </section>
        {notice && <p className={styles.success} role="status">{notice === "bought" ? t("הסקין נוסף לארון שלכם. אפשר ללבוש ולשמור, או להמשיך למדוד.", "Added to your wardrobe. Wear and save it, or keep trying things on.") : t("הדמות נשמרה. נתראה במשחק!", "Character saved. See you in the game!")}</p>}
        {!data.shop_enabled && <p className={styles.warning}>{t("רכישות ייפתחו אחרי הפעלת החנות ומערכת המטבעות בשרת.", "Purchases open when the shop and coin system are active on the server.")}</p>}
        <section className={styles.collection} aria-labelledby="collection-title">
          <div className={styles.collectionHeading}><div><h2 id="collection-title">{t("מה תלוי על הקולב?", "Fresh off the rack.")}</h2><p>{t("בוחרים חולצה כדי לראות את ההדפס מקרוב. המדידה חינם.", "Pick a shirt to see the print up close. Trying it on is free.")}</p></div><div className={styles.filters} aria-label={t("סינון חולצות", "Filter shirts")}>{([["memes", t("חולצות עם אופי", "Meme shirts")], ["classics", t("הקלאסיקות", "The classics")], ["owned", t("הארון שלי", "My wardrobe")]] as const).map(([key, label]) => <button key={key} type="button" aria-pressed={filter === key} onClick={() => setFilter(key)}>{label}</button>)}</div></div>
          <div className={styles.rail}>{catalog.map(skin => {
            const owned = data.owned_skins.includes(skin.key);
            const wearing = data.avatar.skin === skin.key;
            return <article key={skin.key} className={styles.product}>
              <button className={styles.productArt} type="button" aria-label={t(`לראות מקרוב: ${skin.label.he}`, `See print up close: ${skin.label.en}`)} aria-pressed={featured?.key === skin.key} onClick={() => showPrint(skin.key)}><span className={styles.smallHanger} aria-hidden="true"/><ShirtArtwork skin={skin.key} size={240}/><span className={styles.enlarge}><ZoomIn size={15} aria-hidden="true"/>{t("ההדפס מקרוב", "See the print")}</span></button>
              <div className={styles.productInfo}><h3>{skin.label[lang]}</h3><p>{skin.description[lang]}</p><div className={styles.productBottom}><span className={styles.price}>{owned ? <><Check size={15} aria-hidden="true"/>{wearing ? t("לבוש כרגע", "Wearing") : t("בארון", "Owned")}</> : <><Coins size={17} aria-hidden="true"/>{skin.price}</>}</span>{owned ? <button disabled={!!busy || !data.enabled || sameAvatar(data.avatar, { ...draft, skin: skin.key })} onClick={() => void change("save", undefined, { ...draft, skin: skin.key })}>{wearing && !changed ? t("לבוש כרגע", "Wearing") : t("ללבוש ולשמור", "Wear and save")}</button> : <button disabled={!!busy || !data.shop_enabled || data.balance < skin.price} onClick={() => void change("buy", skin.key)}>{busy === skin.key ? t("רוכשים…", "Buying…") : data.balance < skin.price ? t("חסרים מטבעות", "Need coins") : t(`לקנות ב־${skin.price}`, `Buy for ${skin.price}`)}</button>}</div></div>
            </article>;
          })}</div>
        </section>
        <section id="my-character" className={styles.editorSection} aria-labelledby="character-title">
          <div className={styles.editorHeading}><h2 id="character-title" ref={editorHeading} tabIndex={-1}>{t("קודם כול, תהיו אתם.", "First, make it you.")}</h2><p>{t("הרכיב והצבע בחינם, תמיד. כל דמות מתחילה בחולצת Job_Run.", "Your component and color are always free. Every character starts with a Job_Run shirt.")}</p></div>
          <div className={styles.editor}>
            <div className={styles.stage}><div className={styles.characterFrame}><LogicAvatar config={draft} size={330} label={t("תצוגת הדמות שבחרתם", "Preview of your selected character")}/></div><p>{ownsDraft ? changed ? t("הדמות החדשה שלכם — שומרים כשמוכנים.", "Your new look — save when you're ready.") : t("זאת הדמות שלכם. מוכנים לסיבוב?", "That's your character. Ready for a round?") : t("הסקין הזה למדידה. רכשו אותו בדוכן כדי לשמור.", "This skin is a try-on. Buy it at the booth to save.")}</p></div>
            <div className={styles.options}>
              <fieldset disabled={!!busy}><legend>{t("איזה רכיב אתם?", "What's your component?")}</legend><div className={styles.components}>{data.components.map(component => <button key={component.key} type="button" aria-pressed={draft.component === component.key} onClick={() => select({ component: component.key })}><LogicAvatar config={{ ...draft, component: component.key }} size={70}/><span>{component.label[lang]}</span>{draft.component === component.key && <Check size={14} className={styles.selectedCheck} aria-hidden="true"/>}</button>)}</div></fieldset>
              <fieldset disabled={!!busy}><legend>{t("הצבע שלכם", "Your color")}</legend><div className={styles.colors}>{data.colors.map(color => <button key={color.key} type="button" aria-label={color.label[lang]} aria-pressed={draft.color === color.key} title={color.label[lang]} onClick={() => select({ color: color.key })}><span style={{ backgroundColor: color.hex }}/>{draft.color === color.key && <Check size={17} aria-hidden="true"/>}</button>)}</div></fieldset>
              <div className={styles.saveRow}><button className={styles.primary} disabled={!!busy || !data.enabled || !ownsDraft || !changed} onClick={() => void change("save")}>{busy === "save" ? t("שומרים…", "Saving…") : t("לשמור את הדמות", "Save character")}</button><span role="status">{notice === "saved" ? t("נשמר. נתראה במשחק!", "Saved. See you in the game!") : !data.enabled ? t("הבחירות כאן לתצוגה בלבד", "Selections are preview-only here") : !changed ? t("השינויים שלכם שמורים", "Your look is saved") : t("יש שינויים שלא נשמרו", "You have unsaved changes")}</span></div>
            </div>
          </div>
        </section>
      </>}
      <footer className={styles.footer}>{t("למטבעות אין ערך כספי. אי אפשר לקנות או לפדות אותם. הסקינים אינם משנים ניקוד או סיכויי ניצחון.", "Coins have no monetary value and cannot be bought or cashed out. Skins do not change scores or your chance of winning.")}</footer>
    </main>
  </div>;
}
