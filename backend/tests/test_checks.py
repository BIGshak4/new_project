import pytest

from app.engine.checks import (
    BooleanParseError,
    check_numeric,
    check_truth_table,
    parse_boolean,
    run_check,
    truth_table,
)

ABC = ["A", "B", "C"]


class TestBooleanParser:
    def test_operator_spellings_agree(self):
        reference = truth_table("(A & B) | (~C)", ABC)
        for expression in ["AB + C'", "A*B + !C", "A and B or not C", "A·B ∨ ~C", "F = AB + C'"]:
            assert truth_table(expression, ABC) == reference, expression

    def test_precedence_not_and_xor_or(self):
        # A + B ^ C & A  ==  A | (B ^ (C & A))
        assert truth_table("A + B ^ C & A", ABC) == truth_table("A | (B ^ (C & A))", ABC)

    def test_postfix_complement_binds_to_group(self):
        assert truth_table("(A + B)'", ["A", "B"]) == [1, 0, 0, 0]

    def test_adjacency_with_parentheses(self):
        assert truth_table("A(B + C)", ABC) == truth_table("A & (B | C)", ABC)

    def test_demorgan_equivalence(self):
        assert truth_table("(AB)'", ["A", "B"]) == truth_table("A' + B'", ["A", "B"])

    def test_multi_letter_variables_need_explicit_and(self):
        assert truth_table("sel & en", ["sel", "en"]) == [0, 0, 0, 1]
        with pytest.raises(BooleanParseError):
            parse_boolean("selen", ["sel", "en"])

    @pytest.mark.parametrize("bad", ["A +", "(A + B", "A $ B", "A + D", "__import__('os')", ""])
    def test_rejects_garbage_without_executing(self, bad):
        with pytest.raises(BooleanParseError):
            parse_boolean(bad, ABC)

    @pytest.mark.parametrize("hostile", [lambda: "(" * 500 + "A" + ")" * 500, lambda: " + ".join(["A&B"] * 20000)],
                             ids=["deep_nesting", "sixty_thousand_terms"])
    def test_hostile_input_is_rejected_not_crashed(self, hostile):
        with pytest.raises(BooleanParseError):
            parse_boolean(hostile(), ABC)

    def test_long_complement_chains_do_not_recurse(self):
        assert truth_table("~" * 1500 + "A", ABC) == truth_table("A", ABC)
        assert truth_table("A" + "'" * 1501, ABC) == truth_table("~A", ABC)


class TestExpressionExtraction:
    spec = {"variables": ABC, "minterms": [3, 5, 6, 7], "output_name": "alarm"}

    @pytest.mark.parametrize("text,passed", [
        ("I would say alarm = AB + AC + BC because each pair suffices.", True),
        ("so alarm=AB+AC+BC.", True),
        ("alarm = (A+B)(A+C)(B+C) which is the POS form", True),
        ("Rows: 011, 101, 110, 111 give 1.\nalarm = AB + AC + BC\nXOR is parity.", True),
        ("A\nB\nalarm = A + B + C", False),
        ("I think C is the most important sensor.", None),
        ("ALARM = ab + ac + bc", None),
    ])
    def test_prose_around_the_expression(self, text, passed):
        assert check_truth_table(self.spec, text).passed is passed


class TestTruthTableCheck:
    spec = {"variables": ABC, "expression": "AB + A'C"}

    def test_equivalent_expression_passes(self):
        # consensus theorem: AB + A'C + BC == AB + A'C
        result = check_truth_table(self.spec, "AB + A'C + BC")
        assert result.passed is True

    def test_wrong_expression_reports_rows(self):
        result = check_truth_table(self.spec, "AB + C")
        assert result.passed is False
        assert result.mismatches and {"row", "inputs", "expected", "got"} <= result.mismatches[0].keys()

    def test_dont_cares_are_ignored(self):
        spec = {"variables": ["A", "B"], "minterms": [3], "dont_cares": [1, 2]}
        assert check_truth_table(spec, "A + B").passed is True      # differs only on don't-care rows
        assert check_truth_table(spec, "A'").passed is False

    def test_table_answer(self):
        spec = {"variables": ["A", "B"], "outputs": [0, 1, 1, 0]}
        assert check_truth_table(spec, {"outputs": [0, 1, 1, 0]}).passed is True
        assert check_truth_table(spec, {"expression": "A ^ B"}).passed is True

    def test_unparseable_answer_is_none_not_false(self):
        result = check_truth_table(self.spec, "it depends on the clock")
        assert result.passed is None


class TestNumericCheck:
    def test_bare_number_uses_expected_unit(self):
        assert check_numeric({"expected": 12.5, "unit": "ns", "tolerance_abs": 0.1}, "12.5").passed is True

    def test_unit_conversion(self):
        spec = {"expected": 12.5, "unit": "ns", "tolerance_abs": 0.1}
        assert check_numeric(spec, "12500 ps").passed is True
        assert check_numeric(spec, "0.0125 us").passed is True
        assert check_numeric(spec, "12.5 ms").passed is False

    def test_frequency(self):
        spec = {"expected": 80, "unit": "MHz", "tolerance_rel": 0.01}
        assert check_numeric(spec, "f_max = 80 MHz").passed is True
        assert check_numeric(spec, "0.08 GHz").passed is True
        assert check_numeric(spec, "90 MHz").passed is False

    def test_wrong_unit_kind_fails(self):
        assert check_numeric({"expected": 5, "unit": "ns"}, "5 MHz").passed is False

    def test_no_number(self):
        assert check_numeric({"expected": 5}, "about five").passed is None

    def test_relative_tolerance_default(self):
        assert check_numeric({"expected": 1000}, 1009).passed is True
        assert check_numeric({"expected": 1000}, 1011).passed is False


def test_run_check_dispatch():
    assert run_check(None, "x") is None
    assert run_check({"type": "sim", "spec": {}}, "x").passed is None
    check = {"type": "truth_table", "spec": {"variables": ["A", "B"], "expression": "A ^ B"}}
    assert run_check(check, "AB' + A'B").passed is True
    with pytest.raises(ValueError):
        run_check({"type": "magic", "spec": {}}, "x")
