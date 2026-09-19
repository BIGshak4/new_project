import test from "node:test";
import assert from "node:assert/strict";
import { EditorState } from "@codemirror/state";
import { CompletionContext } from "@codemirror/autocomplete";
import { cpp } from "@codemirror/lang-cpp";
import { cCompletionSources } from "../src/lib/c-code-completions";

function context(doc: string, explicit = false) {
  const state = EditorState.create({ doc, extensions: [cpp()] });
  return new CompletionContext(state, doc.length, explicit);
}

test("C completes standard functions and C++ keeps its own vocabulary", async () => {
  const c = await cCompletionSources.c(context("pri"));
  assert.equal(c?.from, 0);
  assert.ok(
    c?.options.some((o) => o.label === "printf" && o.detail === "<stdio.h>"),
  );
  assert.ok(!c?.options.some((o) => o.label === "class"));
  const cpp = await cCompletionSources.cpp(context("std::ve"));
  assert.equal(cpp?.from, 0);
  assert.ok(cpp?.options.some((o) => o.label === "std::vector"));
});

test("C completion is suppressed in comments, strings and character literals", async () => {
  for (const doc of [
    "// pri",
    "/* pri",
    'const char *s = "pri',
    "char c = 'p",
  ]) {
    assert.equal(await cCompletionSources.c(context(doc, true)), null, doc);
    assert.equal(await cCompletionSources.words(context(doc, true)), null, doc);
  }
});

test("local identifiers are suggested and a loop snippet inserts editable code", async () => {
  const words = await cCompletionSources.words(
    context("int sample_count = 0;\nsamp"),
  );
  assert.ok(words?.options.some((o) => o.label === "sample_count"));
  const result = await cCompletionSources.c(context("fo"));
  const completion = result?.options.find((o) => o.label === "for");
  assert.equal(typeof completion?.apply, "function");
  let state = EditorState.create({ doc: "fo" });
  if (typeof completion?.apply === "function") {
    completion.apply(
      {
        get state() {
          return state;
        },
        dispatch: (spec: Parameters<typeof state.update>[0]) => {
          state = state.update(spec).state;
        },
      } as Parameters<typeof completion.apply>[0],
      completion,
      0,
      2,
    );
  }
  assert.match(
    state.doc.toString(),
    /^for \(size_t i = 0; i < count; \+\+i\) \{\n/,
  );
  assert.ok(state.doc.toString().endsWith("\n}"));
});
