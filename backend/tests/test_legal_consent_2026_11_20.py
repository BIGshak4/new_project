"""The privacy policy and the consent of sign-up (Shaked, 2026-11-19: "make a privacy that the user agrees to when
he signs; he needs to agree for us collecting data to adjust the program for each user specifically").

What must hold (Harel's legal report and checklist):
* the policy is not shown, and nothing is asked or blocked, while a fact is missing from it;
* one consent for one use, the text in both languages, the version that was shown recorded with the server's time;
* the proof is tied to the verified account; a repeat changes nothing; a new text asks again;
* enforcement is a switch, and only bites once the policy is published.

In-memory store, scripted model.
"""

from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import STATUS_FOR_CODE, ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.runtime import build_runtime
from app.schemas.bank import LANGUAGES
from app.services.legal import LegalService, load_documents
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, scripted

LEGAL = SEEDS / "legal"
MIGRATION = Path(__file__).resolve().parents[2] / "supabase" / "migrations" / "20261120090000_user_consent.sql"
MEMBER = "tester@example.com"
HEBREW = re.compile(r"[֐-׿]")
APPROVED = ("אני מאשר/ת שהאתר יאסוף וישמור את התשובות שלי, ההערכות שהן מקבלות ונתוני התרגול שלי, וישתמש בהם כדי "
            "להתאים לי אישית את תוכנית ההכנה, השאלות והמשוב. קראתי את מדיניות הפרטיות.")
FACTS = {"operator": "JobRun Test Operator", "contact_email": "privacy@example.com", "minimum_age": 18}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def published_copy(tmp_path: Path, *, version: str | None = None, **changes) -> Path:
    """The real texts with the missing facts filled in and the status flipped, as the founders will do."""
    target = tmp_path / f"legal-{uuid.uuid4().hex[:6]}"
    shutil.copytree(LEGAL, target)
    manifest = json.loads((target / "legal.json").read_text(encoding="utf-8"))
    manifest["privacy"].update({"status": "published", "facts": dict(FACTS)})
    if version:
        manifest["consents"][0]["version"] = version
    for key, value in changes.items():
        manifest["privacy"][key] = value
    (target / "legal.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return target


def service(catalog, directory: Path = LEGAL, *, store=None, require: bool = False) -> tuple[LegalService, InMemoryStore]:
    store = store or InMemoryStore(catalog)
    return LegalService(store, load_documents(directory), require_consent=require), store


class NoStore:
    """A store that must not be touched: the draft answers without reading a table that may not exist yet."""

    def transaction(self):
        raise AssertionError("the consent table was read while the policy is a draft")


# ----------------------------------------------------------------------------- the documents


class TestTheDocuments:
    def test_the_real_policy_is_a_draft_that_names_what_is_missing(self):
        documents = load_documents(LEGAL)
        assert documents.status == "draft" and not documents.published
        assert set(documents.missing_facts) == {"operator", "contact_email", "minimum_age"}
        assert len(documents.open_items) >= 8 and any("lawyer" in item for item in documents.open_items)
        assert set(documents.policy) == set(LANGUAGES)

    def test_the_consent_is_the_text_shaked_approved_and_it_is_one_consent_for_one_use(self):
        documents = load_documents(LEGAL)
        assert [c.key for c in documents.consents] == ["personalisation"]
        consent = documents.consents[0]
        assert consent.required and consent.text["he"] == APPROVED
        assert not HEBREW.search(consent.text["en"]) and "adapt" in consent.text["en"] and "privacy policy" in consent.text["en"]
        # nothing about marketing, employers or "any future use" rides on it (the checklist, section 3)
        for word in ("marketing", "updates", "newsletter", "שיווק", "עדכונים", "דיוור"):
            assert word not in consent.text["en"] and word not in consent.text["he"]

    def test_both_languages_say_the_same_things(self):
        documents = load_documents(LEGAL)
        hebrew, english = documents.policy["he"], documents.policy["en"]
        assert len(re.findall(r"^## ", hebrew, re.M)) == len(re.findall(r"^## ", english, re.M)) == 12
        assert [m[0] for m in re.finditer(r"^## (\d+)\.", hebrew, re.M)] == [m[0] for m in re.finditer(r"^## (\d+)\.", english, re.M)]
        assert not HEBREW.search(english) and HEBREW.search(hebrew)
        for text in (hebrew, english):
            assert "2026-11-20" in text and "{version}" not in text
            # every outside service the code sends personal data to is named (the report: "a policy of truth")
            for vendor in ("Supabase", "DigitalOcean", "OpenAI", "Vercel"):
                assert vendor in text, vendor
            # the facts the founders still owe, each used at least once
            for fact in ("{operator}", "{contact_email}", "{minimum_age}"):
                assert fact in text, fact

    def test_what_the_policy_says_is_sent_to_the_model_is_what_the_code_sends(self):
        """Section 5 promises that no name, e-mail or account id goes to OpenAI: the request the provider builds has
        no user field, and the prompt builders never read an e-mail or a username."""
        app_dir = Path(__file__).resolve().parent.parent / "app"
        provider = (app_dir / "engine" / "providers.py").read_text(encoding="utf-8")
        assert "store=False" in provider and "safety_identifier" not in provider and not re.search(r"\buser=str\(", provider)
        for name in ("evaluator.py", "feedback.py", "generator.py", "reporter.py"):
            source = (app_dir / "engine" / name).read_text(encoding="utf-8")
            assert "email" not in source and "username" not in source and "user_id" not in source, name

    def test_a_published_policy_must_be_complete(self, tmp_path):
        ready = load_documents(published_copy(tmp_path))
        assert ready.published and not ready.missing_facts
        for language in LANGUAGES:
            assert "{" not in ready.policy[language] and "privacy@example.com" in ready.policy[language]
            assert "JobRun Test Operator" in ready.policy[language] and "18" in ready.policy[language]
        with pytest.raises(ValueError, match="contact_email"):
            load_documents(published_copy(tmp_path, facts={**FACTS, "contact_email": None}))
        with pytest.raises(ValueError, match="contact_email"):
            load_documents(published_copy(tmp_path, facts={**FACTS, "contact_email": ""}))
        with pytest.raises(ValueError, match="draft or published"):
            load_documents(published_copy(tmp_path, status="live"))

    def test_a_consent_needs_both_languages_and_a_key_of_its_own(self, tmp_path):
        directory = published_copy(tmp_path)
        manifest = json.loads((directory / "legal.json").read_text(encoding="utf-8"))
        manifest["consents"].append(dict(manifest["consents"][0]))
        (directory / "legal.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(ValueError, match="twice"):
            load_documents(directory)
        manifest["consents"] = [{**manifest["consents"][0], "text": {"he": APPROVED, "en": " "}}]
        (directory / "legal.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(ValueError, match="no text in en"):
            load_documents(directory)

    def test_the_migration_keeps_the_table_to_the_api(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        assert "create table public.user_consent" in sql and "references auth.users(id) on delete cascade" in sql
        assert "enable row level security" in sql
        assert "revoke all on public.user_consent from public, anon, authenticated" in sql
        assert "grant select, insert on public.user_consent to service_role" in sql
        assert "create policy" not in sql and "update" not in sql.split("grant")[1]       # proof is never edited
        assert "ip" not in re.findall(r"^\s+(\w+) ", sql, re.M)                            # no address column


# ----------------------------------------------------------------------------- while it is a draft


class TestWhileItIsADraft:
    async def test_nothing_is_shown_asked_recorded_or_blocked(self, catalog):
        legal = LegalService(NoStore(), load_documents(LEGAL), require_consent=True)
        user = uuid.uuid4()
        assert not legal.enforced
        with pytest.raises(ApiError) as hidden:
            legal.policy("he")
        assert hidden.value.code == "not_found" and hidden.value.status == 404
        assert legal.consent_texts("he") == [] == legal.consent_texts("en")
        assert await legal.status(user) == {"active": False, "enforced": False, "missing": [], "given": []}
        await legal.check(user)                                                # nobody is locked out
        with pytest.raises(ApiError) as refused:
            await legal.record(user, key="personalisation", version="2026-11-20", language="he", source="signup")
        assert refused.value.code == "conflict"


# ----------------------------------------------------------------------------- once it is published


class TestOncePublished:
    async def test_the_policy_and_the_text_are_served_in_both_languages(self, catalog, tmp_path):
        legal, _ = service(catalog, published_copy(tmp_path))
        hebrew, english = legal.policy("he"), legal.policy("en")
        assert hebrew["version"] == english["version"] == "2026-11-20"
        assert hebrew["markdown"].startswith("# מדיניות הפרטיות") and english["markdown"].startswith("# JobRun privacy policy")
        assert legal.consent_texts("he") == [{"key": "personalisation", "version": "2026-11-20", "required": True,
                                              "text": APPROVED}]
        assert legal.consent_texts("en")[0]["text"].startswith("I agree that the site may collect")

    async def test_agreeing_is_recorded_once_with_the_text_that_was_shown(self, catalog, tmp_path):
        legal, store = service(catalog, published_copy(tmp_path))
        user, other = uuid.uuid4(), uuid.uuid4()
        before = await legal.status(user)
        assert before == {"active": True, "enforced": False, "missing": ["personalisation"], "given": []}
        after = await legal.record(user, key="personalisation", version="2026-11-20", language="he", source="signup")
        assert after["missing"] == [] and len(after["given"]) == 1
        row = after["given"][0]
        assert (row["key"], row["version"], row["policy_version"], row["language"], row["source"]) == \
            ("personalisation", "2026-11-20", "2026-11-20", "he", "signup")
        assert row["accepted_at"].startswith("20") and "T" in row["accepted_at"]         # the server's clock
        # a repeat (a double click, the prompt after the sign-up box) keeps the first record as it was
        again = await legal.record(user, key="personalisation", version="2026-11-20", language="en", source="prompt")
        assert again["given"] == after["given"] and len(store.consents) == 1
        assert (await legal.status(other))["missing"] == ["personalisation"]             # one account's proof is its own

    async def test_what_cannot_be_recorded(self, catalog, tmp_path):
        legal, store = service(catalog, published_copy(tmp_path))
        user = uuid.uuid4()
        for wrong, code in (({"version": "2025-01-01"}, "stale_version"), ({"key": "marketing"}, "not_found"),
                            ({"source": "import"}, "validation"), ({"language": "fr"}, "validation")):
            with pytest.raises(ApiError) as refused:
                await legal.record(user, **{"key": "personalisation", "version": "2026-11-20", "language": "he",
                                            "source": "signup", **wrong})
            assert refused.value.code == code, wrong
        assert store.consents == {}

    async def test_a_new_text_asks_everyone_again(self, catalog, tmp_path):
        legal, store = service(catalog, published_copy(tmp_path))
        user = uuid.uuid4()
        await legal.record(user, key="personalisation", version="2026-11-20", language="he", source="signup")
        newer, _ = service(catalog, published_copy(tmp_path, version="2027-01-01"), store=store)
        status = await newer.status(user)
        assert status["missing"] == ["personalisation"] and status["given"] == []       # the old row is history, kept
        await newer.record(user, key="personalisation", version="2027-01-01", language="he", source="prompt")
        assert len(store.consents) == 2 and (await newer.status(user))["missing"] == []

    async def test_the_switch_blocks_only_until_the_user_agrees(self, catalog, tmp_path):
        directory = published_copy(tmp_path)
        relaxed, _ = service(catalog, directory, require=False)
        await relaxed.check(uuid.uuid4())                                      # published, switch off: nobody blocked
        legal, store = service(catalog, directory, require=True)
        user = uuid.uuid4()
        assert legal.enforced
        with pytest.raises(ApiError) as blocked:
            await legal.check(user)
        assert (blocked.value.code, blocked.value.status) == ("consent_required", 403) == \
            ("consent_required", STATUS_FOR_CODE["consent_required"])
        await legal.record(user, key="personalisation", version="2026-11-20", language="en", source="prompt")
        await legal.check(user)
        legal.store = NoStore()                                                # known to have agreed: no further read
        await legal.check(user)


# ----------------------------------------------------------------------------- over HTTP


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=scripted([GOOD] * 4), store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def signed_in() -> dict:
    _, token = make_token(email=MEMBER)
    return {"Authorization": f"Bearer {token}"}


class TestOverHttp:
    async def test_as_shipped_the_draft_is_invisible_and_nobody_is_asked(self, client):
        assert app.state.runtime.legal is not None and not app.state.runtime.legal.documents.published
        hidden = await client.get("/v1/legal/privacy")
        assert hidden.status_code == 404 and hidden.json()["error"]["code"] == "not_found"
        assert (await client.get("/v1/legal/consents?language=en")).json() == []
        headers = signed_in()
        assert (await client.get("/v1/me/consents", headers=headers)).json() == \
            {"active": False, "enforced": False, "missing": [], "given": []}
        refused = await client.post("/v1/me/consents", headers=headers, json={
            "key": "personalisation", "version": "2026-11-20", "language": "he", "source": "signup"})
        assert refused.status_code == 409
        started = await client.post("/v1/practice/attempts", headers=headers, json={"question_key": "example-sensor-majority"})
        assert started.status_code == 201                                      # practice is untouched
        health = (await client.get("/health")).json()
        assert health.get("privacy_consent", "off") == "off"

    async def test_published_and_required_sign_up_to_first_question(self, client, catalog, tmp_path):
        runtime = app.state.runtime
        runtime.legal = LegalService(runtime.store, load_documents(published_copy(tmp_path)), require_consent=True)
        # before an account exists: the policy and the text of the box, without a token
        policy = await client.get("/v1/legal/privacy?language=en")
        assert policy.status_code == 200 and policy.json()["markdown"].startswith("# JobRun privacy policy")
        assert "max-age" in policy.headers["Cache-Control"]
        box = (await client.get("/v1/legal/consents?language=he")).json()
        assert box == [{"key": "personalisation", "version": "2026-11-20", "required": True, "text": APPROVED}]
        # the record needs the account: no token, no proof
        body = {"key": box[0]["key"], "version": box[0]["version"], "language": "he", "source": "signup"}
        assert (await client.post("/v1/me/consents", json=body)).status_code == 401
        headers = signed_in()
        status = (await client.get("/v1/me/consents", headers=headers)).json()
        assert status["active"] and status["enforced"] and status["missing"] == ["personalisation"]
        blocked = await client.post("/v1/practice/attempts", headers=headers, json={"question_key": "example-sensor-majority"})
        assert blocked.status_code == 403 and blocked.json()["error"]["code"] == "consent_required"
        assert (await client.post("/v1/interviews", headers=headers, json={"duration_min": 20})).status_code == 403
        # who-am-I, the wallet and the consent routes themselves stay open, so the prompt can be shown
        assert (await client.get("/v1/me", headers=headers)).status_code == 200
        # a request that names another account, or an unknown field, is refused: the token decides who agreed
        assert (await client.post("/v1/me/consents", headers=headers, json={**body, "user_id": str(uuid.uuid4())})).status_code == 422
        assert (await client.post("/v1/me/consents", headers=headers, json={**body, "version": "old"})).status_code == 409
        agreed = await client.post("/v1/me/consents", headers=headers, json=body)
        assert agreed.status_code == 200 and agreed.json()["missing"] == [] and agreed.headers["Cache-Control"] == "no-store"
        assert len(runtime.store.consents) == 1
        started = await client.post("/v1/practice/attempts", headers=headers, json={"question_key": "example-sensor-majority"})
        assert started.status_code == 201
