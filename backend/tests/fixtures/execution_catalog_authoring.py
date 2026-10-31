"""Trusted authoring models for execution_cases.json; never accepts learner source.

Generate with .venv/Scripts/python.exe tests/fixtures/execution_catalog_authoring.py.
Finite examples check behavior, not complexity, prohibited operations, or hardware area.
Expected results are private broker data and must never be sent into a learner VM.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND.parent


def pair_sum(a, target):
    for i in range(len(a)):
        for j in range(i + 1, len(a)):
            if a[i] + a[j] == target:
                return [i, j]
    return None


def brackets(text, mixed=False):
    # An independent reduction oracle, deliberately not the candidate stack method.
    if mixed:
        text = "".join(c for c in text if c in "()[]{}")
    while True:
        shorter = text.replace("()", "").replace("[]", "").replace("{}", "")
        if shorter == text:
            return not text
        text = shorter


def max_subarray(a):
    if not a:
        return None
    candidates = [(sum(a[i:j + 1]), i, j) for i in range(len(a)) for j in range(i, len(a))]
    best = min(candidates, key=lambda item: (-item[0], item[1], item[2]))
    return list(best)


def longest_mod3(a):
    candidates = [(j - i + 1, i, j) for i in range(len(a)) for j in range(i, len(a))
                  if sum(a[i:j + 1]) % 3 == 0]
    return list(min(candidates, key=lambda item: (-item[0], item[1], item[2]))) if candidates else [0, None, None]


def postfix(tokens):
    # Recursively consume the expression from the right; no evaluator stack is shared.
    def consume(end):
        token = tokens[end]
        if isinstance(token, int):
            return token, end - 1
        right, end = consume(end - 1)
        left, end = consume(end)
        return {"+": lambda: left + right, "-": lambda: left - right, "*": lambda: left * right}[token](), end
    value, remaining = consume(len(tokens) - 1)
    assert remaining == -1
    return value


def fibonacci(n):
    # Count tilings / binomial identity, independent of iterative candidate recurrence.
    from math import comb
    return sum(comb(n - 1 - twos, twos) for twos in range((n - 1) // 2 + 1)) if n else 0


def reverse_words(text):
    import re
    return "".join(reversed(re.findall(r" +|[^ ]+", text)))


def two_missing(a):
    return sorted(set(range(len(a) + 2)) - set(a))


def one_missing(a):
    return next(iter(set(range(len(a) + 1)) - set(a)))


ORACLES = {
    "example-count-set-bits": lambda n: sum(int(c) for c in f"{n:032b}"),
    "example-power-of-two-check": lambda n: n in {2**i for i in range(32)},
    "example-extract-register-field": lambda n, lsb, width: (n // (2**lsb)) % (2**width),
    "example-first-greater-or-equal": lambda a, target: next((i for i, x in enumerate(a) if x >= target), len(a)),
    "example-merge-measurement-streams": lambda a, b: sorted(a + b),
    "example-pair-sum-indices": pair_sum,
    "example-balanced-brackets": brackets,
    "prep-power-of-two-check": lambda n: n in {2**i for i in range(32)},
    "prep-reverse-exactly-eight-bits-without-array": lambda n: int(f"{n:08b}"[::-1], 2),
    "prep-byte-popcount-parallel-and-lookup": lambda n: sum(int(c) for c in f"{n:08b}"),
    "prep-one-active-bit-signed-int32-pattern": lambda n: f"{n % (2**32):032b}".count("1") == 1,
    "prep-ascii-letter-palindrome-two-pointers": lambda s: s == s[::-1],
    "prep-balanced-brackets-mixed-text": lambda s: brackets(s, mixed=True),
    "prep-first-equal-in-sorted-array": lambda a, v: a.index(v) if v in a else -1,
    "prep-maximum-sum-contiguous-subarray": max_subarray,
    "prep-postfix-expression-stack-evaluation": postfix,
    "prep-three-color-in-place-partition": sorted,
    "prep-two-missing-zero-through-n-plus-one-no-aux-array": two_missing,
    "prep-one-two-missing-values": one_missing,
    "prep-longest-contiguous-sum-divisible-by-three": longest_mod3,
    "prep-software-fibonacci-recursion-improvement": fibonacci,
    "prep-all-distinct-string-permutations": lambda s: sorted({"".join(p) for p in itertools.permutations(s)}),
    "prep-reverse-words-using-character-reversal": reverse_words,
}


COUNTER_STIMULUS = [(1, 1), (0, 0)] + [(int(i in (15, 29)), int(i % 5 not in (0, 1))) for i in range(45)]
SEQUENCE_STIMULUS = [(1, 1)] + [(0, int(c)) for c in "1101110111010011011010110110"] + [(1, 1)] + [(0, int(c)) for c in "1011101101"]


def counter_output():
    out = []
    enabled_since_reset = 0
    for rst, enable in COUNTER_STIMULUS:
        enabled_since_reset = 0 if rst else enabled_since_reset + enable
        out.append(str(enabled_since_reset % 6))
    return "\n".join(out) + "\n"


def sequence_output():
    history = ""
    out = []
    for rst, bit in SEQUENCE_STIMULUS:
        history = "" if rst else history + str(bit)
        out.append(str(int(history.endswith("1101"))))
    return "\n".join(out) + "\n"


def scalar_program(entry, language):
    suffix = "c" if language == "c" else "cpp"
    return ('#include <stdio.h>\n#include <stdint.h>\n#include <inttypes.h>\n'
            f'#include "solution.{suffix}"\n'
            'int main(void) { uint32_t n; if (scanf("%" SCNu32, &n) != 1) return 2;\n'
            f'  printf("%u\\n", (unsigned){entry}(n)); return 0; }}\n')


def scalar_languages(entry, inputs, oracle, *, include_c=True):
    cases = [{"args": [n], "expected": oracle(n)} for n in inputs]
    languages = {
        "python": {"kind": "function", "entry": entry, "cases": cases,
                   "starter": f"def {entry}(n):\n    # Return the result; do not print it.\n    raise NotImplementedError\n"},
        "javascript": {"kind": "function", "entry": entry, "cases": cases,
                       "starter": f"function {entry}(n) {{\n  // Return the result; do not print it.\n  throw new Error('Implement me');\n}}\n"},
    }
    if include_c:
        for language in ("c", "cpp"):
            languages[language] = {
                "kind": "program", "driver": scalar_program(entry, language),
                "cases": [{"stdin": f"{n}\n", "expected_stdout": f"{int(oracle(n))}\n"} for n in inputs],
                "starter": f"#include <stdint.h>\nuint32_t {entry}(uint32_t n) {{\n    /* Return the result; do not define main. */\n    return 0;\n}}\n",
            }
    return languages


def build_manifest():
    bank = json.loads((BACKEND / "seeds/questions/example_bank.json").read_text(encoding="utf-8"))
    questions = {}

    def add(key, entry, params, inputs, he, en, *, js=True, unordered=False):
        cases = [{"args": args, "expected": ORACLES[key](*args), **({"unordered": True} if unordered else {})}
                 for args in inputs]
        languages = {"python": {"kind": "function", "entry": entry, "cases": cases,
                                "starter": f"def {entry}({', '.join(params)}):\n    raise NotImplementedError\n"}}
        if js:
            languages["javascript"] = {"kind": "function", "entry": entry, "cases": cases,
                                       "starter": f"function {entry}({', '.join(params)}) {{\n  throw new Error('Implement me');\n}}\n"}
        questions[key] = {"contract": {"he": he, "en": en}, "languages": languages}

    legacy_entries = {
        "example-count-set-bits": ("count_set_bits", ["n"], "החזירו את מספר ביטי ה־1 במילה unsigned בת 32 ביט.", "Return the number of set bits in an unsigned 32-bit value."),
        "example-power-of-two-check": ("is_power_of_two", ["n"], "החזירו ערך בוליאני: האם n בתחום unsigned32 הוא חזקה של 2. אפס אינו חזקה.", "Return a Boolean indicating whether unsigned32 n is a power of two. Zero is not."),
        "example-extract-register-field": ("extract_field", ["reg", "lsb", "width"], "החזירו את השדה המיושר לימין. הקלט חוקי וכולל width=32.", "Return the right-aligned field. Inputs obey the prompt and include width=32."),
        "example-first-greater-or-equal": ("lower_bound", ["a", "target"], "החזירו את האינדקס הראשון שערכו לפחות target, או len(a).", "Return the first index with value at least target, or the array length."),
        "example-merge-measurement-streams": ("merge", ["a", "b"], "החזירו מערך ממוזג וממוין המשמר את כל הכפילויות.", "Return the merged sorted array, preserving every duplicate."),
        "example-pair-sum-indices": ("pair_sum", ["a", "target"], "החזירו [i,j] לשני אינדקסים שונים, או null/None כשאין זוג. למקרים כאן יש זוג יחיד; סדר האינדקסים חופשי.", "Return [i,j] for distinct indices, or null/None when absent. Cases have a unique pair; index order is unrestricted."),
        "example-balanced-brackets": ("is_balanced", ["text"], "החזירו בוליאני עבור קינון תקין של (), [] ו־{}. מחרוזת ריקה תקינה.", "Return a Boolean for correctly nested (), [] and {}. Empty input is valid."),
    }
    for q in bank:
        if q["key"] not in legacy_entries:
            continue
        key = q["key"]
        entry, params, he, en = legacy_entries[key]
        inputs = [c["args"] for c in q["deterministic_check"]["spec"]["cases"]]
        add(key, entry, params, inputs, he, en)
        if key == "example-pair-sum-indices":
            for language in questions[key]["languages"].values():
                for case in language["cases"]:
                    if case["expected"] is not None:
                        case["unordered"] = True

    # Add boundary patterns missed by a scalar shortcut (sign bit, full word, empty input).
    words = [0, 1, 2, 3, 7, 16, 31, 255, 256, 65535, 2147483647, 2147483648, 4294967295]
    for key, entry in (("example-count-set-bits", "count_set_bits"), ("example-power-of-two-check", "is_power_of_two")):
        original = next(q for q in bank if q["key"] == key)
        values = sorted(set(words + [c["args"][0] for c in original["deterministic_check"]["spec"]["cases"]]))
        questions[key]["languages"] = scalar_languages(entry, values, ORACLES[key])
        questions[key]["contract"]["en"] += f" Python/JavaScript: {entry}(n). C/C++: uint32_t {entry}(uint32_t n), returning 0/1 for a Boolean. Do not define main."
        questions[key]["contract"]["he"] += f" חתימת Python/JavaScript: {entry}(n). ב־C/C++: uint32_t {entry}(uint32_t n), עם 0/1 לתוצאה בוליאנית, ללא main."

    add("prep-power-of-two-check", "is_power_of_two", ["n"], [[n] for n in words],
        "ממשו is_power_of_two(n) עבור unsigned32; החזירו בוליאני. נבדקת התוצאה; מספר הפעולות נבדק בהסבר.",
        "Implement is_power_of_two(n) for unsigned32, returning a Boolean. Tests check output; the operation-count argument is reviewed separately.")
    questions["prep-power-of-two-check"]["languages"] = scalar_languages("is_power_of_two", words, ORACLES["prep-power-of-two-check"])
    questions["prep-power-of-two-check"]["contract"]["en"] += " C/C++ signature: uint32_t is_power_of_two(uint32_t n), returning 0/1; no main."
    questions["prep-power-of-two-check"]["contract"]["he"] += " ב־C/C++ החתימה uint32_t is_power_of_two(uint32_t n), תוצאה 0/1, ללא main."

    byte_patterns = [0, 1, 2, 3, 4, 7, 8, 15, 16, 17, 31, 32, 42, 63, 64, 65,
                     85, 102, 127, 128, 129, 153, 170, 192, 204, 224, 240, 247, 251, 253, 254, 255]
    for key, entry, he, en in (
        ("prep-reverse-exactly-eight-bits-without-array", "reverse8", "החזירו את היפוך כל שמונת הביטים; אפסים מובילים נכללים. נבדק החלק של רוחב 8 בלבד.", "Return the reversal of all eight bits, including leading zeros. This tests only the fixed-eight-bit part."),
        ("prep-byte-popcount-parallel-and-lookup", "popcount8", "החזירו מספר ביטי 1 בבית. הבדיקות אינן מוכיחות היעדר לולאה או שימוש בטבלה.", "Return a byte's set-bit count. Output checks cannot establish loop-free operation or table use."),
    ):
        questions[key] = {"contract": {
            "he": he + f" Python/JavaScript: {entry}(n). ב־C/C++: uint32_t {entry}(uint32_t n), ללא main; הקלט 0..255.",
            "en": en + f" Python/JavaScript: {entry}(n). C/C++: uint32_t {entry}(uint32_t n), no main; input 0..255.",
        }, "languages": scalar_languages(entry, byte_patterns, ORACLES[key])}

    add("prep-one-active-bit-signed-int32-pattern", "is_one_bit_active", ["n"],
        [[n] for n in [-2147483648, -2147483647, -1, 0, 1, 2, 3, 524288, 786432, 2147483647]],
        "ממשו is_one_bit_active(n) והחזירו בוליאני על כל דפוס int32, כולל ביט הסימן; INT32_MIN מחזיר true.",
        "Implement is_one_bit_active(n), returning a Boolean over the whole int32 pattern, including the sign bit; INT32_MIN is true.")
    add("prep-ascii-letter-palindrome-two-pointers", "is_palindrome", ["text"],
        [[s] for s in ["", "a", "Aa", "aBa", "abba", "abca", "abcba", "ZzZ", "abAB"]],
        "ממשו is_palindrome(text) עבור אותיות ASCII בלבד, בהשוואה רגישה לאות גדולה/קטנה. נבדקים רק קלטים חוקיים.",
        "Implement is_palindrome(text) for ASCII letters with case-sensitive comparison. Only promised valid inputs are tested.")
    add("prep-balanced-brackets-mixed-text", "is_balanced", ["text"],
        [[s] for s in ["", "hello", "a(b[c]{d})", "([)]", ")text(", "((text)", "{a+[b*(c)]}", "a]b", "x<>y"]],
        "ממשו is_balanced(text); התעלמו מתווים שאינם (), [] או {}. החזירו בוליאני. אין תחביר מרכאות או הערות מיוחד.",
        "Implement is_balanced(text), ignoring characters outside (), [] and {}. Return a Boolean; quotes/comments have no special syntax.")
    add("prep-first-equal-in-sorted-array", "first_equal", ["a", "value"],
        [[[], 1], [[1, 2, 2, 2, 3, 3, 3, 4], 3], [[1, 1, 1], 1], [[1, 2], 0], [[1, 2], 3], [[-5, -2, -2, 0], -2], [[5], 5]],
        "ממשו first_equal(a,value); החזירו אינדקס ראשון או ‎-1 בהיעדר ערך. זמן ריצה לוגריתמי דורש גם בדיקת ההסבר.",
        "Implement first_equal(a,value), returning the first index or -1 when absent. Logarithmic complexity also needs reasoning review.")
    add("prep-maximum-sum-contiguous-subarray", "max_subarray", ["a"],
        [[a] for a in [[], [-5], [-8, -2, -6], [0, 0], [1, -1, 1], [-2, 1, -3, 4, -1, 2, 1, -5, 4], [1, 2, -1], [-1, 2, 0, -2]]],
        "נבדק החלק המערכי: max_subarray(a) מחזירה [sum,start,end] עם קצוות כוללים ואפס־בסיס, או null/None לריק. בשוויון: תחילה התחלה מוקדמת ואז סוף מוקדם. לא נבדק ממשק הזרם.",
        "Array part only: max_subarray(a) returns [sum,start,end] with inclusive zero-based bounds, or null/None for empty input. Ties prefer earliest start then earliest end. The stream interface is not tested.")
    add("prep-postfix-expression-stack-evaluation", "evaluate_postfix", ["tokens"],
        [[[3, 2, "+", 5, "+", 2, "*"]], [[9]], [[3, 8, "-"]], [[-3, 2, "*"]], [[8, 3, 2, "-", "-"]], [[0, 5, "*", 4, "+"]]],
        "ממשו evaluate_postfix(tokens) עם מספרים שלמים והפעולות +,-,*. נבדקים ביטויים חוקיים בלבד; טיפול בקלט פסול נבדק בהסבר.",
        "Implement evaluate_postfix(tokens) with integer tokens and +,-,*. Only valid expressions are executed; invalid-input handling is reviewed separately.")
    add("prep-three-color-in-place-partition", "sort012", ["a"],
        [[a] for a in [[], [0], [2, 0, 1], [2, 2, 1, 0, 2, 0], [1, 1, 1], [0, 0, 2, 2], [2, 1, 0, 2, 1, 0]]],
        "נבדקת הרחבת 0/1/2: sort012(a) מסדרת במקום ומחזירה את המערך המסודר. הבדיקות משוות את הפלט בלבד; עבודה במקום, מעבר יחיד וזיכרון דורשים סקירה.",
        "Numeric 0/1/2 extension: sort012(a) mutates and returns the sorted array. Tests compare the returned values only; in-place operation, one traversal and memory use need review.")
    add("prep-two-missing-zero-through-n-plus-one-no-aux-array", "two_missing", ["a"],
        [[a] for a in [[], [0], [2], [3, 0], [6, 1, 4, 0, 2], [4, 3, 2, 1]]],
        "ממשו two_missing(a); len(a)=n, הערכים שונים ב־0..n+1. החזירו את שני החסרים בכל סדר. הבדיקה אינה מודדת זיכרון עזר.",
        "Implement two_missing(a): n distinct entries from 0..n+1. Return both missing numbers in any order. Tests do not measure auxiliary storage.", unordered=True)
    add("prep-one-two-missing-values", "missing_zero_to_n", ["a"],
        [[a] for a in [[], [0], [1], [3, 0, 1], [4, 1, 0, 2], [0, 1, 2, 3]]],
        "נבדק סעיף C בלבד: missing_zero_to_n(a), שבו n=len(a), עם ערכים שונים ב־0..n; החזירו את החסר היחיד. חלקי 1..N ושני חסרים אינם נבדקים כאן.",
        "Part C only: missing_zero_to_n(a), n=len(a), contains distinct values in 0..n. Return the one missing value. The 1..N/two-omission parts are not tested here.")
    add("prep-longest-contiguous-sum-divisible-by-three", "longest_mod3", ["a"],
        [[a] for a in [[], [1], [3], [1, 2], [1, 2, 4, 5, 6, 7], [1, 1, 1, 1], [2, 2], [6, 3, 9]]],
        "ממשו longest_mod3(a) לקלט חיובי; החזירו [length,start,end] עם סוף כולל. בהיעדר מקטע: [0,null,null]. בשוויון בחרו התחלה ואז סוף מוקדמים.",
        "Implement longest_mod3(a) for positive inputs; return [length,start,end] with inclusive end. No interval gives [0,null,null]. Ties prefer earlier start then end.")
    add("prep-software-fibonacci-recursion-improvement", "fibonacci", ["n"],
        [[n] for n in [0, 1, 2, 3, 4, 5, 10, 20, 30]],
        "ממשו fibonacci(n) ל־0..30 עם F0=0,F1=1. נבדק הערך בלבד; השוואת רקורסיה לאיטרציה והסיבוכיות נבדקות בהסבר.",
        "Implement fibonacci(n) for 0..30, with F0=0,F1=1. Tests check values; recursion versus iteration and complexity require reasoning review.")
    add("prep-all-distinct-string-permutations", "permutations", ["text"],
        [[s] for s in ["", "a", "ab", "abc", "aab", "aabb", "aaaa"]],
        "מתאם הבדיקה: permutations(text) מחזירה מערך של כל הפרמוטציות השונות, במקום הדפסה. הסדר חופשי; אין כפילויות. לפרמוטציה של הריק הפלט [\"\"].",
        "Test adapter: permutations(text) returns every distinct permutation as an array instead of printing. Order is arbitrary; no duplicates. Empty input gives [\"\"].", unordered=True)
    add("prep-reverse-words-using-character-reversal", "reverse_words", ["text"],
        [[s] for s in ["", "abc", "I am an engineer", " a  bb ", "one   two three", "   ", "a b c"]],
        "נבדק סעיף B: reverse_words(text) מחזירה סדר מילים הפוך ומשמרת את כל התווים, כולל היפוך סדר רצפי הרווחים. השימוש המחייב בפונקציית היפוך תווים דורש סקירה.",
        "Part B: reverse_words(text) returns reversed word order, retaining all characters and reversing the order of space runs. Mandatory reuse of the character-reversal function needs review.")

    counter_tb = '''`timescale 1ns/1ps
module tb;
reg clk=0, rst=0, enable=0;
wire [2:0] count;
enabled_mod_six_counter dut(.clk(clk),.rst(rst),.enable(enable),.count(count));
task sample(input r, input e);
begin
  clk=0; rst=r; enable=e; #5; clk=1; #1; $display("%0d",count); #4;
end
endtask
initial begin
''' + "".join(f"  sample(1'b{r},1'b{e});\n" for r, e in COUNTER_STIMULUS) + "  $finish(0);\nend\nendmodule\n"
    counter_starter = '''module enabled_mod_six_counter(input clk, rst, enable, output reg [2:0] count);
// Synchronous active-high reset, rising edge. Advance modulo 6 only when enabled.
always @(posedge clk) begin
    if (rst) count <= 3'd0;
    else begin
        // Implement update and recovery of states 6,7.
    end
end
endmodule
'''
    questions["prep-enabled-mod-six-counter"] = {"contract": {
        "he": "מודול enabled_mod_six_counter(clk,rst,enable,count[2:0]); reset סינכרוני פעיל בגבוה, חזית עולה, ספירת 0..5. נדגמים פלטים לאחר החזית, כולל השהיה, גלישה ואיפוס תוך enable=1. אין הזרקת מצבים פנימיים; התאוששות 6/7 דורשת סקירה.",
        "en": "Module enabled_mod_six_counter(clk,rst,enable,count[2:0]); rising edge, synchronous active-high reset, count 0..5. Samples cover holds, wrap and reset with enable=1. No internal-state injection: recovery from 6/7 needs review.",
    }, "languages": {lang: {"kind": "hdl", "top": "tb", "testbench": counter_tb,
                            "expected_stdout": counter_output(), "starter": counter_starter}
                     for lang in ("verilog", "systemverilog")}}

    sequence_tb = '''`timescale 1ns/1ps
module tb;
reg clk=0, rst=0, bit_in=0;
wire found;
sequence_1101 dut(.clk(clk),.rst(rst),.bit_in(bit_in),.found(found));
task sample(input r, input b);
begin
  clk=0; rst=r; bit_in=b; #5; clk=1; #1; $display("%0d",found); #4;
end
endtask
initial begin
''' + "".join(f"  sample(1'b{r},1'b{b});\n" for r, b in SEQUENCE_STIMULUS) + "  $finish(0);\nend\nendmodule\n"
    sequence_starter = '''module sequence_1101(input clk, rst, bit_in, output found);
// Overlapping Moore detector: found reflects the state after the sampling edge.
// Synchronous active-high reset clears found and all matched prefix history.
assign found = 1'b0;
endmodule
'''
    questions["prep-serial-1101-state-storage-count"] = {"contract": {
        "he": "נבדק ממשק Moore לאחר חזית: sequence_1101(clk,rst,bit_in,found), reset סינכרוני פעיל בגבוה. found=1 בדיוק כשארבעת הביטים האחרונים שנקלטו מאז reset הם 1101, כולל חפיפה. זה אינו בודק את טענת מינימום רכיבי הזיכרון או ממשק Mealy.",
        "en": "Post-edge Moore interface: sequence_1101(clk,rst,bit_in,found), synchronous active-high reset. found=1 exactly when the last four sampled bits since reset are 1101, including overlaps. Storage optimality and a Mealy timing alternative are not tested.",
    }, "languages": {lang: {"kind": "hdl", "top": "tb", "testbench": sequence_tb,
                            "expected_stdout": sequence_output(), "starter": sequence_starter}
                     for lang in ("verilog", "systemverilog")}}

    majority_tb = '''`timescale 1ns/1ps
module tb;
reg a,b,c; wire y; integer i;
majority3 dut(.a(a),.b(b),.c(c),.y(y));
initial begin
  for(i=0;i<8;i=i+1) begin {a,b,c}=i; #1; $display("%0d",y); end
  $finish(0);
end
endmodule
'''
    majority_vhdl_tb = '''library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_textio.all;
use ieee.numeric_std.all;
use std.textio.all;
entity tb is end entity;
architecture test of tb is
  signal x : std_logic_vector(2 downto 0) := (others => '0');
  signal y : std_logic;
begin
  dut: entity work.majority3 port map(a=>x(2),b=>x(1),c=>x(0),y=>y);
  process
    variable l : line;
  begin
    for i in 0 to 7 loop
      x <= std_logic_vector(to_unsigned(i,3)); wait for 1 ns;
      write(l, y); writeline(output,l);
    end loop;
    wait;
  end process;
end architecture;
'''
    majority_expected = "\n".join(str(int(sum(bits) >= 2)) for bits in itertools.product((0, 1), repeat=3)) + "\n"
    questions["example-sensor-majority"] = {"contract": {
        "he": "ממשק הבדיקה: רכיב צירופי majority3 עם כניסות ביט a,b,c ופלט y. הפלט 1 אם לפחות שתי כניסות הן 1. כל שמונת הצירופים נבדקים; אין שעון.",
        "en": "Test interface: combinational majority3 with one-bit a,b,c inputs and y output. y=1 iff at least two inputs are 1. All eight combinations are tested; no clock.",
    }, "languages": {
        lang: {"kind": "hdl", "top": "tb", "testbench": majority_tb, "expected_stdout": majority_expected,
               "starter": "module majority3(input a,b,c, output y);\nassign y = 1'b0;\nendmodule\n"}
        for lang in ("verilog", "systemverilog")
    }}
    questions["example-sensor-majority"]["languages"]["vhdl"] = {
        "kind": "hdl", "top": "tb", "testbench": majority_vhdl_tb, "expected_stdout": majority_expected,
        "starter": "library ieee;\nuse ieee.std_logic_1164.all;\nentity majority3 is\n  port(a,b,c: in std_logic; y: out std_logic);\nend entity;\narchitecture rtl of majority3 is\nbegin\n  y <= '0';\nend architecture;\n",
    }

    for key, module, width_in, width_out, values, oracle, he, en in (
        ("prep-eight-bit-unsigned-lower-clamp-sixty-four", "clamp64", 8, 8, range(256), lambda n: max(n, 64),
         "ממשו רכיב צירופי clamp64 עם x[7:0],y[7:0] unsigned; y=max(x,64). כל 256 הערכים נבדקים.",
         "Implement combinational clamp64 with unsigned x[7:0],y[7:0]; y=max(x,64). All 256 values are tested."),
        ("prep-unsigned-two-bit-combinational-square", "square2", 2, 4, range(4), lambda n: n*n,
         "ממשו רכיב צירופי square2 עם x[1:0],y[3:0] unsigned; y=x*x. ארבעת הקלטים נבדקים; אין בדיקת שטח או מגבלות שערים.",
         "Implement combinational square2 with unsigned x[1:0],y[3:0]; y=x*x. All four inputs are tested; gate/area restrictions need review."),
    ):
        tb = f'''`timescale 1ns/1ps
module tb;
reg [{width_in-1}:0] x; wire [{width_out-1}:0] y; integer i;
{module} dut(.x(x),.y(y));
initial begin
  for(i=0;i<{len(values)};i=i+1) begin x=i; #1; $display("%0d",y); end
  $finish(0);
end
endmodule
'''
        questions[key] = {"contract": {"he": he, "en": en}, "languages": {
            lang: {"kind": "hdl", "top": "tb", "testbench": tb,
                   "expected_stdout": "\n".join(str(oracle(n)) for n in values) + "\n",
                   "starter": f"module {module}(input [{width_in-1}:0] x, output [{width_out-1}:0] y);\nassign y = 0;\nendmodule\n"}
            for lang in ("verilog", "systemverilog")
        }}

    # Every function contract names the callable interface; this is a test adapter, not a new question.
    for question in questions.values():
        for language, spec in question["languages"].items():
            if spec["kind"] == "function":
                sig = spec["starter"].splitlines()[0].removeprefix("def ").removeprefix("function ").rstrip(": {")
                for lang in ("he", "en"):
                    if sig not in question["contract"][lang]:
                        question["contract"][lang] += f" {language}: {sig}."
    return {"version": 1, "questions": questions}


def build_smoke():
    """Developer-controlled sources for root's actual compiler/VM/browser smoke checks."""
    pop_python = "def count_set_bits(n):\n    count = 0\n    while n:\n        count += n & 1\n        n >>= 1\n    return count\n"
    pop_js = "function count_set_bits(n) {\n  let count = 0;\n  while (n !== 0) { count += n & 1; n >>>= 1; }\n  return count;\n}\n"
    pop_c = "#include <stdint.h>\nuint32_t count_set_bits(uint32_t n) {\n    uint32_t count = 0;\n    while (n) { count += n & 1u; n >>= 1; }\n    return count;\n}\n"
    counter = (ROOT / "interview_preparation/solutions/prep_202_enabled_mod_six_counter.sv").read_text(encoding="utf-8")
    counter = counter[counter.index("module "):]
    counter_v = counter.replace("input logic", "input").replace("output logic", "output reg").replace("always_ff", "always")
    vhdl = "library ieee;\nuse ieee.std_logic_1164.all;\nentity majority3 is\nport(a,b,c: in std_logic; y: out std_logic);\nend entity;\narchitecture rtl of majority3 is\nbegin\ny <= (a and b) or (a and c) or (b and c);\nend architecture;\n"
    cases = []
    for language, correct, wrong, syntax in (
        ("python", pop_python, "def count_set_bits(n):\n    return 0\n", "def count_set_bits(n)\n    return 0\n"),
        ("javascript", pop_js, "function count_set_bits(n) { return 0; }\n", "function count_set_bits( {\n"),
        ("c", pop_c, "#include <stdint.h>\nuint32_t count_set_bits(uint32_t n) { return 0; }\n", "#include <stdint.h>\nuint32_t count_set_bits(uint32_t n) { return n }\n"),
        ("cpp", pop_c, "#include <stdint.h>\nuint32_t count_set_bits(uint32_t n) { return 0; }\n", "#include <stdint.h>\nuint32_t count_set_bits(uint32_t n) { return n }\n"),
        ("verilog", counter_v, counter_v.replace("else if (enable)", "else if (1'b1)"), "module enabled_mod_six_counter(\n"),
        ("systemverilog", counter, counter.replace("else if (enable)", "else if (1'b1)"), "module enabled_mod_six_counter(\n"),
        ("vhdl", vhdl, vhdl.replace("(a and b) or (a and c) or (b and c)", "a xor b xor c"), vhdl.replace("y: out std_logic);", "y: out std_logic)")),
    ):
        key = "example-count-set-bits" if language in ("python", "javascript", "c", "cpp") else "example-sensor-majority" if language == "vhdl" else "prep-enabled-mod-six-counter"
        cases.append({"language": language, "question_key": key, "correct": correct, "wrong": wrong, "syntax_error": syntax})
    seq = (ROOT / "interview_preparation/solutions/prep_204_sequence_1101.sv").read_text(encoding="utf-8")
    cases.append({"language": "systemverilog", "question_key": "prep-serial-1101-state-storage-count",
                  "correct": seq[seq.index("module "):],
                  "wrong": seq[seq.index("module "):].replace("assign found = state == 3'd4;", "assign found = 1'b0;"),
                  "syntax_error": "module sequence_1101(\n"})
    return {"version": 1, "cases": cases}


if __name__ == "__main__":
    (BACKEND / "seeds/execution_cases.json").write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BACKEND / "tests/fixtures/execution_smoke.json").write_text(json.dumps(build_smoke(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
