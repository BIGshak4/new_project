import styles from "./muxi-mascot.module.css";

export type MuxiMascotProps = {
  pose?: "wave" | "point" | "think" | "celebrate";
  pointDirection?: "left" | "right" | "down";
  className?: string;
  label?: string;
};

/** A four-input multiplexer who helps people choose their next learning step. */
export function MuxiMascot({
  pose = "wave",
  pointDirection = "right",
  className,
  label,
}: MuxiMascotProps) {
  const pointingLeft = pose === "point" && pointDirection === "left";
  const pointingDown = pose === "point" && pointDirection === "down";

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 220 220"
      className={[styles.mascot, className].filter(Boolean).join(" ")}
      data-pose={pose}
      data-point-direction={pointDirection}
      role={label ? "img" : undefined}
      aria-label={label || undefined}
      aria-hidden={label ? undefined : true}
      focusable="false"
    >
      <g className={styles.character}>
        {/* Short legs keep the silhouette unmistakably a circuit symbol. */}
        <path className={styles.limb} d="M88 167v31m49-46 6 29-6 17" />
        <path className={styles.shoe} d="M88 196c-9 0-15 4-15 9h22v-7m42-2c9 0 15 4 15 9h-22v-7" />

        <g className={styles.leftArm} transform="translate(12 2)">
          {pointingLeft ? (
            <>
              <path className={styles.limb} d="M65 105 47 94H27" />
              <path className={styles.hand} d="M31 89H17c-4 0-4 5 0 5h8l-4 3c-5 4-1 11 4 10l12-5 3-9-9-4Z" />
            </>
          ) : pose === "celebrate" ? (
            <>
              <path className={styles.limb} d="m65 105-42-9-9-25" />
              <path className={styles.hand} transform="translate(-12 0)" d="m34 75-7-9c-2-3 1-6 4-3l4 4-3-11c-1-4 4-5 5-1l3 10 3-6c2-3 6-1 4 3l-3 13-5 4-5-4Z" />
            </>
          ) : (
            <>
              <path className={styles.limb} d="m65 101-30-5-7 12" />
              <path className={styles.hand} d="M23 105c-6 2-7 8-3 12l6 3c5 1 10-4 8-9l-3-7-8 1Z" />
            </>
          )}
        </g>

        {/* A 4:1 MUX: four data inputs, two bottom select lines, one output. */}
        <g className={styles.pins}>
          <path data-mux-pin="input" d="M48 51h29" />
          <path data-mux-pin="input" d="M48 84h29" />
          <path data-mux-pin="input" d="M48 117h29" />
          <path data-mux-pin="input" d="M48 150h29" />
          <path data-mux-pin="select" d="M105 168v27" />
          <path data-mux-pin="select" d="M121 162v33" />
          <path data-mux-pin="output" d="M148 100h29" />
        </g>

        <path className={styles.body} d="M77 22 148 48v104l-71 26Z" />
        <path className={styles.edge} d="m84 31 57 21" />
        <g className={styles.face}>
          {pose === "celebrate" ? (
            <g className={styles.happyEyes}>
              <path d="m89 94 6-5 6 5m19 0 6-5 6 5" />
            </g>
          ) : (
            <>
              <ellipse className={styles.eye} cx="95" cy="93" rx="5" ry="7" />
              <ellipse className={styles.eye} cx="126" cy="93" rx="5" ry="7" />
              <circle className={styles.eyeGlint} cx="96.5" cy="90.5" r="1.5" />
              <circle className={styles.eyeGlint} cx="127.5" cy="90.5" r="1.5" />
            </>
          )}
          <path className={styles.brow} d={pose === "think" ? "m88 79 12-4m21 4 11 1" : "m89 79 12-1m20 0 11 1"} />
          <path className={styles.smile} d={pose === "think" ? "M103 121q9-3 16 0" : "M101 117q10 12 21-1"} />
          <path className={styles.cheek} d="M85 110h7m39 0h7" />
        </g>

        <g className={styles.rightArm} transform="translate(-3 12)">
          {pose === "point" ? (
            pointingLeft ? (
              <>
                <path className={styles.limb} d="m151 109 15 12-1 10" />
                <path className={styles.hand} d="M161 128c-6 1-8 8-3 12l6 3c6 0 10-5 7-10l-3-6-7 1Z" />
              </>
            ) : pointingDown ? (
              <>
                <path className={styles.limb} d="m151 109 23 11v26" />
                <path className={styles.hand} d="M168 143v19c0 4 5 4 5 0v-8l3 5c3 4 10 1 9-5l-5-13-8-2-4 4Z" />
              </>
            ) : (
              <>
                <path className={styles.limb} d="m151 108 19-8h18" />
                <path className={styles.hand} d="M185 95h15c4 0 4 5 0 5h-8l4 3c5 4 1 11-4 10l-12-5-3-9 8-4Z" />
              </>
            )
          ) : pose === "think" ? (
            <>
              <path className={styles.limb} d="m151 108 10 12-21 1" />
              <path className={styles.hand} d="m140 125-10-3c-5-1-7-7-2-10l9-4c4-2 7 2 4 5l-3 2 6 1-4 9Z" />
            </>
          ) : (
            <g className={styles.wavingHand}>
              <path className={styles.limb} d="m151 109 19-13 7-23" />
              <path className={styles.hand} d="m172 77-5-11c-1-4 3-6 5-2l2 5 2-13c1-4 6-3 5 1l-1 11 5-8c2-3 6-1 4 3l-6 14-6 4-5-4Z" />
            </g>
          )}
        </g>
        {pose === "celebrate" && (
          <g className={styles.sparks}>
            <path d="m29 39 4 9m13-18 1 8m123 1-5 7m21 1-7 4" />
            <circle cx="19" cy="55" r="2" />
            <circle cx="190" cy="30" r="2" />
          </g>
        )}
      </g>
    </svg>
  );
}
