import { Suspense } from "react";
import { Rubik, Heebo, Secular_One, Noto_Serif_Hebrew } from "next/font/google";
import { ConceptPreview } from "./preview";

const rubik = Rubik({ subsets: ["hebrew", "latin"], weight: ["400", "500", "700", "900"], variable: "--concept-rubik", display: "swap" });
const heebo = Heebo({ subsets: ["hebrew", "latin"], weight: ["400", "500", "700", "900"], variable: "--concept-heebo", display: "swap" });
const secular = Secular_One({ subsets: ["hebrew", "latin"], weight: "400", variable: "--concept-secular", display: "swap" });
const editorial = Noto_Serif_Hebrew({ subsets: ["hebrew"], weight: ["400", "700", "900"], variable: "--concept-editorial", display: "swap" });

export default function Page() {
  return <div className={`${rubik.variable} ${heebo.variable} ${secular.variable} ${editorial.variable}`}><Suspense fallback={<p>טוענים את העיצוב…</p>}><ConceptPreview /></Suspense></div>;
}
