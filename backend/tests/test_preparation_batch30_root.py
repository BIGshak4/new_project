"""Meaningful independent checks for the branch-free mapping and MUX library."""
import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "interview_preparation"


def test_mapping_and_mux_actual_models():
    spec = importlib.util.spec_from_file_location("batch30_root", ROOT / "checks/check_prep_119_120.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify()
    assert result["generalized_direction_checks"] == 131072
    assert result["single_mux_wiring_choices_exhausted"] == 64


def test_mapping_primary_implementation_has_no_branch_or_conditional_expression():
    tree = ast.parse((ROOT / "solutions/prep_119_toggle_nine_thirteen.py").read_text("utf-8"))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "toggle_nine_thirteen")
    assert not any(isinstance(node, (ast.If, ast.IfExp, ast.Match)) for node in ast.walk(function))
