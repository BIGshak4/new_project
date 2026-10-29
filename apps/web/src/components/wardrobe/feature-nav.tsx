import { Gamepad2, ShoppingBag } from "lucide-react";
import { LogicAvatar } from "./logic-avatar";
import { DEFAULT_AVATAR, type AvatarConfig, type AvatarLanguage } from "../../lib/avatar-types";
import styles from "./feature-nav.module.css";

export function FeatureNav({ lang, avatar, hideAvatar = false, demo = false, current }: { lang: AvatarLanguage; avatar?: AvatarConfig | null; hideAvatar?: boolean; demo?: boolean; current?: "games" | "shop" }) {
  const he = lang === "he", base = demo ? "/games/preview" : "/games";
  return <nav className={styles.nav} aria-label={he ? "משחקים, חנות והדמות שלי" : "Games, shop and my character"}>
    <a href={base} aria-current={current === "games" ? "page" : undefined}><Gamepad2 size={18} aria-hidden="true" /><span>{he ? "משחקים" : "Games"}</span></a>
    <a href={`${base}/shop`} aria-current={current === "shop" ? "page" : undefined}><ShoppingBag size={18} aria-hidden="true" /><span>{he ? "החנות של מוקסי" : "Muxi's shop"}</span></a>
    {!hideAvatar && <a className={styles.identity} href={`${base}/shop#my-character`} aria-label={he ? "הדמות שלי — עיצוב חינמי" : "My character — free customization"} title={he ? "הדמות שלי" : "My character"}><LogicAvatar config={avatar ?? DEFAULT_AVATAR} size={56} /></a>}
  </nav>;
}
