import { useId } from "react";

const MEMES = new Set(["negative_feedback", "works_on_my_machine", "binary_people", "gate_keeper", "sleep_not_found", "resistance_futile"]);
export function shirtPalette(skin: string) {
  const dark = MEMES.has(skin) || skin === "cosmic";
  return { fabric: dark ? "#242438" : "#f2f6f4", ink: dark ? "#fff3cd" : "#35204f", collar: dark ? "#3a3850" : "#d7e3de", seam: dark ? "#8c87a4" : "#9caea6" };
}

/** Shared technical shirt graphics: the worn version and the merchandise zoom use the same drawing. */
export function PrintArtwork({ skin, compact = false }: { skin: string; compact?: boolean }) {
  const ink = shirtPalette(skin).ink;
  const accent = skin === "negative_feedback" || skin === "resistance_futile" ? "#f3c85f" : "#a9e4cf";
  const text = { fill: ink, fontFamily: "Arial, sans-serif", fontWeight: 800, textAnchor: "middle" as const, direction: "ltr" as const, stroke: "none" };
  // Small avatars communicate a distinct emblem; the merchandise view retains the complete joke.
  if (compact && MEMES.has(skin)) {
    if (skin === "negative_feedback") return <g data-print-symbol="negative-feedback"><text {...text} fill={accent} x="50" y="55" fontSize="42">−FB</text></g>;
    if (skin === "works_on_my_machine") return <g data-print-symbol="terminal"><g stroke={accent} strokeWidth="4" fill="none" strokeLinejoin="round"><rect x="8" y="8" width="84" height="54" rx="5"/><path d="M3 68H97L87 75H13Z"/></g><text {...text} fill={accent} x="50" y="48" fontSize="35" fontFamily="monospace">&gt;_</text></g>;
    if (skin === "binary_people") return <g data-print-symbol="binary"><text {...text} fill={accent} x="50" y="61" fontSize="62" fontFamily="monospace">01</text></g>;
    if (skin === "gate_keeper") return <g data-print-symbol="and"><text {...text} fill={accent} x="50" y="54" fontSize="39">AND</text></g>;
    if (skin === "sleep_not_found") return <g data-print-symbol="404"><text {...text} fill="#c2b3f5" x="50" y="57" fontSize="52">404</text></g>;
    return <g data-print-symbol="resistance"><text {...text} fill={accent} x="50" y="57" fontSize="61">Ω</text><path d="M13 69H25l4-5 7 10 7-10 7 10 7-10 7 10 7-10 4 5H87" fill="none" stroke={accent} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/></g>;
  }
  if (skin === "negative_feedback") return <g>
    <text {...text} x="50" y="9" fontSize="8">I ONLY GIVE</text><text {...text} x="50" y="19" fontSize="7.5">NEGATIVE FEEDBACK</text>
    <g fill="none" stroke={accent} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M42 34 66 47 42 60Z"/><path d="M7 39H15l2-3 3 6 3-6 3 6 3-6 2 3H42M66 47H92M34 39V26H43l2-3 3 6 3-6 3 6 3-6 2 3H77V47M31 55H42M31 55V67M24 67H38M27 70H35M30 73H32"/><circle cx="34" cy="39" r="1.8" fill={accent}/><circle cx="77" cy="47" r="1.8" fill={accent}/></g>
    <g fill={accent} fontFamily="Arial, sans-serif" fontSize="5.5" fontWeight="700" stroke="none"><text x="45" y="41">−</text><text x="45" y="57">+</text><text x="7" y="49">IN</text><text x="81" y="58">OUT</text><text x="19" y="33">R1</text><text x="48" y="33">R2</text></g>
  </g>;
  if (skin === "works_on_my_machine") return <g><text {...text} x="50" y="11" fontSize="8.5">WORKS ON</text><text {...text} x="50" y="23" fontSize="8.5">MY MACHINE</text><g stroke={accent} strokeWidth="2" fill="none" strokeLinejoin="round"><rect x="23" y="32" width="54" height="31" rx="3"/><path d="M16 67H84L78 72H22Z"/><path d="m35 42 7 6-7 6M49 55H62"/></g><circle cx="71" cy="37" r="1.5" fill={accent}/></g>;
  if (skin === "binary_people") return <g><text {...text} x="50" y="11" fontSize="8">THERE ARE 10</text><text {...text} x="50" y="23" fontSize="7.5">TYPES OF PEOPLE</text><text {...text} fill={accent} x="50" y="56" fontSize="29" fontFamily="monospace">01</text><text {...text} x="50" y="72" fontSize="5.3">YOU GET IT. OR YOU DON’T.</text></g>;
  if (skin === "gate_keeper") return <g><text {...text} x="50" y="11" fontSize="9">KEEP CALM</text><text {...text} x="50" y="23" fontSize="9">AND GATE ON</text><g stroke={accent} fill="none" strokeWidth="2" strokeLinecap="round"><path d="M39 33H53A17 17 0 0 1 53 67H39ZM22 41H39M22 59H39M70 50H84"/></g><g {...text} fill={accent} fontSize="8"><text x="17" y="44">1</text><text x="17" y="62">1</text><text x="90" y="53">1</text></g></g>;
  if (skin === "sleep_not_found") return <g><text {...text} fill="#c2b3f5" x="50" y="28" fontSize="29">404</text><text {...text} x="50" y="42" fontSize="8">SLEEP NOT FOUND</text><g fill="none" stroke={accent} strokeWidth="2" strokeLinecap="round"><path d="M21 58q8 8 16 0M62 58q8 8 16 0M41 69q9-5 18 0"/></g><text {...text} fill="#c2b3f5" x="84" y="53" fontSize="10">z</text></g>;
  if (skin === "resistance_futile") return <g><text {...text} x="50" y="11" fontSize="8.5">RESISTANCE</text><text {...text} x="50" y="23" fontSize="9">IS FUTILE</text><g stroke={accent} strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round"><path d="M9 48H25l5-9 8 18 8-18 8 18 8-18 8 18 5-9H92"/></g><text {...text} fill={accent} x="50" y="75" fontSize="7">Ω MY GOODNESS</text></g>;
  if (skin === "circuit") return <g stroke="#2e7d67" strokeWidth="2" fill="none"><path d="M11 20H34V9M89 20H66V9M11 58H34V70M89 58H66V70"/><circle cx="34" cy="8" r="3"/><circle cx="66" cy="8" r="3"/><rect x="33" y="25" width="34" height="28" rx="5"/><path d="M42 32v13h16V32"/></g>;
  if (skin === "cosmic") return <g fill="#e5dcff"><path d="m50 13 4 12 12 4-12 4-4 12-4-12-12-4 12-4Z"/><circle cx="21" cy="20" r="3"/><circle cx="80" cy="51" r="2"/><circle cx="22" cy="62" r="2.4"/><path d="M26 48Q56 17 77 35Q87 48 52 59" fill="none" stroke="#b8a4ef" strokeWidth="2"/></g>;
  if (skin === "gold") return <g fill="#8d6320"><path d="m25 31 3 24h44l3-24-17 10-8-17-8 17Z"/><path d="M30 61H70" fill="none" stroke="#8d6320" strokeWidth="3" strokeLinecap="round"/></g>;
  if (skin === "aurora") return <g stroke="#6a5b9e" strokeWidth="3" fill="none" strokeLinecap="round" opacity=".8"><path d="M13 46Q30 20 49 44T88 40M13 56Q30 30 49 54T88 50"/></g>;
  return <g><text {...text} x="50" y="44" fontSize="15">Job_Run</text><path d="M26 54H74" stroke="#8da89e" strokeWidth="2" strokeLinecap="round"/></g>;
}

export function ShirtPrint({ skin, className, label, compact = false }: { skin: string; className?: string; label?: string; compact?: boolean }) {
  return <svg className={className} viewBox="0 0 100 78" role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true} xmlns="http://www.w3.org/2000/svg"><PrintArtwork skin={skin} compact={compact}/></svg>;
}

/** A large merchandise view makes the shirt joke readable before purchase. */
export function ShirtArtwork({ skin, size = 240, className, label }: { skin: string; size?: number; className?: string; label?: string }) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const palette = shirtPalette(skin);
  const fill = skin === "gold" || skin === "aurora" ? `url(#merch-${id})` : palette.fabric;
  return <svg width={size} height={size} viewBox="0 0 180 190" className={className} role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true} xmlns="http://www.w3.org/2000/svg">
    <defs><linearGradient id={`merch-${id}`} x1="0" y1="0" x2="1" y2="1"><stop stopColor={skin === "gold" ? "#ffe4a0" : "#b2efd9"}/><stop offset=".5" stopColor={skin === "gold" ? "#d8ad4d" : "#bfc4f3"}/><stop offset="1" stopColor={skin === "gold" ? "#f8d886" : "#f1c8dc"}/></linearGradient></defs>
    <path d="M61 17 42 24 9 62 32 82 47 65V170Q47 177 55 177H125Q133 177 133 170V65L148 82 171 62 138 24 119 17Z" fill={fill} stroke="#35204f" strokeWidth="3" strokeLinejoin="round"/>
    <path d="M61 17Q89 48 119 17L110 14Q90 35 70 14Z" fill={palette.collar} stroke="#35204f" strokeWidth="2.5"/>
    <path d="M52 165H128" stroke={palette.seam} strokeWidth="1.3" opacity=".7"/>
    <svg x="48" y="55" width="84" height="91" viewBox="0 0 100 78"><PrintArtwork skin={skin}/></svg>
    <text x="90" y="163" textAnchor="middle" fontFamily="Arial, sans-serif" fontWeight="700" fontSize="7" fill={palette.ink} direction="ltr">Job_Run</text>
  </svg>;
}
