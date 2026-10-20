"""Paying for the site: the plans, Stripe Checkout, the customer portal and Stripe's webhook.

Not mandatory while `REQUIRE_PAYMENT` is off (Shaked, 2026-10-20): every route here works, but no practice route
refuses an unpaid user. The web app shows the payment screen at the start of the flow with a visible "continue for
free for now" while `free_option_visible` is true.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Header, Query, Request
from pydantic import BaseModel, Field

from app.api.deps import Billing, CurrentAccess

router = APIRouter(prefix="/v1", tags=["billing"])


class BillingPlanView(BaseModel):
    key: str
    label: str
    description: str
    amount_agorot: int                          # the price in agorot (4900 = ₪49); the screen formats it, never the server
    currency: str
    mode: str                                   # subscription | payment
    interval: str | None = None                 # month, for a subscription
    days: int | None = None                     # a package's length
    available: bool                             # a Stripe price exists for it on this server


class BillingView(BaseModel):
    status: str                                 # free | active | trialing | past_due | canceled | expired
    plan: str | None = None
    period_end: datetime | None = None          # paid through (subscription: the current period; package: its end)
    cancel_at_period_end: bool = False
    entitled: bool                              # may practise under the current rules (always true while payment is optional)
    required: bool                              # REQUIRE_PAYMENT: when true, unpaid users get 402 payment_required on practice routes
    free_option_visible: bool                   # show "continue for free for now" on the payment screen
    configured: bool                            # the server has Stripe keys; false = the buttons explain payment is not set up
    plans: list[BillingPlanView] = Field(default_factory=list)


class CheckoutRequest(BaseModel):
    plan: str = Field(..., max_length=40, description="a plan key from GET /v1/me/billing")
    language: str = Field("he", pattern="^(en|he)$")


class CheckoutResponse(BaseModel):
    url: str                                    # Stripe's hosted payment page; the browser navigates there


class PortalResponse(BaseModel):
    url: str                                    # Stripe's customer portal: change card, cancel, invoices


def _view(status, language: str) -> BillingView:
    return BillingView(status=status.status, plan=status.plan, period_end=status.period_end,
                       cancel_at_period_end=status.cancel_at_period_end, entitled=status.entitled, required=status.required,
                       free_option_visible=status.free_option_visible, configured=status.configured,
                       plans=[BillingPlanView(key=p.key, label=p.text("label", language), description=p.text("description", language),
                                       amount_agorot=p.amount_agorot, currency=p.currency, mode=p.mode, interval=p.interval,
                                       days=p.days, available=bool(p.stripe_price and status.configured)) for p in status.plans])


@router.get("/me/billing", response_model=BillingView, summary="The caller's paid status and the plans on offer")
async def my_billing(access: CurrentAccess, billing: Billing,
                     language: str = Query("he", pattern="^(en|he)$")) -> BillingView:
    return _view(await billing.status(access.user_id), language)


@router.post("/me/billing/checkout", response_model=CheckoutResponse, summary="Start a Stripe Checkout for a plan")
async def checkout(body: CheckoutRequest, access: CurrentAccess, billing: Billing) -> CheckoutResponse:
    url = await billing.checkout(access.user_id, plan_key=body.plan, email=access.email, language=body.language)
    return CheckoutResponse(url=url)


@router.post("/me/billing/portal", response_model=PortalResponse, summary="Open Stripe's customer portal (cancel, change card)")
async def portal(access: CurrentAccess, billing: Billing) -> PortalResponse:
    return PortalResponse(url=await billing.portal(access.user_id))


@router.post("/billing/webhook", summary="Stripe's webhook (signature-verified, idempotent); not for the browser",
             include_in_schema=False)
async def webhook(request: Request, billing: Billing,
                  stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None) -> dict:
    payload = await request.body()
    return await billing.handle_webhook(payload, stripe_signature)
