"use client";

import Image from "next/image";
import { useState, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Code2,
  CircuitBoard,
  MessagesSquare,
} from "lucide-react";
import { SignOff } from "./sign-off";

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
  const [a, setA] = useState(0),
    [b, setB] = useState(1);
  const t = (hebrew: string, english: string) => (he ? hebrew : english);
  const Arrow = he ? ArrowLeft : ArrowRight;
  return (
    <div className="ion-landing">
      <header className="topnav ion-landing-nav">
        <a href="/" className="wordmark" dir="ltr">
          <span>.</span>jobrun
        </a>
        <nav aria-label={t("ניווט", "Navigation")}>
          <a href="#how-it-works">{t("איך מתרגלים", "How it works")}</a>
          <a href="#signin">{t("כניסה לתרגול", "Sign in")}</a>
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
                {t("בואו נמצא את הכיוון שלכם", "Find your starting point")}{" "}
                <Arrow size={20} />
              </a>
              <a className="text-button" href="#how-it-works">
                {t("איך זה עובד?", "How does it work?")}
              </a>
            </div>
            <div className="ion-hero-topics">
              <span dir="ltr">Digital design</span>
              <span dir="ltr">C / C++</span>
              <span>{t("חשיבה לוגית", "Problem solving")}</span>
            </div>
          </div>
          <div className="ion-art">
            <div className="ion-chip-scene">
              <i className="ion-orbit" aria-hidden="true" />
              <i className="ion-orbit two" aria-hidden="true" />
              <div className="ion-chip">
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
                <strong aria-hidden="true">{a ^ b}</strong>
              </div>
            </div>
            <div className="ion-inputs" dir="ltr">
              <button
                onClick={() => setA(1 - a)}
                aria-label={`A: ${a}`}
                aria-pressed={a === 1}
              >
                A <b>{a}</b>
              </button>
              <button
                onClick={() => setB(1 - b)}
                aria-label={`B: ${b}`}
                aria-pressed={b === 1}
              >
                B <b>{b}</b>
              </button>
              <span>
                Y = <output aria-live="polite">{a ^ b}</output>
              </span>
            </div>
            <p>
              {t(
                "שני קלטים. לחצו ושנו את התוצאה.",
                "Two inputs. Tap to change the output.",
              )}
            </p>
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
        <section className="ion-signin" id="signin">
          <div>
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
          {children}
        </section>
      </main>
      <SignOff lang={he ? "he" : "en"} />
    </div>
  );
}
