"""Paying for the site: plans, Stripe Checkout, the customer portal, the webhook, and who is entitled.

Shaked, 2026-10-20: a payment page at the start of the flow, not mandatory for now. `require_payment` (off) is the
only switch between "everyone practises" and "paid users practise"; the rest of this module works the same either
way, so the switch can be flipped without a deploy. Card data never reaches us: Stripe's hosted page takes it.

The Stripe calls are two form-encoded POSTs and one signature check, done with httpx (no SDK): a `StripeGateway`
protocol with the real `HttpStripe` and a `FakeStripe` for tests and for a server without keys.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol

import httpx

from app.api.errors import ApiError
from app.repo.billing import STATUSES, Subscription

log = logging.getLogger("app.billing")

STRIPE_API = "https://api.stripe.com/v1"
SIGNATURE_TOLERANCE_SECONDS = 300
HANDLED_EVENTS = ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated",
                  "customer.subscription.deleted", "invoice.payment_failed", "invoice.paid")


@dataclass
class Plan:
    key: str
    label: dict[str, str]
    description: dict[str, str]
    amount_agorot: int
    currency: str
    mode: str                                 # subscription | payment
    interval: str | None = None               # month, for a subscription
    days: int | None = None                   # a package's length (none of the current plans)
    daily_questions: int | None = None        # the plan's cap on questions a day (regular 30, premium 50)
    stripe_price: str | None = None           # the Stripe price id, from the settings

    def text(self, field_name: str, language: str) -> str:
        values = getattr(self, field_name)
        return values.get(language) or values.get("en") or next(iter(values.values()), "")


def load_plans(path: Path, prices: dict[str, str | None]) -> list[Plan]:
    """seeds/billing_plans.json plus the Stripe price ids from the settings (by the file's `stripe_price_setting`)."""
    plans = []
    for item in json.loads(path.read_text(encoding="utf-8")):
        plans.append(Plan(key=item["key"], label=item["label"], description=item.get("description", {}),
                          amount_agorot=int(item["amount_agorot"]), currency=item.get("currency", "ils"),
                          mode=item["mode"], interval=item.get("interval"), days=item.get("days"),
                          daily_questions=item.get("daily_questions"),
                          stripe_price=prices.get(item.get("stripe_price_setting", ""))))
    return plans


class StripeGateway(Protocol):
    async def create_checkout_session(self, *, mode: str, price: str, user_id: uuid.UUID, email: str | None,
                                      customer_id: str | None, plan: str, success_url: str, cancel_url: str) -> dict: ...
    async def create_portal_session(self, *, customer_id: str, return_url: str) -> dict: ...
    def verify(self, payload: bytes, signature_header: str | None) -> dict: ...


def verify_signature(payload: bytes, signature_header: str | None, secret: str, *, now: float | None = None) -> dict:
    """Stripe's webhook signature: `t=<unix>,v1=<hmac-sha256 of "<t>.<payload>">`. Raises on anything wrong."""
    if not signature_header:
        raise ApiError("validation", "missing Stripe-Signature")
    parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
    stamp, given = parts.get("t"), parts.get("v1")
    if not stamp or not given or not stamp.isdigit():
        raise ApiError("validation", "malformed Stripe-Signature")
    if abs((now or time.time()) - int(stamp)) > SIGNATURE_TOLERANCE_SECONDS:
        raise ApiError("validation", "stale Stripe-Signature")
    expected = hmac.new(secret.encode(), f"{stamp}.".encode() + payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, given):
        raise ApiError("forbidden", "Stripe-Signature does not match")
    try:
        return json.loads(payload)
    except ValueError as exc:
        raise ApiError("validation", "the webhook body is not JSON") from exc


class HttpStripe:
    """The two Stripe calls we make, form-encoded over httpx, plus the signature check."""

    def __init__(self, secret_key: str, webhook_secret: str | None, *, timeout: float = 20.0):
        self.secret_key, self.webhook_secret, self.timeout = secret_key, webhook_secret, timeout

    async def _post(self, path: str, data: dict) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{STRIPE_API}{path}", data=data, auth=(self.secret_key, ""))
        if response.status_code >= 400:
            message = (response.json().get("error") or {}).get("message", "") if response.headers.get("content-type", "").startswith("application/json") else ""
            log.warning("stripe %s -> %s %s", path, response.status_code, message[:120])
            raise ApiError("evaluation_unavailable", "the payment provider refused the request; try again in a minute", status=503)
        return response.json()

    async def create_checkout_session(self, *, mode, price, user_id, email, customer_id, plan, success_url, cancel_url):
        data = {"mode": mode, "line_items[0][price]": price, "line_items[0][quantity]": "1",
                "success_url": success_url, "cancel_url": cancel_url, "client_reference_id": str(user_id),
                "metadata[user_id]": str(user_id), "metadata[plan]": plan, "allow_promotion_codes": "true"}
        if mode == "subscription":
            data["subscription_data[metadata][user_id]"] = str(user_id)
            data["subscription_data[metadata][plan]"] = plan
        if customer_id:
            data["customer"] = customer_id
        elif email:
            data["customer_email"] = email
        return await self._post("/checkout/sessions", data)

    async def create_portal_session(self, *, customer_id, return_url):
        return await self._post("/billing_portal/sessions", {"customer": customer_id, "return_url": return_url})

    def verify(self, payload, signature_header):
        if not self.webhook_secret:
            raise ApiError("evaluation_unavailable", "the webhook secret is not configured", status=503)
        return verify_signature(payload, signature_header, self.webhook_secret)


class FakeStripe:
    """No keys: checkout and portal return a page that explains payment is not configured; the webhook verifies
    against a fixed test secret. Tests drive it directly."""

    secret = "whsec_test"

    def __init__(self):
        self.sessions: list[dict] = []

    async def create_checkout_session(self, *, mode, price, user_id, email, customer_id, plan, success_url, cancel_url):
        session = {"id": f"cs_test_{len(self.sessions) + 1}", "url": f"https://checkout.stripe.test/{plan}/{user_id}",
                   "mode": mode, "customer": customer_id or f"cus_test_{str(user_id)[:8]}", "metadata": {"user_id": str(user_id), "plan": plan}}
        self.sessions.append(session)
        return session

    async def create_portal_session(self, *, customer_id, return_url):
        return {"url": f"https://billing.stripe.test/portal/{customer_id}"}

    def verify(self, payload, signature_header):
        return verify_signature(payload, signature_header, self.secret)

    def sign(self, payload: bytes, *, now: float | None = None) -> str:
        stamp = int(now or time.time())
        digest = hmac.new(self.secret.encode(), f"{stamp}.".encode() + payload, hashlib.sha256).hexdigest()
        return f"t={stamp},v1={digest}"


@dataclass
class BillingConfig:
    plans: list[Plan]
    require_payment: bool = False
    free_option_visible: bool = True          # the "continue for free for now" choice on the payment screen
    site_url: str = "https://jobrun-practice.netlify.app"
    configured: bool = False                  # real Stripe keys present


@dataclass
class BillingStatus:
    status: str
    plan: str | None
    period_end: datetime | None
    cancel_at_period_end: bool
    entitled: bool
    required: bool
    free_option_visible: bool
    configured: bool
    plans: list[Plan] = field(default_factory=list)


class BillingService:
    def __init__(self, store, gateway: StripeGateway, config: BillingConfig):
        self.store, self.gateway, self.config = store, gateway, config
        self._entitled_cache: dict[uuid.UUID, tuple[float, Subscription]] = {}

    def plan(self, key: str) -> Plan:
        for plan in self.config.plans:
            if plan.key == key:
                return plan
        raise ApiError("validation", f"unknown plan {key!r}")

    async def status(self, user_id: uuid.UUID) -> BillingStatus:
        async with self.store.transaction() as tx:
            subscription = await tx.load_subscription(user_id)
        return BillingStatus(status=subscription.status, plan=subscription.plan, period_end=subscription.period_end,
                             cancel_at_period_end=subscription.cancel_at_period_end, entitled=subscription.entitled(),
                             required=self.config.require_payment, free_option_visible=self.config.free_option_visible,
                             configured=self.config.configured, plans=list(self.config.plans))

    async def _current(self, user_id: uuid.UUID) -> Subscription:
        """The user's subscription, cached a minute (cleared on every webhook event)."""
        cached = self._entitled_cache.get(user_id)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        async with self.store.transaction() as tx:
            subscription = await tx.load_subscription(user_id)
        self._entitled_cache[user_id] = (time.monotonic() + 60, subscription)
        if len(self._entitled_cache) > 10_000:
            self._entitled_cache.clear()
        return subscription

    async def is_entitled(self, user_id: uuid.UUID) -> bool:
        """What the practice routes ask when payment is required."""
        if not self.config.require_payment:
            return True
        return (await self._current(user_id)).entitled()

    async def daily_limit(self, user_id: uuid.UUID, *, default: int) -> int:
        """How many questions this user may start today: the plan's cap while the plan is live, else the default
        (which is what a free user gets while payment is optional)."""
        subscription = await self._current(user_id)
        if not subscription.entitled() or not subscription.plan:
            return default
        plan = next((p for p in self.config.plans if p.key == subscription.plan), None)
        return plan.daily_questions if plan and plan.daily_questions else default

    async def checkout(self, user_id: uuid.UUID, *, plan_key: str, email: str | None, language: str = "he") -> str:
        """The URL of Stripe's payment page for this plan. The user comes back to the site either way."""
        plan = self.plan(plan_key)
        if not self.config.configured or not plan.stripe_price:
            raise ApiError("evaluation_unavailable", "payment is not set up on this server yet", status=503)
        async with self.store.transaction() as tx:
            current = await tx.load_subscription(user_id)
        if current.entitled() and current.status in ("active", "trialing") and plan.mode == "subscription" and current.subscription_id:
            raise ApiError("already_submitted", "you already have an active subscription; manage it from the billing page")
        base = self.config.site_url.rstrip("/")
        session = await self.gateway.create_checkout_session(
            mode=plan.mode, price=plan.stripe_price, user_id=user_id, email=email, customer_id=current.customer_id,
            plan=plan.key, success_url=f"{base}/?billing=success&lang={language}", cancel_url=f"{base}/?billing=cancel&lang={language}")
        log.info("checkout session %s user=%s plan=%s", session.get("id"), user_id, plan.key)      # never the URL, never a card
        return session["url"]

    async def portal(self, user_id: uuid.UUID) -> str:
        async with self.store.transaction() as tx:
            current = await tx.load_subscription(user_id)
        if not current.customer_id:
            raise ApiError("not_found", "no payment on this account yet")
        if not self.config.configured:
            raise ApiError("evaluation_unavailable", "payment is not set up on this server yet", status=503)
        session = await self.gateway.create_portal_session(customer_id=current.customer_id, return_url=self.config.site_url)
        return session["url"]

    # ------------------------------------------------------------------ the webhook

    async def handle_webhook(self, payload: bytes, signature_header: str | None) -> dict:
        """Apply one Stripe event. Signature-verified; idempotent (an event id is applied once); unknown events are
        acknowledged and ignored, as Stripe expects a 2xx for everything it delivers."""
        event = self.gateway.verify(payload, signature_header)
        event_id, kind = str(event.get("id") or ""), str(event.get("type") or "")
        data = (event.get("data") or {}).get("object") or {}
        if not event_id or not kind:
            raise ApiError("validation", "the event has no id or type")
        if kind not in HANDLED_EVENTS:
            return {"received": True, "applied": False, "kind": kind}
        async with self.store.transaction() as tx:
            user_id = await self._user_for(tx, data)
            if not await tx.record_billing_event(event_id=event_id, kind=kind, user_id=user_id, summary=self._summary(kind, data)):
                return {"received": True, "applied": False, "kind": kind, "duplicate": True}
            if user_id is None:
                log.warning("stripe event %s %s: no user could be matched", event_id, kind)
                return {"received": True, "applied": False, "kind": kind, "unmatched": True}
            subscription = await tx.load_subscription(user_id)
            changed = self._apply(kind, data, subscription)
            if changed:
                subscription.updated_at = datetime.now(UTC)
                await tx.save_subscription(subscription)
        self._entitled_cache.pop(user_id, None)
        log.info("stripe %s applied user=%s status=%s plan=%s", kind, user_id, subscription.status, subscription.plan)
        return {"received": True, "applied": changed, "kind": kind}

    async def _user_for(self, tx, data: dict) -> uuid.UUID | None:
        metadata = data.get("metadata") or {}
        raw = metadata.get("user_id") or data.get("client_reference_id")
        if raw:
            try:
                return uuid.UUID(str(raw))
            except ValueError:
                pass
        customer = data.get("customer")
        if isinstance(customer, dict):
            customer = customer.get("id")
        if customer:
            known = await tx.subscription_by_customer(str(customer))
            if known is not None:
                return known.user_id
        return None

    @staticmethod
    def _summary(kind: str, data: dict) -> dict:
        """What we keep of an event: ids, status, amounts; never a card, never an address."""
        keep = {k: data.get(k) for k in ("id", "status", "customer", "subscription", "mode", "payment_status",
                                          "amount_total", "currency", "cancel_at_period_end", "current_period_end")}
        keep["plan"] = (data.get("metadata") or {}).get("plan")
        return {k: (v if not isinstance(v, dict) else v.get("id")) for k, v in keep.items() if v is not None}

    def _apply(self, kind: str, data: dict, s: Subscription) -> bool:
        before = (s.status, s.plan, s.customer_id, s.subscription_id, s.period_end, s.cancel_at_period_end)
        customer = data.get("customer")
        if isinstance(customer, dict):
            customer = customer.get("id")
        if customer:
            s.customer_id = str(customer)
        plan_key = (data.get("metadata") or {}).get("plan")
        if kind == "checkout.session.completed":
            if data.get("payment_status") not in (None, "paid", "no_payment_required"):
                return False
            if plan_key:
                s.plan = plan_key
            if data.get("mode") == "payment":                  # a package: paid now, good for the plan's days
                plan = next((p for p in self.config.plans if p.key == plan_key), None)
                days = (plan.days if plan and plan.days else 90)
                start = s.period_end if s.period_end and s.period_end > datetime.now(UTC) else datetime.now(UTC)
                s.period_end = start + timedelta(days=days)
                s.status, s.subscription_id, s.cancel_at_period_end = "active", None, False
            else:                                            # a subscription: the subscription events carry the dates
                sub = data.get("subscription")
                s.subscription_id = sub.get("id") if isinstance(sub, dict) else (str(sub) if sub else s.subscription_id)
                s.status = "active" if s.status not in ("trialing",) else s.status
        elif kind in ("customer.subscription.created", "customer.subscription.updated"):
            s.subscription_id = str(data.get("id") or s.subscription_id or "") or None
            status = str(data.get("status") or "")
            s.status = status if status in STATUSES else ("active" if status in ("incomplete", "unpaid") and s.status == "active" else s.status)
            if status in ("incomplete_expired", "unpaid"):
                s.status = "past_due"
            if plan_key:
                s.plan = plan_key
            end = data.get("current_period_end")
            if isinstance(end, (int, float)):
                s.period_end = datetime.fromtimestamp(end, tz=UTC)
            s.cancel_at_period_end = bool(data.get("cancel_at_period_end"))
        elif kind == "customer.subscription.deleted":
            s.status, s.cancel_at_period_end = "canceled", False
            end = data.get("current_period_end")
            if isinstance(end, (int, float)):
                s.period_end = datetime.fromtimestamp(end, tz=UTC)
        elif kind == "invoice.payment_failed":
            if s.status in ("active", "trialing"):
                s.status = "past_due"
        elif kind == "invoice.paid":
            if s.status == "past_due":
                s.status = "active"
            end = ((data.get("lines") or {}).get("data") or [{}])[0].get("period", {}).get("end") if isinstance(data.get("lines"), dict) else None
            if isinstance(end, (int, float)):
                s.period_end = datetime.fromtimestamp(end, tz=UTC)
        return before != (s.status, s.plan, s.customer_id, s.subscription_id, s.period_end, s.cancel_at_period_end)
