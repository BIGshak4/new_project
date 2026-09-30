import { Suspense } from "react";
import { Preview } from "./preview";

export default function Page() {
  return <Suspense fallback={<p>טוענים את ההדמיה…</p>}><Preview /></Suspense>;
}
