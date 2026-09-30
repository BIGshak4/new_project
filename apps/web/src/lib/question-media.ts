import sourceScreenshots from "./source-screenshots.json";
import type { ResourceMedia } from "./practice-api";

const withheld = new Set<string>(sourceScreenshots);

// Compatibility for already-issued resource responses during the API rollout.
// The server enforces the same boundary using the manifest's source_path.
export function visibleQuestionMedia(media: ResourceMedia[]): ResourceMedia[] {
  return media.filter(item => !withheld.has(item.filename));
}
