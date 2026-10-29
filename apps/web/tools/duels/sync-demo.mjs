/** Curated public preview fixtures only. Never import this dataset into the live game client. */
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const seed = new URL("../../../../backend/seeds/duel_quiz.json", import.meta.url);
const destination = new URL("../../src/components/duels/quiz-demo-data.json", import.meta.url);
const sources = new Set([
  "quick-hw-03", "quick-hw-05", "quick-hw-09", "quick-hw-10", "quick-hw-15",
  "quick-hw-21", "quick-hw-40", "quick-sw-02", "quick-sw-03", "quick-sw-61",
]);
const questions = JSON.parse(readFileSync(seed, "utf8")).questions.filter(q => sources.has(q.source_key));
for (const source of sources) {
  const rows = questions.filter(q => q.source_key === source);
  if (rows.length !== 5 || new Set(rows.map(q => q.variant)).size !== 5) {
    throw new Error(`Expected five distinct curated variants for ${source}`);
  }
}
const serialized = JSON.stringify({
  _about: "Public, unreviewed demonstration questions. Simulated opponent and coins; no real match data. Synced from the curated seed subset by tools/duels/sync-demo.mjs.",
  questions,
}, null, 2) + "\n";
if (process.argv.includes("--check")) {
  if (readFileSync(destination, "utf8") !== serialized) throw new Error("Demo fixture differs from source. Run node tools/duels/sync-demo.mjs.");
  console.log(`Demo fixture matches ${questions.length} curated variants.`);
} else {
  writeFileSync(destination, serialized);
  console.log(`Wrote ${questions.length} demonstration variants to ${fileURLToPath(destination)}`);
}
