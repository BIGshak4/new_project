export type ColorPalette = {
  id: string;
  name: string;
  nameEn: string;
  description: string;
  theme: "light" | "dark";
  treatment:
    | "fog"
    | "sage"
    | "celadon"
    | "olive"
    | "mineral"
    | "paper"
    | "split"
    | "graphite"
    | "forest"
    | "fern";
  tokens: {
    bg: string;
    surface: string;
    surface2: string;
    ink: string;
    muted: string;
    line: string;
    accent: string;
    accentInk: string;
    link: string;
    soft: string;
  };
  swatches: readonly string[];
};

// These candidates belong only to /color-preview. Their semantic roles let the
// same product simulation compare each treatment without changing production.
export const colorPalettes: readonly ColorPalette[] = [
  {
    id: "fog",
    name: "ערפל כסוף",
    nameEn: "Silver fog",
    description: "אפור כסוף קריר עם רמז ירוק; הסגול נשאר חד והמשטחים כמעט נעלמים.",
    theme: "light",
    treatment: "fog",
    tokens: {
      bg: "#eef1ef",
      surface: "#fafcf9",
      surface2: "#e1e8e3",
      ink: "#35204f",
      muted: "#62506e",
      line: "#78837a",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#e2dbe8",
    },
    swatches: ["#eef1ef", "#e1e8e3", "#35204f", "#634086"],
  },
  {
    id: "sage",
    name: "סטודיו מרווה",
    nameEn: "Sage studio",
    description: "מרווה חמה כרקע עבודה, עם משטחים בהירים וסגול עמוק שמכוון לפעולה.",
    theme: "light",
    treatment: "sage",
    tokens: {
      bg: "#e0e8dd",
      surface: "#f4f7ef",
      surface2: "#d1dfcf",
      ink: "#35204f",
      muted: "#5d4869",
      line: "#707b66",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#e1d8e9",
    },
    swatches: ["#e0e8dd", "#d1dfcf", "#35204f", "#634086"],
  },
  {
    id: "celadon",
    name: "סלדון",
    nameEn: "Celadon",
    description: "ירוק מנטה מעושן ומשטחי סלדון; ניגוד רענן לסגול השזיף של הטקסט.",
    theme: "light",
    treatment: "celadon",
    tokens: {
      bg: "#d5e5dd",
      surface: "#edf5ee",
      surface2: "#bfd7c9",
      ink: "#35204f",
      muted: "#574365",
      line: "#5e796c",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#ded5e7",
    },
    swatches: ["#d5e5dd", "#bfd7c9", "#35204f", "#634086"],
  },
  {
    id: "olive",
    name: "אבן וזית",
    nameEn: "Stone and olive",
    description: "אפור אבן חם הנוטה לזית, עם שכבות חול ירקרק ונוכחות סגולה שקטה.",
    theme: "light",
    treatment: "olive",
    tokens: {
      bg: "#e5e6d8",
      surface: "#f5f4e8",
      surface2: "#d6dac2",
      ink: "#35204f",
      muted: "#5d4c67",
      line: "#727b60",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#e2d9e6",
    },
    swatches: ["#e5e6d8", "#d6dac2", "#35204f", "#634086"],
  },
  {
    id: "mineral",
    name: "מינרל",
    nameEn: "Mineral",
    description: "אפור מינרלי בגוון ירוק קריר; קווי חלוקה ברורים שומרים על אופי טכני.",
    theme: "light",
    treatment: "mineral",
    tokens: {
      bg: "#e0e6e5",
      surface: "#f2f6f4",
      surface2: "#cbd8d5",
      ink: "#35204f",
      muted: "#5b4a68",
      line: "#687a74",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#dfd9e8",
    },
    swatches: ["#e0e6e5", "#cbd8d5", "#35204f", "#634086"],
  },
  {
    id: "paper",
    name: "נייר ירוק",
    nameEn: "Green paper",
    description: "נייר אפרפר עם נגיעה ירוקה ומעטפת בהירה; תחושה רכה לקריאה ממושכת.",
    theme: "light",
    treatment: "paper",
    tokens: {
      bg: "#e9ece3",
      surface: "#f8f9f2",
      surface2: "#dce4d5",
      ink: "#35204f",
      muted: "#62516e",
      line: "#75816d",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#e4dce9",
    },
    swatches: ["#e9ece3", "#dce4d5", "#35204f", "#634086"],
  },
  {
    id: "split",
    name: "קו ירוק",
    nameEn: "Green divide",
    description: "שדה אפור בהיר מול ירוק מעושן; חלוקת רקעים מדגישה את המבנה הקיים.",
    theme: "light",
    treatment: "split",
    tokens: {
      bg: "#f0f2ef",
      surface: "#f9faf6",
      surface2: "#bfcec1",
      ink: "#35204f",
      muted: "#584365",
      line: "#627164",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#633c87",
      soft: "#e1d8e9",
    },
    swatches: ["#f0f2ef", "#bfcec1", "#35204f", "#634086"],
  },
  {
    id: "graphite",
    name: "גרפיט",
    nameEn: "Graphite",
    description: "גרפיט ירקרק עמוק עם שכבות פחם; לבנדר מאיר את הטקסט ואת הפעולות.",
    theme: "dark",
    treatment: "graphite",
    tokens: {
      bg: "#262c2a",
      surface: "#303a35",
      surface2: "#3a463e",
      ink: "#f2eafa",
      muted: "#c6b9d1",
      line: "#8e9c90",
      accent: "#c1a3e5",
      accentInk: "#2f1c41",
      link: "#d3b7f2",
      soft: "#44364f",
    },
    swatches: ["#262c2a", "#3a463e", "#f2eafa", "#c1a3e5"],
  },
  {
    id: "forest",
    name: "יער לילי",
    nameEn: "Forest night",
    description: "ירוק יער לילי ושכבות עמוקות; סגול לבנדר בולט מעל האווירה הכהה.",
    theme: "dark",
    treatment: "forest",
    tokens: {
      bg: "#182e28",
      surface: "#223e33",
      surface2: "#2d4c3d",
      ink: "#f6edff",
      muted: "#cbbdd6",
      line: "#8b9f8f",
      accent: "#c1a3e5",
      accentInk: "#2d1c3f",
      link: "#ddc2ff",
      soft: "#493850",
    },
    swatches: ["#182e28", "#2d4c3d", "#f6edff", "#c1a3e5"],
  },
  {
    id: "fern",
    name: "שרך",
    nameEn: "Fern",
    description: "ירוק שרך אפור ומורגש, עם משטחים בגוון עלים וסגול שמאזן את הרוויה.",
    theme: "light",
    treatment: "fern",
    tokens: {
      bg: "#c3d2c6",
      surface: "#e7eee3",
      surface2: "#adbfaf",
      ink: "#35204f",
      muted: "#4f3b5f",
      line: "#50634f",
      accent: "#634086",
      accentInk: "#fffaf2",
      link: "#5b347e",
      soft: "#d8cde2",
    },
    swatches: ["#c3d2c6", "#adbfaf", "#35204f", "#634086"],
  },
];

export function paletteById(id: string | null): ColorPalette {
  return colorPalettes.find((palette) => palette.id === id) ?? colorPalettes[0];
}
