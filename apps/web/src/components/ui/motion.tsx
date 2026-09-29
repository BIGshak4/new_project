"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { MotionConfig, animate, motion, useReducedMotion } from "motion/react";
import { countDisplay } from "../../lib/ui";

/**
 * The motion layer. One rule from the brief: motion answers the reader (something arrived, something unlocked,
 * something counted), never decorates. Everything here follows the "reduce motion" setting: MotionConfig turns
 * transform animations off, and the helpers below fall back to a static render.
 */
export function MotionProvider({ children }: { children: ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}

/** The spring every arrival uses: quick, a little bounce, settles fast. */
export const spring = { type: "spring", stiffness: 420, damping: 30, mass: 0.8 } as const;
/** The spring for something that pops (a badge, a pill, a tick): more bounce. */
export const popSpring = { type: "spring", stiffness: 520, damping: 22 } as const;

/** Slides up and fades in on mount. `delay` in seconds. */
export function Reveal({
  children,
  delay = 0,
  className,
  as = "div",
  ...rest
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "p" | "aside" | "li";
} & Record<string, unknown>) {
  const reduced = useReducedMotion();
  const Tag = motion[as];
  return (
    <Tag
      className={className}
      initial={reduced ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...spring, delay }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

/** Scales in with a bounce on mount. For badges, pills and ticks. */
export function Pop({
  children,
  delay = 0,
  className,
  ...rest
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
} & Record<string, unknown>) {
  const reduced = useReducedMotion();
  return (
    <motion.span
      className={className}
      style={{ display: "inline-flex", animation: "none" }}
      initial={reduced ? false : { opacity: 0, scale: 0.6 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ ...popSpring, delay }}
      {...rest}
    >
      {children}
    </motion.span>
  );
}

/** A number that counts from its previous value to the new one (about 0.8 s), or jumps under reduced motion. */
export function CountUp({ value, className }: { value: number; className?: string }) {
  const reduced = useReducedMotion();
  const [shown, setShown] = useState(countDisplay(value));
  const previous = useRef(countDisplay(value));
  useEffect(() => {
    const target = countDisplay(value);
    const from = previous.current;
    previous.current = target;
    if (reduced || from === target) {
      setShown(target);
      return;
    }
    const controls = animate(from, target, {
      duration: Math.min(1.2, 0.4 + Math.abs(target - from) / 120),
      ease: "easeOut",
      onUpdate: (v) => setShown(countDisplay(v)),
    });
    return () => controls.stop();
  }, [value, reduced]);
  return <span className={className}>{shown}</span>;
}

/** A gentle repeated breath for the one thing on the page that asks to be pressed. Off under reduced motion. */
export function Breathe({ children, className, active = true }: { children: ReactNode; className?: string; active?: boolean }) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      animate={active && !reduced ? { scale: [1, 1.035, 1] } : { scale: 1 }}
      transition={active && !reduced ? { duration: 2.6, ease: "easeInOut", repeat: Infinity, repeatDelay: 0.6 } : { duration: 0 }}
    >
      {children}
    </motion.div>
  );
}

export { motion, AnimatePresence, useReducedMotion } from "motion/react";
