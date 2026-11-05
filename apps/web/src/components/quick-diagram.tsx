"use client";

import { useId } from "react";
import type { QuickDiagram } from "../lib/fundamentals";

export function QuickDiagramView({ diagram, lang }: { diagram: QuickDiagram; lang: "he" | "en" }) {
  const marker = `quick-arrow-${useId().replace(/:/g, "")}`;
  const label = lang === "he" ? "שרטוט הפתרון" : "Solution diagram";
  const defs = <defs><marker id={marker} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" /></marker></defs>;
  const arrow = `url(#${marker})`;
  if (diagram.kind === "gate") {
    const dataInputs = diagram.gate === "MUX" ? diagram.inputs.slice(0, 2) : diagram.inputs;
    return <figure className="quick-diagram"><svg viewBox="0 0 380 170" role="img" aria-label={`${label}: ${diagram.gate}`} direction="ltr">
      <title>{`${label}: ${diagram.gate}`}</title>{defs}
      <rect x="140" y="35" width="110" height="85" rx="7" className="quick-svg-node" />
      <text x="195" y="82" textAnchor="middle" className="quick-svg-gate">{diagram.gate}</text>
      {dataInputs.map((input, i) => { const y = dataInputs.length === 1 ? 77 : 58 + i * 38;
        return <g key={input}><text x="12" y={y + 5} className={input.length > 3 ? "quick-svg-small" : undefined}>{input}</text><path d={`M86 ${y} H137`} markerEnd={arrow} />
          {diagram.gate === "MUX" && <text x="152" y={y + 5} className="quick-svg-small">{i}</text>}</g>;
      })}
      <path d="M250 77 H325" markerEnd={arrow} /><text x="336" y="82">{diagram.output}</text>
      {diagram.gate === "MUX" && <><path d="M195 157 V123" markerEnd={arrow} /><text x="210" y="154">{diagram.inputs[2]}</text></>}
    </svg><figcaption>{label}</figcaption></figure>;
  }
  const positions = new Map(diagram.states.map((state, i) => [state, diagram.states.length === 1 ? 190 : 70 + i * 240 / (diagram.states.length - 1)]));
  return <figure className="quick-diagram"><svg viewBox="0 0 380 260" role="img" aria-label={label} direction="ltr">
    <title>{label}</title>{defs}
    <path d={`M${positions.get(diagram.initial)! - 58} 132 H${positions.get(diagram.initial)! - 28}`} markerEnd={arrow} />
    {diagram.transitions.map((edge, i) => {
      const from = positions.get(edge.from)!, to = positions.get(edge.to)!;
      if (from === to) return <g key={i}><path d={`M${from - 17} 111 C${from - 65} 22 ${from + 65} 22 ${from + 17} 111`} markerEnd={arrow} /><text x={from} y="52" textAnchor="middle" className="quick-svg-small">{edge.label}</text></g>;
      const forward = from < to, distance = Math.abs(to - from), direction = distance > 200 ? (forward ? 1 : -1) : (forward ? -1 : 1);
      const bend = distance > 200 ? 88 : 48;
      return <g key={i}><path d={`M${from + (forward ? 23 : -23)} ${132 + direction * 9} Q${(from + to) / 2} ${132 + direction * bend * 2} ${to + (forward ? -25 : 25)} ${132 + direction * 9}`} markerEnd={arrow} />
        <text x={(from + to) / 2} y={132 + direction * (bend + 10)} textAnchor="middle" className="quick-svg-small">{edge.label}</text></g>;
    })}
    {diagram.states.map(state => <g key={state}><circle cx={positions.get(state)} cy="132" r="25" className="quick-svg-node" /><text x={positions.get(state)} y="137" textAnchor="middle">{state}</text></g>)}
  </svg><figcaption>{lang === "he" ? "חץ ללא מקור מסמן את מצב ההתחלה. כיתובי החצים מתארים קלט, ולעיתים גם פלט, לפי השאלה." : "The incoming arrow marks the initial state. Transition labels describe inputs and, where specified, outputs."}</figcaption></figure>;
}
