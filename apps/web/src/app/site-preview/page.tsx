import { Suspense } from "react";
import { Heebo } from "next/font/google";
import { SiteSimulation } from "./simulation";

const heebo = Heebo({
  subsets: ["hebrew", "latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--site-heebo",
  display: "swap",
});

export default function Page() {
  return (
    <div className={heebo.variable}>
      <Suspense fallback={<p>טוענים את ההדמיה…</p>}>
        <SiteSimulation />
      </Suspense>
    </div>
  );
}
