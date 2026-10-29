import { Shirt } from "lucide-react";
import catalog from "../../lib/avatar-catalog.json";
import type { AvatarConfig, AvatarLanguage } from "../../lib/avatar-types";
import { ShirtPrint, shirtPalette } from "../wardrobe/shirt-print";
import styles from "./game-avatar.module.css";

/** Compact characters keep their silhouettes; full jokes stay available at reading size. */
export function DuelLooks({me, opponent, lang}: {me: AvatarConfig; opponent: AvatarConfig; lang: AvatarLanguage}) {
  const he = lang === "he";
  return <details className={styles.looks}><summary><Shirt size={18} aria-hidden="true" />{he ? "החולצות שלנו מקרוב" : "Our shirts, up close"}</summary><div className={styles.prints}>{[me, opponent].map((config,index) => {
    const name = catalog.skins.find(skin => skin.key === config.skin)?.label[lang] ?? "Job_Run";
    return <section key={index}><h3>{index === 0 ? he ? "אתם" : "You" : he ? "היריב" : "Opponent"} · {name}</h3><div style={{backgroundColor:shirtPalette(config.skin).fabric}}><ShirtPrint skin={config.skin} label={name} /></div></section>;
  })}</div></details>;
}
