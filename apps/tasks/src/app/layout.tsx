import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "JobRun — סביבת העבודה",
  description: "לוח העבודה הפרטי של הראל ושקד.",
  robots: { index: false, follow: false },
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="he" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
