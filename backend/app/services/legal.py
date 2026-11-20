"""The privacy policy and the consent a user gives when signing up (Shaked, 2026-11-19: "he needs to agree for us
collecting data to adjust the program for each user specifically").

Built on Harel's legal report (`reports/`, JR-L03, JR-L09, JR-L10) and its checklist (`docs/privacy-accessibility-
consent-checklist-2026-11-04.md`):

* one consent for one use (personalisation), never a box that covers every future use;
* the proof is kept by the server: who (the verified user), when (the server's clock), which version of which
  text, in which language, from which screen. No IP address, and nothing the browser could invent counts as proof;
* the policy describes what the site really does, and is not shown to anyone while a fact is missing. Until the
  founders fill in the operator, the contact address and the minimum age, and a lawyer has read it, the policy is a
  draft: the public route answers 404, no consent can be recorded and nobody is blocked.

The texts are content (`seeds/legal/`). A new version of a consent text asks every user again.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.api.errors import ApiError
from app.schemas.bank import LANGUAGES
from app.services.store import Store

SOURCES = ("signup", "prompt")                     # the sign-up form, or the one-time prompt for an existing account
_FACT = re.compile(r"\{([a-z_]+)\}")


@dataclass(frozen=True)
class Consent:
    key: str
    version: str
    required: bool
    text: dict[str, str]


@dataclass(frozen=True)
class LegalDocuments:
    version: str
    status: str                                    # draft | published
    policy: dict[str, str]                         # language -> markdown, facts filled in
    consents: tuple[Consent, ...]
    open_items: tuple[str, ...] = ()
    missing_facts: tuple[str, ...] = field(default=())

    @property
    def published(self) -> bool:
        return self.status == "published"


def load_documents(directory: Path) -> LegalDocuments:
    """Read `seeds/legal/`. A published policy with a fact missing, or a consent without both languages, is refused
    at start: a page with a blank where the operator's name belongs must never reach a user."""
    manifest = json.loads((directory / "legal.json").read_text(encoding="utf-8"))
    privacy = manifest["privacy"]
    status = privacy.get("status", "draft")
    if status not in ("draft", "published"):
        raise ValueError(f"legal.json: status must be draft or published, not {status!r}")
    facts = {"version": privacy["version"], **{k: v for k, v in (privacy.get("facts") or {}).items() if v not in (None, "")}}
    policy, missing = {}, set()
    for language in LANGUAGES:
        text = (directory / f"privacy.{language}.md").read_text(encoding="utf-8")
        missing |= {name for name in _FACT.findall(text) if name not in facts}
        policy[language] = _FACT.sub(lambda m: str(facts.get(m[1], m[0])), text)
    consents = []
    for item in manifest.get("consents", []):
        absent = [language for language in LANGUAGES if not (item.get("text") or {}).get(language, "").strip()]
        if absent:
            raise ValueError(f"legal.json: consent {item.get('key')!r} has no text in {', '.join(absent)}")
        consents.append(Consent(key=item["key"], version=item["version"], required=bool(item.get("required")),
                                text=dict(item["text"])))
    if len({c.key for c in consents}) != len(consents):
        raise ValueError("legal.json: a consent key is listed twice")
    if status == "published" and missing:
        raise ValueError(f"legal.json: the policy is published but these facts are missing: {', '.join(sorted(missing))}")
    return LegalDocuments(version=privacy["version"], status=status, policy=policy, consents=tuple(consents),
                          open_items=tuple(privacy.get("open_items") or ()), missing_facts=tuple(sorted(missing)))


class LegalService:
    def __init__(self, store: Store, documents: LegalDocuments, *, require_consent: bool = False):
        self.store = store
        self.documents = documents
        self.require_consent = require_consent
        self._agreed: set[uuid.UUID] = set()       # users known to hold every required consent at today's versions

    @property
    def enforced(self) -> bool:
        """Practice is closed to a user who has not agreed only when the switch is on AND the policy is published."""
        return self.require_consent and self.documents.published

    def policy(self, language: str) -> dict:
        if not self.documents.published:
            raise ApiError("not_found", "the privacy policy is not published yet")
        return {"version": self.documents.version, "language": language, "markdown": self.documents.policy[language]}

    def consent_texts(self, language: str) -> list[dict]:
        """What the sign-up form shows; empty while the policy the texts refer to is not published."""
        if not self.documents.published:
            return []
        return [{"key": c.key, "version": c.version, "required": c.required, "text": c.text[language]}
                for c in self.documents.consents]

    async def status(self, user_id: uuid.UUID) -> dict:
        if not self.documents.published:           # nothing to agree to yet; the table is not read (it may not exist)
            return {"active": False, "enforced": False, "missing": [], "given": []}
        async with self.store.transaction() as tx:
            given = await tx.user_consents(user_id)
        current = {(c.key, c.version) for c in self.documents.consents}
        held = {(row["key"], row["version"]) for row in given}
        missing = [c.key for c in self.documents.consents if c.required and (c.key, c.version) not in held]
        if not missing:
            self._agreed.add(user_id)
        return {"active": True, "enforced": self.enforced, "missing": missing,
                "given": [row for row in given if (row["key"], row["version"]) in current]}

    async def record(self, user_id: uuid.UUID, *, key: str, version: str, language: str, source: str) -> dict:
        """The user agreed to the text they were shown. The time is the server's; a repeat changes nothing."""
        if not self.documents.published:
            raise ApiError("conflict", "the privacy policy is not published yet, so no consent can be recorded")
        consent = next((c for c in self.documents.consents if c.key == key), None)
        if consent is None:
            raise ApiError("not_found", f"there is no consent called {key!r}")
        if version != consent.version:
            raise ApiError("stale_version", "the consent text has changed; show the current text and ask again")
        if language not in LANGUAGES or source not in SOURCES:
            raise ApiError("validation", "language or source is not one this server knows")
        async with self.store.transaction() as tx:
            await tx.add_user_consent(user_id, key=key, version=version, policy_version=self.documents.version,
                                      language=language, source=source)
        return await self.status(user_id)

    async def check(self, user_id: uuid.UUID) -> None:
        """Refuse (403 consent_required) a user who has not agreed, when that is enforced. One read per user per
        process: an agreement is never taken back while the account exists, and a new text version is a new process."""
        if not self.enforced or user_id in self._agreed:
            return
        if (await self.status(user_id))["missing"]:
            raise ApiError("consent_required", "agree to the privacy consent before practising", status=403)
