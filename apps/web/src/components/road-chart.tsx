"use client";

import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Lang } from "./auth";
import type { TimelinePoint } from "../lib/practice-api";
import { chartRows, type ChartRow } from "../lib/timeline";
import { useReducedMotion } from "./ui/motion";

/** The brief's colours, as hex because SVG presentation attributes are the safest place for them. */
const COLOURS = { strong: "#1b7f4e", partial: "#ffb703", weak: "#b5651d", level: "#1c64b8", grid: "#e3e7ee", label: "#5d6b80" };

/**
 * "The road so far" from the third practice day on: stacked bars per day (strong, partial, needs work) and the
 * average level as a line on its own axis, with a tooltip per day. Drawn left-to-right in both languages, as
 * charts are; labels and the tooltip are in the page's language.
 */
export function RoadChart({ timeline, lang }: { timeline: TimelinePoint[]; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const reduced = useReducedMotion();
  const rows = chartRows(timeline, lang);
  // one level point alone reads as a stray dot; the line appears once there are two days with a level
  const hasLevel = rows.filter((r) => r.level !== null).length >= 2;
  return (
    <div className="road-chart" dir="ltr" role="img" aria-label={t("תשובות לפי יום ורמה ממוצעת", "Answers per day and average level")}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 8, right: hasLevel ? 8 : 4, bottom: 0, left: -18 }} barCategoryGap="30%">
          <CartesianGrid vertical={false} stroke={COLOURS.grid} strokeWidth={2} />
          <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: COLOURS.grid, strokeWidth: 2 }} tick={{ fontSize: 12, fontWeight: 700, fill: COLOURS.label }} interval="preserveStartEnd" minTickGap={18} />
          <YAxis yAxisId="answers" allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 12, fontWeight: 700, fill: COLOURS.label }} width={34} />
          {hasLevel && (
            <YAxis yAxisId="level" orientation="right" domain={[1, 5]} ticks={[1, 3, 5]} tickLine={false} axisLine={false} tick={{ fontSize: 12, fontWeight: 700, fill: COLOURS.level }} width={26} />
          )}
          <Tooltip content={<RoadTooltip lang={lang} />} cursor={{ fill: "rgba(35, 48, 42, 0.06)" }} />
          <Bar yAxisId="answers" dataKey="weak" stackId="answers" fill={COLOURS.weak} isAnimationActive={!reduced} animationDuration={700} />
          <Bar yAxisId="answers" dataKey="partial" stackId="answers" fill={COLOURS.partial} isAnimationActive={!reduced} animationDuration={700} />
          <Bar yAxisId="answers" dataKey="strong" stackId="answers" fill={COLOURS.strong} radius={[6, 6, 0, 0]} isAnimationActive={!reduced} animationDuration={700} />
          {hasLevel && (
            <Line yAxisId="level" type="monotone" dataKey="level" stroke={COLOURS.level} strokeWidth={3} dot={{ r: 4, strokeWidth: 3, fill: "#fff" }} activeDot={{ r: 6 }} connectNulls isAnimationActive={!reduced} animationDuration={900} animationBegin={400} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

function RoadTooltip({ active, payload, lang }: { active?: boolean; payload?: { payload: ChartRow }[]; lang: Lang }) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="road-tooltip" dir={lang === "he" ? "rtl" : "ltr"}>
      <strong>{row.label}</strong>
      <span>
        {row.answered === 1 ? t("תשובה אחת", "1 answer") : `${row.answered} ${t("תשובות", "answers")}`}
        {" · "}
        {row.strong} {t("חזקות", "strong")}, {row.partial} {t("חלקיות", "partial")}, {row.weak} {t("לחיזוק", "to strengthen")}
      </span>
      {row.level !== null && (
        <span className="road-tooltip-level">
          {t("רמה ממוצעת", "Average level")} {row.level.toFixed(1)}
        </span>
      )}
    </div>
  );
}
