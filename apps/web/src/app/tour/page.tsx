"use client";
import { useEffect, useState } from "react";
import { MuxiTour } from "../../components/tour/muxi-tour";
import { LanguageMenu } from "../../components/ui/language-menu";
import { ThemeToggle } from "../../components/ui/theme-toggle";

/** Public introduction uses local examples; it requires no practice account or API calls. */
export default function TourPage() {
  const [lang, setLang] = useState<"he" | "en">("he");
  useEffect(() => { try { if (localStorage.getItem("jobrun-language") === "en") setLang("en"); } catch {} }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    try { localStorage.setItem("jobrun-language", lang); } catch {}
  }, [lang]);
  return <MuxiTour lang={lang} standalone controls={<><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>} onClose={() => { window.location.assign("/#signin"); }} />;
}
