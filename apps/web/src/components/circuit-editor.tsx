"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  useUpdateNodeInternals,
  type NodeProps,
  type Node,
  type Edge,
  type Connection,
  type ReactFlowInstance,
} from "@xyflow/react";
import {
  Expand,
  Undo2,
  Redo2,
  Trash2,
  Plus,
  Download,
  RotateCcw,
  StepForward,
} from "lucide-react";
import "@xyflow/react/dist/style.css";
import {
  ports,
  makePart,
  connectionError,
  reconfigure,
  hasCount,
  powerCount,
  mask,
  simulate,
  signalKey,
  type Circuit,
  type Part,
  type Kind,
  type Simulation,
  type Signal,
} from "../lib/circuit";
import type { Lang } from "./auth";

type GateNode = Node<{ part: Part; simulation: Simulation | null }, "gate">;
const signalText = (v: Signal | undefined, bits = 1) =>
  v == null
    ? "?"
    : bits === 1
      ? String(v)
      : `${v} · 0x${v.toString(16).toUpperCase()}`;
const pinTop = (height: number, index: number, count: number) =>
  25 + (0.12 + ((index + 0.5) * 0.76) / count) * (height - 40);
export function GateSymbol({ kind }: { kind: Kind }) {
  const inverted = ["not", "nand", "nor", "xnor"].includes(kind);
  let path = "M18 12H142V88H18Z";
  if (["and", "nand"].includes(kind))
    path = "M22 12H80C145 12 145 88 80 88H22Z";
  if (["or", "nor", "xor", "xnor"].includes(kind))
    path = "M25 12Q98 6 136 50Q98 94 25 88Q56 50 25 12Z";
  if (["not", "buffer"].includes(kind)) path = "M24 12L136 50L24 88Z";
  if (kind === "mux") path = "M24 8L136 25V75L24 92Z";
  if (kind === "demux") path = "M24 25L136 8V92L24 75Z";
  if (["input", "constant", "clock"].includes(kind))
    path = "M22 20H118L142 50L118 80H22Z";
  if (kind === "output") path = "M22 20H138V80H22L6 50Z";
  return (
    <svg
      className="gate-symbol"
      viewBox="0 0 160 100"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d={path} vectorEffect="non-scaling-stroke" />
      {["xor", "xnor"].includes(kind) && (
        <path
          d="M15 12Q46 50 15 88"
          fill="none"
          vectorEffect="non-scaling-stroke"
        />
      )}
      {inverted && (
        <ellipse
          cx="143"
          cy="50"
          rx="6"
          ry="6"
          vectorEffect="non-scaling-stroke"
        />
      )}
    </svg>
  );
}
function Gate({ data, selected, id }: NodeProps<GateNode>) {
  const p = data.part,
    pins = ports(p),
    height = Math.max(
      110,
      Math.max(pins.inputs.length, pins.outputs.length) * 24 + 40,
    );
  const update = useUpdateNodeInternals();
  useEffect(() => {
    update(id);
  }, [id, p.count, p.bits, p.kind, update]);
  const output =
    data.simulation?.signals[
      signalKey(id, p.kind === "output" ? "display" : pins.outputs[0]?.id)
    ];
  return (
    <div
      className={`logic-part ${selected ? "selected" : ""}`}
      style={{ height }}
    >
      <span className="part-label" dir="auto">
        {p.label}
      </span>
      <svg className="pin-leads" width="170" height={height} aria-hidden="true">
        {(["inputs", "outputs"] as const).flatMap((side) =>
          pins[side].map((pin, i) => {
            const y = pinTop(height, i, pins[side].length),
              fraction = (i + 0.5) / pins[side].length;
            const left = ["or", "nor", "xor", "xnor"].includes(p.kind)
              ? 25 + 62 * fraction * (1 - fraction)
              : ["and", "nand"].includes(p.kind)
                ? 22
                : ["not", "buffer", "mux", "demux"].includes(p.kind)
                  ? 24
                  : p.kind === "output"
                    ? 6
                    : 18;
            const right =
              pins.outputs.length > 1 ? (p.kind === "demux" ? 136 : 142) : 80;
            return (
              <line
                key={`${side}-${pin.id}`}
                x1={side === "inputs" ? 0 : (right * 170) / 160}
                x2={side === "inputs" ? (left * 170) / 160 : 170}
                y1={y}
                y2={y}
                stroke="#405c50"
                strokeWidth="1.6"
              />
            );
          }),
        )}
      </svg>
      <GateSymbol kind={p.kind} />
      {!["and", "nand", "or", "nor", "xor", "xnor", "not", "buffer"].includes(
        p.kind,
      ) && (
        <span className="symbol-name" aria-hidden="true">
          {p.kind === "half-adder"
            ? "HA"
            : p.kind === "full-adder"
              ? "FA"
              : p.kind === "comparator"
                ? "CMP"
                : p.kind === "register"
                  ? "REG"
                  : p.kind.toUpperCase()}
        </span>
      )}
      {(["inputs", "outputs"] as const).map((side) =>
        pins[side].map((pin, i) => {
          const top = pinTop(height, i, pins[side].length);
          return (
            <div key={`${side}-${pin.id}`}>
              <Handle
                id={pin.id}
                type={side === "inputs" ? "target" : "source"}
                position={side === "inputs" ? Position.Left : Position.Right}
                style={{ top }}
                title={`${pin.label} · ${pin.bits} bit`}
              />
              <span className={`pin-label ${side}`} style={{ top }}>
                {pin.label}
                {pin.bits > 1 && <small>[{pin.bits}]</small>}
              </span>
            </div>
          );
        }),
      )}
      {data.simulation && (
        <span className={`part-reading ${output ? "high" : ""}`}>
          {signalText(output, p.bits)}
        </span>
      )}
    </div>
  );
}
const nodeTypes = { gate: Gate };
const groups: { he: string; en: string; kinds: Kind[] }[] = [
  {
    he: "שערים",
    en: "Gates",
    kinds: ["and", "or", "xor", "not", "nand", "nor", "xnor", "buffer"],
  },
  {
    he: "ניתוב",
    en: "Routing",
    kinds: ["mux", "demux", "encoder", "decoder", "splitter", "joiner"],
  },
  {
    he: "קלט ופלט",
    en: "Input & output",
    kinds: ["input", "output", "constant", "clock"],
  },
  {
    he: "חשבון וזיכרון",
    en: "Arithmetic & memory",
    kinds: [
      "half-adder",
      "full-adder",
      "adder",
      "comparator",
      "dff",
      "register",
      "counter",
    ],
  },
];

export default function CircuitEditor({
  value,
  onChange,
  lang,
  readOnly = false,
}: {
  value: Circuit;
  onChange?: (c: Circuit) => void;
  lang: Lang;
  readOnly?: boolean;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [selected, setSelected] = useState<string | null>(null),
    [selectedWire, setSelectedWire] = useState<string | null>(null);
  const [group, setGroup] = useState(0),
    [notice, setNotice] = useState("");
  const [running, setRunning] = useState(false),
    [simulation, setSimulation] = useState<Simulation | null>(null);
  const [undo, setUndo] = useState<Circuit[]>([]),
    [redo, setRedo] = useState<Circuit[]>([]);
  const [full, setFull] = useState(false),
    [sourcePin, setSourcePin] = useState(""),
    [targetPin, setTargetPin] = useState("");
  const dialog = useRef<HTMLDialogElement>(null),
    flow = useRef<ReactFlowInstance<GateNode, Edge> | null>(null);
  const part = value.parts.find((p) => p.id === selected);
  useEffect(() => {
    if (running) setSimulation((old) => simulate(value, old ?? undefined));
  }, [value, running]);
  useEffect(() => {
    if (full) dialog.current?.showModal();
  }, [full]);
  function change(next: Circuit, record = true) {
    if (readOnly || !onChange) return;
    if (record) {
      setUndo((old) => [...old.slice(-39), value]);
      setRedo([]);
    }
    onChange(next);
  }
  function connect(c: Connection) {
    if (!c.sourceHandle || !c.targetHandle) return;
    const w = {
      source: c.source,
      sourcePort: c.sourceHandle,
      target: c.target,
      targetPort: c.targetHandle,
    };
    const issue = connectionError(value, w);
    if (issue || value.wires.length >= 200) {
      setNotice(
        issue === "width"
          ? t(
              "רוחבי החיבור שונים. התאימו רוחב או השתמשו במפצל.",
              "Different bus widths. Match widths or use a splitter.",
            )
          : issue === "occupied"
            ? t(
                "לכניסה הזאת כבר מחובר חוט. מחקו אותו לפני חיבור חדש.",
                "This input already has a wire. Remove it before reconnecting.",
              )
            : t(
                "לא ניתן לחבר את הנקודות האלה.",
                "These pins cannot be connected.",
              ),
      );
      return;
    }
    change({
      ...value,
      wires: [...value.wires, { ...w, id: crypto.randomUUID() }],
    });
    setNotice("");
  }
  function updatePart(patch: Partial<Part>) {
    if (!part) return;
    const updated = { ...part, ...patch };
    updated.value &= mask(updated.bits);
    const next = reconfigure(value, updated);
    if (next.wires.length < value.wires.length)
      setNotice(
        t(
          "חיבורים שכבר לא התאימו הוסרו. אפשר לבטל את השינוי.",
          "Incompatible wires were removed. You can undo this change.",
        ),
      );
    change(next);
  }
  function remove() {
    change({
      ...value,
      parts: value.parts.filter((p) => p.id !== selected),
      wires: value.wires.filter(
        (w) =>
          w.id !== selectedWire &&
          w.source !== selected &&
          w.target !== selected,
      ),
    });
    setSelected(null);
    setSelectedWire(null);
  }
  function add(kind: Kind) {
    if (value.parts.length >= 100) {
      setNotice(
        t("אפשר עד 100 רכיבים למעגל.", "Up to 100 components per circuit."),
      );
      return;
    }
    const p = makePart(kind, value.parts.length);
    const number = value.parts.filter((n) => n.kind === kind).length + 1;
    if (number > 1) p.label += ` ${number}`;
    change({ ...value, parts: [...value.parts, p] });
    setSelected(p.id);
    setSelectedWire(null);
    setTimeout(
      () =>
        flow.current?.fitView({
          nodes: [{ id: p.id }],
          padding: 0.2,
          minZoom: 1,
          maxZoom: 1.2,
          duration: 0,
        }),
      80,
    );
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "jobrun-circuit.json";
    a.click();
    URL.revokeObjectURL(url);
  }
  const nodes: GateNode[] = useMemo(
    () =>
      value.parts.map((p) => ({
        id: p.id,
        type: "gate",
        position: { x: p.x, y: p.y },
        selected: p.id === selected,
        data: { part: p, simulation: running ? simulation : null },
      })),
    [value.parts, selected, simulation, running],
  );
  const edges: Edge[] = useMemo(
    () =>
      value.wires.map((w) => {
        const n = simulation?.signals[signalKey(w.source, w.sourcePort)];
        return {
          id: w.id,
          source: w.source,
          target: w.target,
          sourceHandle: w.sourcePort,
          targetHandle: w.targetPort,
          type: "smoothstep",
          selected: w.id === selectedWire,
          label: running ? signalText(n) : undefined,
          style: {
            stroke: running
              ? n == null
                ? "#8c6323"
                : n > 0
                  ? "#225d48"
                  : "#69766f"
              : "#405c50",
            strokeWidth: w.id === selectedWire ? 3.5 : 2,
          },
          labelStyle: { fill: "#172c27", fontSize: 12 },
          labelBgStyle: { fill: "#f6f7f2" },
        };
      }),
    [value.wires, simulation, running, selectedWire],
  );
  const outputs = value.parts.flatMap((p) =>
    ports(p).outputs.map((port) => ({ p, port })),
  );
  const inputs = value.parts.flatMap((p) =>
    ports(p).inputs.map((port) => ({ p, port })),
  );
  const content = (
    <div className="circuit-workbench" dir={lang === "he" ? "rtl" : "ltr"}>
      <div className="circuit-toolbar">
        <strong>{t("שרטוט מעגל", "Circuit drawing")}</strong>
        <div className="row">
          {!readOnly && (
            <>
              <button
                type="button"
                aria-label={t("ביטול שינוי במעגל", "Undo circuit change")}
                disabled={!undo.length}
                onClick={() => {
                  setRedo((r) => [...r, value]);
                  onChange?.(undo.at(-1)!);
                  setUndo((u) => u.slice(0, -1));
                }}
              >
                <Undo2 size={16} />
              </button>
              <button
                type="button"
                aria-label={t("ביצוע שינוי מחדש במעגל", "Redo circuit change")}
                disabled={!redo.length}
                onClick={() => {
                  setUndo((u) => [...u, value]);
                  onChange?.(redo.at(-1)!);
                  setRedo((r) => r.slice(0, -1));
                }}
              >
                <Redo2 size={16} />
              </button>
              <button
                type="button"
                disabled={!part && !selectedWire}
                aria-label={t(
                  "מחיקת הרכיב או החוט המסומן",
                  "Delete selected component or wire",
                )}
                onClick={remove}
              >
                <Trash2 size={16} />
              </button>
            </>
          )}
          <button
            type="button"
            onClick={download}
            aria-label={t("הורדת השרטוט", "Download circuit")}
          >
            <Download size={16} />
          </button>
          <button
            type="button"
            onClick={() => {
              if (full) dialog.current?.close();
              setFull(!full);
            }}
          >
            <Expand size={16} />
            {full ? t("חזרה לתשובה", "Back to answer") : t("הרחבה", "Expand")}
          </button>
        </div>
      </div>
      {!readOnly && (
        <div className="component-library">
          <div
            className="component-groups"
            aria-label={t("קבוצות רכיבים", "Component groups")}
          >
            {groups.map((g, i) => (
              <button
                type="button"
                key={g.en}
                aria-pressed={i === group}
                onClick={() => setGroup(i)}
              >
                {t(g.he, g.en)}
              </button>
            ))}
          </div>
          <div className="component-palette" dir="ltr">
            {groups[group].kinds.map((kind) => (
              <button
                type="button"
                key={kind}
                onClick={() => add(kind)}
                title={t("הוספת רכיב", "Add component")}
              >
                <GateSymbol kind={kind} />
                <span>{kind.toUpperCase()}</span>
                <Plus size={12} />
              </button>
            ))}
          </div>
        </div>
      )}
      <p className="circuit-guide">
        {readOnly
          ? t(
              "זהו השרטוט שנשלח. אפשר להגדיל ולהריץ אותו בלי לשנות את התשובה.",
              "This is your submitted circuit. Zoom and simulate without changing the answer.",
            )
          : t(
              "בחרו רכיב להוספה. גררו אותו למקום, ואז חברו נקודת יציאה מימין לנקודת כניסה משמאל. לחיצה על רכיב פותחת את ההגדרות שלו.",
              "Add a component, drag it into place, then connect a right output pin to a left input pin. Select a component to configure it.",
            )}
      </p>
      <div className="circuit-viewport-tools">
        <span>
          {t(
            "גררו את הרקע כדי לנוע במעגל.",
            "Drag the background to pan around the circuit.",
          )}
        </span>
        <button
          type="button"
          onClick={() =>
            void flow.current?.fitView({
              padding: 0.2,
              minZoom: 1,
              maxZoom: 1.2,
            })
          }
        >
          {t("תצוגה קריאה", "Readable view")}
        </button>
        <button
          type="button"
          onClick={() =>
            void flow.current?.fitView({
              padding: 0.2,
              minZoom: 0.15,
              maxZoom: 1.2,
            })
          }
        >
          {t("כל המעגל", "Whole circuit")}
        </button>
      </div>
      <div
        className="circuit-canvas"
        dir="ltr"
        aria-label={t("לוח שרטוט מעגל", "Circuit canvas")}
      >
        <ReactFlow<GateNode, Edge>
          key={full ? "expanded" : "inline"}
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onInit={(instance) => {
            flow.current = instance;
          }}
          fitView
          fitViewOptions={{ padding: 0.2, minZoom: 1, maxZoom: 1.2 }}
          minZoom={0.15}
          maxZoom={2.5}
          snapToGrid
          snapGrid={[10, 10]}
          connectOnClick
          nodesDraggable={!readOnly}
          nodesConnectable={!readOnly}
          deleteKeyCode={null}
          onConnect={connect}
          onNodeClick={(_, n) => {
            setSelected(n.id);
            setSelectedWire(null);
          }}
          onEdgeClick={(_, e) => {
            setSelectedWire(e.id);
            setSelected(null);
          }}
          onPaneClick={() => {
            setSelected(null);
            setSelectedWire(null);
          }}
          onNodeDragStart={() => {
            setUndo((u) => [...u.slice(-39), value]);
            setRedo([]);
          }}
          onNodesChange={(changes) => {
            const positions = changes.filter((c) => c.type === "position");
            if (!readOnly && positions.length)
              change(
                {
                  ...value,
                  parts: value.parts.map((p) => {
                    const c = positions.find((c) => c.id === p.id);
                    return c?.position
                      ? {
                          ...p,
                          x: Math.max(-20000, Math.min(20000, c.position.x)),
                          y: Math.max(-20000, Math.min(20000, c.position.y)),
                        }
                      : p;
                  }),
                },
                false,
              );
          }}
        >
          <Background gap={20} size={1} color="#c8d4ca" />
          <Controls showInteractive={false} showFitView={false} />
        </ReactFlow>
        {!value.parts.length && (
          <div className="circuit-empty">
            {t("המעגל שלכם מתחיל כאן", "Your circuit starts here")}
            <span>
              {t(
                "בחרו שער מהספרייה למעלה כדי להתחיל.",
                "Choose a gate from the library above to begin.",
              )}
            </span>
          </div>
        )}
      </div>
      {!readOnly && !!value.parts.length && (
        <label className="component-picker">
          {t("בחירת רכיב להגדרה", "Select component to configure")}
          <select
            value={selected ?? ""}
            onChange={(e) => {
              setSelected(e.target.value || null);
              setSelectedWire(null);
            }}
          >
            <option value="">{t("בחירה", "Select")}</option>
            {value.parts.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
      )}
      {!readOnly && part && (
        <div className="part-properties">
          <label>
            {t("שם הרכיב", "Component label")}
            <input
              value={part.label}
              maxLength={40}
              onChange={(e) => updatePart({ label: e.target.value })}
              dir="auto"
            />
          </label>
          {hasCount(part.kind) && (
            <label>
              {["decoder", "demux"].includes(part.kind)
                ? t("מספר יציאות", "Output count")
                : t("מספר כניסות", "Input count")}
              <select
                value={part.count}
                onChange={(e) => updatePart({ count: Number(e.target.value) })}
              >
                {(powerCount(part.kind)
                  ? [2, 4, 8, 16]
                  : [2, 3, 4, 5, 6, 7, 8, 16]
                ).map((n) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
          )}
          {![
            "clock",
            "encoder",
            "decoder",
            "half-adder",
            "full-adder",
          ].includes(part.kind) && (
            <label>
              {t("רוחב נתונים בביטים", "Data width in bits")}
              <select
                value={part.bits}
                onChange={(e) => updatePart({ bits: Number(e.target.value) })}
              >
                {Array.from({ length: 16 }, (_, i) => (
                  <option key={i}>{i + 1}</option>
                ))}
              </select>
            </label>
          )}
          {["input", "constant"].includes(part.kind) && (
            <label>
              {t("ערך כניסה", "Input value")}
              <input
                type="number"
                min={0}
                max={mask(part.bits)}
                value={part.value}
                onChange={(e) =>
                  updatePart({
                    value: Math.max(
                      0,
                      Math.min(
                        mask(part.bits),
                        Math.trunc(Number(e.target.value) || 0),
                      ),
                    ),
                  })
                }
              />
              {part.bits === 1 && (
                <button
                  type="button"
                  onClick={() => updatePart({ value: part.value ? 0 : 1 })}
                >
                  {t("החלפת", "Toggle")} 0 / 1
                </button>
              )}
            </label>
          )}
          <p className="small muted">
            {ports(part).inputs.length} {t("כניסות", "inputs")} ·{" "}
            {ports(part).outputs.length} {t("יציאות", "outputs")}
            {["encoder", "decoder", "mux", "demux"].includes(part.kind) && (
              <>
                {" "}
                ·{" "}
                {t(
                  "רוחב הבחירה נגזר ממספר הקווים",
                  "Selection width follows the line count",
                )}
              </>
            )}
          </p>
        </div>
      )}
      {!readOnly && value.parts.length > 1 && (
        <details className="circuit-connect">
          <summary>
            {t(
              "חיבור באמצעות רשימה (גם למקלדת ולנייד)",
              "Connect using a list (keyboard & mobile)",
            )}
          </summary>
          <div className="row">
            <label>
              {t("יציאה", "Output")}
              <select
                value={sourcePin}
                onChange={(e) => setSourcePin(e.target.value)}
              >
                <option value="">{t("בחירה", "Select")}</option>
                {outputs.map(({ p, port }) => (
                  <option
                    key={`${p.id}:${port.id}`}
                    value={`${p.id}:${port.id}`}
                  >
                    {p.label} · {port.id} [{port.bits}]
                  </option>
                ))}
              </select>
            </label>
            <label>
              {t("כניסה", "Input")}
              <select
                value={targetPin}
                onChange={(e) => setTargetPin(e.target.value)}
              >
                <option value="">{t("בחירה", "Select")}</option>
                {inputs.map(({ p, port }) => (
                  <option
                    key={`${p.id}:${port.id}`}
                    value={`${p.id}:${port.id}`}
                  >
                    {p.label} · {port.id} [{port.bits}]
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              disabled={!sourcePin || !targetPin}
              onClick={() => {
                const [source, sourceHandle] = sourcePin.split(":"),
                  [target, targetHandle] = targetPin.split(":");
                connect({ source, sourceHandle, target, targetHandle });
              }}
            >
              {t("חיבור", "Connect")}
            </button>
          </div>
        </details>
      )}
      <div className="simulation-bar">
        <button
          type="button"
          className={running ? "" : "primary"}
          disabled={!value.parts.length}
          aria-pressed={running}
          onClick={() => {
            setRunning(!running);
            setSimulation(simulate(value));
          }}
        >
          {running
            ? t("עצירת סימולציה", "Stop simulation")
            : t("הרצת סימולציה", "Run simulation")}
        </button>
        {running && (
          <>
            <button
              type="button"
              onClick={() =>
                setSimulation((old) =>
                  simulate(value, old ?? undefined, old?.clock ? 0 : 1),
                )
              }
            >
              <StepForward size={16} />
              {t("צעד שעון", "Clock step")} · {simulation?.clock ?? 0}
            </button>
            <button
              type="button"
              onClick={() => setSimulation(simulate(value))}
            >
              <RotateCcw size={16} />
              {t("איפוס", "Reset")}
            </button>
          </>
        )}
        <span className="small muted">
          {value.parts.length}/100 {t("רכיבים", "components")} ·{" "}
          {value.wires.length}/200 {t("חוטים", "wires")}
        </span>
      </div>
      {running && (
        <p className="small muted circuit-guide">
          {t(
            "? = ערך לא ידוע או חיבור חסר. הרכיבים הסדרתיים מתחילים ב־0 ודוגמים בעליית שעון. איפוס פעיל ב־1. הסימולציה לוגית וללא זמני השהיה; היא לא בודקת אם הפתרון עונה לשאלה.",
            "? = unknown or missing input. Sequential components start at 0 and sample on a rising clock; reset is active-high. This is zero-delay logic simulation, not an assessment of your answer.",
          )}
          {simulation?.unstable && (
            <strong>
              {t(
                " המעגל לא התייצב. בדקו משוב מעגלי.",
                " The circuit did not settle. Check feedback loops.",
              )}
            </strong>
          )}
        </p>
      )}
      {running && !!simulation?.unsupportedClocks?.length && (
        <p className="circuit-notice" role="status">
          {t(
            "סימולציה של שעון שנוצר משער או מרכיב זיכרון אינה נתמכת עדיין. חברו רכיב שעון או כניסה ישירות לפין השעון; הפלט הלא נתמך מסומן ב־?.",
            "Derived or ripple clocks are not supported yet. Connect a clock or input directly to CLK; unsupported outputs are marked ?.",
          )}
        </p>
      )}
      {notice && (
        <p className="circuit-notice" role="status">
          {notice}
        </p>
      )}
    </div>
  );
  return full ? (
    <dialog
      ref={dialog}
      className="circuit-dialog"
      onCancel={() => setFull(false)}
      onClose={() => setFull(false)}
      aria-label={t("עורך מעגלים מורחב", "Expanded circuit editor")}
    >
      {content}
    </dialog>
  ) : (
    content
  );
}
