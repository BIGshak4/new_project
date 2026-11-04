"""Permanent account identities and explicit, owner-scoped friendship requests."""

import re

from sqlalchemy.exc import IntegrityError

from app.api.errors import ApiError
from app.services.usernames import display_username, username_key, username_reason

FRIEND_LIMIT, PENDING_LIMIT = 200, 100
_CODE = re.compile(r"[0-9A-F]{8}\Z")


class IdentityService:
    def __init__(self, store, avatars):
        self.store, self.avatars = store, avatars

    @staticmethod
    async def _available(tx):
        if not await tx.identities_available():
            raise ApiError("evaluation_unavailable", "account identity is not enabled on this server yet", status=503)

    @staticmethod
    def _identity(row):
        if row is None:
            raise ApiError("not_found", "this account profile is not available")
        return {"username": row["username"], "friend_code": row["friend_code"],
                "can_claim_username": row["username"] is None}

    async def get(self, user_id):
        async with self.store.transaction() as tx:
            await self._available(tx)
            return self._identity(await tx.load_identity(user_id))

    async def availability(self, username):
        reason = username_reason(username)
        if reason:
            return {"available": False, "reason": reason}
        async with self.store.transaction() as tx:
            await self._available(tx)
            taken = await tx.username_taken(username_key(username))
        return {"available": not taken, "reason": "taken" if taken else None}

    async def claim(self, user_id, username):
        reason = username_reason(username)
        if reason:
            raise ApiError(f"username_{reason}", "choose a valid, respectful username", status=422)
        normalized = display_username(username)
        try:
            async with self.store.transaction() as tx:
                await self._available(tx)
                await tx.lock_usage(user_id, "identity")
                current = await tx.load_identity(user_id)
                if current is None:
                    raise ApiError("not_found", "this account profile is not available")
                if current["username"] is not None:
                    if current["username"] == normalized:
                        return self._identity(current)  # an uncertain first claim may safely retry the same name
                    raise ApiError("username_immutable", "a claimed username cannot be changed", status=409)
                if await tx.username_taken(username_key(normalized)):
                    raise ApiError("username_taken", "this username is already taken", status=409)
                row = await tx.claim_username(user_id, normalized)
                if row is None:
                    raise ApiError("username_immutable", "a claimed username cannot be changed", status=409)
                return self._identity(row)
        except IntegrityError as exc:
            # The database's unique normalized-name index decides races across server processes.
            raise ApiError("username_taken", "this username is already taken", status=409) from exc

    async def friends(self, user_id):
        async with self.store.transaction() as tx:
            await self._available(tx)
            return await self._friends(tx, user_id)

    async def _friends(self, tx, user_id):
        rows = await tx.friend_relationships(user_id)
        peer_ids = list({row["recipient_id"] if row["requester_id"] == user_id else row["requester_id"] for row in rows})
        people = await tx.load_identities(peer_ids)
        avatars = await tx.load_avatars(peer_ids) if await tx.avatars_available() else {}
        result = {"friends": [], "incoming": [], "outgoing": []}
        for row in rows:
            peer = row["recipient_id"] if row["requester_id"] == user_id else row["requester_id"]
            identity = people.get(str(peer))
            if identity is None:
                continue
            avatar = avatars.get(str(peer))
            person = {"user_id": str(peer), "username": identity["username"], "friend_code": identity["friend_code"],
                      "avatar": self.avatars._state(avatar)[0] if avatar else None}
            if row["status"] == "accepted":
                result["friends"].append(person)
            else:
                key = "outgoing" if row["requester_id"] == user_id else "incoming"
                result[key].append({"id": str(row["id"]), "person": person, "created_at": row["created_at"].isoformat()})
        return result

    @staticmethod
    async def _named(tx, user_id):
        row = await tx.load_identity(user_id)
        if row is None or row["username"] is None:
            raise ApiError("username_required", "claim your permanent username in your profile first", status=409)

    @staticmethod
    async def _lock_pair(tx, user_id, other_id):
        # A single lock order covers the pair and both users' aggregate quotas across server processes.
        first, second = sorted((user_id, other_id), key=str)
        await tx.lock_usage(first, f"friendship:{second}")
        await tx.lock_usage(first, "friends")
        await tx.lock_usage(second, "friends")

    @staticmethod
    async def _room(tx, user_id, *, incoming=False):
        rows = await tx.friend_relationships(user_id)
        if sum(row["status"] == "accepted" for row in rows) >= FRIEND_LIMIT:
            raise ApiError("friend_limit", "the friend limit has been reached", status=409)
        owner = "recipient_id" if incoming else "requester_id"
        if sum(row["status"] == "pending" and row[owner] == user_id for row in rows) >= PENDING_LIMIT:
            raise ApiError("friend_limit", "the pending friend-request limit has been reached", status=409)

    async def request(self, user_id, friend_code):
        code = friend_code.strip().upper()
        if not _CODE.fullmatch(code):
            raise ApiError("friend_invalid_code", "a friend code contains eight hexadecimal characters", status=422)
        try:
            async with self.store.transaction() as tx:
                await self._available(tx)
                await self._named(tx, user_id)
                target = await tx.identity_by_code(code)
                if target is None:
                    raise ApiError("friend_not_found", "no account has this friend code", status=404)
                other = target["id"]
                if other == user_id:
                    raise ApiError("friend_self", "you cannot add your own account", status=422)
                await self._lock_pair(tx, user_id, other)
                existing = await tx.friend_relationship(user_id, other_id=other)
                if existing is not None:
                    if existing["status"] == "pending" and existing["recipient_id"] == user_id:
                        raise ApiError("friend_request_received", "this person already sent you a request; accept it from incoming requests", status=409)
                    return await self._friends(tx, user_id)  # same request or accepted friendship is idempotent
                await self._room(tx, user_id)
                await self._room(tx, other, incoming=True)
                await tx.add_friend_request(user_id, other)
                return await self._friends(tx, user_id)
        except IntegrityError as exc:
            raise ApiError("friend_request_conflict", "this request changed; refresh your friend list", status=409) from exc

    async def accept(self, user_id, request_id):
        async with self.store.transaction() as tx:
            await self._available(tx)
            await self._named(tx, user_id)
            row = await tx.friend_relationship(user_id, request_id=request_id)
            if row is None or row["recipient_id"] != user_id:
                raise ApiError("not_found", "this incoming request is not available")
            await self._lock_pair(tx, user_id, row["requester_id"])
            row = await tx.friend_relationship(user_id, request_id=request_id)
            if row is None:
                raise ApiError("not_found", "this incoming request is not available")
            if row["status"] != "accepted":
                for person in (user_id, row["requester_id"]):
                    if sum(r["status"] == "accepted" for r in await tx.friend_relationships(person)) >= FRIEND_LIMIT:
                        raise ApiError("friend_limit", "the friend limit has been reached", status=409)
                await tx.accept_friend_request(user_id, request_id)
            return await self._friends(tx, user_id)

    async def dismiss(self, user_id, request_id, *, incoming):
        async with self.store.transaction() as tx:
            await self._available(tx)
            row = await tx.friend_relationship(user_id, request_id=request_id)
            owner = "recipient_id" if incoming else "requester_id"
            if row is None or row[owner] != user_id:
                raise ApiError("not_found", "this request is not available")
            other = row["requester_id"] if incoming else row["recipient_id"]
            await self._lock_pair(tx, user_id, other)
            row = await tx.friend_relationship(user_id, request_id=request_id)
            if row is None:
                return await self._friends(tx, user_id)
            if row["status"] != "pending":
                raise ApiError("friend_request_conflict", "this request was already accepted; remove the friendship instead", status=409)
            await tx.delete_friend_request(user_id, request_id, incoming)
            return await self._friends(tx, user_id)

    async def remove(self, user_id, other_id):
        if user_id == other_id:
            raise ApiError("friend_self", "you cannot remove your own account", status=422)
        async with self.store.transaction() as tx:
            await self._available(tx)
            await self._lock_pair(tx, user_id, other_id)
            await tx.remove_friend(user_id, other_id)
            return await self._friends(tx, user_id)
