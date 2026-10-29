"use client";

import { useEffect, useState } from "react";
import { demoAvatarClient } from "../../lib/avatar-demo";
import type { AvatarClient, AvatarPayload } from "../../lib/avatar-types";
import { AvatarWelcome } from "./avatar-onboarding";

/** An explicit, isolated preview of the optional first-use screen. */
export function AvatarWelcomePreview() {
  const [preview, setPreview] = useState<{client: AvatarClient; data: AvatarPayload} | null>(null);
  useEffect(() => {
    const client = demoAvatarClient();
    let current = true;
    void client.get().then(data => { if (current) setPreview({client, data}); });
    return () => { current = false; };
  }, []);
  return <><aside style={{padding: "12px 5%", color: "var(--muted)", background: "var(--surface-2)"}} dir="rtl">תצוגת הדגמה של בחירת דמות לאחר הרשמה · השינויים נשמרים להדגמה בלבד.</aside>{preview ? <AvatarWelcome {...preview} lang="he" onContinue={() => window.location.assign("/games/preview/shop#my-character")} /> : <p role="status">טוענים את הדמות…</p>}</>;
}
