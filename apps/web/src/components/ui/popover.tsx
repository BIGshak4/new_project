"use client";

import * as RadixPopover from "@radix-ui/react-popover";
import { HelpCircle } from "lucide-react";
import type { ReactNode } from "react";

/**
 * A small "?" that opens an explanation beside it. Radix handles focus, Escape, click-outside and placement
 * near the screen edge. Used for text that a reader needs once, not on every visit (how hints affect the grade).
 */
export function HelpPopover({ label, children, side = "bottom" }: { label: string; children: ReactNode; side?: "top" | "bottom" }) {
  return (
    <RadixPopover.Root>
      <RadixPopover.Trigger asChild>
        <button type="button" className="icon-button help-trigger" aria-label={label}>
          <HelpCircle size={18} aria-hidden="true" />
        </button>
      </RadixPopover.Trigger>
      <RadixPopover.Portal>
        <RadixPopover.Content className="ui-popover" side={side} align="start" sideOffset={8} collisionPadding={12}>
          {children}
          <RadixPopover.Arrow className="ui-popover-arrow" width={16} height={8} />
        </RadixPopover.Content>
      </RadixPopover.Portal>
    </RadixPopover.Root>
  );
}
