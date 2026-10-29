"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, CircleHelp, Coins, RefreshCw, Shirt, ShoppingBag, Sparkles } from "lucide-react";
import { MuxiMascot } from "../tour/muxi-mascot";
import { LogicAvatar } from "./logic-avatar";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { DEFAULT_AVATAR, sameAvatar, type AvatarClient, type AvatarConfig, type AvatarLanguage, type AvatarPayload } from "../../lib/avatar-types";
import styles from "./wardrobe.module.css";

function errorText(error: unknown, lang: AvatarLanguage) {
  const e = error as { code?: string; status?: number };
  const he = lang === "he";
  if (e.code === "unauthenticated") return he ? "ההתחברות השתנתה. היכנסו מחדש כדי לשמור." : "Your sign-in changed. Sign in again to save.";
  if (e.status === 402) return he ? "אין מספיק מטבעות לסקין הזה. היתרה שלכם נשמרה." : "You do not have enough coins for this skin. Your balance is unchanged.";
  if (e.status === 503 || e.code === "configuration") return he ? "החנות עדיין אינה זמינה בשרת. אפשר להתרשם ממנה בהדגמה." : "The shop is not available on the server yet. Explore the preview meanwhile.";
  if (e.status === 422 || e.code === "validation") return he ? "לא ניתן לשמור את הבחירה הזאת. רעננו ובחרו פריט מהמאגר." : "This selection could not be saved. Refresh and choose a catalog item.";
  return he ? "לא הצלחנו לאשר את הפעולה. רעננו את החנות כדי לבדוק מה נשמר לפני ניסיון נוסף." : "We could not confirm the action. Refresh the shop to check what was saved before trying again.";
}

export function Wardrobe({ client, lang, controls, demo = false }: { client: AvatarClient; lang: AvatarLanguage; controls?: React.ReactNode; demo?: boolean }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [data, setData] = useState<AvatarPayload | null>(null);
  const [draft, setDraft] = useState<AvatarConfig>(DEFAULT_AVATAR);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [notice, setNotice] = useState("");
  const mounted = useRef(false);
  const generation = useRef(0);
  const working = useRef(false);
  const Back = lang === "he" ? ArrowRight : ArrowLeft;
  async function refresh() {
    if (working.current) return;
    const version = ++generation.current;
    setBusy("refresh"); setError(null);
    try {
      const next = await client.get();
      if (mounted.current && generation.current === version) { setData(next); setDraft(next.avatar); }
    } catch (e) { if (mounted.current && generation.current === version) setError(e); }
    finally { if (mounted.current && generation.current === version) setBusy(""); }
  }
  useEffect(() => { mounted.current = true; void refresh(); return () => { mounted.current = false; generation.current++; }; }, [client]);

  async function change(action: "save" | "buy", skin?: string) {
    if (working.current || !data) return;
    working.current = true;
    const version = ++generation.current;
    setBusy(skin ?? action); setError(null); setNotice("");
    try {
      const next = action === "buy" ? await client.buy(skin!) : await client.save(draft);
      if (mounted.current && generation.current === version) {
        setData(next);
        if (action === "save") setDraft(next.avatar);
        setNotice(action === "buy" ? "bought" : "saved");
      }
    } catch (e) { if (mounted.current && generation.current === version) setError(e); }
    finally { working.current = false; if (mounted.current && generation.current === version) setBusy(""); }
  }
  const ownsDraft = data?.owned_skins.includes(draft.skin) ?? false;
  const changed = data ? !sameAvatar(data.avatar, draft) : false;
  function select(next: Partial<AvatarConfig>) { setDraft(current => ({ ...current, ...next })); setNotice(""); }
  return <div className={styles.shell} dir={lang === "he" ? "rtl" : "ltr"}>
    <header className={styles.header}><a href="/" className={styles.brand}>JobRun<span>{t("הדמות שלי", "My character")}</span></a><div className={styles.controls}><button type="button" aria-haspopup="dialog" aria-label={t("דיווח על בעיה", "Report a problem")} title={t("דיווח על בעיה", "Report a problem")} onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={18} aria-hidden="true"/></button>{controls}</div></header>
    <main className={styles.main}>
      <div className={styles.topline}><a href={demo ? "/games/preview" : "/games"}><Back size={17}/>{t("לחדר המשחקים", "Back to games")}</a><span><Coins size={18}/>{data ? data.balance : "—"} {t(demo ? "מטבעות הדגמה" : "מטבעות", demo ? "demo coins" : "coins")}</span></div>
      {demo && <aside className={styles.demo}><strong>{t("חנות לדוגמה", "Shop preview")}</strong><span>{t("התאמה ורכישה במטבעות הדגמה בלבד. שום דבר כאן אינו משנה את החשבון שלכם.", "Customization and purchases use demo coins only. Nothing here changes your account.")}</span><a href="/games/shop">{t("לחנות האמיתית", "Open your real shop")}</a></aside>}
      <div className={styles.heading}><div><h1>{t("רכיב קטן. אופי גדול.", "A little logic. A lot of you.")}</h1><p>{t("בוחרים רכיב, מוצאים את הצבע שלכם ויוצאים למשחק עם חולצת Job_Run.", "Pick a component, find your color and join the game in your Job_Run shirt.")}</p></div><Shirt size={34} strokeWidth={1.4} aria-hidden="true"/></div>
      {!!error && <div className={styles.error} role="alert"><span>{errorText(error, lang)}</span><button disabled={!!busy} onClick={() => void refresh()}><RefreshCw size={16}/>{t("רענון החנות", "Refresh shop")}</button></div>}
      {!data && !error && <p role="status">{t("מוקסי מסדר את המדף…", "Muxi is arranging the shelf…")}</p>}
      {data && <>
        {!data.enabled && <p className={styles.warning}>{t("שמירת הדמויות ממתינה להפעלה בשרת. אפשר לנסות את הבחירות כאן, או לפתוח את ההדגמה.", "Character saving is awaiting server activation. You can explore the choices here or open the preview.")} <a href="/games/preview/shop">{t("להדגמה", "Try preview")}</a></p>}
        <section className={styles.editor} aria-label={t("עיצוב הדמות", "Customize your character")}>
          <div className={styles.stage}><div className={styles.characterFrame}><LogicAvatar config={draft} size={300} label={t("תצוגת הדמות שבחרתם", "Preview of your selected character")}/></div><p>{ownsDraft ? changed ? t("הדמות החדשה שלכם — שומרים כשמוכנים.", "Your new look — save when you are ready.") : t("זאת הדמות שלכם. מוכנים לסיבוב?", "That's your character. Ready for a round?") : t("מודדים סקין חדש. רכשו אותו בחנות כדי לשמור.", "Trying a new skin. Buy it below to save this look.")}</p></div>
          <div className={styles.options}>
            <fieldset disabled={!!busy}><legend>{t("איזה רכיב אתם?", "What's your component?")}</legend><div className={styles.components}>{data.components.map(component => <button key={component.key} type="button" aria-pressed={draft.component === component.key} onClick={() => select({ component: component.key })}><LogicAvatar config={{ ...draft, component: component.key }} size={66}/><span>{component.label[lang]}</span>{draft.component === component.key && <Check size={14} className={styles.selectedCheck}/>}</button>)}</div></fieldset>
            <fieldset disabled={!!busy}><legend>{t("הצבע שלכם", "Your color")}</legend><div className={styles.colors}>{data.colors.map(color => <button key={color.key} type="button" aria-label={color.label[lang]} aria-pressed={draft.color === color.key} title={color.label[lang]} onClick={() => select({ color: color.key })}><span style={{ backgroundColor: color.hex }}/>{draft.color === color.key && <Check size={17}/>}</button>)}</div></fieldset>
            <div className={styles.saveRow}><button className={styles.primary} disabled={!!busy || !data.enabled || !ownsDraft || !changed} onClick={() => void change("save")}>{busy === "save" ? t("שומרים…", "Saving…") : t("לשמור את הדמות", "Save character")}</button><span role="status">{notice === "saved" ? t("נשמר. נתראה במשחק!", "Saved. See you in the game!") : !data.enabled ? t("הבחירות כאן לתצוגה בלבד", "Selections are preview-only here") : !changed ? t("השינויים שלכם שמורים", "Your look is saved") : t("יש שינויים שלא נשמרו", "You have unsaved changes")}</span></div>
          </div>
        </section>
        <section className={styles.shop} aria-labelledby="muxi-shop-title">
          <div className={styles.shopWelcome}><div className={styles.seller}><MuxiMascot pose={notice === "bought" ? "celebrate" : "wave"} className={styles.muxi} label={t("מוקסי, המוכר בחנות", "Muxi, your shopkeeper")}/><div className={styles.counter}><ShoppingBag size={22}/><span>MUXI’S</span></div></div><div><h2 id="muxi-shop-title">{t("החנות של מוקסי", "Muxi’s little shop")}</h2><p>{notice === "bought" ? t("בחירה מעולה! הסקין כבר בארון שלכם. עכשיו אפשר ללבוש אותו.", "Excellent choice! Your skin is in the wardrobe. You can wear it now.") : t("״היי! שמרתי לכם כמה דברים יפים. אין פה קיצורי דרך לניצחון — רק עוד קצת אופי.״", "“Hi! I saved you some lovely things. No shortcuts to winning here — just a little more personality.”")}</p><span className={styles.shopNote}><Sparkles size={15}/>{t("סקינים קבועים · אותה יכולת משחק", "Keep your skins · same game skills")}</span></div></div>
          {!data.shop_enabled && <p className={styles.warning}>{t("רכישות ייפתחו אחרי הפעלת החנות ומערכת המטבעות בשרת.", "Purchases open when the shop and coin system are active on the server.")}</p>}
          <div className={styles.shelf}>{data.skins.map(skin => {
            const owned = data.owned_skins.includes(skin.key);
            const wearing = data.avatar.skin === skin.key;
            const trying = draft.skin === skin.key;
            return <article key={skin.key} className={`${styles.product} ${trying ? styles.trying : ""}`}>
              <button className={styles.tryOn} type="button" aria-label={t(`למדוד ${skin.label.he}`, `Try ${skin.label.en}`)} aria-pressed={trying} disabled={!!busy} onClick={() => select({ skin: skin.key })}><LogicAvatar config={{ ...draft, skin: skin.key }} size={192}/><span>{trying ? t("על הדמות שלכם", "On your character") : t("למדידה", "Try it on")}</span></button>
              <div className={styles.productInfo}><h3>{skin.label[lang]}</h3><p>{skin.description[lang]}</p><div className={styles.productBottom}><span className={styles.price}>{owned ? <><Check size={15}/>{wearing ? t("לבוש כרגע", "Wearing") : t("בארון שלכם", "In your wardrobe")}</> : <><Coins size={16}/>{skin.price}</>}</span>{owned ? <button disabled={!!busy || trying} onClick={() => select({ skin: skin.key })}>{trying ? t("נבחר", "Selected") : t("לבחור", "Select")}</button> : <button className={styles.buy} disabled={!!busy || !data.shop_enabled || data.balance < skin.price} onClick={() => void change("buy", skin.key)}>{busy === skin.key ? t("רוכשים…", "Buying…") : data.balance < skin.price ? t("חסרים מטבעות", "Need more coins") : t(`לקנות ב־${skin.price}`, `Buy for ${skin.price}`)}</button>}</div></div>
            </article>;
          })}</div>
          {notice === "bought" && <p role="status" className={styles.purchaseNote}>{t("הסקין נוסף לארון שלכם. בחרו אותו ואז לחצו על ״לשמור את הדמות״.", "The skin is in your wardrobe. Select it, then press Save character.")}</p>}
        </section>
      </>}
      <footer className={styles.footer}>{t("למטבעות אין ערך כספי. אי אפשר לקנות או לפדות אותם. הסקינים אינם משנים ניקוד או סיכויי ניצחון.", "Coins have no monetary value and cannot be bought or cashed out. Skins do not change scores or your chance of winning.")}</footer>
    </main>
  </div>;
}
