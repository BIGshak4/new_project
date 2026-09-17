import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "JobRun — תרגול לראיון הבא",
  description: "סביבת תרגול לראיונות חומרה ותוכנה. פיילוט פרטי.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
