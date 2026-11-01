"""Validate private execution contracts/oracles, without executing learner source.

Real compiler/VM smoke checks use fixtures/execution_smoke.json separately. These
tests do not claim compilation, synthesis, complexity, or formal verification.
"""

from __future__ import annotations

import itertools
import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parents[1]
AUTHORING = runpy.run_path(str(BACKEND / "tests/fixtures/execution_catalog_authoring.py"))
MANIFEST = json.loads((BACKEND / "seeds/execution_cases.json").read_text(encoding="utf-8"))
SMOKE = json.loads((BACKEND / "tests/fixtures/execution_smoke.json").read_text(encoding="utf-8"))
POSITIVE = json.loads((BACKEND / "tests/fixtures/execution_positive.json").read_text(encoding="utf-8"))
ORACLES = dict(AUTHORING["ORACLES"])
QUESTIONS = MANIFEST["questions"]
LANGUAGES = {"python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl"}
CATALOG = {
    q["key"]: q
    for filename in ("example_bank.json", "preparation_bank.json")
    for q in json.loads((BACKEND / "seeds/questions" / filename).read_text(encoding="utf-8"))
}
SPECS = [(key, language, spec) for key, question in QUESTIONS.items()
         for language, spec in question["languages"].items()]


def word_list_mode_oracle(words):
    # Independent list-count selection, deliberately not the reference's hash
    # table plus second pass. Python max keeps the first maximum on a tie.
    if not words:
        return None
    winner = max(words, key=words.count)
    return [winner, words.count(winner)]


ORACLES.update({
    "prep-merge-k-sorted-linked-lists": lambda lists: sorted(value for values in lists for value in values),
    "prep-most-frequent-word-list": word_list_mode_oracle,
    "prep-ascii-word-anagrams": lambda left, right: sorted(left) == sorted(right),
    "prep-stable-move-zeroes-to-end": lambda values: [value for value in values if value != 0] + [0] * values.count(0),
})


def fifo_request_transcript_oracle(stdin):
    """A linear sequence oracle, without ring-index-based queue decisions."""
    integers = list(map(int, stdin.split()))
    capacity, steps = integers[:2]
    assert capacity > 0 and steps >= 0 and len(integers) == 2 + 3 * steps
    pending, output = [], []
    writes = reads = 0
    for offset in range(2, len(integers), 3):
        write_request, value, read_request = integers[offset:offset + 3]
        wrote = bool(write_request and len(pending) < capacity)
        if wrote:
            pending.append(value)
            writes += 1
        read = bool(read_request and pending)
        answer = pending.pop(0) if read else 0
        reads += int(read)
        output.append(f"{int(wrote)} {int(read)} {answer}")
    output.append(f"{reads % capacity} {writes % capacity} {int(len(pending) == capacity)} {int(not pending)}")
    return "\n".join(output) + "\n"


# Hand-derived transcripts independently bind every C dictionary adapter case.
DICTIONARY_EXPECTED = {
    "0\n": "S 0\n",
    "4\nP a one\nG a\nP a two\nG a\n": "0\nV one\n0\nV two\nS 1\n",
    "6\nP a x\nP b y\nD a\nG a\nG b\nD b\n": "0\n0\n0\nN\nV y\n0\nS 0\n",
    "4\nP _ _\nG _\nD _\nG _\n": "0\nV \n0\nN\nS 0\n",
    "5\nP A first\nP a second\nG A\nG a\nD missing\n": "0\n0\nV first\nV second\n3\nS 2\n",
    "5\nP c third\nP b second\nP a first\nD b\nG c\n": "0\n0\n0\n0\nV third\nS 2\n",
}

CSV_EXPECTED = {
    "": [], "\n": [[""]], ",": [["", ""]], "a,b,": [["a", "b", ""]],
    "name,value\r\nx,12\r\n": [["name", "value"], ["x", "12"]],
    '"a,b",c': [["a,b", "c"]], '"a\r\nb","c""d"\r\n': [["a\r\nb", 'c"d']],
    '""': [[""]], '""""': [['"']], " a , b ": [[" a ", " b "]],
    "x\nlast,": [["x"], ["last", ""]], '"a\nb",c\n': [["a\nb", "c"]],
}


def test_manifest_is_versioned_and_all_contracts_belong_to_current_catalog():
    assert MANIFEST["version"] == 1
    assert len(QUESTIONS) == 36
    assert set(QUESTIONS) <= CATALOG.keys()
    for question in QUESTIONS.values():
        assert set(question["contract"]) == {"he", "en"}
        assert re.search(r"[א-ת]", question["contract"]["he"])
        assert not re.search(r"[א-ת]", question["contract"]["en"])
        assert question["languages"]
        assert set(question["languages"]) <= LANGUAGES


@pytest.mark.parametrize("key,language,spec", SPECS, ids=[f"{key}/{lang}" for key, lang, _ in SPECS])
def test_language_specs_have_complete_safe_contract_shapes(key, language, spec):
    assert isinstance(spec["starter"], str) and spec["starter"].strip()
    if spec["kind"] == "function":
        assert language in {"python", "javascript"}
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", spec["entry"])
        assert spec["entry"] in QUESTIONS[key]["contract"]["en"]
        assert 1 <= len(spec["cases"]) <= 32
        for case in spec["cases"]:
            assert isinstance(case["args"], list)
            assert "expected" in case
            assert set(case) <= {"args", "expected", "unordered"}
    elif spec["kind"] == "program":
        assert language in {"c", "cpp"}
        assert f'#include "solution.{language}"' in spec["driver"]
        assert "main(" in spec["driver"]
        assert 1 <= len(spec["cases"]) <= 32
        for case in spec["cases"]:
            assert isinstance(case["stdin"], str)
            assert isinstance(case["expected_stdout"], str)
    else:
        assert spec["kind"] == "hdl"
        assert language in {"verilog", "systemverilog", "vhdl"}
        assert re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", spec["top"])
        assert spec["testbench"].strip()
        assert spec["expected_stdout"].strip()
        # Oracle comparisons belong in the trusted broker, not the learner VM.
        assert "expected_stdout" not in spec["testbench"]
        assert "$fatal" not in spec["testbench"]
        assert "assert " not in spec["testbench"]
        if language in {"verilog", "systemverilog"}:
            # Icarus 12 prints a diagnostic footer for default $finish; its
            # verbosity argument must be zero to keep the stdout oracle exact.
            assert "$finish(0);" in spec["testbench"]
            assert "$finish;" not in spec["testbench"]


def test_all_seven_preexisting_python_tests_keep_their_test_inputs():
    existing = {q["key"]: q["deterministic_check"]["spec"] for q in CATALOG.values()
                if (q.get("deterministic_check") or {}).get("type") == "code_tests"}
    assert len(existing) == 7
    for key, old in existing.items():
        spec = QUESTIONS[key]["languages"]["python"]
        assert spec["kind"] == "function"
        assert spec["entry"] in old["entry"]
        for old_case in old["cases"]:
            matches = [case for case in spec["cases"] if case["args"] == old_case["args"]]
            assert matches, (key, old_case["args"])
            result = matches[0]["expected"]
            acceptable = old_case.get("accept", [old_case.get("expected")])
            if old_case.get("unordered") and isinstance(result, list):
                assert sorted(result) in [sorted(x) for x in acceptable]
            else:
                assert result in acceptable


@pytest.mark.parametrize("key,language,spec", [item for item in SPECS if item[2]["kind"] == "function"])
def test_function_expected_results_match_independent_reference_models(key, language, spec):
    oracle = ORACLES[key]
    for case in spec["cases"]:
        result = oracle(*case["args"])
        if case.get("unordered"):
            assert sorted(result) == sorted(case["expected"])
        else:
            assert result == case["expected"]


@pytest.mark.parametrize("key,language,spec", [item for item in SPECS if item[2]["kind"] == "program"])
def test_c_and_cpp_driver_cases_use_the_same_independent_scalar_oracles(key, language, spec):
    for case in spec["cases"]:
        if key == "prep-c-fifo-write-then-read-requests":
            assert language == "c"
            assert case["expected_stdout"] == fifo_request_transcript_oracle(case["stdin"])
            continue
        if key == "prep-c-linked-list-dictionary-ownership":
            assert language == "c"
            assert case["expected_stdout"] == DICTIONARY_EXPECTED[case["stdin"]]
            continue
        n = int(case["stdin"].strip())
        assert case["expected_stdout"] == f"{int(ORACLES[key](n))}\n"


def test_new_software_profiles_exercise_their_distinguishing_contract_boundaries():
    merge = QUESTIONS["prep-merge-k-sorted-linked-lists"]["languages"]["python"]["cases"]
    assert any(case["args"] == [[]] and case["expected"] == [] for case in merge)
    assert any(case["args"] == [[[], [], []]] and case["expected"] == [] for case in merge)
    assert any(case["expected"] == [2] * 6 for case in merge)

    mode = QUESTIONS["prep-most-frequent-word-list"]["languages"]["python"]["cases"]
    assert {"args": [["a", "b", "b", "a"]], "expected": ["a", 2]} in mode
    assert {"args": [["Cat", "cat", "Cat"]], "expected": ["Cat", 2]} in mode
    assert {"args": [["", "x", ""]], "expected": ["", 2]} in mode
    assert {"args": [[]], "expected": None} in mode

    anagrams = QUESTIONS["prep-ascii-word-anagrams"]["languages"]["python"]["cases"]
    assert {"args": ["aab", "abb"], "expected": False} in anagrams
    assert {"args": ["Ab", "ba"], "expected": False} in anagrams
    assert {"args": ["", ""], "expected": True} in anagrams
    assert {"args": ["abc", "ab"], "expected": False} in anagrams

    zeroes = QUESTIONS["prep-stable-move-zeroes-to-end"]["languages"]["python"]["cases"]
    assert {"args": [[1, 0, 9, 0, 3, 4, 5, 1]], "expected": [1, 9, 3, 4, 5, 1, 0, 0]} in zeroes
    assert {"args": [[0, -1, 0, -1, 2, 0]], "expected": [-1, -1, 2, 0, 0, 0]} in zeroes
    assert {"args": [[]], "expected": []} in zeroes


def test_fifo_profile_covers_empty_full_both_requests_and_wrap_without_conflation():
    spec = QUESTIONS["prep-c-fifo-write-then-read-requests"]["languages"]["c"]
    by_input = {case["stdin"]: case["expected_stdout"] for case in spec["cases"]}
    assert by_input["1 1\n1 7 1\n"] == "1 1 7\n0 0 0 1\n"
    assert by_input["1 2\n1 7 0\n1 9 1\n"] == "1 0 0\n0 1 7\n0 0 0 1\n"
    assert any(int(case["stdin"].split()[1]) > int(case["stdin"].split()[0]) for case in spec["cases"])
    for case in spec["cases"]:
        assert case["expected_stdout"] == fifo_request_transcript_oracle(case["stdin"])


def test_csv_profile_expected_rows_bind_quotes_multiline_empty_and_preserved_spaces():
    spec = QUESTIONS["prep-streaming-csv-parser-without-library"]["languages"]["python"]
    assert {case["args"][0] for case in spec["cases"]} == set(CSV_EXPECTED)
    for case in spec["cases"]:
        assert case["expected"] == CSV_EXPECTED[case["args"][0]]
    fixture = next(case for case in POSITIVE["cases"]
                   if case["question_key"] == "prep-streaming-csv-parser-without-library")
    namespace = {}
    exec(compile(fixture["source"], "<committed-CSV-reference>", "exec"), namespace)
    for text, expected in CSV_EXPECTED.items():
        for cut in range(len(text) + 1):
            assert list(namespace["iter_csv_rows"]([text[:cut], text[cut:]])) == expected
    for text in ['"unterminated', '"a"b', 'a"b', 'a\r']:
        with pytest.raises(ValueError):
            namespace["parse_csv"](text)


def test_dictionary_profile_is_self_contained_and_hand_checked():
    key = "prep-c-linked-list-dictionary-ownership"
    spec = QUESTIONS[key]["languages"]["c"]
    assert {case["stdin"] for case in spec["cases"]} == set(DICTIONARY_EXPECTED)
    for case in spec["cases"]:
        assert case["expected_stdout"] == DICTIONARY_EXPECTED[case["stdin"]]
    fixture = next(case for case in POSITIVE["cases"] if case["question_key"] == key)
    assert not re.search(r'^\s*#\s*include\s+"', fixture["source"], re.M)
    assert "typedef struct Dict Dict;" in fixture["source"]
    assert "dict_put" in fixture["source"] and "dict_destroy" in fixture["source"]
    assert '#include "solution.c"' in spec["driver"]


def test_reverse_profile_includes_identity_sensitive_cases_without_claiming_to_prove_identity():
    key = "prep-reverse-singly-linked-list-in-place"
    spec = QUESTIONS[key]["languages"]["python"]
    by_input = {tuple(case["args"][0]): case["expected"] for case in spec["cases"]}
    assert by_input[()] == [] and by_input[(1,)] == [1]
    assert by_input[(1, 2)] == [2, 1] and by_input[(0, 0, 0)] == [0, 0, 0]
    assert by_input[(-3, 0, 9, -3)] == [-3, 9, 0, -3]
    assert "value" in QUESTIONS[key]["contract"]["en"].lower()
    assert "identity" in QUESTIONS[key]["contract"]["en"].lower()


@pytest.mark.parametrize("key,language", [
    ("prep-c-linked-list-dictionary-ownership", "c"),
    ("prep-reverse-singly-linked-list-in-place", "python"),
    ("prep-streaming-csv-parser-without-library", "python"),
])
def test_latest_profiles_have_one_positive_and_semantically_wrong_fixture(key, language):
    positive = [item for item in POSITIVE["cases"] if item["question_key"] == key and item["language"] == language]
    smoke = [item for item in SMOKE["cases"] if item["question_key"] == key and item["language"] == language]
    assert len(positive) == len(smoke) == 1
    assert positive[0]["source"] == smoke[0]["correct"]
    if language == "python":
        namespace = {}
        exec(compile(smoke[0]["wrong"], "<committed-wrong-reference>", "exec"), namespace)
        spec = QUESTIONS[key]["languages"][language]
        assert any(namespace[spec["entry"]](*case["args"]) != case["expected"] for case in spec["cases"])


@pytest.mark.parametrize("key", [
    "prep-merge-k-sorted-linked-lists", "prep-most-frequent-word-list",
    "prep-ascii-word-anagrams", "prep-stable-move-zeroes-to-end",
    "prep-c-fifo-write-then-read-requests",
])
def test_each_new_profile_has_exactly_one_matching_positive_and_smoke_fixture(key):
    languages = set(QUESTIONS[key]["languages"])
    assert languages == ({"c"} if "fifo" in key else {"python"})
    for language in languages:
        positive = [item for item in POSITIVE["cases"] if item["question_key"] == key and item["language"] == language]
        smoke = [item for item in SMOKE["cases"] if item["question_key"] == key and item["language"] == language]
        assert len(positive) == len(smoke) == 1
        assert positive[0]["source"] == smoke[0]["correct"]
        assert len(QUESTIONS[key]["languages"][language]["cases"]) >= 5


def test_byte_boundary_patterns_and_exhaustive_truth_tables_are_not_only_happy_paths():
    for key in ("prep-reverse-exactly-eight-bits-without-array", "prep-byte-popcount-parallel-and-lookup"):
        cases = QUESTIONS[key]["languages"]["python"]["cases"]
        values = {c["args"][0] for c in cases}
        assert len(values) == 32
        assert {0, 1, 128, 255, 85, 170} <= values
        assert {1 << i for i in range(8)} <= values
    expected = [int(a + b + c >= 2) for a, b, c in itertools.product((0, 1), repeat=3)]
    for spec in QUESTIONS["example-sensor-majority"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected
    for spec in QUESTIONS["prep-eight-bit-unsigned-lower-clamp-sixty-four"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == [64] * 65 + list(range(65, 256))
    for spec in QUESTIONS["prep-unsigned-two-bit-combinational-square"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == [0, 1, 4, 9]


def test_enabled_counter_transcript_uses_legal_states_reset_priority_holds_and_wrap():
    stimuli = AUTHORING["COUNTER_STIMULUS"]
    # Independent state-transition model vs author's enabled-since-reset arithmetic.
    state = 0
    expected = []
    for reset, enabled in stimuli:
        if reset:
            state = 0
        elif enabled:
            state = (state + 1) % 6
        expected.append(state)
    assert all(0 <= state <= 5 for state in expected)
    assert any(a == 5 and b == 0 for a, b in zip(expected, expected[1:], strict=False))
    assert any(not rst and not en for rst, en in stimuli)
    assert any(rst and en for rst, en in stimuli)
    for spec in QUESTIONS["prep-enabled-mod-six-counter"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected


def test_1101_transcript_matches_independent_prefix_fsm_and_includes_overlap():
    # Longest matching prefix transition oracle; author used last-four-bit history.
    transitions = ((0, 1), (0, 2), (3, 2), (0, 4), (0, 2))
    state = 0
    expected = []
    for reset, bit in AUTHORING["SEQUENCE_STIMULUS"]:
        state = 0 if reset else transitions[state][bit]
        expected.append(int(state == 4))
    hits = [i for i, value in enumerate(expected) if value]
    assert any(b - a == 3 for a, b in zip(hits, hits[1:], strict=False)), "1101101 must exercise overlap"
    for spec in QUESTIONS["prep-serial-1101-state-storage-count"]["languages"].values():
        assert list(map(int, spec["expected_stdout"].splitlines())) == expected


@pytest.mark.parametrize("key,args,expected", [
    ("example-count-set-bits", [2147483648], 1),
    ("example-power-of-two-check", [0], False),
    ("example-extract-register-field", [4294967295, 0, 32], 4294967295),
    ("example-pair-sum-indices", [[6], 12], None),
    ("example-balanced-brackets", ["([)]"], False),
    ("prep-reverse-exactly-eight-bits-without-array", [1], 128),
    ("prep-one-active-bit-signed-int32-pattern", [-2147483648], True),
    ("prep-ascii-letter-palindrome-two-pointers", ["Aa"], False),
    ("prep-first-equal-in-sorted-array", [[1, 2], 3], -1),
    ("prep-maximum-sum-contiguous-subarray", [[-8, -2, -6]], [-2, 1, 1]),
    ("prep-maximum-sum-contiguous-subarray", [[0, 0]], [0, 0, 0]),
    ("prep-postfix-expression-stack-evaluation", [[3, 8, "-"]], -5),
    ("prep-one-two-missing-values", [[]], 0),
    ("prep-two-missing-zero-through-n-plus-one-no-aux-array", [[]], [0, 1]),
    ("prep-longest-contiguous-sum-divisible-by-three", [[1]], [0, None, None]),
])
def test_real_counterexamples_are_present_in_the_shipped_cases(key, args, expected):
    cases = QUESTIONS[key]["languages"]["python"]["cases"]
    assert {"args": args, "expected": expected} in cases or any(
        case["args"] == args and case["expected"] == expected for case in cases)


def test_smoke_fixtures_cover_correct_wrong_and_syntax_in_all_seven_languages():
    assert SMOKE["version"] == 1
    assert {case["language"] for case in SMOKE["cases"]} == LANGUAGES
    for case in SMOKE["cases"]:
        assert case["language"] in QUESTIONS[case["question_key"]]["languages"]
        assert all(isinstance(case[k], str) and case[k].strip() for k in ("correct", "wrong", "syntax_error"))
        assert len({case[k] for k in ("correct", "wrong", "syntax_error")}) == 3
    assert any(c["question_key"] == "prep-serial-1101-state-storage-count" for c in SMOKE["cases"])


def test_manifest_and_smoke_are_reproducible_author_artifacts():
    assert AUTHORING["build_manifest"]() == MANIFEST
    assert AUTHORING["build_smoke"]() == SMOKE
    assert AUTHORING["build_positive"]() == POSITIVE


def test_positive_developer_sources_cover_every_manifest_question_language_pair_once():
    assert POSITIVE["version"] == 1
    assert len(POSITIVE["cases"]) == len(SPECS)
    pairs = [(case["question_key"], case["language"]) for case in POSITIVE["cases"]]
    assert len(set(pairs)) == len(pairs)
    assert set(pairs) == {(key, language) for key, language, _ in SPECS}
    assert all(case["source"].strip() for case in POSITIVE["cases"])


@pytest.mark.parametrize("fixture", [case for case in POSITIVE["cases"] if case["language"] == "python"],
                         ids=lambda case: case["question_key"])
def test_committed_trusted_python_references_match_independent_expected_values(fixture):
    # This is a developer-only check of sources authored directly above and
    # committed in execution_positive.json. No network/learner source is accepted.
    namespace = {}
    exec(compile(fixture["source"], "<committed-developer-reference>", "exec"), namespace)
    spec = QUESTIONS[fixture["question_key"]]["languages"]["python"]
    for case in spec["cases"]:
        args = json.loads(json.dumps(case["args"]))  # sort012 intentionally mutates its input.
        actual = namespace[spec["entry"]](*args)
        expected = ORACLES[fixture["question_key"]](*case["args"])
        if case.get("unordered"):
            assert sorted(actual) == sorted(expected)
        else:
            assert type(actual) is type(expected)
            assert actual == expected


def test_committed_trusted_javascript_references_match_the_private_oracles():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is needed to validate developer-authored JavaScript reference fixtures")
    payload = []
    for fixture in POSITIVE["cases"]:
        if fixture["language"] != "javascript":
            continue
        spec = QUESTIONS[fixture["question_key"]]["languages"]["javascript"]
        payload.append({"question_key": fixture["question_key"], "source": fixture["source"], "entry": spec["entry"],
                        "args": [case["args"] for case in spec["cases"]]})
    script = """
const fs = require('node:fs'), vm = require('node:vm');
const fixtures = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = fixtures.map(fixture => fixture.args.map(args => {
  const context = vm.createContext({args});
  // Only the committed developer references are evaluated, never HTTP source.
  return vm.runInContext(fixture.source + '\\n' + fixture.entry + '(...args)', context, {timeout:500});
}));
process.stdout.write(JSON.stringify(results));
"""
    process = subprocess.run([node, "-e", script], input=json.dumps(payload).encode("utf-8"),
        capture_output=True, check=False, timeout=15)
    assert process.returncode == 0, process.stderr.decode("utf-8", errors="replace")
    actual = json.loads(process.stdout)
    for fixture, values in zip(payload, actual, strict=True):
        key = fixture["question_key"]
        spec = QUESTIONS[key]["languages"]["javascript"]
        for case, value in zip(spec["cases"], values, strict=True):
            if case.get("unordered"):
                assert sorted(value) == sorted(case["expected"])
            else:
                assert type(value) is type(case["expected"])
                assert value == case["expected"], (key, case["args"])


@pytest.mark.asyncio
async def test_backend_loads_private_specs_and_only_publishes_contracts_and_starters():
    from app.schemas.bank import BankQuestion
    from app.services.code_execution import CodeExecutionService

    settings = SimpleNamespace(code_execution_url="", code_execution_signing_seed=None,
        supabase_service_role_key=None, code_execution_enabled=False, code_execution_daily_limit=20,
        code_execution_per_minute=4, code_execution_concurrency=1, seeds_dir=BACKEND / "seeds")
    service = CodeExecutionService(settings)
    try:
        for key, question in QUESTIONS.items():
            bank_question = BankQuestion.model_validate(CATALOG[key])
            capabilities = await service.capabilities(bank_question)
            assert not capabilities.available
            assert set(capabilities.tested_languages) == set(question["languages"])
            assert capabilities.contract == question["contract"]
            for language, authored in question["languages"].items():
                spec = service.spec(bank_question, language)
                assert spec == {k: v for k, v in authored.items() if k != "starter"}
                assert capabilities.starters[language] == authored["starter"]
            public = capabilities.model_dump()
            assert "cases" not in public
            assert "testbench" not in public
            assert "expected_stdout" not in public
    finally:
        await service.aclose()
