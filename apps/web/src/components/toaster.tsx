"use client";

import { Toaster as SonnerToaster } from "sonner";

/** One toaster for the app: quiet confirmations at the top, in the page's direction, styled from the brief. */
export function Toaster() {
  return (
    <SonnerToaster
      position="top-center"
      dir="auto"
      duration={3200}
      gap={10}
      offset={16}
      toastOptions={{ unstyled: true, classNames: { toast: "ui-toast", title: "ui-toast-title", description: "ui-toast-text", icon: "ui-toast-icon" } }}
    />
  );
}

export { toast } from "sonner";
