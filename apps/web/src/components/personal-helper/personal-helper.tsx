"use client";

import dynamic from "next/dynamic";
import { BidiText } from "../bidi-text";
import { proseDirection } from "../../lib/bidi-segments";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, ArrowRight, ChevronLeft, ChevronRight, ExternalLink, House, MessageCircle, X } from "lucide-react";
import { observeAuthUser } from "../../lib/auth-access";
import { supabase } from "../../lib/supabase";
import { helperDestinations, helperTargets, helperTopics, type HelperAction, type HelperChoice, type HelperText, type HelperTopicId } from "../../lib/personal-helper";
import { openSupportReport } from "../../lib/support-report";
import { openUserInbox } from "../../lib/user-inbox";
import { LogicAvatar } from "../wardrobe/logic-avatar";
import { ThemeToggle } from "../ui/theme-toggle";
import { useHelperAvatar } from "./use-helper-avatar";
import styles from "./personal-helper.module.css";

const MuxiTour = dynamic(() => import("../tour/muxi-tour").then(module => module.MuxiTour), {
  ssr: false,
  loading: () => <p className={styles.tourLoading} role="status">טוענים את הסיור… / Loading the tour…</p>,
});
type Lang = "he" | "en";
type Turn = { topic: HelperTopicId; selected?: HelperText };

/** A separate surface: it never modifies the workspace header or unmounts an answer. */
export function PersonalHelper() {
  const pathname = usePathname();
  const [userId, setUserId] = useState<string>();
  const [lang, setLang] = useState<Lang>("he");
  useEffect(() => observeAuthUser(supabase.auth, user => setUserId(user?.id)), []);
  useEffect(() => {
    const sync = () => setLang(document.documentElement.lang.startsWith("en") ? "en" : "he");
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    return () => observer.disconnect();
  }, []);
  const demo = pathname.startsWith("/games/preview");
  const visible = pathname === "/" || pathname === "/games" || pathname === "/games/shop" || demo || pathname.startsWith("/duel/");
  if (!visible) return null;
  return <HelperConversation key={`${userId ?? "visitor"}:${demo}`} userId={userId} demo={demo} lang={lang} />;
}

function HelperConversation({ userId, demo, lang }: { userId?: string; demo: boolean; lang: Lang }) {
  // Every fresh visit starts minimized; opening the helper is always an explicit choice.
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([{ topic: "root" }]);
  const [notice, setNotice] = useState<HelperText | null>(null);
  const [tourOpen, setTourOpen] = useState(false);
  const { avatar, status } = useHelperAvatar(userId, demo);
  const launcher = useRef<HTMLButtonElement>(null);
  const currentHeading = useRef<HTMLHeadingElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const currentTurn = useRef<HTMLDivElement>(null);
  const id = useId();
  const he = lang === "he";
  const topic = helperTopics[turns.at(-1)!.topic];
  const t = (hebrew: string, english: string) => he ? hebrew : english;

  useEffect(() => {
    if (!open) return;
    currentHeading.current?.focus({ preventScroll: true });
    if (body.current && currentTurn.current) body.current.scrollTop = currentTurn.current.offsetTop;
  }, [open, turns]);

  function minimize(restoreFocus = true) {
    setOpen(false);
    if (restoreFocus) requestAnimationFrame(() => launcher.current?.focus({ preventScroll: true }));
  }

  function goTo(choice: HelperChoice) {
    setNotice(null);
    if (choice.topic) setTurns(previous => [...previous, { topic: choice.topic!, selected: choice.label }]);
    else if (choice.action) act(choice.action);
  }

  function act(action: HelperAction) {
    if (action.type === "support" || action.type === "inbox") {
      // The native modal restores focus to a persistent, visible launcher on close.
      minimize();
      requestAnimationFrame(() => {
        if (action.type === "support") openSupportReport(action.category);
        else openUserInbox();
      });
      return;
    }
    if (action.type === "tour") {
      minimize();
      requestAnimationFrame(() => setTourOpen(true));
      return;
    }
    if (action.type === "focus") {
      const target = helperTargets[action.target].split(",")
        .flatMap(selector => [...document.querySelectorAll<HTMLElement>(selector.trim())])
        .find(element => !element.closest("[inert], [hidden], [data-muxi-station]") && !element.matches(":disabled") && element.getClientRects().length > 0);
      if (!target) {
        setNotice({
          he: "הכלי הזה לא פתוח בעמוד הנוכחי. פתחו שאלה מתאימה במאגר והתחילו תרגול, או בחרו בסיור כדי להתנסות בו. אפשר לחזור אליי גם מתוך השאלה.",
          en: "This tool isn’t open on the current page. Open a suitable library question and start practicing, or try it in the tour. I’ll be here inside the question, too.",
        });
        return;
      }
      minimize(false);
      requestAnimationFrame(() => {
        const control = target.matches("button, input, textarea, select, [contenteditable=true], [tabindex]")
          ? target : target.querySelector<HTMLElement>("button, textarea, input, [contenteditable=true], [tabindex]") ?? target;
        if (!control.matches("button, input, textarea, select, [contenteditable=true], [tabindex]")) {
          control.tabIndex = -1;
          control.addEventListener("blur", () => control.removeAttribute("tabindex"), { once: true });
        }
        target.scrollIntoView({ block: "center", behavior: "instant" });
        control.focus({ preventScroll: true });
      });
    }
  }

  function href(action: Extract<HelperAction, { type: "navigate" }>) {
    if (demo && action.destination === "games") return "/games/preview";
    if (demo && action.destination === "shop") return "/games/preview/shop";
    return helperDestinations[action.destination];
  }

  return <>
    <div className={styles.dock} dir={he ? "rtl" : "ltr"} lang={lang} data-personal-helper>
      {!open ? <button ref={launcher} type="button" className={styles.launcher} onClick={() => setOpen(true)}
        aria-label={t("פתיחת העוזר האישי", "Open personal helper")} aria-haspopup="dialog" aria-expanded={false} aria-controls={`${id}-panel`}>
        <LogicAvatar config={avatar} size={70} />
        <span><MessageCircle size={17} aria-hidden="true" />{t("צריכים עזרה?", "Need a hand?")}</span>
      </button> : <section role="dialog" aria-modal={false} id={`${id}-panel`} aria-labelledby={`${id}-title`} className={styles.panel}
        onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); minimize(); } }}>
        <header className={styles.header}>
          <LogicAvatar config={avatar} size={60} />
          <div><h2 id={`${id}-title`}>{t("העוזר האישי", "Your site helper")}</h2>
            <p>{t("מכירים את האתר, צעד אחר צעד", "One step at a time, together")}</p></div>
          <button type="button" className={styles.iconButton} onClick={() => minimize()} aria-label={t("מזעור העוזר", "Minimize helper")}><X size={20} aria-hidden="true" /></button>
        </header>
        <div ref={body} className={styles.body}>
          {turns.map((turn, index) => {
            const item = helperTopics[turn.topic];
            const current = index === turns.length - 1;
            return <div key={`${index}-${turn.topic}`} ref={current ? currentTurn : undefined} className={styles.turn}>
              {turn.selected && <p className={styles.userMessage} dir={proseDirection(turn.selected[lang], he ? "rtl" : "ltr")}><BidiText>{turn.selected[lang]}</BidiText></p>}
              <div className={styles.reply}>
                <h3 tabIndex={-1} ref={current ? currentHeading : undefined} dir={proseDirection(item.title[lang], he ? "rtl" : "ltr")}><BidiText>{item.title[lang]}</BidiText></h3>
                {item.messages.map((message, i) => <p key={i} dir={proseDirection(message[lang], he ? "rtl" : "ltr")}><BidiText>{message[lang]}</BidiText></p>)}
              </div>
            </div>;
          })}
          <div className={styles.choices} role="group" aria-label={t("איך ממשיכים?", "What would you like to do?")}>
            {topic.choices.map((choice, index) => choice.action?.type === "navigate"
              ? <a key={index} className={styles.choice} href={href(choice.action)} target="_blank" rel="noopener" referrerPolicy="same-origin">
                  <span><BidiText>{choice.label[lang]}</BidiText><small>{t("פתיחה בלשונית חדשה", "Opens in a new tab")}</small></span><ExternalLink size={16} aria-hidden="true" />
                </a>
              : <button key={index} type="button" className={styles.choice} onClick={() => goTo(choice)}>
                  <span><BidiText>{choice.label[lang]}</BidiText></span>{he ? <ChevronLeft size={18} aria-hidden="true" /> : <ChevronRight size={18} aria-hidden="true" />}
                </button>)}
          </div>
          {notice && <div className={styles.notice} role="status"><p dir={proseDirection(notice[lang], he ? "rtl" : "ltr")}><BidiText>{notice[lang]}</BidiText></p><button type="button" onClick={() => act({ type: "tour" })}>{t("להתנסות בסיור", "Try the tour")}</button></div>}
          {turns.length === 1 && <p className={styles.caption}>{t("בוחרים נושא, ואני אכוון אתכם לכלים המתאימים.", "Choose a topic and I’ll help you find the right tools.")}</p>}
          {status === "fallback" && userId && <p className={styles.caption}>{t("הדמות האישית לא זמינה כרגע. העזרה עדיין כאן.", "Your avatar is unavailable right now. You can still use the helper.")}</p>}
        </div>
        <footer className={styles.footer}>
          <button type="button" disabled={turns.length === 1} onClick={() => { setNotice(null); setTurns(previous => previous.slice(0, -1)); }}>
            {he ? <ArrowRight size={16} aria-hidden="true" /> : <ArrowLeft size={16} aria-hidden="true" />}{t("צעד אחורה", "Go back")}
          </button>
          <button type="button" disabled={turns.length === 1} onClick={() => { setNotice(null); setTurns([{ topic: "root" }]); }}><House size={16} aria-hidden="true" />{t("כל הנושאים", "All topics")}</button>
        </footer>
      </section>}
    </div>
    {tourOpen && createPortal(<div role={!userId ? "dialog" : undefined} aria-modal={!userId ? true : undefined} aria-label={!userId ? t("סיור עם מוקסי", "Tour with Muxi") : undefined}>
      <MuxiTour lang={lang} userId={userId} standalone={!userId} controls={<ThemeToggle lang={lang} />}
        onClose={() => { setTourOpen(false); requestAnimationFrame(() => launcher.current?.focus({ preventScroll: true })); }} />
    </div>, document.body)}
  </>;
}
