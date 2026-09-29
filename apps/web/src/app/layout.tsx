import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "../components/toaster";
import { MotionProvider } from "../components/ui/motion";
export const metadata: Metadata = {
  title: "JobRun — תרגול לראיון הבא",
  description: "סביבת תרגול לראיונות חומרה ותוכנה. פיילוט פרטי.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>
        <MotionProvider>{children}</MotionProvider>
        <Toaster />
      </body>
    </html>
  );
}
