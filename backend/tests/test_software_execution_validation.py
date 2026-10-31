"""Operator-harness safety and assertion tests; no network or live execution."""

import hashlib
import json
import subprocess
import sys
import uuid

import httpx
import pytest
from app.config import Settings
from scripts.validate_software_execution import (
    BACKEND,
    PREFIX,
    LiveHTTPError,
    Validator,
    accepted,
    allocate,
    fixture_plan,
    is_software,
    output_dir,
)


def test_selection_matches_explicit_ui_category_override():
    assert is_software({"category": "software", "subject": "reasoning"})
    assert is_software({"category": None, "subject": "relevant_programming"})
    assert not is_software({"category": "hardware", "subject": "relevant_programming"})
    assert not is_software({"category": "logic", "subject": "programming"})


def test_exact_software_scope_plans_all_suites_and_cpp_checks_with_headroom():
    scope = json.loads((BACKEND / "tests/fixtures/software_question_scope.json").read_text(encoding="utf-8"))
    positives = json.loads((BACKEND / "tests/fixtures/execution_positive.json").read_text(encoding="utf-8"))["cases"]
    questions = [{"key": q["question_key"]} for q in scope["questions"]]
    budgets, assignments = allocate(questions, positives, maximum=4, minimum=4)
    assert len(questions) == len(assignments) == 66
    assert len(budgets) == 4 and sum(b["runs"] for b in budgets) == 183
    assert all(b["runs"] < 60 and b["attempts"] < 30 for b in budgets)
    jobs = [job for q in questions for job in fixture_plan(q["key"], positives)]
    assert sum(job["kind"] == "question_suite" for job in jobs) == 56
    assert sum(job["kind"] == "compile_error_probe" for job in jobs) == 66
    for q in questions:
        planned = fixture_plan(q["key"], positives)
        assert sum(job["language"] == "cpp" and job["kind"] != "compile_error_probe" for job in planned) == 1
    with pytest.raises(ValueError, match="allowance"):
        allocate(questions, positives, maximum=1)


def test_scope_matches_current_software_seeds_and_preserves_the_63_question_live_report():
    scope = json.loads((BACKEND / 'tests/fixtures/software_question_scope.json').read_bytes())
    seeds = {q['key']: q for name in ('example_bank.json', 'preparation_bank.json')
             for q in json.loads((BACKEND / 'seeds/questions' / name).read_bytes())}
    expected = {key for key, q in seeds.items()
                if is_software({'category': q.get('assets', {}).get('category'), 'subject': q['subject']})}
    rows = {q['question_key']: q for q in scope['questions']}
    assert len(rows) == len(scope['questions']) == scope['current_seed_count'] == 66
    assert rows.keys() == expected
    for key, row in rows.items():
        payload = json.dumps(seeds[key], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        assert hashlib.sha256(payload).hexdigest() == row['seed_question_sha256'], key
    assert set(scope['current_seed_additions']) == {
        'prep-damaged-triple-groups', 'prep-top-two-distinct-and-mode', 'prep-opaque-c-linked-list-adt'}
    historical = scope['historical_live_validation']
    assert historical['question_count'] == 63 and historical['planned_execution_jobs'] == 177
    assert historical['scope_fixture_sha256'] == '4fb0d4a93f2be2e1296548e20db6511857f1123959aa6db805e2d7d44270954a'
    report = BACKEND.parent / historical['report_path']
    expected_report_hash = 'e33959853626c6db7edf3e4f9e6cf756c0b5a8128668a1f3bf006d745cd53463'
    assert hashlib.sha256(report.read_bytes()).hexdigest() == historical['report_sha256'] == expected_report_hash


@pytest.mark.parametrize("changes", [{"compiled": None}, {"executed": False}, {"passed_count": 1},
                                     {"status": "completed"}, {"passed": None}, {"test_count": 0}])
def test_question_suite_never_accepts_incomplete_facts(changes):
    passed = dict(status="passed", compiled=True, executed=True, passed=True, test_count=14, passed_count=14)
    assert accepted("question_suite", passed)
    assert not accepted("question_suite", {**passed, **changes})


def test_standalone_probe_does_not_claim_question_correctness():
    result = dict(status="completed", compiled=True, executed=True, passed=None,
                  test_count=0, passed_count=0, stdout="jobrun-probe:42\n")
    assert accepted("transport_probe", result)
    assert not accepted("transport_probe", {**result, "passed": True})
    assert not accepted("transport_probe", {**result, "stdout": "jobrun-probe:41"})
    assert not accepted("transport_probe", {**result, "passed_count": 1})
    assert not accepted("question_suite", result)


def test_compile_error_requires_diagnostic_without_erasing_planned_tests():
    result = dict(status="compile_error", compiled=False, executed=False, passed=None,
                  test_count=17, passed_count=0, compile_output="error: invalid syntax")
    assert accepted("compile_error_probe", result)
    assert not accepted("compile_error_probe", {**result, "compile_output": ""})
    assert not accepted("compile_error_probe", {**result, "executed": True})
    assert not accepted("compile_error_probe", {**result, "passed_count": 1})


def test_live_and_ignored_destination_are_required_before_credentials():
    script = BACKEND / "scripts/validate_software_execution.py"
    result = subprocess.run([sys.executable, str(script), "provision", "--output", "elsewhere"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2 and "requires explicit --live" in result.stderr
    with pytest.raises(ValueError, match="ignored"):
        output_dir(BACKEND / "workdir/credentials")


def test_cleanup_refuses_unowned_identity_and_keeps_recovery_credentials(tmp_path):
    settings = Settings(_env_file=None, supabase_url="https://supabase.invalid", supabase_service_role_key="fixture-only")
    validator = Validator(settings, tmp_path, "https://api.invalid", "https://site.invalid")
    validator.state["accounts"] = [{"id": str(uuid.uuid4()), "email": "real-person@example.com", "password": "private-fixture"}]
    validator.save()
    requests = []
    validator.client.close()
    validator.client = httpx.Client(transport=httpx.MockTransport(lambda r: requests.append(r)))
    try:
        with pytest.raises(ValueError, match="outside this exact"):
            validator.cleanup()
        assert not requests and validator.state_path.exists()
        report = json.loads(validator.report_path.read_text(encoding="utf-8"))
        assert "private-fixture" not in json.dumps(report) and "real-person" not in json.dumps(report)
    finally:
        validator.close()


def test_cleanup_verifies_exact_auth_identity_and_cascade_rows(tmp_path):
    settings = Settings(_env_file=None, supabase_url="https://supabase.invalid", supabase_service_role_key="fixture-only")
    validator = Validator(settings, tmp_path, "https://api.invalid", "https://site.invalid")
    owned_email = f"{PREFIX}{validator.state['run_id']}-0@example.com"
    validator.state["accounts"] = [{"id": str(uuid.uuid4()), "email": owned_email, "password": "private-fixture"}]
    validator.save()
    events, deleted = [], False

    def respond(request):
        nonlocal deleted
        events.append((request.method, request.url.path))
        if "/auth/v1/admin/users/" in request.url.path:
            if request.method == "DELETE":
                deleted = True
                return httpx.Response(200, json={})
            return httpx.Response(404, json={}) if deleted else httpx.Response(200, json={"email": owned_email})
        return httpx.Response(200, json=[])

    validator.client.close()
    validator.client = httpx.Client(transport=httpx.MockTransport(respond))
    try:
        result = validator.cleanup()
        assert result["owned_accounts_deleted"] == 1 and not validator.state_path.exists()
        assert len([event for event in events if event[0] == "DELETE"]) == 2
        report = validator.report_path.read_text(encoding="utf-8")
        assert "private-fixture" not in report and owned_email not in report and "fixture-only" not in report
        assert validator.report["cleanup"]["private_credentials_removed"]
    finally:
        validator.close()


@pytest.mark.parametrize("status", [403, 500])
def test_member_rest_denial_never_broadens_grants_and_only_403_uses_operator_flow(tmp_path, status):
    settings = Settings(_env_file=None, supabase_url="https://supabase.invalid", supabase_service_role_key="fixture-only")
    validator = Validator(settings, tmp_path, "https://api.invalid", "https://site.invalid")
    events = []

    def respond(request):
        events.append((request.method, request.url.path))
        if request.url.path == "/auth/v1/admin/users":
            return httpx.Response(200, json={"id": str(uuid.uuid4())})
        if request.url.path == "/rest/v1/jr_members":
            return httpx.Response(status, json={"message": "fixture denial"})
        if request.url.path == "/auth/v1/token":
            return httpx.Response(200, json={"access_token": "private-fixture-token"})
        raise AssertionError("Unexpected request")

    validator.client.close()
    validator.client = httpx.Client(transport=httpx.MockTransport(respond))
    try:
        if status == 500:
            with pytest.raises(LiveHTTPError) as error:
                validator.create_account()
            assert error.value.status == 500 and not validator.state.get("membership_via_operator")
        else:
            validator.create_account()
            assert validator.state["membership_via_operator"]
            assert validator.state["accounts"][0]["membership_pending"]
        assert validator.state_path.exists()  # Recovery identity survives a later membership failure.
        assert "private-fixture-token" not in validator.report_path.read_text(encoding="utf-8")
        assert not any("policy" in path or "grant" in path for _, path in events)
    finally:
        validator.close()


def test_operator_membership_requires_explicit_cleanup_attestation(tmp_path):
    settings = Settings(_env_file=None, supabase_url="https://supabase.invalid", supabase_service_role_key="fixture-only")
    validator = Validator(settings, tmp_path, "https://api.invalid", "https://site.invalid")
    validator.state["membership_via_operator"] = True
    try:
        with pytest.raises(ValueError, match="operator-members-removed"):
            validator.cleanup()
    finally:
        validator.close()
