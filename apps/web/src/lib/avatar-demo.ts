/** Public shop preview only. It does not call an API or change a real wallet. */
import catalog from "./avatar-catalog.json";
import { DEFAULT_AVATAR, type AvatarClient, type AvatarConfig, type AvatarPayload, type AvatarSkin } from "./avatar-types";

const STORAGE = "jobrun-avatar-shop-demo-v1";
type DemoState = { avatar: AvatarConfig; owned_skins: string[]; balance: number; onboarding_completed?: boolean };
const initial = (): DemoState => ({ avatar: { ...DEFAULT_AVATAR }, owned_skins: ["classic"], balance: 160, onboarding_completed: false });
function read(): DemoState {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE) ?? "null") as DemoState | null;
    if (saved && Array.isArray(saved.owned_skins) && Number.isFinite(saved.balance) && saved.avatar &&
      catalog.components.some(c => c.key === saved.avatar.component) && catalog.colors.some(c => c.key === saved.avatar.color) &&
      catalog.skins.some(s => s.key === saved.avatar.skin) && saved.owned_skins.includes(saved.avatar.skin)) return saved;
  } catch { /* Preview works without browser storage. */ }
  return initial();
}
export function getDemoAvatar(): AvatarConfig { return read().avatar; }

export function demoAvatarClient(): AvatarClient {
  let state = read();
  function result(): AvatarPayload { return structuredClone({ ...catalog, skins: catalog.skins as AvatarSkin[], ...state, enabled: true, shop_enabled: true, shirt_text: "Job_Run", capabilities: { persistent_avatar: true, cosmetic_shop: true } }); }
  function persist() { try { sessionStorage.setItem(STORAGE, JSON.stringify(state)); } catch {} }
  return {
    get: async () => result(),
    save: async config => {
      if (!catalog.components.some(c => c.key === config.component) || !catalog.colors.some(c => c.key === config.color) || !state.owned_skins.includes(config.skin)) throw new Error("Unknown or unowned cosmetic");
      state = { ...state, avatar: { ...config }, onboarding_completed: true }; persist(); return result();
    },
    buy: async key => {
      const skin = catalog.skins.find(s => s.key === key);
      if (!skin) throw new Error("Unknown skin");
      if (state.owned_skins.includes(key)) return result();
      if (state.balance < skin.price) throw Object.assign(new Error("Not enough demo coins"), { status: 402 });
      state.balance -= skin.price; state.owned_skins.push(key); persist(); return result();
    },
    completeOnboarding: async config => {
      const avatar = { ...state.avatar, ...config };
      if (!catalog.components.some(c => c.key === avatar.component) || !catalog.colors.some(c => c.key === avatar.color)) throw new Error("Unknown free choice");
      state = { ...state, avatar, onboarding_completed: true }; persist(); return result();
    },
  };
}
