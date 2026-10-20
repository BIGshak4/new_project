"""The price of a plan with a target profit after everything (Shaked, 2026-10-20: "35 percent profit after all").

    cd backend && uv run python scripts/pricing.py                       # both plans with the default assumptions
    uv run python scripts/pricing.py --answers 150 --users 30 --profit 0.35

Inputs, all overridable: the model cost per scored answer (measured on production on 2026-10-20: $0.0745 across
the judge, the follow-up, the feedback and the tip), the exchange rate, Stripe's fee (2.9 % + ₪1.20 per charge for
Israeli cards), the fixed monthly cost shared by the paying users (Render, Supabase, Netlify), and VAT (18 %).

    price_net  = (model cost + fixed share) x (1 + profit) / (1 - stripe %) + stripe fixed
    price      = price_net x (1 + VAT)
"""

from __future__ import annotations

import argparse
import math

MODEL_COST_PER_ANSWER_USD = 0.0745     # production average, 2026-10-20 (37 attempts, $2.76)
USD_TO_ILS = 3.7
STRIPE_PERCENT = 0.029
STRIPE_FIXED_ILS = 1.20
FIXED_MONTHLY_USD = 50.0               # Render + Supabase + Netlify, roughly
VAT = 0.18

PLANS = {"regular": {"daily_cap": 30, "answers_per_month": 110}, "premium": {"daily_cap": 50, "answers_per_month": 240}}


def price_ils(answers_per_month: float, *, paying_users: int, profit: float, model_cost_usd: float = MODEL_COST_PER_ANSWER_USD,
              usd_to_ils: float = USD_TO_ILS, fixed_monthly_usd: float = FIXED_MONTHLY_USD) -> dict:
    model = answers_per_month * model_cost_usd * usd_to_ils
    fixed = fixed_monthly_usd * usd_to_ils / max(1, paying_users)
    net = (model + fixed) * (1 + profit) / (1 - STRIPE_PERCENT) + STRIPE_FIXED_ILS
    gross = net * (1 + VAT)
    return {"model_cost_ils": round(model, 1), "fixed_share_ils": round(fixed, 1), "price_net_ils": round(net, 1),
            "price_ils": round(gross, 1), "suggested_ils": int(math.ceil(gross / 10.0) * 10 - 1)}


def answers_for_profit(price_ils_gross: float, *, paying_users: int, profit: float) -> float:
    """How many answers a month a given price still carries at the target profit (and at break-even when profit=0)."""
    net = price_ils_gross / (1 + VAT)
    fixed = FIXED_MONTHLY_USD * USD_TO_ILS / max(1, paying_users)
    model_budget = (net - STRIPE_FIXED_ILS) * (1 - STRIPE_PERCENT) / (1 + profit) - fixed
    return max(0.0, model_budget / (MODEL_COST_PER_ANSWER_USD * USD_TO_ILS))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profit", type=float, default=0.35)
    parser.add_argument("--users", type=int, default=50, help="paying users sharing the fixed costs")
    parser.add_argument("--answers", type=float, default=None, help="answers a month to price a single plan on")
    parser.add_argument("--cost", type=float, default=MODEL_COST_PER_ANSWER_USD, help="model cost per scored answer, USD")
    args = parser.parse_args()
    if args.answers is not None:
        print(price_ils(args.answers, paying_users=args.users, profit=args.profit, model_cost_usd=args.cost))
        return
    for key, plan in PLANS.items():
        p = price_ils(plan["answers_per_month"], paying_users=args.users, profit=args.profit, model_cost_usd=args.cost)
        print(f"{key:8} cap {plan['daily_cap']}/day, priced on {plan['answers_per_month']} answers/month: "
              f"model ₪{p['model_cost_ils']}, fixed ₪{p['fixed_share_ils']}, net ₪{p['price_net_ils']}, "
              f"incl. VAT ₪{p['price_ils']} -> suggested ₪{p['suggested_ils']}")
        for price in (p["suggested_ils"],):
            print(f"          at ₪{price}: {args.profit:.0%} profit up to {answers_for_profit(price, paying_users=args.users, profit=args.profit):.0f} "
                  f"answers/month, break-even at {answers_for_profit(price, paying_users=args.users, profit=0.0):.0f}; "
                  f"the daily cap allows {plan['daily_cap'] * 30}")


if __name__ == "__main__":
    main()
