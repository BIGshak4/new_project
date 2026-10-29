import { useId } from "react";
import { AVATAR_COLORS, DEFAULT_AVATAR, type AvatarConfig } from "../../lib/avatar-types";
import { PrintArtwork, shirtPalette } from "./shirt-print";
import styles from "./logic-avatar.module.css";

export type LogicAvatarProps = { config?: AvatarConfig; size?: number; label?: string; className?: string; facing?: "left" | "right"; compact?: boolean };

/** A broad colored neck tucks into a tailored collar; every component has its own silhouette. */
export function LogicAvatar({ config = DEFAULT_AVATAR, size = 280, label, className, facing = "right", compact = size <= 180 }: LogicAvatarProps) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const color = AVATAR_COLORS[config.color] ?? AVATAR_COLORS.violet;
  const component = ["and", "or", "xor", "mux", "dff"].includes(config.component) ? config.component : "mux";
  const skin = config.skin;
  const palette = shirtPalette(skin);
  const boxy = component === "dff", round = component === "and";
  const head = component === "and" ? "M83 36H145C180 36 205 60 205 91S180 146 145 146H83Q75 146 75 138V44Q75 36 83 36Z"
    : component === "or" || component === "xor" ? "M76 36Q110 91 76 146H142Q184 140 212 91Q184 42 142 36Z"
    : component === "dff" ? "M89 36H194Q205 36 205 47V135Q205 146 194 146H89Q78 146 78 135V47Q78 36 89 36Z"
    : "M87 32Q82 31 82 38V146Q82 153 89 151L201 125Q207 123 207 117V66Q207 59 201 57Z";
  const shirt = boxy ? "M111 153Q95 153 84 162L62 187Q58 193 64 198L81 210Q86 213 91 206L96 199V270Q96 280 106 280H178Q188 280 188 270V199L193 206Q198 213 203 210L220 198Q226 193 222 187L200 162Q189 153 172 153Z"
    : round ? "M112 153Q95 155 83 167L64 188Q59 194 66 199L82 209Q88 213 92 205L98 198Q90 231 96 265Q98 279 111 281H174Q188 280 190 266Q195 232 187 198L193 205Q197 213 203 209L219 199Q226 194 221 188L202 167Q190 155 172 153Z"
    : "M112 153Q98 154 87 164L65 186Q59 193 66 199L82 210Q87 213 92 207L99 198L94 269Q93 280 104 281H181Q192 280 191 269L186 198L193 207Q198 213 203 210L219 199Q226 193 220 186L198 164Q187 154 172 153Z";
  const shirtFill = skin === "aurora" || skin === "gold" ? `url(#shirt-${id})` : palette.fabric;
  const legs = "M115 270 110 303Q109 308 101 309H88Q82 309 82 316H125L129 276M159 276 162 309H205Q205 302 198 302H185Q178 302 177 296L172 270";
  const arms = "M78 195Q62 208 51 191L43 180M207 195Q222 208 233 191L241 180";
  const hands = "M45 183Q32 188 29 177Q26 165 37 163Q44 160 48 170Q52 177 45 183ZM239 183Q252 188 255 177Q258 165 247 163Q240 160 236 170Q232 177 239 183Z";
  const pins = component === "mux" ? "M57 57H82M57 82H82M57 107H82M57 132H82M207 91H232"
    : component === "dff" ? "M54 64H78M54 119H78M205 64H229M78 111 91 119 78 127"
    : "M52 62H87M52 120H87M207 91H232";
  return <svg className={[styles.avatar, className].filter(Boolean).join(" ")} width={size} height={size} viewBox="0 0 284 334" role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true} focusable="false" xmlns="http://www.w3.org/2000/svg" data-component={component}>
    <defs><linearGradient id={`shirt-${id}`} x1="0" y1="0" x2="1" y2="1"><stop stopColor={skin === "gold" ? "#ffe4a0" : "#b2efd9"}/><stop offset=".5" stopColor={skin === "gold" ? "#d8ad4d" : "#bfc4f3"}/><stop offset="1" stopColor={skin === "gold" ? "#f8d886" : "#f1c8dc"}/></linearGradient></defs>
    <ellipse cx="142" cy="318" rx={round ? 71 : 65} ry="8" fill="currentColor" opacity=".09"/>
    <g stroke="#35204f" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" transform={facing === "left" ? "translate(284 0) scale(-1 1)" : undefined}>
      {/* A restrained outer rim separates anatomy from dark surfaces without recoloring face ink. */}
      <g fill="none" stroke="var(--avatar-edge, transparent)" strokeWidth="7" data-avatar-edge="silhouette">
        <path d={legs}/><path d={arms} strokeWidth="17"/><path d={hands}/><path d={shirt}/><path d={pins} strokeWidth="6"/>
        {component === "xor" && <path d="M60 37Q95 91 60 146"/>}
      </g>
      <path d={legs} fill="#35204f"/>
      <path d={arms} fill="none" strokeWidth="13"/>
      <path d={arms} fill="none" stroke={color} strokeWidth="7"/>
      <path d={hands} fill={color}/>
      <path d="M122 123H163V164Q143 179 122 164Z" fill={color} data-avatar-neck="integrated"/>
      <path d={shirt} fill={shirtFill} data-avatar-shirt="body"/>
      <path d="M112 153Q141 182 172 153L164 150Q142 167 122 150Z" fill={palette.collar} strokeWidth="3"/>
      <path d="M89 175 102 184M195 175 182 184M102 268Q143 274 183 268" fill="none" stroke={palette.seam} strokeWidth="2" opacity=".65"/>
      {skin === "circuit" && <g stroke="#2e7d67" strokeWidth="2" fill="none"><path d="M102 201H113V188M181 199H170V187M103 255H116V266M181 255H167V267"/><circle cx="113" cy="186" r="3"/><circle cx="170" cy="185" r="3"/></g>}
      {skin === "cosmic" && <g fill="#e5dcff" stroke="none"><circle cx="106" cy="185" r="2.3"/><circle cx="175" cy="192" r="2"/><circle cx="111" cy="253" r="2"/><path d="m176 244 2.5 5 5 1-5 2-2.5 5-1.5-5-5-2 5-1Z"/></g>}
      <path d={head} fill={color}/>
      {component === "xor" && <path d="M60 37Q95 91 60 146" fill="none" strokeWidth="4"/>}
      <path d={pins} fill="none" strokeWidth="3"/>
      <path d="m96 47 24 3" fill="none" stroke="#fff" strokeWidth="5" opacity=".42"/>
      {skin === "gold" && <path d="m114 34-7-20 23 9 15-17 15 17 24-9-7 22Z" fill="#f4cc67" strokeWidth="3"/>}
      {skin === "cosmic" && <path d="M78 48Q143 12 209 61" fill="none" stroke="#b9a4ef" strokeWidth="8"/>}
      {skin === "aurora" && <path d="M83 134Q141 166 208 121" fill="none" stroke={`url(#shirt-${id})`} strokeWidth="7"/>}
      <ellipse cx="117" cy="91" rx="6" ry="8" fill="#35204f" stroke="none"/><ellipse cx="165" cy="91" rx="6" ry="8" fill="#35204f" stroke="none"/>
      <circle cx="119" cy="88" r="2" fill="#fff" stroke="none"/><circle cx="167" cy="88" r="2" fill="#fff" stroke="none"/>
      <path d="M125 113Q141 130 158 112" fill="none" strokeWidth="3.5"/>
      <path d="M100 109h9M175 109h9" fill="none" stroke="#f7d7d4" strokeWidth="5"/>
    </g>
    {/* Lettering is outside the facing transform so opponents never wear mirrored words. */}
    <svg x="105" y="182" width="75" height="78" viewBox="0 0 100 78" overflow="visible" data-avatar-print={compact ? "compact" : "full"}><PrintArtwork skin={skin} compact={compact}/></svg>
    <text x="143" y="273" textAnchor="middle" fill={palette.ink} fontFamily="Arial, sans-serif" fontWeight="700" fontSize="7.5" direction="ltr">Job_Run</text>
    {component === "dff" && <g fontFamily="Arial, sans-serif" fontWeight="700" fontSize="12" fill="#35204f"><text x={facing === "left" ? "194" : "89"} y="67" direction="ltr">D</text><text x={facing === "left" ? "82" : "184"} y="67" direction="ltr">Q</text></g>}
  </svg>;
}
