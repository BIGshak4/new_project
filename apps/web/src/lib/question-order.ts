import { useEffect, useState } from "react";

/** One fresh browser seed per visit; the server and first client render agree. */
export function useQuestionOrderSeed(): number {
  const [seed, setSeed] = useState(0);
  useEffect(() => {
    setSeed(window.crypto.getRandomValues(new Uint32Array(1))[0]);
  }, []);
  return seed;
}

/** Fisher–Yates over canonical keys, independent of API order and UI language.
 * Shuffle the complete catalog once, then filter that order for every view. */
export function shuffleQuestions<T>(items: readonly T[], seed: number, key: (item: T) => string): T[] {
  const result = [...items].sort((a, b) => key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0);
  let state = seed >>> 0;
  const random = () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = Math.imul(state ^ (state >>> 15), 1 | state);
    value ^= value + Math.imul(value ^ (value >>> 7), 61 | value);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
