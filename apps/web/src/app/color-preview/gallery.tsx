"use client";

import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Copy,
  ExternalLink,
  Monitor,
  Smartphone,
} from "lucide-react";
import { SiteSimulation } from "../site-preview/simulation";
import { screens, type Screen } from "../site-preview/data";
import { colorPalettes, paletteById, type ColorPalette } from "./palettes";
import styles from "./preview.module.css";

const frameMessage = "jobrun-color-preview";

function previewPath(params: URLSearchParams, embedded: boolean) {
  const next = new URLSearchParams(params);
  next.set("palette", paletteById(next.get("palette")).id);
  next.set("style", "ion-light");
  next.set("motion", "0");
  if (!screens.includes(next.get("screen") as Screen)) next.set("screen", "home");
  if (embedded) next.set("embed", "1");
  else next.delete("embed");
  return `/color-preview?${next.toString()}`;
}

function candidateStyle(palette: ColorPalette): CSSProperties {
  return {
    ...Object.fromEntries(
      Object.entries(palette.tokens).map(([name, value]) => [`--candidate-${name}`, value]),
    ),
    "--candidate-color-scheme": palette.theme,
  } as CSSProperties;
}

function EmbeddedPreview({ palette, screen }: { palette: ColorPalette; screen: Screen }) {
  const params = useSearchParams();
  const normalized = params.get("style") === "ion-light" && params.get("motion") === "0";

  useEffect(() => {
    if (!normalized) {
      window.history.replaceState(null, "", previewPath(new URLSearchParams(params.toString()), true));
      return;
    }
    if (window.parent !== window) {
      window.parent.postMessage(
        { source: frameMessage, path: `${window.location.pathname}${window.location.search}` },
        window.location.origin,
      );
    }
  }, [normalized, params]);

  return (
    <div
      className={styles.preview}
      style={candidateStyle(palette)}
      data-color-palette={palette.id}
      data-palette={palette.id}
      data-preview-theme={palette.theme}
      data-screen={screen}
    >
      <p className={styles.demoNotice} dir="rtl" lang="he">
        תצוגת עיצוב בלבד · תוכן לדוגמה · בחירת הצבע כאן אינה משנה את האתר
      </p>
      {normalized ? <SiteSimulation /> : <p className={styles.loading}>טוענים את התצוגה…</p>}
    </div>
  );
}

export function ColorPreviewGallery() {
  const params = useSearchParams();
  const palette = paletteById(params.get("palette"));
  const screen = screens.includes(params.get("screen") as Screen)
    ? (params.get("screen") as Screen)
    : "home";
  const embedded = params.get("embed") === "1";

  if (embedded) return <EmbeddedPreview palette={palette} screen={screen} />;

  return <Gallery palette={palette} screen={screen} />;
}

function Gallery({ palette, screen }: { palette: ColorPalette; screen: Screen }) {
  const params = useSearchParams();
  const phone = params.get("device") === "phone";
  const frameRef = useRef<HTMLIFrameElement>(null);
  const shareField = useRef<HTMLInputElement>(null);
  const [frameReady, setFrameReady] = useState(false);
  const [frameRevision, setFrameRevision] = useState(0);
  const [observedPath, setObservedPath] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "copied" | "manual">("idle");
  const [manualLink, setManualLink] = useState("");
  const index = colorPalettes.findIndex((candidate) => candidate.id === palette.id);
  const path = previewPath(new URLSearchParams(params.toString()), true);
  const fullSizePath = observedPath || path;
  const displayedScreen = observedPath
    ? new URLSearchParams(observedPath.split("?")[1]).get("screen") ?? screen
    : screen;

  const update = useCallback(
    (changes: Record<string, string>) => {
      const next = new URLSearchParams(observedPath.split("?")[1] ?? params.toString());
      for (const [key, value] of Object.entries(changes)) next.set(key, value);
      if ("screen" in changes) next.delete("question");
      if (previewPath(next, true) === path && observedPath && observedPath !== path) {
        setFrameRevision((revision) => revision + 1);
      }
      if ("palette" in changes || "screen" in changes) {
        setFrameReady(false);
        setObservedPath("");
      }
      setCopyState("idle");
      window.history.pushState(null, "", previewPath(next, false));
    },
    [observedPath, params, path],
  );

  const move = useCallback(
    (direction: number) => {
      const next = colorPalettes[(index + direction + colorPalettes.length) % colorPalettes.length];
      update({ palette: next.id });
    },
    [index, update],
  );

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target;
      if (
        event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
        (target instanceof Element && target.closest("input, textarea, select, [contenteditable]:not([contenteditable='false'])"))
      ) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      move(event.key === "ArrowLeft" ? 1 : -1);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [move]);

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      if (
        event.origin !== window.location.origin ||
        event.source !== frameRef.current?.contentWindow ||
        event.data?.source !== frameMessage ||
        typeof event.data.path !== "string"
      ) return;
      const next = new URL(event.data.path, window.location.origin);
      if (next.pathname === "/color-preview" && next.searchParams.get("embed") === "1") {
        setObservedPath(`${next.pathname}${next.search}`);
        setCopyState("idle");
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  useEffect(() => {
    if (copyState === "manual") {
      shareField.current?.focus();
      shareField.current?.select();
    }
    if (copyState !== "copied") return;
    const timer = window.setTimeout(() => setCopyState("idle"), 2600);
    return () => window.clearTimeout(timer);
  }, [copyState]);

  async function copyLink() {
    const share = new URL(fullSizePath, window.location.origin);
    share.searchParams.delete("embed");
    share.searchParams.set("device", phone ? "phone" : "desktop");
    try {
      await navigator.clipboard.writeText(share.href);
      setCopyState("copied");
    } catch {
      setManualLink(share.href);
      setCopyState("manual");
    }
  }

  return (
    <main className={styles.gallery} dir="rtl" lang="he">
      <header className={styles.galleryHeader}>
        <div className={styles.heading}>
          <a className={styles.wordmark} href="/" aria-label="JobRun — האתר הראשי" dir="ltr">
            jobrun<span>.</span>
          </a>
          <div className={styles.headingText}>
            <h1>אפור, ירוק והסגול שלנו</h1>
            <p>עשרה כיווני רקע · תצוגת עיצוב מקומית</p>
          </div>
        </div>
        <div className={styles.actions}>
          <button className={styles.utilityButton} onClick={copyLink}>
            {copyState === "copied" ? <Check size={16} /> : <Copy size={16} />}
            {copyState === "copied" ? "הקישור הועתק" : "העתקת קישור"}
          </button>
          <a className={styles.fullSizeButton} href={fullSizePath} target="_blank" rel="noopener noreferrer">
            <ExternalLink size={16} />
            פתיחה בגודל מלא
          </a>
        </div>
      </header>

      <nav className={styles.palettes} aria-label="בחירת כיוון צבע">
        {colorPalettes.map((candidate) => (
          <button
            className={styles.paletteButton}
            key={candidate.id}
            data-color-palette-button={candidate.id}
            aria-pressed={candidate.id === palette.id}
            title={`${candidate.name} · ${candidate.nameEn}`}
            onClick={() => candidate.id !== palette.id && update({ palette: candidate.id })}
          >
            <span className={styles.swatches} aria-hidden="true">
              {candidate.swatches.map((color, swatchIndex) => (
                <i key={`${color}-${swatchIndex}`} style={{ backgroundColor: color }} />
              ))}
              {candidate.id === palette.id && <span className={styles.swatchCheck}><Check size={12} /></span>}
            </span>
            <span>{candidate.name}</span>
          </button>
        ))}
      </nav>

      <section className={styles.previewToolbar} aria-label="הגדרות תצוגה">
        <div className={styles.current} aria-live="polite" aria-atomic="true">
          <strong>{palette.name}</strong>
          <p>{palette.description}</p>
        </div>
        <div className={styles.previewControls}>
          <div className={styles.segmented} role="group" aria-label="בחירת מסך">
            <button data-preview-screen="home" aria-pressed={displayedScreen === "home"} onClick={() => displayedScreen !== "home" && update({ screen: "home" })}>דף הבית</button>
            <button data-preview-screen="library" aria-pressed={displayedScreen !== "home"} onClick={() => displayedScreen !== "library" && update({ screen: "library" })}>מאגר שאלות</button>
          </div>
          <div className={styles.segmented} role="group" aria-label="רוחב תצוגה">
            <button className={styles.deviceButton} aria-label="תצוגת מחשב" title="תצוגת מחשב" aria-pressed={!phone} onClick={() => phone && update({ device: "desktop" })}><Monitor size={17} /></button>
            <button className={styles.deviceButton} aria-label="תצוגת טלפון" title="תצוגת טלפון" aria-pressed={phone} onClick={() => !phone && update({ device: "phone" })}><Smartphone size={17} /></button>
          </div>
          <div className={styles.paletteNavigation}>
            <button aria-label="כיוון הצבע הקודם" title="כיוון קודם · חץ ימינה" onClick={() => move(-1)}><ArrowRight size={17} /></button>
            <span aria-label={`כיוון ${index + 1} מתוך ${colorPalettes.length}`} dir="ltr">{index + 1} / {colorPalettes.length}</span>
            <button aria-label="כיוון הצבע הבא" title="כיוון הבא · חץ שמאלה" onClick={() => move(1)}><ArrowLeft size={17} /></button>
          </div>
        </div>
      </section>

      {copyState === "manual" && (
        <div className={styles.manualShare}>
          <label htmlFor="color-preview-link">ההעתקה האוטומטית לא זמינה. סמנו והעתיקו את הקישור:</label>
          <input ref={shareField} id="color-preview-link" value={manualLink} readOnly dir="ltr" />
        </div>
      )}
      <p className={styles.srOnly} role="status">{copyState === "copied" ? "הקישור לתצוגה הנבחרת הועתק" : ""}</p>

      <section className={styles.stage} data-device={phone ? "phone" : "desktop"} aria-label={`תצוגת ${palette.name}`}>
        <div className={styles.frameShell}>
          {!frameReady && <p className={styles.frameLoading} role="status">טוענים את {palette.name}…</p>}
          <iframe
            key={frameRevision}
            ref={frameRef}
            className={styles.siteFrame}
            data-color-preview-frame
            src={path}
            title={`JobRun — ${palette.name} — ${displayedScreen === "home" ? "דף הבית" : "מאגר השאלות"}`}
            onLoad={() => setFrameReady(true)}
          />
        </div>
      </section>
    </main>
  );
}
