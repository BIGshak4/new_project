"use client";

import * as RadixSelect from "@radix-ui/react-select";
import { Check, ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import { fromSelectValue, toSelectValue } from "../../lib/ui";

export type SelectOption = { value: string; label: string };

/**
 * A select styled like the app's fields, built on Radix so the keyboard, Escape, focus return, type-ahead and
 * screen readers all work, in both directions. `value` may be "" for "all"; the empty string is mapped for Radix.
 */
export function Select({
  value,
  onChange,
  options,
  ariaLabel,
  dir,
  icon,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  ariaLabel: string;
  dir: "rtl" | "ltr";
  icon?: ReactNode;
  className?: string;
}) {
  return (
    <RadixSelect.Root value={toSelectValue(value)} onValueChange={(v) => onChange(fromSelectValue(v))} dir={dir}>
      <RadixSelect.Trigger className={`ui-select-trigger ${className ?? ""}`} aria-label={ariaLabel}>
        {icon}
        <span className="ui-select-value">
          <RadixSelect.Value />
        </span>
        <RadixSelect.Icon className="ui-select-chevron">
          <ChevronDown size={16} aria-hidden="true" />
        </RadixSelect.Icon>
      </RadixSelect.Trigger>
      <RadixSelect.Portal>
        <RadixSelect.Content className="ui-select-content" position="popper" sideOffset={6} align="start" collisionPadding={12}>
          <RadixSelect.Viewport className="ui-select-viewport">
            {options.map((o) => (
              <RadixSelect.Item key={o.value} value={toSelectValue(o.value)} className="ui-select-item">
                <RadixSelect.ItemText>{o.label}</RadixSelect.ItemText>
                <RadixSelect.ItemIndicator className="ui-select-tick">
                  <Check size={15} aria-hidden="true" />
                </RadixSelect.ItemIndicator>
              </RadixSelect.Item>
            ))}
          </RadixSelect.Viewport>
        </RadixSelect.Content>
      </RadixSelect.Portal>
    </RadixSelect.Root>
  );
}
