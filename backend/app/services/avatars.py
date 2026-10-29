"""Free logical-component customization and one-time, server-priced cosmetic purchases."""
from __future__ import annotations

import json
from pathlib import Path

from app.api.errors import ApiError

DEFAULT_AVATAR = {"component": "mux", "color": "violet", "skin": "classic"}


def load_catalog(path: Path) -> dict:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    for group in ("components", "colors", "skins"):
        items = catalog[group]
        if len({i["key"] for i in items}) != len(items):
            raise ValueError(f"duplicate avatar {group}")
        if any(not i.get("label", {}).get(lang) for i in items for lang in ("he", "en")):
            raise ValueError(f"avatar {group} must have bilingual labels")
    if any(i["price"] < 0 or not isinstance(i["price"], int) for i in catalog["skins"]):
        raise ValueError("skin price must be a nonnegative integer")
    return catalog


class AvatarsService:
    def __init__(self, store, coins, catalog):
        self.store, self.coins, self.catalog = store, coins, catalog

    def _state(self, row):
        known = {s["key"] for s in self.catalog["skins"]}
        owned = {"classic", *((row or {}).get("owned_skins") or [])} & known
        avatar = {k: (row or {}).get(k, value) for k, value in DEFAULT_AVATAR.items()}
        if avatar["skin"] not in owned:
            avatar["skin"] = "classic"
        return avatar, sorted(owned)

    async def _view(self, tx, user_id):
        enabled = await tx.avatars_available()
        avatar, owned = self._state(await tx.load_avatar(user_id) if enabled else None)
        shop_enabled = enabled and await self.coins.enabled(tx)
        if shop_enabled:
            await self.coins.ensure_gift(tx, user_id)
        return {"avatar": avatar, "owned_skins": owned, **self.catalog,
                "balance": await tx.coin_balance(user_id) if shop_enabled else 0,
                "enabled": enabled, "shop_enabled": shop_enabled, "shirt_text": "Job_Run",
                "capabilities": {"persistent_avatar": True, "cosmetic_shop": True}}

    async def get(self, user_id):
        async with self.store.transaction() as tx:
            await tx.lock_usage(user_id, "coins")
            return await self._view(tx, user_id)

    async def _available(self, tx):
        if not await tx.avatars_available():
            raise ApiError("evaluation_unavailable", "avatar customization is not enabled on this server yet", status=503)

    async def save(self, user_id, avatar):
        for field, group in (("component", "components"), ("color", "colors"), ("skin", "skins")):
            if avatar[field] not in {i["key"] for i in self.catalog[group]}:
                raise ApiError("validation", f"unknown avatar {field}")
        async with self.store.transaction() as tx:
            await self._available(tx)
            await tx.lock_usage(user_id, "coins")
            _, owned = self._state(await tx.load_avatar(user_id))
            if avatar["skin"] not in owned:
                raise ApiError("forbidden", "this skin is not owned by this account")
            await tx.save_avatar(user_id, avatar, owned)
            return await self._view(tx, user_id)

    async def buy(self, user_id, skin):
        item = next((i for i in self.catalog["skins"] if i["key"] == skin), None)
        if item is None:
            raise ApiError("validation", "unknown cosmetic skin")
        async with self.store.transaction() as tx:
            await self._available(tx)
            await tx.lock_usage(user_id, "coins")
            if not await self.coins.enabled(tx):
                raise ApiError("evaluation_unavailable", "coins are not enabled on this server yet", status=503)
            avatar, owned = self._state(await tx.load_avatar(user_id))
            if skin not in owned:
                await self.coins.ensure_gift(tx, user_id)
                price = item["price"]
                if await tx.coin_balance(user_id) < price:
                    raise ApiError("usage_limit", "not enough coins for this skin", status=402)
                if price:
                    await tx.coin_add(user_id=user_id, delta=-price, kind="spend", reference=f"cosmetic:{skin}",
                                      item=skin, meta={"cosmetic_skin": skin})
                owned.append(skin)
                await tx.save_avatar(user_id, avatar, owned)
            return await self._view(tx, user_id)

    async def public_configs(self, user_ids):
        """Only visible component/color/skin for authorized duel participants, never ownership or balances."""
        async with self.store.transaction() as tx:
            users = list({user for user in user_ids if user})
            rows = await tx.load_avatars(users) if await tx.avatars_available() else {}
            return {str(user): self._state(rows.get(str(user)))[0] for user in users}
