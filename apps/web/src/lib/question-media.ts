import sourceScreenshots from "./source-screenshots.json";
import type { ResourceMedia } from "./practice-api";

const withheld = new Set<string>(sourceScreenshots.map(filename => filename.toLowerCase()));

// Bare IDs and dated intake filenames are reserved for archived source images.
// Authored illustrations use descriptive names without an intake date.
const archivedImageName = /^prep-\d{3,}(?:-(?:.+-)?\d{4}-\d{2}-\d{2})?\.[^.]+$/i;
const archivedSourcePath = /(?:^|\/)sources(?:\/|$)/i;

function isArchivedSource(item: ResourceMedia): boolean {
  const filename = item.filename.replaceAll("\\", "/");
  // Normal API responses omit provenance, but cached/manifest-backed responses
  // may contain it. Never rely on the prompt/solution role to hide sources.
  const sourcePath = "source_path" in item ? item.source_path : undefined;
  if (archivedSourcePath.test(filename)
    || (typeof sourcePath === "string" && archivedSourcePath.test(sourcePath.replaceAll("\\", "/")))) {
    return true;
  }
  const basename = filename.slice(filename.lastIndexOf("/") + 1);
  return withheld.has(basename.toLowerCase())
    || (item.kind === "image" && archivedImageName.test(basename));
}

// Compatibility for already-issued resource responses during the API rollout.
// The server enforces the same boundary using the manifest's source_path.
export function visibleQuestionMedia(media: ResourceMedia[]): ResourceMedia[] {
  return media.filter(item => !isArchivedSource(item));
}
