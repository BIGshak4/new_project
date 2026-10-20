"""Paying for the site (Shaked, 2026-10-20): plans, Stripe Checkout, the portal, the webhook, entitlement — on the
in-memory store with the fake Stripe gateway. Not mandatory: REQUIRE_PAYMENT off is the default and stays so."""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.repo.billing import Subscription
from app.runtime import build_runtime
from app.services.billing import BillingConfig, BillingService, FakeStripe, load_plans, verify_signature
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, scripted

USER = uuid.uuid4()


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def plans(configured=True):
    prices = {"stripe_price_monthly": "price_monthly_test", "stripe_price_package": "price_package_test"} if configured \
        else {"stripe_price_monthly": None, "stripe_price_package": None}
    return load_plans(SEEDS / "billing_plans.json", prices)


def service(catalog, *, configured=True, require_payment=False):
    store = InMemoryStore(catalog)
    gateway = FakeStripe()
    svc = BillingService(store, gateway, BillingConfig(plans=plans(configured), require_payment=require_payment,
                                                       configured=configured, site_url="https://site.test"))
    return svc, store, gateway


def event(kind: str, data: dict, event_id: str | None = None) -> bytes:
    return json.dumps({"id": event_id or f"evt_{uuid.uuid4().hex[:10]}", "type": kind, "data": {"object": data}}).encode()


class TestPlans:
    def test_the_two_plans_load_with_their_prices_and_words(self):
        loaded = plans()
        assert [p.key for p in loaded] == ["monthly", "package"]
        monthly, package = loaded
        assert monthly.mode == "subscription" and monthly.interval == "month" and monthly.amount_agorot == 4900
        assert package.mode == "payment" and package.days == 90 and package.amount_agorot == 14900
        assert monthly.text("label", "he") == "חודשי" and package.text("label", "en") == "Three months"
        assert monthly.stripe_price == "price_monthly_test"
        assert all(p.stripe_price is None for p in plans(configured=False))


class TestTheStatusAndTheSwitch:
    async def test_a_new_user_is_free_and_entitled_while_payment_is_optional(self, catalog):
        svc, _, _ = service(catalog)
        status = await svc.status(USER)
        assert status.status == "free" and status.entitled is False and status.required is False
        assert status.free_option_visible is True and len(status.plans) == 2
        assert await svc.is_entitled(USER) is True                         # the switch is off: everyone practises

    async def test_with_the_switch_on_only_a_paid_user_is_entitled(self, catalog):
        svc, store, _ = service(catalog, require_payment=True)
        assert await svc.is_entitled(USER) is False
        store.subscriptions[USER] = Subscription(user_id=USER, status="active", plan="monthly", customer_id="cus_1")
        svc._entitled_cache.clear()
        assert await svc.is_entitled(USER) is True
        store.subscriptions[USER] = Subscription(user_id=USER, status="active", plan="package",
                                                 period_end=datetime.now(UTC) - timedelta(days=1))
        svc._entitled_cache.clear()
        assert await svc.is_entitled(USER) is False                        # a package that ran out
        store.subscriptions[USER] = Subscription(user_id=USER, status="past_due", plan="monthly")
        svc._entitled_cache.clear()
        assert await svc.is_entitled(USER) is False


class TestCheckoutAndPortal:
    async def test_checkout_returns_stripes_page_and_remembers_nothing_sensitive(self, catalog):
        svc, _, gateway = service(catalog)
        url = await svc.checkout(USER, plan_key="monthly", email="u@example.com", language="en")
        assert url.startswith("https://checkout.stripe.test/monthly/")
        assert gateway.sessions[-1]["mode"] == "subscription" and gateway.sessions[-1]["metadata"]["user_id"] == str(USER)
        with pytest.raises(ApiError) as refused:
            await svc.checkout(USER, plan_key="gold", email=None)
        assert refused.value.code == "validation"

    async def test_without_stripe_keys_checkout_says_payment_is_not_set_up(self, catalog):
        svc, _, _ = service(catalog, configured=False)
        with pytest.raises(ApiError) as refused:
            await svc.checkout(USER, plan_key="monthly", email=None)
        assert refused.value.code == "evaluation_unavailable" and refused.value.status == 503
        status = await svc.status(USER)
        assert status.configured is False

    async def test_the_portal_needs_a_customer(self, catalog):
        svc, store, _ = service(catalog)
        with pytest.raises(ApiError) as refused:
            await svc.portal(USER)
        assert refused.value.code == "not_found"
        store.subscriptions[USER] = Subscription(user_id=USER, status="active", plan="monthly", customer_id="cus_9")
        assert (await svc.portal(USER)).endswith("/portal/cus_9")


class TestTheWebhook:
    def test_signatures_are_checked_and_stale_ones_refused(self):
        gateway = FakeStripe()
        payload = event("invoice.paid", {"id": "in_1"})
        assert verify_signature(payload, gateway.sign(payload), gateway.secret)["type"] == "invoice.paid"
        for bad in (None, "t=abc,v1=00", gateway.sign(payload).replace("v1=", "v1=0")):
            with pytest.raises(ApiError):
                verify_signature(payload, bad, gateway.secret)
        with pytest.raises(ApiError, match="stale"):
            verify_signature(payload, gateway.sign(payload, now=time.time() - 3600), gateway.secret)

    async def test_a_package_payment_opens_ninety_days_and_a_repeat_delivery_is_ignored(self, catalog):
        svc, store, gateway = service(catalog)
        payload = event("checkout.session.completed", {"id": "cs_1", "mode": "payment", "payment_status": "paid",
                                                       "customer": "cus_p", "client_reference_id": str(USER),
                                                       "metadata": {"user_id": str(USER), "plan": "package"}}, event_id="evt_pkg")
        result = await svc.handle_webhook(payload, gateway.sign(payload))
        assert result["applied"] is True
        sub = store.subscriptions[USER]
        assert sub.status == "active" and sub.plan == "package" and sub.customer_id == "cus_p"
        assert sub.period_end is not None and 89 <= (sub.period_end - datetime.now(UTC)).days <= 90
        again = await svc.handle_webhook(payload, gateway.sign(payload))
        assert again["duplicate"] is True and store.subscriptions[USER].period_end == sub.period_end

    async def test_a_subscription_lives_through_its_events(self, catalog):
        svc, store, gateway = service(catalog)
        end = int((datetime.now(UTC) + timedelta(days=30)).timestamp())
        steps = [
            ("checkout.session.completed", {"id": "cs_2", "mode": "subscription", "payment_status": "paid", "customer": "cus_s",
                                            "subscription": "sub_1", "client_reference_id": str(USER), "metadata": {"user_id": str(USER), "plan": "monthly"}}),
            ("customer.subscription.updated", {"id": "sub_1", "status": "active", "customer": "cus_s", "current_period_end": end,
                                               "cancel_at_period_end": False, "metadata": {"plan": "monthly"}}),
            ("invoice.payment_failed", {"id": "in_2", "customer": "cus_s"}),
            ("invoice.paid", {"id": "in_3", "customer": "cus_s"}),
            ("customer.subscription.updated", {"id": "sub_1", "status": "active", "customer": "cus_s", "current_period_end": end,
                                               "cancel_at_period_end": True}),
            ("customer.subscription.deleted", {"id": "sub_1", "status": "canceled", "customer": "cus_s", "current_period_end": end}),
        ]
        statuses = []
        for kind, data in steps:
            payload = event(kind, data)
            await svc.handle_webhook(payload, gateway.sign(payload))
            statuses.append(store.subscriptions[USER].status)
        assert statuses == ["active", "active", "past_due", "active", "active", "canceled"]
        sub = store.subscriptions[USER]
        assert sub.subscription_id == "sub_1" and sub.period_end is not None and sub.plan == "monthly"
        # the customer id matched the later events to the user even without metadata
        assert all(e["user_id"] == USER for e in store.billing_events.values())

    async def test_unknown_and_unmatched_events_are_acknowledged_not_applied(self, catalog):
        svc, store, gateway = service(catalog)
        payload = event("charge.refunded", {"id": "ch_1"})
        assert (await svc.handle_webhook(payload, gateway.sign(payload)))["applied"] is False
        orphan = event("invoice.paid", {"id": "in_9", "customer": "cus_nobody"})
        result = await svc.handle_webhook(orphan, gateway.sign(orphan))
        assert result["applied"] is False and result.get("unmatched") is True
        assert not store.subscriptions


MEMBER = "member@example.com"


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True,
                        interview_reviewed_only=False, suggest_reviewed_only=False)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=scripted([GOOD, GOOD, GOOD]),
                                      store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestOverHttp:
    async def test_billing_routes_and_the_webhook(self, client):
        _, token = make_token(email=MEMBER)
        headers = {"Authorization": f"Bearer {token}"}
        body = (await client.get("/v1/me/billing?language=he", headers=headers)).json()
        assert body["status"] == "free" and body["required"] is False and body["entitled"] is False
        assert body["free_option_visible"] is True and [p["key"] for p in body["plans"]] == ["monthly", "package"]
        assert body["plans"][0]["label"] == "חודשי" and body["plans"][0]["available"] is False     # no keys on the test server
        assert body["configured"] is False
        refused = await client.post("/v1/me/billing/checkout", json={"plan": "monthly"}, headers=headers)
        assert refused.status_code == 503 and refused.json()["error"]["code"] == "evaluation_unavailable"
        assert (await client.post("/v1/me/billing/checkout", json={"plan": "x" * 41}, headers=headers)).status_code == 422
        assert (await client.post("/v1/me/billing/portal", headers=headers)).status_code == 404
        # the webhook needs a valid signature and no user token
        gateway = app.state.runtime.billing.gateway
        payload = event("charge.refunded", {"id": "ch"})
        assert (await client.post("/v1/billing/webhook", content=payload)).status_code == 422
        ok = await client.post("/v1/billing/webhook", content=payload, headers={"Stripe-Signature": gateway.sign(payload)})
        assert ok.status_code == 200 and ok.json()["received"] is True
        # practice still works for a free user while payment is optional
        started = await client.post("/v1/practice/attempts", json={"question_key": "example-sensor-majority"}, headers=headers)
        assert started.status_code == 201, started.text

    async def test_with_payment_required_an_unpaid_member_gets_402_and_billing_stays_open(self, client):
        billing = app.state.runtime.billing
        billing.config.require_payment = True
        try:
            _, token = make_token(email=MEMBER)
            headers = {"Authorization": f"Bearer {token}"}
            refused = await client.post("/v1/practice/attempts", json={"question_key": "example-sensor-majority"}, headers=headers)
            assert refused.status_code == 402 and refused.json()["error"]["code"] == "payment_required"
            assert (await client.get("/v1/me/billing", headers=headers)).status_code == 200
            assert (await client.get("/v1/me/progress", headers=headers)).status_code == 200
        finally:
            billing.config.require_payment = False
            billing._entitled_cache.clear()
