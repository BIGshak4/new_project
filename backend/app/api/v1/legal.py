"""The privacy policy and the consent given at sign-up (services/legal.py).

Two routes are public, because the policy must be readable before any information is given and the sign-up form
shows the consent text before an account exists: GET /v1/legal/privacy and GET /v1/legal/consents. The record of a
consent is written only for a signed-in user, from the verified token, never from an id in the request.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentAccess, Legal

router = APIRouter(tags=["legal"])


class PrivacyPolicyView(BaseModel):
    version: str
    language: str
    markdown: str


class ConsentTextView(BaseModel):
    key: str                                    # personalisation
    version: str                                # send it back with the agreement: it names the text that was shown
    required: bool                              # an unticked required box means no account
    text: str


class GivenConsentView(BaseModel):
    key: str
    version: str
    policy_version: str
    language: str
    source: str
    accepted_at: str


class ConsentStatusView(BaseModel):
    active: bool                                # false while the policy is not published: ask for nothing
    enforced: bool                              # true: practice answers 403 consent_required until `missing` is empty
    missing: list[str] = Field(default_factory=list)       # required consents not given at the current text
    given: list[GivenConsentView] = Field(default_factory=list)


class ConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., min_length=1, max_length=40)
    version: str = Field(..., min_length=1, max_length=40)
    language: Literal["he", "en"]               # the language of the text the user read
    source: Literal["signup", "prompt"]         # the sign-up form, or the one-time prompt of an existing account


@router.get("/v1/legal/privacy", response_model=PrivacyPolicyView,
            summary="The privacy policy, readable without an account; 404 until it is published")
async def privacy_policy(legal: Legal, response: Response,
                         language: str = Query("he", pattern="^(en|he)$")) -> PrivacyPolicyView:
    response.headers["Cache-Control"] = "public, max-age=300"
    return PrivacyPolicyView(**legal.policy(language))


@router.get("/v1/legal/consents", response_model=list[ConsentTextView],
            summary="The consent texts the sign-up form shows; empty until the policy is published")
async def consent_texts(legal: Legal, response: Response,
                        language: str = Query("he", pattern="^(en|he)$")) -> list[ConsentTextView]:
    response.headers["Cache-Control"] = "public, max-age=300"
    return [ConsentTextView(**item) for item in legal.consent_texts(language)]


@router.get("/v1/me/consents", response_model=ConsentStatusView, summary="Which consents I have given, and what is missing")
async def my_consents(access: CurrentAccess, legal: Legal, response: Response) -> ConsentStatusView:
    response.headers["Cache-Control"] = "no-store"
    return ConsentStatusView(**await legal.status(access.user_id))


@router.post("/v1/me/consents", response_model=ConsentStatusView,
             summary="Record that I agreed to a consent text (the version I was shown)")
async def give_consent(body: ConsentRequest, access: CurrentAccess, legal: Legal, response: Response) -> ConsentStatusView:
    response.headers["Cache-Control"] = "no-store"
    return ConsentStatusView(**await legal.record(access.user_id, key=body.key, version=body.version,
                                                  language=body.language, source=body.source))
