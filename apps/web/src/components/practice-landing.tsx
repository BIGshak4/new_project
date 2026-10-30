"use client";

import Image from "next/image";
import { useEffect, useReducer, useRef, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Code2,
  CircuitBoard,
  Compass,
  MousePointer2,
  MessagesSquare,
} from "lucide-react";
import { SignOff } from "./sign-off";
import { LandingXorControls } from "./landing-xor-controls";
import { LandingCompanyReports } from "./landing-company-reports";
import { LandingTestimonials } from "./landing-testimonials";
import { MuxiMascot } from "./tour/muxi-mascot";
import { INITIAL_LANDING_BITS, landingXorOutput, toggleLandingBit } from "../lib/landing-xor";
import styles from "./practice-landing.module.css";

/** The approved Ion visual, with the production authentication form and actual product capabilities. */
export function PracticeLanding({
  he,
  controls,
  children,
}: {
  he: boolean;
  controls?: ReactNode;
  children: ReactNode;
}) {
  const [bits, toggleBit] = useReducer(toggleLandingBit, INITIAL_LANDING_BITS);
  const signinRef = useRef<HTMLElement>(null);
  useEffect(() => {
    // Authentication resolves before this section mounts, after native fragment scrolling.
    if (window.location.hash === "#signin") signinRef.current?.scrollIntoView({ block: "start" });
  }, []);
  const t = (hebrew: string, english: string) => (he ? hebrew : english);
  const Arrow = he ? ArrowLeft : ArrowRight;
  return (
    <div className="ion-landing">
      <header className={`topnav ion-landing-nav ${styles.landingNav}`}>
        <a href="/" className="wordmark" dir="ltr">
          <span>.</span>jobrun
        </a>
        <nav className={styles.landingNavigation} aria-label={t("ניווט", "Navigation")}>
          <a href="#how-it-works">{t("איך מתרגלים", "How it works")}</a>
          <a href="#signin">{t("הרשמה וכניסה", "Sign up / Sign in")}</a>
          <a className={styles.navTour} href="/tour">
            <Compass size={17} aria-hidden="true" />
            <span>{t("סיור עם מוקסי", "Tour with Muxi")}</span>
          </a>
        </nav>
        <div className="topnav-actions">{controls}</div>
      </header>
      <main>
        <section className="ion-hero">
          <div className="ion-hero-copy">
            <h1>
              {t("הרעיון הבא", "Your next idea")}
              <br />
              <em>{t("מתחיל אצלך.", "starts here.")}</em>
            </h1>
            <p>
              {t(
                "הכנה לראיונות חומרה ותוכנה, בעברית ובאנגלית. לתרגל את הידע. להסביר את הדרך. להגיע עם ביטחון.",
                "Hardware and software interview preparation, in Hebrew and English. Practice your knowledge. Explain your reasoning. Arrive with confidence.",
              )}
            </p>
            <div className="ion-hero-actions">
              <a className="primary" href="#signin">
                {t("יצירת חשבון או כניסה", "Sign up or sign in")}{" "}
                <Arrow size={20} />
              </a>
              <a className={styles.tourButton} href="/tour" aria-describedby="landing-tour-description">
                <Compass size={20} aria-hidden="true" />
                {t("סיור עם מוקסי", "Tour with Muxi")}
              </a>
            </div>
            <p id="landing-tour-description" className={styles.tourDescription}>
              {t(
                "מכירים את האתר לפני שנרשמים: מוקסי מדגים את הכלים ואתם מתנסים. ללא הרשמה.",
                "Explore before signing up: Muxi demonstrates the tools and you try them. No account needed.",
              )}
            </p>
            <div className="ion-hero-topics">
              <span dir="ltr">Digital design</span>
              <span dir="ltr">C / C++</span>
              <span>{t("חשיבה לוגית", "Problem solving")}</span>
            </div>
            <LandingCompanyReports he={he} className={styles.companyReports} />
          </div>
          <div className={`ion-art ${styles.binaryArt}`}>
            <div className="ion-chip-scene">
              <i className="ion-orbit" aria-hidden="true" />
              <i className="ion-orbit two" aria-hidden="true" />
              <div className={`ion-chip ${styles.chip}`}>
                <Image
                  src="/design-worlds/ion-chip.png"
                  alt={t(
                    "שבב סיליקון סגול עם מגעים מתכתיים",
                    "Violet silicon chip with metallic contacts",
                  )}
                  fill
                  sizes="(max-width:700px) 310px, 460px"
                  priority
                />
                <strong aria-hidden="true">{landingXorOutput(bits)}</strong>
              </div>
            </div>
            <p className={styles.xorHint} id="landing-xor-hint">
              <MousePointer2 size={18} aria-hidden="true" />
              <span>{t("נסו בעצמכם: לחצו על A או B וראו איך תוצאת ה־XOR משתנה.", "Try it: toggle A or B and watch the XOR output change.")}</span>
            </p>
            <LandingXorControls bits={bits} he={he} onToggle={toggleBit} className={styles.binaryControls} descriptionId="landing-xor-hint" />
          </div>
        </section>
        <section className="ion-home-flow" id="how-it-works">
          <h2>
            {t("מהשאלה הראשונה,", "From your first question,")}
            <br />
            {t("עד לרגע שהכול מתחבר.", "to the moment it clicks.")}
          </h2>
          <div>
            <article>
              <Code2 size={25} />
              <h3>{t("נותנים למחשבה מקום", "Make room for thought")}</h3>
              <p>
                {t(
                  "כותבים הסבר וקוד, משרטטים מעגל או מצרפים פתרון בכתב יד. רמזים מדורגים עוזרים כשנתקעים.",
                  "Explain your reasoning, write code, draw a circuit or attach a handwritten answer. Progressive hints help when you get stuck.",
                )}
              </p>
            </article>
            <article>
              <CircuitBoard size={25} />
              <h3>{t("לומדים לפי היעד שלכם", "Learn toward your goal")}</h3>
              <p>
                {t(
                  "מגדירים תפקיד, תאריך וזמן יומי. התוכנית והתרגול עוזרים להתמקד במיומנויות שצריך לחזק.",
                  "Choose a role, interview date and daily time. Your plan helps focus practice on the skills that need work.",
                )}
              </p>
            </article>
            <article>
              <MessagesSquare size={25} />
              <h3>{t("מתכוננים לרגע האמת", "Get ready for the interview")}</h3>
              <p>
                {t(
                  "מתרגלים גם ראיון מדומה, חוזרים למשוב ורואים את הדרך שעשיתם. המשובים בפיילוט נבדקים ומשתפרים.",
                  "Practice a mock interview, revisit feedback and see your progress. Pilot feedback is being reviewed and improved.",
                )}
              </p>
            </article>
          </div>
        </section>
        <section className={`ion-signin ${styles.signinSection}`} id="signin" ref={signinRef}>
          <div className={styles.signinIntro}>
            <h2>{t("הצעד הבא שלכם.", "Your next step.")}</h2>
            <p>
              {t(
                "נכנסים, בוחרים יעד ומתחילים משאלה אחת. החשבון שומר את התרגול וההתקדמות שלכם.",
                "Sign in, choose a goal and start with one question. Your account keeps your practice and progress together.",
              )}
            </p>
            <p className="muted small">
              {t(
                "כרגע בפיילוט פרטי לחברים שהוזמנו.",
                "Currently a private pilot for invited members.",
              )}
            </p>
          </div>
          <div className={styles.signinTour}>
              <MuxiMascot className={styles.tourMascot} />
              <div>
                <h3>{t("רוצים להכיר לפני שנרשמים?", "Want to explore before signing up?")}</h3>
                <p>{t("מוקסי ילווה אתכם בהדגמות של התרגול, כתיבת קוד, בניית מעגלים ומשוב. אפשר להתנסות בלי חשבון ולבחור סיור קצר או מעמיק.", "Let Muxi show you practice, coding, circuit building and feedback. Try the tools without an account, with a short or in-depth tour.")}</p>
                <a className={styles.tourButton} href="/tour">
                  {t("לסיור עם מוקסי — ללא הרשמה", "Tour with Muxi — no account needed")}
                  <Arrow size={18} aria-hidden="true" />
                </a>
              </div>
          </div>
          {children}
        </section>
        <LandingTestimonials he={he} className={styles.testimonials} />
      </main>
      <SignOff lang={he ? "he" : "en"} />
    </div>
  );
}
