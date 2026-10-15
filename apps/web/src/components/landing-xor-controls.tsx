import { landingXorOutput, type LandingBits, type LandingBitInput } from "../lib/landing-xor";

/** Native toggle buttons keep the same interaction on touch, mouse and keyboard. */
export function LandingXorControls({
  bits,
  he,
  onToggle,
  className,
}: {
  bits: LandingBits;
  he: boolean;
  onToggle: (input: LandingBitInput) => void;
  className?: string;
}) {
  return (
    <div className={className} role="group" aria-label={he ? "שער XOR אינטראקטיבי" : "Interactive XOR gate"} dir="ltr">
      {(["a", "b"] as const).map(input => (
        <button
          key={input}
          type="button"
          onClick={() => onToggle(input)}
          aria-label={`${he ? "קלט" : "Input"} ${input.toUpperCase()}`}
          aria-pressed={bits[input] === 1}
        >
          <span aria-hidden="true">{input.toUpperCase()}</span>
          <b aria-hidden="true" data-bit={bits[input]}>{bits[input]}</b>
        </button>
      ))}
      <span aria-hidden="true" data-xor-label>XOR</span>
      <output aria-label={he ? "תוצאת XOR" : "XOR output"} aria-live="polite" aria-atomic="true" data-value={landingXorOutput(bits)}>
        <span aria-hidden="true">Y = </span>{landingXorOutput(bits)}
      </output>
    </div>
  );
}
