import { Children, cloneElement, Fragment, isValidElement, type ReactElement, type ReactNode } from "react";
import { segmentBidiText } from "../lib/bidi-segments";

type InlineProps = { children?: ReactNode; dir?: string; style?: { direction?: string; unicodeBidi?: string }; dangerouslySetInnerHTML?: unknown; node?: { tagName?: string } };
type InlineTree = { original: ReactNode; text: string; children?: InlineTree[]; element?: ReactElement<InlineProps> };
const transparentTags = new Set(["a", "abbr", "b", "code", "del", "em", "i", "mark", "s", "small", "span", "strong", "sub", "sup", "u"]);

function inlineTree(node: ReactNode): InlineTree | null {
  if (typeof node === "string" || typeof node === "number") return { original: node, text: String(node) };
  if (!isValidElement<InlineProps>(node)) return null;
  const tag = typeof node.type === "string" ? node.type : node.props.node?.tagName;
  // Markdown supplies renderer components with the original HAST tag in props.
  // Explicit direction wrappers, code blocks and unknown components stay opaque.
  // Inline code is kept intact inside the enclosing isolate, never re-tokenized.
  if (node.type !== Fragment && (!tag || !transparentTags.has(tag))) return null;
  if (node.props.dir || node.props.style?.direction || node.props.style?.unicodeBidi || node.props.dangerouslySetInnerHTML) return null;
  const children = Children.toArray(node.props.children).map(inlineTree);
  if (children.some(child => child === null)) return null;
  const known = children as InlineTree[];
  return { original: node, text: known.map(child => child.text).join(""), children: known, element: node };
}

function sliceTree(tree: InlineTree, start: number, end: number, key: string): ReactNode {
  if (start === 0 && end === tree.text.length) return tree.original;
  if (!tree.element || !tree.children) return tree.text.slice(start, end);
  let offset = 0;
  const children = tree.children.flatMap((child, index) => {
    const from = Math.max(0, start - offset);
    const to = Math.min(child.text.length, end - offset);
    offset += child.text.length;
    return to > from ? [sliceTree(child, from, to, `${key}-${index}`)] : [];
  });
  return cloneElement(tree.element, { key }, children);
}

function renderRun(trees: InlineTree[], key: number): ReactNode[] {
  const text = trees.map(tree => tree.text).join("");
  let start = 0;
  return segmentBidiText(text).map((segment, index) => {
    const end = start + segment.text.length;
    let offset = 0;
    const children = trees.flatMap((tree, treeIndex) => {
      const from = Math.max(0, start - offset);
      const to = Math.min(tree.text.length, end - offset);
      offset += tree.text.length;
      return to > from ? [sliceTree(tree, from, to, `${key}-${index}-${treeIndex}`)] : [];
    });
    start = end;
    return segment.direction === "ltr" ? <bdi key={`${key}-${index}`} dir="ltr">{children}</bdi> : <Fragment key={`${key}-${index}`}>{children}</Fragment>;
  });
}

/** Keep technical expressions intact inside surrounding Hebrew prose. */
export function BidiText({ children }: { children?: ReactNode }) {
  const result: ReactNode[] = [];
  let run: InlineTree[] = [];
  const flush = () => {
    if (run.length) result.push(...renderRun(run, result.length));
    run = [];
  };
  for (const child of Children.toArray(children)) {
    const tree = inlineTree(child);
    if (tree) run.push(tree);
    else { flush(); result.push(child); }
  }
  flush();
  return <>{result}</>;
}
