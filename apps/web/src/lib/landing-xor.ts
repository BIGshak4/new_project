export type Bit = 0 | 1;
export type LandingBits = Readonly<{ a: Bit; b: Bit }>;
export type LandingBitInput = keyof LandingBits;

export const INITIAL_LANDING_BITS: LandingBits = { a: 0, b: 1 };

/** Functional updates keep quick pointer and keyboard presses in order. */
export function toggleLandingBit(state: LandingBits, input: LandingBitInput): LandingBits {
  return { ...state, [input]: state[input] === 1 ? 0 : 1 };
}

export function landingXorOutput({ a, b }: LandingBits): Bit {
  return a === b ? 0 : 1;
}
