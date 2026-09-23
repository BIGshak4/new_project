"""The TypeScript client (apps/web/src/lib/practice-api.ts) must match the backend's OpenAPI document.

Field names of every response model are compared both ways, and every /v1 route the backend serves
must be called by the client. A change on either side fails here instead of in the browser."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

CLIENT = Path(__file__).resolve().parents[2] / "apps" / "web" / "src" / "lib" / "practice-api.ts"
pytestmark = pytest.mark.skipif(not CLIENT.exists(), reason="apps/web not checked out")

# OpenAPI schema name -> TypeScript type name
MODELS = {"QuestionSummary": "QuestionSummary", "QuestionDetail": "QuestionDetail", "HintView": "Hint",
          "CheckView": "Check", "CardView": "Card", "TipView": "Tip", "SubmissionView": "Submission",
          "FollowUpView": "FollowUp", "AttemptView": "Attempt", "SkillProgress": "SkillProgress",
          "ProgressView": "Progress", "Me": "Me",
          "InterviewView": "Interview", "InterviewTurnView": "InterviewTurn", "InterviewPlanSkill": "InterviewPlanSkill",
          "InterviewListItem": "InterviewListItem", "FitView": "Fit", "SkillReportView": "SkillReport",
          "LabelledSkill": "LabelledSkill", "InterviewReportView": "InterviewReport",
          "CompanyTag": "CompanyTag", "JobTypeView": "JobType", "CompanyView": "Company", "GoalView": "Goal",
          "ProgressOverview": "ProgressOverview", "TimelinePoint": "TimelinePoint", "PlanItemView": "PlanItem",
          "PlanView": "Plan"}


def ts_fields(source: str, type_name: str) -> set[str]:
    match = re.search(rf"export type {type_name} = (?:\w+ & )?\{{(.*?)\}};", source, re.S)
    assert match, f"type {type_name} not found in practice-api.ts"
    body = match.group(1)
    while re.search(r"\{[^{}]*\}", body):                          # collapse nested object literals
        body = re.sub(r"\{[^{}]*\}", "_", body)
    return {m.group(1) for m in re.finditer(r"(?:^|[;\n])\s*(\w+)\??:", body)}


@pytest.fixture(scope="module")
def spec():
    with TestClient(app) as client:
        return client.get("/openapi.json").json()


@pytest.fixture(scope="module")
def source():
    return CLIENT.read_text(encoding="utf-8")


@pytest.mark.parametrize("schema_name, ts_name", list(MODELS.items()))
def test_every_response_field_is_typed_both_ways(spec, source, schema_name, ts_name):
    schema = spec["components"]["schemas"][schema_name]
    backend = set(schema["properties"])
    if schema_name == "QuestionDetail":                             # `QuestionSummary & {...}` in TS
        backend -= set(spec["components"]["schemas"]["QuestionSummary"]["properties"])
    client = ts_fields(source, ts_name)
    assert client == backend, f"{ts_name}: missing in TS {backend - client}, extra in TS {client - backend}"


def test_every_v1_route_is_called_by_the_client(spec, source):
    routes = {(m.upper(), p) for p, ops in spec["paths"].items() if p.startswith("/v1") for m in ops}
    called = set()
    for method, path in re.findall(r'call<[^>]+>\(\s*"(GET|POST)",\s*["`]([^"`]+)["`]', source):
        normalized = re.sub(r"\$\{q\([^)]*\)\}", "", path)          # drop the query-string helper
        normalized = re.sub(r"\$\{[^}]+\}", "{}", normalized)
        called.add((method, normalized))
    missing = []
    for method, path in routes:
        pattern = re.sub(r"\{[^}]+\}", "{}", path)
        if not any(m == method and re.sub(r"\{[^}]+\}", "{}", c).rstrip("/") == pattern for m, c in called):
            missing.append(f"{method} {path}")
    assert not missing, f"routes without a client function: {missing}"


def test_error_codes_are_typed(spec, source):
    from app.api.errors import STATUS_FOR_CODE
    typed = set(re.findall(r'\|\s*"(\w+)"', source.split("export type ApiErrorCode")[1].split(";")[0]))
    assert set(STATUS_FOR_CODE) - {"stale_version"} <= typed, set(STATUS_FOR_CODE) - typed


def test_enum_literals_match_the_engine(source):
    from app.schemas.engine import Band, EvidenceStatus
    assert set(re.findall(r'status: ((?:"\w+"(?: \| )?)+);', source.split("export type SkillProgress")[1].split("};")[0])[0]
               .replace('"', "").split(" | ")) == {e.value for e in EvidenceStatus}
    assert set(re.findall(r'"(\w+)"', source.split("export type Band =")[1].split(";")[0])) == {b.value for b in Band}
