"use client";

/**
 * Hand-drawn sketches, one per subject, in the bench's ink. Wobbly lines come from a turbulence displacement
 * filter, so the drawing looks made with a pen rather than a plotter. Decorative: always aria-hidden, with the
 * caption (when any) in the coach's handwriting.
 */
const FAMILY: Record<string, "mux" | "fsm" | "clock" | "adder" | "hdl" | "code" | "notes"> = {
  digital_fundamentals: "mux",
  digital_logic: "mux",
  digital_design: "hdl",
  sequential_logic: "clock",
  fsms: "fsm",
  relevant_programming: "code",
  programming: "code",
  software_fundamentals: "code",
  reasoning: "notes",
  problem_solving: "notes",
  communication: "notes",
  projects_behavioral: "notes",
};

export function sketchFor(subject: string | null | undefined): keyof typeof DRAWINGS {
  return FAMILY[subject ?? ""] ?? "mux";
}

const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 2.2, strokeLinecap: "round", strokeLinejoin: "round" } as const;
const label = { fontFamily: "'Amatic SC', cursive", fontWeight: 700, fontSize: 13, fill: "currentColor", stroke: "none" } as const;

const DRAWINGS = {
  mux: (
    <>
      <path d="M52 14 L100 30 L100 90 L52 106 Z" />
      <path d="M20 30 H52 M20 50 H52 M20 70 H52 M20 90 H52" />
      <path d="M100 60 H132" />
      <path d="M70 106 V116 M84 106 V116" />
      <text x="24" y="26" {...label}>d0</text>
      <text x="24" y="86" {...label}>d3</text>
      <text x="66" y="119" {...label} textAnchor="end">s1 s0</text>
    </>
  ),
  fsm: (
    <>
      <circle cx="40" cy="60" r="24" />
      <circle cx="112" cy="60" r="24" />
      <path d="M62 50 Q76 30 90 50" />
      <path d="M86 44 L90 50 L84 52" />
      <path d="M90 70 Q76 90 62 70" />
      <path d="M66 76 L62 70 L68 68" />
      <path d="M8 32 L16 40" />
      <text x="40" y="64" {...label} textAnchor="middle">S0</text>
      <text x="112" y="64" {...label} textAnchor="middle">S1</text>
      <text x="76" y="26" {...label} textAnchor="middle">in=1</text>
    </>
  ),
  clock: (
    <>
      <path d="M10 40 H30 V16 H60 V40 H90 V16 H120 V40 H140" />
      <path d="M10 88 H48 V72 H140" />
      <path d="M60 50 V96" strokeDasharray="4 4" />
      <path d="M48 60 H60 M52 56 L48 60 L52 64" />
      <path d="M60 60 H72 M68 56 L72 60 L68 64" />
      <text x="54" y="112" {...label} textAnchor="middle">tsu   th</text>
      <text x="8" y="12" {...label}>clk</text>
      <text x="8" y="70" {...label}>d</text>
    </>
  ),
  adder: (
    <>
      <path d="M20 40 H50 V80 H20 Z M70 40 H100 V80 H70 Z M120 40 H140" />
      <path d="M50 60 H70" />
      <path d="M35 22 V40 M85 22 V40" />
      <path d="M35 80 V98 M85 80 V98" />
      <text x="35" y="64" {...label} textAnchor="middle">FA</text>
      <text x="85" y="64" {...label} textAnchor="middle">FA</text>
      <text x="60" y="54" {...label} textAnchor="middle">c</text>
    </>
  ),
  hdl: (
    <>
      <path d="M22 22 H130" />
      <path d="M30 44 H110 M30 62 H96 M30 80 H118" />
      <path d="M14 34 Q10 60 14 90" />
      <path d="M136 34 Q140 60 136 90" />
      <text x="24" y="18" {...label}>always @(posedge clk)</text>
      <text x="30" y="106" {...label}>end</text>
    </>
  ),
  code: (
    <>
      <path d="M16 40 H136 V78 H16 Z" />
      <path d="M40 40 V78 M64 40 V78 M88 40 V78 M112 40 V78" />
      <path d="M76 100 V84 M70 90 L76 84 L82 90" />
      <text x="28" y="64" {...label} textAnchor="middle">3</text>
      <text x="52" y="64" {...label} textAnchor="middle">1</text>
      <text x="76" y="64" {...label} textAnchor="middle">4</text>
      <text x="100" y="64" {...label} textAnchor="middle">1</text>
      <text x="124" y="64" {...label} textAnchor="middle">5</text>
      <text x="76" y="114" {...label} textAnchor="middle">i</text>
    </>
  ),
  notes: (
    <>
      <path d="M30 16 H120 V108 H30 Z" />
      <path d="M44 40 H106 M44 58 H98 M44 76 H104" />
      <path d="M36 40 L40 44 L46 36 M36 58 L40 62 L46 54" />
      <path d="M36 76 H46" />
    </>
  ),
};

export function SubjectSketch({ subject, caption, className }: { subject: string | null | undefined; caption?: string; className?: string }) {
  const kind = sketchFor(subject);
  const id = `wob-${kind}`;
  return (
    <div className={`sketch ${className ?? ""}`} aria-hidden="true">
      <svg viewBox="0 0 150 122" {...stroke}>
        <filter id={id}>
          <feTurbulence baseFrequency="0.035" numOctaves="2" seed="7" />
          <feDisplacementMap in="SourceGraphic" scale="2.2" />
        </filter>
        <g filter={`url(#${id})`}>{DRAWINGS[kind]}</g>
      </svg>
      {caption && <div className="sketch-cap hand">{caption}</div>}
    </div>
  );
}

/** The handwritten caption that goes with each sketch. */
export function sketchCaption(subject: string | null | undefined, lang: "he" | "en"): string {
  const kind = sketchFor(subject);
  const he: Record<typeof kind, string> = {
    mux: "או עץ של MUX2?",
    fsm: "מור או מילי?",
    clock: "איפה נסגר ה־setup?",
    adder: "מאיפה מגיע ה־carry?",
    hdl: "blocking או לא?",
    code: "מה קורה ב־i האחרון?",
    notes: "קודם הנחות, אחר כך תשובה",
  };
  const en: Record<typeof kind, string> = {
    mux: "or a tree of MUX2s?",
    fsm: "Moore or Mealy?",
    clock: "where does setup close?",
    adder: "where does the carry come from?",
    hdl: "blocking or not?",
    code: "what happens at the last i?",
    notes: "assumptions first, then the answer",
  };
  return (lang === "he" ? he : en)[kind];
}
