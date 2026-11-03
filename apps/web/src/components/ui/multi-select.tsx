"use client";

import * as Popover from "@radix-ui/react-popover";
import { ChevronDown, Search } from "lucide-react";
import { useId, useState, type ReactNode } from "react";
import { normalizeSearch } from "../../lib/question-discovery";
import styles from "./multi-select.module.css";

type Option = { value: string; label: string };

/** Empty selection means all; the popup stays open while several choices are checked. */
export function MultiSelect({ values, onChange, options, label, allLabel, lang, icon, matchesOption }: {
  values: string[]; onChange: (values: string[]) => void; options: Option[];
  label: string; allLabel: string; lang: "he" | "en"; icon?: ReactNode; matchesOption?: (option: Option, search: string) => boolean;
}) {
  const [search, setSearch] = useState("");
  const id = useId();
  const he = lang === "he";
  const chosen = options.filter(option => values.includes(option.value));
  const summary = values.length === 0 ? allLabel : chosen.length === 1 ? chosen[0].label : he ? `${values.length} נבחרו` : `${values.length} selected`;
  const shown = options.filter(option => matchesOption ? matchesOption(option, search) : normalizeSearch(option.label).includes(normalizeSearch(search)));
  return <Popover.Root onOpenChange={() => setSearch("")}>
    <Popover.Trigger asChild><button type="button" className={`ui-select-trigger ${styles.trigger}`} aria-label={label}>
      {icon}<span className={styles.value}>{summary}</span><ChevronDown size={16} aria-hidden="true" />
      {values.length > 0 && <span className={styles.count}>{values.length}</span>}
    </button></Popover.Trigger>
    <Popover.Portal><Popover.Content className={styles.content} sideOffset={6} align="start" collisionPadding={12} dir={he ? "rtl" : "ltr"} aria-labelledby={`${id}-title`}>
      <header className={styles.head}><strong id={`${id}-title`}>{label}</strong><button type="button" className={styles.clear} disabled={!values.length} onClick={() => onChange([])}>{he ? "ניקוי בחירה" : "Clear selection"}</button></header>
      <p className={styles.help}>{he ? "אפשר לבחור כמה. ללא בחירה מוצגות כל האפשרויות." : "Choose several. Leave empty to include all options."}</p>
      <label className={styles.search}><Search size={16} aria-hidden="true" /><span className={styles.srOnly}>{he ? `חיפוש ב${label}` : `Search ${label}`}</span><input value={search} onChange={event => setSearch(event.target.value)} placeholder={he ? "חיפוש באפשרויות…" : "Search options…"} /></label>
      <fieldset className={styles.options}><legend className={styles.srOnly}>{label}</legend>
        {shown.map(option => <label key={option.value} className={styles.option}><input type="checkbox" checked={values.includes(option.value)} onChange={event => onChange(event.target.checked ? [...values, option.value] : values.filter(value => value !== option.value))} /><span dir="auto">{option.label}</span></label>)}
        {!shown.length && <p className={styles.help}>{he ? "לא נמצאו אפשרויות." : "No options found."}</p>}
      </fieldset>
      <Popover.Close asChild><button type="button" className={styles.done}>{he ? "סיום הבחירה" : "Done"}</button></Popover.Close>
    </Popover.Content></Popover.Portal>
  </Popover.Root>;
}
