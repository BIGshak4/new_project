"""Opt-in live validation through the learner API; never executes source on this host.

Stages: provision -> run -> cleanup. Only dedicated disposable QA identities are
created. Private browser credentials stay in an ignored operator directory. The
sanitized report distinguishes question suites from compiler/transport probes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import subprocess
import sys
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import httpx

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
from app.config import Settings  # noqa: E402

PREFIX = "execution-validation-"
LANGUAGES = ["python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl"]
CPP_PROBE = '#include <iostream>\nint main(){ int value; std::cin >> value; std::cout << "jobrun-probe:" << value * 2 << "\\n"; }\n'
CPP_INVALID = "int main( { this is deliberately invalid C++ syntax; }\n"


class LiveHTTPError(RuntimeError):
    def __init__(self, status, path):
        self.status, self.path = status, path
        super().__init__(f"Live validation HTTP {status} at {path}; response withheld.")


def stamp():
    return datetime.now(UTC).isoformat()


def digest(value):
    raw = value.encode() if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def is_software(question):
    """Match web questionCategory, including its explicit-category override."""
    category = question.get("category")
    return category == "software" if category else question.get("subject") in {
        "relevant_programming", "programming", "software_fundamentals"}


def fixture_plan(question_key, positives):
    jobs = [{"kind": "question_suite", **row, "stdin": ""} for row in positives
            if row["question_key"] == question_key]
    if not any(job["language"] == "cpp" for job in jobs):
        jobs.append(dict(kind="transport_probe", question_key=question_key, language="cpp",
                         source=CPP_PROBE, stdin="21\n"))
    jobs.append(dict(kind="compile_error_probe", question_key=question_key, language="cpp",
                     source=CPP_INVALID, stdin=""))
    return jobs


def allocate(questions, positives, maximum=4, minimum=1):
    """Balance real VM costs while respecting unchanged learner allowances."""
    if not 1 <= minimum <= maximum <= 4:
        raise ValueError("Dedicated QA account count must be between one and four.")
    accounts = [dict(attempts=0, runs=0) for _ in range(minimum)]
    assignment = {}
    for question in sorted(questions, key=lambda q: (-len(fixture_plan(q["key"], positives)), q["key"])):
        cost = len(fixture_plan(question["key"], positives))
        eligible = [i for i, item in enumerate(accounts) if item["attempts"] < 30 and item["runs"] + cost <= 60]
        if not eligible:
            if len(accounts) >= maximum or cost > 60:
                raise ValueError("The planned validation exceeds the dedicated-account allowance; no limits were changed.")
            accounts.append(dict(attempts=0, runs=0))
            eligible = [len(accounts) - 1]
        index = min(eligible, key=lambda i: (accounts[i]["runs"], accounts[i]["attempts"]))
        accounts[index]["attempts"] += 1
        accounts[index]["runs"] += cost
        assignment[question["key"]] = index
    return accounts, assignment


def accepted(kind, result):
    if kind == "question_suite":
        return (result.get("status") == "passed" and result.get("passed") is True
                and result.get("compiled") is True and result.get("executed") is True
                and result.get("test_count", 0) > 0
                and result["passed_count"] == result["test_count"])
    if kind == "compile_error_probe":
        return (result.get("status") == "compile_error" and result.get("compiled") is False
                and result.get("executed") is False and result.get("passed") is None
                and result.get("passed_count") == 0
                and bool(result.get("compile_output", "").strip()))
    return (result.get("status") == "completed" and result.get("compiled") is True
            and result.get("executed") is True and result.get("passed") is None
            and result.get("test_count") == 0 and result.get("passed_count") == 0
            and result.get("stdout", "").strip() == "jobrun-probe:42")


def output_dir(value):
    path = Path(value).resolve()
    parent = (ROOT / ".impeccable").resolve()
    if path.parent != parent or not path.name.startswith("execution-"):
        raise ValueError("Output must be an ignored .impeccable/execution-* directory directly under the repository.")
    ignored = subprocess.run(["git", "check-ignore", "-q", str(path / "private-state.json")],
                             cwd=ROOT, check=False, capture_output=True)
    if ignored.returncode != 0:
        raise ValueError("Private QA state must be ignored by Git before any credentials are written.")
    path.mkdir(parents=True, exist_ok=True)
    return path


class Validator:
    def __init__(self, settings, output, api, site):
        for endpoint in [api, site, settings.supabase_url or ""]:
            parts = urlsplit(endpoint)
            if parts.scheme != "https" or parts.username or parts.password or parts.query or parts.fragment:
                raise ValueError("Live endpoints must be credential-free HTTPS origins.")
        if not settings.supabase_service_role_key:
            raise ValueError("Server-only operator credentials are required; never pass them on the command line.")
        self.settings, self.output = settings, output
        self.api, self.site = api.rstrip("/"), site.rstrip("/")
        self.state_path, self.report_path = output / "private-state.json", output / "report.json"
        self.client = httpx.Client(timeout=90, follow_redirects=False, trust_env=False)
        self.sent = {}
        self.positives = json.loads((BACKEND / "tests/fixtures/execution_positive.json").read_text(encoding="utf-8"))["cases"]
        self.state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {
            "schema": 1, "run_id": uuid.uuid4().hex[:12], "api": self.api, "site": self.site,
            "supabase_origin": settings.supabase_url, "accounts": [], "attempts": {}, "completed_jobs": {}}
        if (self.state["api"] != self.api or self.state["site"] != self.site
                or self.state["supabase_origin"] != settings.supabase_url):
            raise ValueError("The saved QA state belongs to different origins.")
        self.report = json.loads(self.report_path.read_text(encoding="utf-8")) if self.report_path.exists() else {
            "schema": 1, "run_id": self.state["run_id"], "started_at": stamp(),
            "scope": "canonical live software category; compiler probes are not question-correctness checks",
            "api": self.api, "site": self.site, "questions": {}, "rows": []}

    def close(self):
        self.client.close()

    def save(self):
        # Never serialize credentials into report.json or standard output.
        if any(path.is_symlink() for path in [self.state_path, self.report_path]):
            raise ValueError("Refusing a symlinked operator-state destination.")
        self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        self.report["updated_at"] = stamp()
        self.report_path.write_text(json.dumps(self.report, indent=2, ensure_ascii=True), encoding="utf-8")

    def request(self, method, url, **kwargs):
        response = self.client.request(method, url, **kwargs)
        if response.status_code >= 400:
            raise LiveHTTPError(response.status_code, urlsplit(url).path)
        return response.json() if response.content else None

    def admin(self):
        key = self.settings.supabase_service_role_key
        return {"apikey": key, "Authorization": f"Bearer {key}"}

    def create_account(self):
        index = len(self.state["accounts"])
        email = f"{PREFIX}{self.state['run_id']}-{index}@example.com"
        password = secrets.token_urlsafe(32)
        user = self.request("POST", self.settings.supabase_url + "/auth/v1/admin/users", headers=self.admin(),
                            json={"email": email, "password": password, "email_confirm": True})
        account = {"id": user["id"], "email": email, "password": password}
        self.state["accounts"].append(account)
        self.save()  # Persist owned identity before the next write, so cleanup survives a later failure.
        if not self.state.get("membership_via_operator"):
            try:
                self.request("POST", self.settings.supabase_url + "/rest/v1/jr_members", headers=self.admin(),
                             json={"email": email, "display_name": "Execution validation QA", "can_manage_tasks": False})
            except LiveHTTPError as exc:
                if exc.status != 403:
                    raise
                # The owner may have a separately scoped database connector. Never broaden REST grants.
                self.state["membership_via_operator"] = True
        account["membership_pending"] = bool(self.state.get("membership_via_operator"))
        self.save()
        self.login(index)

    def login(self, index):
        account = self.state["accounts"][index]
        token = self.request("POST", self.settings.supabase_url + "/auth/v1/token?grant_type=password",
                             headers={"apikey": self.settings.supabase_service_role_key},
                             json={"email": account["email"], "password": account["password"]})
        account["access_token"] = token["access_token"]
        self.save()

    def headers(self, index):
        return {"Authorization": "Bearer " + self.state["accounts"][index]["access_token"]}

    def catalog(self):
        catalogs = {language: self.request("GET", self.api + "/v1/questions", headers=self.headers(0),
                                          params={"language": language}) for language in ["he", "en"]}
        keys = [{q["key"] for q in rows} for rows in catalogs.values()]
        if keys[0] != keys[1]:
            raise RuntimeError("Hebrew and English live catalogs contain different question keys.")
        questions = [q for q in catalogs["he"] if is_software(q)]
        self.report["catalog"] = {language: {"total": len(rows), "sha256": digest(rows)}
                                  for language, rows in catalogs.items()}
        self.report["software_question_keys"] = sorted(q["key"] for q in questions)
        return questions

    def provision(self, maximum, membership_via_operator=False):
        if self.state.get("provisioned"):
            raise ValueError("This QA run is already provisioned; use run or cleanup.")
        if membership_via_operator:
            self.state["membership_via_operator"] = True
        if not self.state["accounts"]:
            self.create_account()
        else:
            self.login(0)
        if self.state.get("membership_via_operator"):
            while len(self.state["accounts"]) < maximum:
                self.create_account()
        try:
            questions = self.catalog()
        except LiveHTTPError as exc:
            if exc.status != 403 or not self.state.get("membership_via_operator"):
                raise
            self.save()
            return {"stage": "membership_pending", "accounts": len(self.state["accounts"]),
                    "next": "Operator inserts only these private-state identities into jr_members; then resume provision."}
        if not questions:
            raise ValueError("The live catalog returned no software questions; no empty validation is accepted.")
        budgets, assignments = allocate(questions, self.positives, maximum, minimum=maximum)
        while len(self.state["accounts"]) < len(budgets):
            self.create_account()
        for index, account in enumerate(self.state["accounts"]):
            self.request("GET", self.api + "/v1/questions", headers=self.headers(index), params={"language": "he"})
            account["membership_pending"] = False
        self.state.update(provisioned=True, assignment=assignments, software_keys=sorted(assignments),
                          positive_fixture_sha256=digest(self.positives))
        self.report.update(account_budgets=budgets, planned_vm_runs=sum(b["runs"] for b in budgets),
                           question_count=len(questions), provisioned_at=stamp(),
                           positive_fixture_sha256=digest(self.positives))
        self.save()
        return {"stage": "provisioned", "questions": len(questions), "accounts": len(budgets),
                "planned_vm_runs": self.report["planned_vm_runs"]}

    def throttle(self, account):
        recent = self.sent.setdefault(account, deque())
        while recent and recent[0] <= time.monotonic() - 62:
            recent.popleft()
        if len(recent) >= 6:
            time.sleep(max(0, recent[0] + 62 - time.monotonic()))
            return self.throttle(account)
        recent.append(time.monotonic())

    def run(self):
        if not self.state.get("provisioned") or self.state.get("cleaned"):
            raise ValueError("Provision the dedicated QA identities before running.")
        if self.state["positive_fixture_sha256"] != digest(self.positives):
            raise ValueError("Positive fixtures changed after provisioning; start a fresh validation run.")
        for index in range(len(self.state["accounts"])):
            self.login(index)
        questions = self.catalog()
        if sorted(q["key"] for q in questions) != self.state["software_keys"]:
            raise RuntimeError("The live software catalog changed after provisioning; create a fresh validation run.")
        self.report["health"] = {"api": self.request("GET", self.api + "/health"),
                                 "site": self.request("GET", self.site + "/api/health")}
        # Interleave dedicated accounts to avoid monopolizing one account's per-minute budget.
        ordered = sorted(questions, key=lambda q: (self.state["assignment"][q["key"]], q["key"]))
        groups = [[q for q in ordered if self.state["assignment"][q["key"]] == i]
                  for i in range(len(self.state["accounts"]))]
        ordered = [group[n] for n in range(max(map(len, groups))) for group in groups if n < len(group)]
        for question in ordered:
            key = question["key"]
            index = self.state["assignment"][key]
            headers = self.headers(index)
            details = {lang: self.request("GET", self.api + "/v1/questions/" + key,
                                          headers=headers, params={"language": lang}) for lang in ["he", "en"]}
            if any(d["key"] != key or not d.get("prompt", "").strip() for d in details.values()):
                raise RuntimeError("Question detail identity or prompt validation failed.")
            if key not in self.state["attempts"]:
                attempt = self.request("POST", self.api + "/v1/practice/attempts", headers=headers,
                                       json={"question_key": key, "language": "he", "mode": "deep",
                                             "source": "library", "screen": "execution-validation"})
                self.state["attempts"][key] = attempt["id"]
                self.save()
            base = self.api + "/v1/practice/attempts/" + self.state["attempts"][key]
            attempt = self.request("GET", base, headers=headers)
            capability = self.request("GET", base + "/execution-capabilities", headers=headers)
            if (attempt["question"]["key"] != key or attempt["submission"] is not None
                    or not capability["available"] or capability["languages"] != LANGUAGES):
                raise RuntimeError("Attempt ownership, no-submission or execution-capability assertion failed.")
            jobs = fixture_plan(key, self.positives)
            fixture_languages = {job["language"] for job in jobs if job["kind"] == "question_suite"}
            if set(capability["tested_languages"]) != fixture_languages:
                raise RuntimeError("Live suite capabilities differ from the committed positive fixtures.")
            self.report["questions"][key] = {"attempt_id": attempt["id"], "category": question.get("category"),
                "subject": question["subject"], "status": question["status"], "assessment_ready": question["assessment_ready"],
                "detail_sha256": {lang: digest(detail) for lang, detail in details.items()},
                "tested_languages": capability["tested_languages"], "languages": capability["languages"],
                "contract_sha256": digest(capability["contract"]), "submission_before": None}
            replay_done = False
            for job in jobs:
                job_id = key + "/" + job["kind"] + "/" + job["language"]
                payload = {"language": job["language"], "source": job["source"], "stdin": job["stdin"],
                           "idempotency_key": "validate-" + self.state["run_id"] + "-" + digest(job_id)[:24]}
                if job_id in self.state["completed_jobs"]:
                    continue
                self.throttle(index)
                result = self.request("POST", base + "/executions", headers=headers, json=payload)
                row = {"question_key": key, "kind": job["kind"], "language": job["language"],
                       "source_sha256": digest(job["source"]), "stdin_sha256": digest(job["stdin"]),
                       "status": result["status"], "compiled": result["compiled"], "executed": result["executed"],
                       "passed": result["passed"], "test_count": result["test_count"],
                       "passed_count": result["passed_count"], "runtime_ms": result["runtime_ms"],
                       "stdout_sha256": digest(result["stdout"]),
                       "compile_output_sha256": digest(result["compile_output"]),
                       "compile_output_length": len(result["compile_output"]), "ok": accepted(job["kind"], result)}
                if not replay_done and job["kind"] != "compile_error_probe":
                    replay = self.request("POST", base + "/executions", headers=headers, json=payload)
                    row["idempotency_replay_equal"] = replay == result
                    row["ok"] = row["ok"] and row["idempotency_replay_equal"]
                    replay_done = True
                self.report["rows"].append(row)
                self.state["completed_jobs"][job_id] = True
                self.save()
                print(json.dumps(row), flush=True)
            after = self.request("GET", base, headers=headers)
            self.report["questions"][key]["submission_after"] = after["submission"]
            if after["submission"] is not None:
                raise RuntimeError("A manual run unexpectedly created a submission.")
            self.save()
        rows = self.report["rows"]
        if len(rows) != self.report["planned_vm_runs"]:
            raise RuntimeError("The completed run count differs from the provisioned plan.")
        if any(not any(row["question_key"] == q["key"] and row.get("idempotency_replay_equal") is True
                       for row in rows) for q in questions):
            raise RuntimeError("At least one question lacks a verified idempotency replay.")
        self.report["summary"] = {"questions": len(questions), "real_vm_runs": len(rows),
            "question_suite_runs": sum(r["kind"] == "question_suite" for r in rows),
            "question_suite_questions": len({r["question_key"] for r in rows if r["kind"] == "question_suite"}),
            "transport_probes": sum(r["kind"] == "transport_probe" for r in rows),
            "compile_error_probes": sum(r["kind"] == "compile_error_probe" for r in rows),
            "passed": sum(r["ok"] for r in rows), "failed": sum(not r["ok"] for r in rows),
            "finished_at": stamp()}
        self.save()
        return self.report["summary"]

    def prepare(self):
        """Create all attempts first so a browser audit can run without spending extra VM jobs."""
        if not self.state.get("provisioned") or self.state.get("cleaned"):
            raise ValueError("Provision the dedicated QA identities before preparing attempts.")
        for index in range(len(self.state["accounts"])):
            self.login(index)
        questions = self.catalog()
        if sorted(q["key"] for q in questions) != self.state["software_keys"]:
            raise RuntimeError("The live software catalog changed after provisioning.")
        for question in questions:
            key = question["key"]
            index = self.state["assignment"][key]
            headers = self.headers(index)
            if key not in self.state["attempts"]:
                attempt = self.request("POST", self.api + "/v1/practice/attempts", headers=headers,
                                       json={"question_key": key, "language": "he", "mode": "deep",
                                             "source": "library", "screen": "execution-validation"})
                self.state["attempts"][key] = attempt["id"]
                self.save()
            base = self.api + "/v1/practice/attempts/" + self.state["attempts"][key]
            capability = self.request("GET", base + "/execution-capabilities", headers=headers)
            if not capability["available"] or capability["languages"] != LANGUAGES:
                raise RuntimeError("Execution is unavailable while preparing the browser audit.")
            self.report["questions"][key] = {"attempt_id": self.state["attempts"][key],
                "tested_languages": capability["tested_languages"], "languages": capability["languages"],
                "prepared_for_browser": True}
            self.save()
        return {"stage": "prepared", "questions": len(questions), "attempts": len(self.state["attempts"])}

    def cleanup(self, operator_members_removed=False):
        if self.state.get("membership_via_operator") and not operator_members_removed:
            raise ValueError("Operator must remove these exact QA memberships, then pass --operator-members-removed.")
        removed = 0
        for index, account in enumerate(self.state["accounts"]):
            expected = f"{PREFIX}{self.state['run_id']}-{index}@example.com"
            if account["email"] != expected:
                raise ValueError("Refusing cleanup of an identity outside this exact disposable QA run.")
            user_id = str(uuid.UUID(account["id"]))
            url = self.settings.supabase_url + "/auth/v1/admin/users/" + user_id
            response = self.client.get(url, headers=self.admin())
            if response.status_code != 404 and (response.status_code != 200 or response.json().get("email") != account["email"]):
                raise RuntimeError("QA identity check failed; nothing was deleted for this entry.")
            if not self.state.get("membership_via_operator"):
                self.request("DELETE", self.settings.supabase_url + "/rest/v1/jr_members", headers=self.admin(),
                             params={"email": "eq." + account["email"]})
            if response.status_code == 200:
                self.request("DELETE", url, headers=self.admin())
                removed += 1
            if self.client.get(url, headers=self.admin()).status_code != 404:
                raise RuntimeError("Deleted QA identity remains accessible; cleanup verification failed.")
            for table, column, value in ([] if self.state.get("membership_via_operator") else [
                    ("user_profile", "id", user_id), ("attempt", "user_id", user_id),
                    ("code_execution_runs", "user_id", user_id), ("jr_members", "email", account["email"])]):
                remaining = self.request("GET", self.settings.supabase_url + "/rest/v1/" + table,
                                         headers=self.admin(), params={column: "eq." + value, "select": "*", "limit": "1"})
                if remaining:
                    raise RuntimeError("Owned QA data remains after cleanup; private recovery state was preserved.")
        self.report["cleanup"] = {"completed_at": stamp(), "owned_accounts_deleted": removed,
                                  "private_credentials_removed": True,
                                  "database_verification": "operator_required" if self.state.get("membership_via_operator") else "verified"}
        self.state["cleaned"] = True
        self.save()
        self.state_path.unlink()
        return {"stage": "cleaned", "owned_accounts_deleted": removed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["provision", "prepare", "run", "cleanup"])
    parser.add_argument("--live", action="store_true", help="Explicitly authorize the chosen live QA stage.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--api", default="https://jobrun-api.onrender.com")
    parser.add_argument("--site", default="https://jobrun-practice.netlify.app")
    parser.add_argument("--max-accounts", type=int, default=4, choices=range(1, 5))
    parser.add_argument("--membership-via-operator", action="store_true",
                        help="Create identities, then pause until the operator inserts exact QA memberships.")
    parser.add_argument("--operator-members-removed", action="store_true",
                        help="Cleanup only: operator confirms the exact QA memberships were removed through their connector.")
    args = parser.parse_args()
    if not args.live:
        parser.error("Every network/write stage requires explicit --live; no action was performed.")
    validator = None
    try:
        validator = Validator(Settings(), output_dir(args.output), args.api, args.site)
        if args.stage == "provision":
            result = validator.provision(args.max_accounts, args.membership_via_operator)
        elif args.stage == "cleanup":
            result = validator.cleanup(args.operator_members_removed)
        else:
            result = getattr(validator, args.stage)()
        print(json.dumps(result), flush=True)
        if args.stage == "run" and result["failed"]:
            return 1
    except Exception as exc:
        print(json.dumps({"stage": args.stage, "error": type(exc).__name__, "detail": str(exc)}), file=sys.stderr)
        return 1
    finally:
        if validator:
            validator.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
