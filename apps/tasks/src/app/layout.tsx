import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "JobRun Admin — ניהול האתר",
  description: "סביבת הניהול הפרטית של הראל ושקד: משתמשים, דיווחי תקלות ומשימות.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
