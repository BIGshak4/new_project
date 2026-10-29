import { useId } from "react";
import { AVATAR_COLORS, DEFAULT_AVATAR, type AvatarConfig } from "../../lib/avatar-types";
import styles from "./logic-avatar.module.css";

export type LogicAvatarProps = { config?: AvatarConfig; size?: number; label?: string; className?: string };

/** A logic-symbol head and a real, always-visible Job_Run team shirt. */
export function LogicAvatar({ config = DEFAULT_AVATAR, size = 240, label, className }: LogicAvatarProps) {
  const id = useId().replace(/:/g, "");
  const color = AVATAR_COLORS[config.color] ?? AVATAR_COLORS.violet;
  const skin = config.skin;
  const shirt = skin === "cosmic" ? "#24254f" : skin === "gold" ? `url(#gold-${id})` : skin === "aurora" ? `url(#aurora-${id})` : "#f2f6f4";
  const darkShirt = skin === "cosmic";
  const head = config.component === "and" ? "M69 28H114C145 28 162 49 162 75S145 122 114 122H69Z"
    : config.component === "or" || config.component === "xor" ? "M63 28Q91 75 63 122H111Q143 119 166 75Q143 31 111 28Z"
    : config.component === "dff" ? "M65 28H159V122H65Z" : "M70 24 158 43V107L70 126Z";
  return <svg className={[styles.avatar, className].filter(Boolean).join(" ")} width={size} height={size} viewBox="0 0 230 250" role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true} focusable="false" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id={`aurora-${id}`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#a7ead5"/><stop offset=".5" stopColor="#b5b7ef"/><stop offset="1" stopColor="#f0bfd7"/></linearGradient>
      <linearGradient id={`gold-${id}`} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#f8dc87"/><stop offset=".5" stopColor="#d5aa42"/><stop offset="1" stopColor="#f6e8b4"/></linearGradient>
    </defs>
    <ellipse cx="116" cy="235" rx="53" ry="7" fill="currentColor" opacity=".07"/>
    <g stroke="#35204f" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M98 204 93 226M133 204 138 226" fill="none"/>
      <path d="M94 225Q79 224 78 233H103V225M137 225Q152 224 153 233H129V225" fill="#35204f"/>
      <path d="M76 150 49 171 38 159M151 151 178 167 188 155" fill="none"/>
      <circle cx="36" cy="156" r="8" fill={color}/><circle cx="191" cy="153" r="8" fill={color}/>
      <path d="M91 126 74 133 58 154 77 167 85 154V208H146V154L154 167 174 154 158 133 138 126Z" fill={shirt}/>
      <path d="M100 126Q114 144 129 126" fill="none" strokeWidth="3"/>
      {skin === "circuit" && <g stroke="#3f8f77" strokeWidth="2" fill="none"><path d="M87 161H99V149M137 150V160H146M88 191H100V202M146 190H132V203"/><circle cx="99" cy="147" r="3"/><circle cx="137" cy="147" r="3"/></g>}
      {skin === "cosmic" && <g fill="#e3d8ff" stroke="none"><circle cx="94" cy="151" r="2"/><circle cx="139" cy="161" r="1.8"/><circle cx="96" cy="196" r="1.6"/><path d="m134 187 2 4 4 1-4 2-2 4-1-4-4-2 4-1Z"/></g>}
      <rect x="85" y="168" width="61" height="19" rx="5" fill={darkShirt ? "#45466b" : "#f2f6f4"} stroke="none"/>
      <path d={head} fill={color}/>
      {config.component === "xor" && <path d="M52 29Q81 75 52 121" fill="none" strokeWidth="3"/>}
      {config.component === "dff" && <><path d="m65 92 13 7-13 7" fill="none" strokeWidth="2"/><path d="M46 51H65M46 99H65M159 51H179" fill="none" strokeWidth="2.5"/><text x="77" y="57" fontFamily="system-ui" fontSize="15" stroke="none" fill="#35204f">D</text><text x="140" y="57" fontFamily="system-ui" fontSize="15" stroke="none" fill="#35204f">Q</text></>}
      {config.component === "mux" ? <g fill="none" strokeWidth="2.5"><path d="M48 44H70M48 65H70M48 86H70M48 107H70M158 75H180M102 120V133M118 116V130"/></g> : config.component !== "dff" && <g fill="none" strokeWidth="2.5"><path d="M43 51H75M43 99H75M162 75H182"/></g>}
      <path d="M86 37 104 35" fill="none" stroke="#fff" strokeWidth="4" opacity=".45"/>
      {skin === "gold" && <path d="m88 24-5-15 17 7 13-13 12 13 18-7-5 15Z" fill="#f2cc61" strokeWidth="2.5"/>}
      {skin === "cosmic" && <path d="M62 33Q109 3 161 37" fill="none" stroke="#b8a0ef" strokeWidth="7"/>}
      {skin === "aurora" && <path d="M65 108Q111 138 166 98" fill="none" stroke={`url(#aurora-${id})`} strokeWidth="6"/>}
      <ellipse cx="98" cy="73" rx="5" ry="7" fill="#35204f" stroke="none"/>
      <ellipse cx="130" cy="73" rx="5" ry="7" fill="#35204f" stroke="none"/>
      <circle cx="99.5" cy="70.8" r="1.7" fill="#fff" stroke="none"/><circle cx="131.5" cy="70.8" r="1.7" fill="#fff" stroke="none"/>
      <path d="M103 93Q114 105 126 92" fill="none" strokeWidth="3"/>
      <path d="M85 88h8M138 88h8" fill="none" stroke="#f6d7d1" strokeWidth="4"/>
    </g>
    <text x="115.5" y="182" textAnchor="middle" fill={darkShirt ? "#fff" : "#35204f"} fontFamily="Arial, sans-serif" fontWeight="700" fontSize="11" direction="ltr">Job_Run</text>
  </svg>;
}
