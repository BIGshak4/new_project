import type { AvatarLanguage } from "../../lib/avatar-types";

export const MEME_SKINS = new Set(["negative_feedback", "works_on_my_machine", "binary_people", "gate_keeper", "sleep_not_found", "resistance_futile"]);

const lines = [
  ["מה תרצו לקנות? החולצות עברו בדיקת תקינות. כמעט כמו הקוד שלכם.", "What can I get you? Every shirt passes a sanity check. Almost like your code."],
  ["יש מידות מ־0 ועד 1. אל תדאגו, מצאנו דרך לייצג גם אתכם.", "Sizes run from 0 to 1. Don't worry, we found a way to represent you too."],
  ["החולצות מגיעות בלי באגים. את אלה תצטרכו להביא מהבית.", "Our shirts ship without bugs. You'll have to bring your own."],
  ["אפשר למדוד חופשי. אצלי רק המחירים קבועים — לא המשתנים.", "Try anything on. Around here only the prices are constants."],
  ["כביסה ב־30 מעלות. קומפילציה בטמפרטורת החדר.", "Wash at 30 degrees. Compile at room temperature."],
  ["הסקינים לא משפרים את הציון. את מצב הרוח? יש סיכוי טוב.", "Skins won't improve your score. Your mood? That's a different story."],
];

export function muxiShopLine(lang: AvatarLanguage, turn: number, context?: "bought" | "saved" | "short") {
  const index = lang === "he" ? 0 : 1;
  if (context === "bought") return ["בחירה מעולה! הוספתי לארון. היא לא תפתור לכם באגים, אבל תיראו מצוין בזמן שתנסו.", "Great choice! It's in your wardrobe. It won't fix your bugs, but you'll look excellent while trying."][index];
  if (context === "saved") return ["זהו, הלוק נשמר! לכו להראות להם מי הרכיב הכי חד במעגל.", "Your look is saved! Go show them the sharpest component in the circuit."][index];
  if (context === "short") return ["הארנק עוד בטעינה. בינתיים אפשר למדוד, ולחזור עם מטבעות מהתרגול.", "Your wallet is still charging. Try it on, then come back with coins from practice."][index];
  return lines[((turn % lines.length) + lines.length) % lines.length][index];
}
