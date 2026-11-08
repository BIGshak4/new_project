"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import type { GuestExercise } from "../../lib/muxi-tour";
import { GuestLibraryDemo } from "./guest-library-demo";

const Hardware = dynamic(() => import("./guest-hardware-demo").then(module => module.GuestHardwareDemo));
const Software = dynamic(() => import("./guest-software-demo").then(module => module.GuestSoftwareDemo));
const Interview = dynamic(() => import("./guest-interview-demo").then(module => module.GuestInterviewDemo));

export function GuestTourExercises({ exercise, lang, onAction }: {
  exercise: GuestExercise; lang: "he" | "en"; onAction: (action: string) => void;
}) {
  // Both software stops refer to the same submitted explanation for this visit.
  const [explanation, setExplanation] = useState("");
  switch (exercise) {
    case "guest-library": return <GuestLibraryDemo lang={lang} onAction={onAction} />;
    case "guest-hardware": return <Hardware lang={lang} onAction={onAction} />;
    case "guest-explain":
    case "guest-code": return <Software key={exercise} station={exercise} lang={lang} onAction={onAction}
      explanation={explanation} onExplanationChange={setExplanation} />;
    case "guest-interview": return <Interview lang={lang} onAction={onAction} />;
  }
}
