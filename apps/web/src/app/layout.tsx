import type { Metadata } from "next";
import {
  Amatic_SC,
  Assistant,
  Frank_Ruhl_Libre,
  Heebo,
  JetBrains_Mono,
} from "next/font/google";
import "./globals.css";
import "./ion.css";
import { themeBootstrap } from "../lib/theme";
import { Toaster } from "../components/toaster";
import { MotionProvider } from "../components/ui/motion";

// Ion is the production face. Older gallery faces remain available without preloading them.
const serif = Frank_Ruhl_Libre({
  subsets: ["hebrew", "latin"],
  weight: ["500", "700", "900"],
  variable: "--nf-serif",
  display: "swap",
  preload: false,
});
const sans = Assistant({
  subsets: ["hebrew", "latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--nf-sans",
  display: "swap",
  preload: false,
});
const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["500"],
  variable: "--nf-mono",
  display: "swap",
});
const hand = Amatic_SC({
  subsets: ["hebrew", "latin"],
  weight: ["700"],
  variable: "--nf-hand",
  display: "swap",
  preload: false,
});
const ion = Heebo({
  subsets: ["hebrew", "latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--nf-ion",
  display: "swap",
});

export const metadata: Metadata = {
  title: "JobRun — תרגול לראיון הבא",
  description: "סביבת תרגול לראיונות חומרה ותוכנה. פיילוט פרטי.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="he"
      dir="rtl"
      data-theme="dark"
      suppressHydrationWarning
      className={`${serif.variable} ${sans.variable} ${mono.variable} ${hand.variable} ${ion.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body>
        <MotionProvider>{children}</MotionProvider>
        <Toaster />
      </body>
    </html>
  );
}
