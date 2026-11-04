import { BookOpen, Gamepad2, Map, MessageSquareText, ShoppingBag } from "lucide-react";
import type { AvatarLanguage } from "../../lib/avatar-types";
import styles from "./feature-nav.module.css";

export type PracticeDestination = "learn" | "library" | "interview";
export type FeatureDestination = PracticeDestination | "games" | "shop";

export function FeatureNav({ lang, demo = false, current, onPracticeNavigate, className, variant = "header" }: {
  lang: AvatarLanguage; demo?: boolean;
  current?: FeatureDestination; onPracticeNavigate?: (view: PracticeDestination) => void;
  className?: string; variant?: "header" | "bottom";
}) {
  const he = lang === "he", base = demo ? "/games/preview" : "/games";
  const items = [
    { id: "learn", icon: Map, href: "/", label: he ? "אזור אישי" : "Personal area" },
    { id: "library", icon: BookOpen, href: "/?view=library&nav=1", label: he ? "מאגר" : "Library" },
    { id: "interview", icon: MessageSquareText, href: "/?view=interview&nav=1", label: he ? "ראיון מדומה" : "Mock interview" },
    { id: "games", icon: Gamepad2, href: base, label: he ? "משחקים" : "Games" },
    { id: "shop", icon: ShoppingBag, href: `${base}/shop`, label: he ? "החנות של מוקסי" : "Muxi's shop" },
  ] as const;
  return <nav className={[styles.nav, variant === "bottom" ? styles.bottom : styles.header, className].filter(Boolean).join(" ")} aria-label={he ? "ניווט ראשי" : "Main navigation"}>
    {items.map(({ id, icon: Icon, href, label }) => <a key={id} className={`tab ${current === id ? "active" : ""}`} href={href} aria-current={current === id ? "page" : undefined}
      onClick={event => {
        if (onPracticeNavigate && ["learn", "library", "interview"].includes(id) && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey && event.button === 0) {
          event.preventDefault(); onPracticeNavigate(id as PracticeDestination);
        }
      }}><Icon size={variant === "bottom" ? 21 : 18} aria-hidden="true" /><span>{label}</span></a>)}
  </nav>;
}
