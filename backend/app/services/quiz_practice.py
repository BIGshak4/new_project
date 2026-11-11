"""A single real bank question for learning the game, without a duel or any reward.

The round token binds a question version to its authenticated owner. It contains no
answer. Service-key-derived signing is stable across API workers; local runtimes
without that key use a process secret and simply expire open rounds on restart.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from app.api.errors import ApiError

ROUND_TTL = timedelta(minutes=15)


class QuizPractice:
    def __init__(self, duels, *, secret: str | None = None):
        self.duels = duels
        material = secret.encode() if secret else secrets.token_bytes(32)
        self.signing_key = hmac.digest(material, b"jobrun:quiz-practice:v1", "sha256")

    @staticmethod
    def _version(question) -> str:
        raw = json.dumps(asdict(question), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _question(question, language: str) -> dict:
        return {"index": 0, "key": question.key, "source_key": question.source_key or question.key,
                "variant": question.variant, "prompt": question.text(question.prompt, language),
                "choices": [question.text(choice, language) for choice in question.choices]}

    def start(self, user_id: uuid.UUID, language: str) -> dict:
        if language not in ("he", "en"):
            raise ApiError("validation", "unsupported question language")
        groups = [items for items in self.duels.quiz_groups().values()
                  if all(question.status == "approved" for question in items)]
        if not groups:
            raise ApiError("no_reviewed_questions", "no approved game questions are available")
        question = secrets.choice(secrets.choice(groups))
        now = self.duels.clock()
        expires = now + ROUND_TTL
        payload = {"user": str(user_id), "key": question.key, "language": language,
                   "version": self._version(question), "iat": int(now.timestamp()),
                   "exp": int(expires.timestamp()), "nonce": secrets.token_hex(8)}
        encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
        signature = hmac.digest(self.signing_key, encoded.encode(), "sha256").hex()
        return {"round_token": encoded + "." + signature, "language": language,
                "expires_at": expires, "question": self._question(question, language)}

    def answer(self, user_id: uuid.UUID, token: str, choice: int) -> dict:
        if type(choice) is not int or choice not in range(4):
            raise ApiError("validation", "choose one of the four options")
        try:
            encoded, signature = token.split(".")
            expected = hmac.digest(self.signing_key, encoded.encode(), "sha256").hex()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("signature")
            payload = json.loads(base64.b64decode(encoded.encode(), altchars=b"-_", validate=True))
            if payload["user"] != str(user_id):
                raise ApiError("forbidden", "this practice round belongs to a different account")
            now = self.duels.clock()
            issued = datetime.fromtimestamp(payload["iat"], UTC)
            expires = datetime.fromtimestamp(payload["exp"], UTC)
            if not issued <= now < expires or expires - issued > ROUND_TTL:
                raise ValueError("expired")
            question = self.duels.quiz.get(payload["key"])
            if question is None or question.status != "approved" or self._version(question) != payload["version"]:
                raise ValueError("content changed")
            language = payload["language"]
            if language not in ("he", "en"):
                raise ValueError("language")
        except (ValueError, TypeError, KeyError, OverflowError):
            raise ApiError("practice_round_expired", "this practice round expired; open a new question", status=409) from None
        return {"question": self._question(question, language), "choice": choice,
                "correct": choice == question.correct, "correct_index": question.correct,
                "explanation": question.text(question.explanation, language)}
