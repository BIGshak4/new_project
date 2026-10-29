import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import ts from "typescript";

const src = fileURLToPath(new URL("../src/", import.meta.url));
const repository = path.resolve(src, "../../..");
const demoClient = path.join(src, "lib/duel-demo.ts");
const demoAnswers = path.join(src, "components/duels/quiz-demo-data.json");
const seeds = path.join(repository, "backend/seeds");

/** Include runtime re-exports and nested import() calls, while excluding erased types. */
function runtimeSpecifiers(source: string, filename: string): string[] {
  const ast = ts.createSourceFile(filename, source, ts.ScriptTarget.Latest, true);
  const specifiers = new Set<string>();
  function walk(node: ts.Node) {
    if (ts.isImportDeclaration(node) && ts.isStringLiteralLike(node.moduleSpecifier)) {
      const clause = node.importClause;
      const names = clause?.namedBindings;
      const erased = clause?.isTypeOnly || (!clause?.name && names && ts.isNamedImports(names) && names.elements.length > 0 && names.elements.every(name => name.isTypeOnly));
      if (!erased) specifiers.add(node.moduleSpecifier.text);
    } else if (ts.isExportDeclaration(node) && !node.isTypeOnly && node.moduleSpecifier && ts.isStringLiteralLike(node.moduleSpecifier)) {
      const names = node.exportClause;
      const erased = names && ts.isNamedExports(names) && names.elements.length > 0 && names.elements.every(name => name.isTypeOnly);
      if (!erased) specifiers.add(node.moduleSpecifier.text);
    } else if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword || (ts.isIdentifier(node.expression) && node.expression.text === "require"))) {
      const argument = node.arguments[0];
      if (argument && ts.isStringLiteralLike(argument)) specifiers.add(argument.text);
    }
    ts.forEachChild(node, walk);
  }
  walk(ast);
  return [...specifiers];
}

function reachable(entry: string): Set<string> {
  const visited = new Set<string>();
  function visit(file: string) {
    if (visited.has(file)) return;
    visited.add(file);
    if (!/\.[cm]?[jt]sx?$/.test(file)) return; // JSON and styles are leaves, still recorded.
    for (const specifier of runtimeSpecifiers(readFileSync(file, "utf8"), file)) {
      if (!specifier.startsWith(".") && !specifier.startsWith("@/")) continue;
      const base = specifier.startsWith("@/") ? path.resolve(src, specifier.slice(2)) : path.resolve(path.dirname(file), specifier);
      const extensions = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json"];
      const candidates = [base, ...extensions.map(ext => base + ext), ...extensions.map(ext => path.join(base, "index" + ext))];
      const target = candidates.find(candidate => existsSync(candidate) && statSync(candidate).isFile());
      assert.ok(target, `Unresolved local runtime import ${specifier} from ${path.relative(src, file)}; extend the graph resolver rather than silently omitting it.`);
      visit(target);
    }
  }
  visit(entry);
  return visited;
}

for (const route of ["app/games/page.tsx", "app/duel/[code]/page.tsx"]) {
  test(`${route} cannot ship demo answers or backend seeds through its import graph`, () => {
    const graph = reachable(path.join(src, route));
    assert.ok(graph.has(path.join(src, "lib/duel-api.ts")), "the real route must retain the authenticated game API");
    assert.ok(!graph.has(demoClient), "the simulator must remain exclusive to the preview route");
    assert.ok(!graph.has(demoAnswers), "draft demo answers must never enter the live game bundle");
    assert.deepEqual([...graph].filter(file => file === seeds || file.startsWith(seeds + path.sep)), [], "backend answer-bearing seeds cannot be imported into a client route");
  });
}

test("the public preview reaches its explicit demo dataset without importing the authenticated API", () => {
  const graph = reachable(path.join(src, "app/games/preview/page.tsx"));
  assert.ok(graph.has(demoClient));
  assert.ok(graph.has(demoAnswers), "the preview must exercise the actual synchronized game dataset");
  assert.ok(!graph.has(path.join(src, "lib/duel-api.ts")), "the simulator must not depend on the live authenticated client");
});

test("boundary scanner follows re-exports, lazy imports and CommonJS while erasing type-only imports", () => {
  const found = runtimeSpecifiers(`
    // import fake from './comment-only';
    import type { Example } from './types-only';
    import { type Example2 } from './named-types-only';
    import value, { type Example3 } from './default-runtime';
    import './side-effect';
    export type { Example4 } from './exported-type';
    export { type Example5 } from './exported-named-type';
    export { actual } from './re-export';
    export * from './barrel';
    const lazy = () => import('./lazy-answers.json');
    function legacy() { return require('./legacy'); }
  `, "fixture.ts");
  assert.deepEqual(found, ["./default-runtime", "./side-effect", "./re-export", "./barrel", "./lazy-answers.json", "./legacy"]);
});
