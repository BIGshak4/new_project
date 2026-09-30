import { Suspense } from "react";
import { StudioPreview } from "./studio";

export default function Page() {
  return <Suspense fallback={<p>טוענים את ההדמיה…</p>}><StudioPreview /></Suspense>;
}
