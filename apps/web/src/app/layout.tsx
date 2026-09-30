import type { Metadata } from "next";
import { Amatic_SC, Assistant, Frank_Ruhl_Libre, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "../components/toaster";
import { MotionProvider } from "../components/ui/motion";

// the bench's four faces, self-hosted by Next (no request to Google at run time, no render-blocking import chain)
const serif = Frank_Ruhl_Libre({ subsets: ["hebrew", "latin"], weight: ["500", "700", "900"], variable: "--nf-serif", display: "swap" });
const sans = Assistant({ subsets: ["hebrew", "latin"], weight: ["400", "500", "600", "700", "800"], variable: "--nf-sans", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], weight: ["500"], variable: "--nf-mono", display: "swap" });
const hand = Amatic_SC({ subsets: ["hebrew", "latin"], weight: ["700"], variable: "--nf-hand", display: "swap" });

export const metadata: Metadata = {
  title: "JobRun — תרגול לראיון הבא",
  description: "סביבת תרגול לראיונות חומרה ותוכנה. פיילוט פרטי.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl" className={`${serif.variable} ${sans.variable} ${mono.variable} ${hand.variable}`}>
      <body>
        <MotionProvider>{children}</MotionProvider>
        <Toaster />
      </body>
    </html>
  );
}
