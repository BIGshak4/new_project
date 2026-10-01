export const siteDirections = [
  {
    id: "studio",
    name: "סטודיו — האתר המלא",
    description:
      "מרחב לימוד בשמנת ומרווה, עם כותרות עריכתיות וחוויית תרגול שקטה.",
    tradeoff: "כל מסכי האתר, עם נתוני הדגמה ופעולות מקומיות.",
    palette: ["#f7f5f0", "#345b44", "#e7edde"],
  },
  {
    id: "ion",
    name: "יון כהה",
    description:
      "יון המקורי: סגול עמוק, ענבר ושבב מרחבי, לאורך כל חוויית הלמידה.",
    tradeoff: "מסכי התרגול ממשיכים את הזהות הכהה עם משטחי עבודה קריאים.",
    palette: ["#171024", "#b6a0ff", "#ffb85c"],
  },
  {
    id: "ion-light",
    name: "יון שמנת",
    description: "אותו יון, עם רקע שמנת, כתב סגול כהה ומשטחים בהירים.",
    tradeoff: "משמר את האופי הטכנולוגי בסביבה בהירה.",
    palette: ["#faf4e8", "#35204f", "#e7dcf2"],
  },
  {
    id: "ion-adaptive",
    name: "יון בהיר ↔ כהה",
    description: "כפתור שמש וירח מחליף בין יון שמנת ליון כהה בכל מסך.",
    tradeoff: "השאלה, הטיוטה והמצב הנוכחי נשמרים בזמן המעבר.",
    palette: ["#faf4e8", "#35204f", "#171024", "#ffb85c"],
  },
  {
    id: "signal",
    name: "סיגנל",
    description:
      "השראה הנדסית מ־Voltage Learning: גרפיט, טורקיז וזהב, בפריסה מקורית לקהל הישראלי.",
    tradeoff: "ניסוי אותות, עברית וכל מסכי המוצר, בלי להעתיק את אתר המקור.",
    palette: ["#0d1b1d", "#70d6c4", "#f4cb65"],
  },
] as const;
export type SiteStyle = (typeof siteDirections)[number]["id"];
export type Screen =
  | "home"
  | "today"
  | "library"
  | "practice"
  | "interview"
  | "progress"
  | "history"
  | "saved"
  | "profile"
  | "auth"
  | "goal"
  | "help";
export type T = (he: string, en: string) => string;
export const screens: Screen[] = [
  "home",
  "today",
  "library",
  "practice",
  "interview",
  "progress",
  "history",
  "saved",
  "profile",
  "auth",
  "goal",
  "help",
];
type Pair = readonly [string, string];
export type Sample = {
  id: string;
  title: Pair;
  topic: Pair;
  category: "hardware" | "software" | "logic";
  company: string;
  aliases: string;
  minutes: number;
  difficulty: Pair;
  prompt: Pair;
  hints: Pair[];
  solution: Pair;
  language: "c" | "verilog";
  code: string;
};
export const questions: Sample[] = [
  {
    id: "xor",
    title: ["כששני ביטים לא מסכימים", "When two bits disagree"],
    topic: ["לוגיקה קומבינטורית", "Combinational logic"],
    category: "hardware",
    company: "Intel",
    aliases: "אינטל",
    minutes: 15,
    difficulty: ["יסודות", "Foundations"],
    prompt: [
      "תכננו מעגל שמקבל שני ביטים A ו־B ומחזיר 1 רק כאשר הם שונים. כתבו טבלת אמת, ממשו באמצעות AND, OR ו־NOT והסבירו איך הייתם בודקים את המימוש.",
      "Design a circuit with two input bits, A and B, that outputs 1 only when they differ. Write a truth table, implement it with AND, OR and NOT, and explain how you would test it.",
    ],
    hints: [
      [
        "התחילו מארבעת הצירופים האפשריים של A ו־B.",
        "Start with the four possible input combinations.",
      ],
      [
        "המוצא צריך להיות 1 עבור 01 וגם עבור 10.",
        "The output should be 1 for 01 and for 10.",
      ],
      [
        "בנו AND לכל אחד משני המקרים, וחברו את התוצאות באמצעות OR.",
        "Build one AND term for each case, then combine them with OR.",
      ],
    ],
    solution: [
      "Y = (A & ~B) | (~A & B). המוצא הוא 0 עבור 00 ו־11, ו־1 עבור 01 ו־10. במעגל קומבינטורי בן שתי כניסות אפשר לבדוק את כל ארבעת המקרים.",
      "Y = (A & ~B) | (~A & B). The output is 0 for 00 and 11, and 1 for 01 and 10. This two-input combinational circuit can be tested exhaustively with all four cases.",
    ],
    language: "verilog",
    code: "module different_bits (\n  input wire a, b,\n  output wire y\n);\n  // Your implementation\nendmodule",
  },
  {
    id: "array",
    title: ["הבאג בקצה המערך", "The bug at the array boundary"],
    topic: ["תכנות ב־C", "C programming"],
    category: "software",
    company: "Intel",
    aliases: "אינטל",
    minutes: 12,
    difficulty: ["יסודות", "Foundations"],
    prompt: [
      "הפונקציה שלפניכם אמורה לסכום n איברים. מצאו ותקנו את השגיאה, התייחסו ל־n=0 ול־n=1, וציינו את סיבוכיות הזמן והזיכרון. הניחו שאין גלישה של הסכום ושעבור n>0 המערך מכיל n איברים תקינים.",
      "This function should sum n elements. Find and fix the bug, address n=0 and n=1, and state time and space complexity. Assume sums do not overflow and, for n>0, the array contains n valid elements.",
    ],
    hints: [
      [
        "מהו האינדקס האחרון במערך עם n איברים?",
        "What is the last index in an array of n elements?",
      ],
      [
        "כשהלולאה מגיעה ל־i=n, היא כבר מחוץ למערך.",
        "When i=n, the loop is already outside the array.",
      ],
      [
        "שנו את תנאי הלולאה ל־i < n. בדקו מה קורה כשהתנאי נכשל כבר בהתחלה.",
        "Use i < n. Check what happens when the condition is false at the start.",
      ],
    ],
    solution: [
      "התנאי הנכון הוא i < n. עבור n=0 לא ניגשים למערך ומוחזר 0. עבור n=1 נגישים רק ל־a[0]. זמן O(n) וזיכרון נוסף O(1).",
      "The condition must be i < n. For n=0 no element is accessed and 0 is returned. For n=1 only a[0] is read. Time O(n), extra space O(1).",
    ],
    language: "c",
    code: "int sum_samples(const int *a, size_t n) {\n  int total = 0;\n  for (size_t i = 0; i <= n; ++i) {\n    total += a[i];\n  }\n  return total;\n}",
  },
  {
    id: "fsm",
    title: ["מכונה שמזהה את הרצף 101", "A machine that detects 101"],
    topic: ["מכונות מצבים", "Finite-state machines"],
    category: "hardware",
    company: "NVIDIA",
    aliases: "אנבידיה נווידיה נבידיה",
    minutes: 20,
    difficulty: ["ביניים", "Intermediate"],
    prompt: [
      "תכננו מכונת Mealy שמזהה רצף סיביות 101 בזרם כניסה. אפשרו רצפים חופפים. תארו את המצבים והמעברים, הגדירו reset ובדקו את הזרם 10101.",
      "Design a Mealy machine that detects 101 in a bit stream. Allow overlapping matches. Describe states and transitions, define reset and test the stream 10101.",
    ],
    hints: [
      [
        "מצב מייצג את הקידומת שכבר זיהיתם.",
        "A state represents the prefix already matched.",
      ],
      [
        "מספיקים מצבים עבור: שום התאמה, 1, ו־10.",
        "Use states for: no prefix, 1 and 10.",
      ],
      [
        "אחרי זיהוי 101, הסיבית האחרונה יכולה להיות תחילתו של הרצף הבא.",
        "After detecting 101, its final bit can start the next match.",
      ],
    ],
    solution: [
      "S0: על 0 נשארים, על 1 עוברים ל־S1. S1: על 1 נשארים, על 0 עוברים ל־S10. S10: על 0 חוזרים ל־S0; על 1 מוציאים 1 וחוזרים ל־S1. בשאר המעברים המוצא 0. reset ל־S0. ב־10101 מתקבלים זיהויים בסיביות 3 ו־5.",
      "S0: 0 stays, 1 goes to S1. S1: 1 stays, 0 goes to S10. S10: 0 goes to S0; 1 outputs 1 and returns to S1. All other transitions output 0. Reset to S0. In 10101, matches end at bits 3 and 5.",
    ],
    language: "verilog",
    code: "// Define states and next-state logic\n// Allow overlapping matches\n",
  },
  {
    id: "missing",
    title: ["מספר אחד חסר", "One number is missing"],
    topic: ["אלגוריתמים", "Algorithms"],
    category: "software",
    company: "Microsoft",
    aliases: "מיקרוסופט",
    minutes: 15,
    difficulty: ["יסודות", "Foundations"],
    prompt: [
      "מערך מכיל את כל המספרים מ־0 עד n, פרט למספר אחד, ללא כפילויות. מצאו את החסר בזמן ליניארי ובזיכרון נוסף קבוע.",
      "An array contains every integer from 0 to n except one, with no duplicates. Find the missing value in linear time and constant extra space.",
    ],
    hints: [
      [
        "איזו פעולה מבטלת שני ערכים זהים?",
        "Which operation cancels two identical values?",
      ],
      [
        "נסו XOR של כל הטווח ושל כל המערך.",
        "Try XOR of the entire range and of every array element.",
      ],
      [
        "כל ערך שמופיע פעמיים מתאפס. נשאר הערך שלא הופיע במערך.",
        "Every paired value cancels. The missing value remains.",
      ],
    ],
    solution: [
      "מבצעים XOR על 0..n ועל איברי המערך. כל זוג זהה מתאפס, ורק המספר החסר נשאר. זמן O(n), זיכרון נוסף O(1).",
      "XOR 0..n and the array elements together. Equal pairs cancel, leaving the missing value. Time O(n), extra space O(1).",
    ],
    language: "c",
    code: "int missing_number(const int *a, int n) {\n  // Your solution\n}",
  },
  {
    id: "clock",
    title: ["רגע, המחוג לא חיכה", "Wait, the hour hand moved"],
    topic: ["חשיבה לוגית", "Logical reasoning"],
    category: "logic",
    company: "Google",
    aliases: "גוגל",
    minutes: 8,
    difficulty: ["חימום", "Warm-up"],
    prompt: [
      "מהי הזווית הקטנה בין מחוגי השעון בשעה 6:30? הסבירו את דרך החישוב ואת ההנחות.",
      "What is the smaller angle between the hands of a clock at 6:30? Explain your calculation and assumptions.",
    ],
    hints: [
      [
        "גם מחוג השעות נע במהלך חצי השעה.",
        "The hour hand also moves during the half hour.",
      ],
      [
        "מחוג השעות מתקדם בחצי מעלה בכל דקה.",
        "The hour hand moves half a degree each minute.",
      ],
      [
        "מחוג הדקות ב־180° ומחוג השעות ב־195°.",
        "The minute hand is at 180°, the hour hand at 195°.",
      ],
    ],
    solution: [
      "הזווית היא 15°. מחוג השעות נע 6×30+30×0.5=195 מעלות, ומחוג הדקות ב־180 מעלות.",
      "The angle is 15°. The hour hand is at 6×30+30×0.5=195 degrees and the minute hand at 180 degrees.",
    ],
    language: "c",
    code: "// Optional calculation\n",
  },
  {
    id: "popcount",
    title: ["כמה ביטים דולקים?", "How many bits are set?"],
    topic: ["מחברים ומעגלים", "Adders and circuits"],
    category: "hardware",
    company: "Apple",
    aliases: "אפל",
    minutes: 18,
    difficulty: ["ביניים", "Intermediate"],
    prompt: [
      "תכננו מעגל שמקבל שמונה ביטים ומחזיר את מספר האחדות. מהו רוחב המוצא המזערי? הציעו מבנה של עץ מחברים.",
      "Design a circuit that counts the ones in eight input bits. What is the minimum output width? Propose an adder tree.",
    ],
    hints: [
      [
        "המוצא יכול לנוע בין 0 ל־8, כולל.",
        "The output ranges from 0 through 8 inclusive.",
      ],
      [
        "סכמו בזוגות, ואז סכמו את סכומי הביניים.",
        "Sum pairs, then combine the partial sums.",
      ],
      ["כדי לייצג 8 נדרשים ארבעה ביטים.", "Representing 8 requires four bits."],
    ],
    solution: [
      "המוצא בן 4 ביטים. סכמו ארבעה זוגות לתוצאות בנות 2 ביטים, חברו לשתי תוצאות בנות 3 ביטים, ואז לסכום סופי בן 4 ביטים. בדקו אפס אחדות, שמונה אחדות ומקרים מעורבים.",
      "The output needs 4 bits. Sum four pairs into 2-bit results, combine into two 3-bit sums, then a final 4-bit sum. Test zero ones, eight ones and mixed inputs.",
    ],
    language: "verilog",
    code: "module popcount8(input [7:0] x, output [3:0] count);\n  // Add the individual bits\nendmodule",
  },
];
export const categoryLabel = (category: string, t: T) =>
  category === "hardware"
    ? t("חומרה", "Hardware")
    : category === "software"
      ? t("תוכנה", "Software")
      : t("היגיון", "Logic");
