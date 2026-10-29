export type AvatarLanguage = "he" | "en";
export type AvatarConfig = { component: string; color: string; skin: string };
export type AvatarText = { he: string; en: string };
export type AvatarSkin = { key: string; label: AvatarText; description: AvatarText; price: number };
export type AvatarPayload = {
  avatar: AvatarConfig;
  owned_skins: string[];
  components: { key: string; label: AvatarText }[];
  colors: { key: string; label: AvatarText; hex: string }[];
  skins: AvatarSkin[];
  balance: number;
  enabled: boolean;
  shop_enabled: boolean;
  shirt_text: string;
  capabilities: { persistent_avatar: boolean; cosmetic_shop: boolean };
};
export type AvatarClient = {
  get(): Promise<AvatarPayload>;
  save(config: AvatarConfig): Promise<AvatarPayload>;
  buy(skin: string): Promise<AvatarPayload>;
};

export const DEFAULT_AVATAR: AvatarConfig = { component: "mux", color: "violet", skin: "classic" };
export const AVATAR_COLORS: Record<string, string> = {
  violet: "#8864B9", mint: "#64B5A3", sky: "#66A9D6", coral: "#E68F78", amber: "#D9AB55", rose: "#CE83AC",
};

export function sameAvatar(a: AvatarConfig, b: AvatarConfig): boolean {
  return a.component === b.component && a.color === b.color && a.skin === b.skin;
}
