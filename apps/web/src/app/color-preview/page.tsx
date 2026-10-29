import type { Metadata } from "next";
import { Suspense } from "react";
import { ColorPreviewGallery } from "./gallery";
import styles from "./preview.module.css";

export const metadata: Metadata = {
  title: "JobRun — עשרה כיוונים באפור וירוק",
  description: "השוואת עשרה רקעים באפור וירוק לצד הסגול של JobRun. תצוגת עיצוב בלבד.",
  robots: { index: false, follow: false },
};

export default function ColorPreviewPage() {
  return (
    <Suspense fallback={<p className={styles.loading}>טוענים את תצוגת הצבעים…</p>}>
      <ColorPreviewGallery />
    </Suspense>
  );
}
