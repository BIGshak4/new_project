/** Promote the author's standalone bold section labels without rewriting the answer or touching code. */
export function solutionMarkdown(text: string): string {
  let fence: { marker: string; length: number } | null = null;
  return text.split("\n").map((line) => {
    const delimiter = /^\s*(`{3,}|~{3,})/.exec(line);
    if (delimiter) {
      const marker = delimiter[1][0];
      if (!fence) fence = { marker, length: delimiter[1].length };
      else if (marker === fence.marker && delimiter[1].length >= fence.length) fence = null;
      return line;
    }
    if (fence) return line;
    const section = /^\*\*([^*\n]+)\*\*\s*(.*)$/.exec(line);
    return section ? `### ${section[1].replace(/:$/, "")}\n\n${section[2]}` : line;
  }).join("\n");
}
