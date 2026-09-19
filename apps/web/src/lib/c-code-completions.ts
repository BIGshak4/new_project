import {
  completeAnyWord,
  completeFromList,
  ifNotIn,
  snippetCompletion,
  type Completion,
} from "@codemirror/autocomplete";
import { cppLanguage } from "@codemirror/lang-cpp";

const keywords = (words: string): Completion[] =>
  words.split(" ").map((label) => ({ label, type: "keyword" }));
const library = (words: string, type: string, detail: string): Completion[] =>
  words.split(" ").map((label) => ({ label, type, detail }));

const common: Completion[] = [
  ...keywords(
    "auto break case char const continue default do double else enum extern float goto inline int long register return short signed sizeof static struct switch typedef union unsigned void volatile",
  ),
  ...library("size_t ptrdiff_t", "type", "<stddef.h>"),
  ...library(
    "int8_t int16_t int32_t int64_t uint8_t uint16_t uint32_t uint64_t",
    "type",
    "<stdint.h>",
  ),
  ...library("NULL", "constant", "<stddef.h>"),
  ...library(
    "printf fprintf snprintf scanf puts getchar fgets fopen fclose",
    "function",
    "<stdio.h>",
  ),
  ...library(
    "malloc calloc realloc free qsort bsearch abs strtol",
    "function",
    "<stdlib.h>",
  ),
  ...library(
    "strlen strcmp strncmp memcpy memmove memset",
    "function",
    "<string.h>",
  ),
  snippetCompletion(
    "for (size_t ${i} = 0; ${i} < ${count}; ++${i}) {\n\t${}\n}",
    { label: "for", type: "keyword", detail: "for (…) { … }" },
  ),
  snippetCompletion("if (${condition}) {\n\t${}\n}", {
    label: "if",
    type: "keyword",
    detail: "if (…) { … }",
  }),
  snippetCompletion("while (${condition}) {\n\t${}\n}", {
    label: "while",
    type: "keyword",
    detail: "while (…) { … }",
  }),
];

const cOnly = keywords(
  "restrict _Alignas _Alignof _Atomic _Bool _Complex _Generic _Imaginary _Noreturn _Static_assert _Thread_local",
);
const cppOnly = [
  ...keywords(
    "alignas alignof bool catch class constexpr consteval constinit delete explicit false friend mutable namespace new noexcept nullptr operator override private protected public reinterpret_cast static_assert static_cast template this thread_local throw true try typename using virtual wchar_t",
  ),
  ...library("std::vector", "class", "<vector>"),
  ...library("std::string", "class", "<string>"),
  ...library("std::array", "class", "<array>"),
  ...library(
    "std::sort std::min std::max std::find",
    "function",
    "<algorithm>",
  ),
  ...library("std::cout std::cin std::endl", "variable", "<iostream>"),
];

// Language data composes with basicSetup rather than replacing Python/JS completions.
// These are local editing aids, not type-aware member lookup or AI-generated answers.
const ignoredNodes = [
  "LineComment",
  "BlockComment",
  "String",
  "RawString",
  "CharLiteral",
  "SystemInclude",
];
export const cCompletionSources = {
  c: ifNotIn(
    ignoredNodes,
    completeFromList([
      ...common,
      ...cOnly,
      ...library("bool true false", "keyword", "<stdbool.h>"),
    ]),
  ),
  cpp: ifNotIn(ignoredNodes, completeFromList([...common, ...cppOnly])),
  words: ifNotIn(ignoredNodes, completeAnyWord),
};

export function cCodeCompletions(language: "c" | "cpp") {
  return [
    cppLanguage.data.of({ autocomplete: cCompletionSources[language] }),
    cppLanguage.data.of({ autocomplete: cCompletionSources.words }),
  ];
}
