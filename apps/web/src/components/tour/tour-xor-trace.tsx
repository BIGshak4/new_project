import styles from "./tour-xor-trace.module.css";

type XorTraceProps = { a: number; b: number; output: number };

export function TourXorTrace({ a, b, output }: XorTraceProps) {
  return <svg className={styles.trace} viewBox="0 0 402 122" direction="ltr" role="img"
    aria-label={`XOR: A = ${a}, B = ${b}, Y = ${output}`}>
    <g className={styles.signal} data-high={a !== 0}>
      <text x="6" y="33">A = {a}</text>
      <path d="M73 27h30l16 16h53" />
      <circle cx="73" cy="27" r="4" />
    </g>
    <g className={styles.signal} data-high={b !== 0}>
      <text x="6" y="101">B = {b}</text>
      <path d="M73 95h30l16-16h53" />
      <circle cx="73" cy="95" r="4" />
    </g>
    <g className={styles.gate} transform="translate(132 11)">
      <path d="M25 12Q98 6 136 50Q98 94 25 88Q56 50 25 12Z" />
      <path className={styles.xorArc} d="M15 12Q46 50 15 88" />
      <text x="80" y="55" textAnchor="middle">XOR</text>
    </g>
    <g className={styles.signal} data-high={output !== 0}>
      <path d="M268 61h53" />
      <circle cx="321" cy="61" r="4" />
      <text x="337" y="67">Y = {output}</text>
    </g>
  </svg>;
}
