import copy
import uuid

import pytest
from pydantic import ValidationError

from app.api.errors import ApiError
from app.engine.catalog import load_catalog
from app.schemas.visual_answer import VisualAnswer
from tests.test_practice_hardening import GOOD, SEEDS, scripted
from tests.test_practice_service import OTHER, USER, Q, service


def visual():
    return {"circuit": {"version": 1, "parts": [{"id": "and", "kind": "and", "label": "AND", "x": 0, "y": 0, "bits": 1, "count": 2, "value": 0}], "wires": []}, "images": []}


@pytest.fixture
def setup():
    return service(load_catalog(SEEDS), scripted([GOOD, GOOD]))


async def test_circuit_only_is_assessed_kept_and_replayed(setup):
    svc, store = setup
    a = await svc.start(USER, question_key=Q, mode="quick", language="he")
    aid = uuid.UUID(a.id)
    await svc.next_hint(USER, aid)
    profiles_before = copy.deepcopy(store.profiles)
    answer = {"text": "", "visual": visual()}
    s, a = await svc.submit(USER, aid, answer, idempotency_key="circuit")
    assert a.status == "done" and s.visual.model_dump() == visual()
    # a drawing is real work: the evaluator sees its netlist and the answer is scored like any other
    assert s.assessed_by == "demo" and s.band is not None and s.evaluated_at is not None and s.hints_seen == 1
    assert "circuit_assessed" in s.flags and "visual_review_pending" not in s.flags
    assert store.metrics and store.profiles != profiles_before
    request = svc.provider.requests[0]
    assert "<candidate_circuit>" in request.user and 'AND "AND"' in request.user and request.images == []
    restored = await svc.get(USER, aid)
    assert restored.submission.visual == s.visual
    replay, _ = await svc.submit(USER, aid, answer, idempotency_key="circuit")
    assert replay.replayed and len(store.attempts[aid]["row"]["submissions"]) == 1
    answer["visual"]["circuit"]["parts"][0]["x"] = 50
    with pytest.raises(ApiError, match="different answer"):
        await svc.submit(USER, aid, answer, idempotency_key="circuit")
    with pytest.raises(ApiError):
        await svc.get(OTHER, aid)
    await svc.reveal_reference(USER, aid)
    assert (await svc.get(USER, aid)).submission.reference_seen is False


async def test_image_only_missing_cross_owner_and_cross_attempt_rejected(setup):
    svc, store = setup
    a = await svc.start(USER, question_key=Q, mode="quick")
    aid = uuid.UUID(a.id)
    image = {"path": f"{USER}/{aid}/{uuid.uuid4()}.jpg", "mime": "image/jpeg", "size": 100, "name": "handwritten.jpg"}
    answer = {"text": "", "visual": {"circuit": None, "images": [image]}}
    with pytest.raises(ApiError, match="image"):
        await svc.submit(USER, aid, answer, idempotency_key="image")
    assert not store.attempts[aid]["row"]["submissions"]
    store.answer_images[image["path"]] = {"mime": "image/jpeg", "size": 100}
    other = await svc.start(USER, question_key=Q, mode="quick")
    with pytest.raises(ApiError, match="image"):
        await svc.submit(USER, uuid.UUID(other.id), answer, idempotency_key="wrong-attempt")
    s, _ = await svc.submit(USER, aid, answer, idempotency_key="image")
    assert s.visual.images[0].path == image["path"] and s.band is None
    # no service key on this server: the photo is kept for a human, nothing is invented about it
    assert s.assessed_by == "unassessed" and s.flags == ["visual_review_pending", "images_not_assessed"]
    assert not svc.provider.requests


@pytest.mark.parametrize("mutate", [
    lambda v: v["circuit"].update(version=2),
    lambda v: v["circuit"]["parts"][0].update(bits=100),
    lambda v: v["circuit"]["parts"][0].update(x=float("inf")),
    lambda v: v["circuit"].update(parts=v["circuit"]["parts"] * 101),
    lambda v: v["circuit"]["parts"][0].update(kind="mux", count=3),
    lambda v: v.update(images=[{"path": "https://example.org/x.jpg", "name": "x", "mime": "image/jpeg", "size": 2}]),
    lambda v: v["circuit"].update(wires=[{"id": "w", "source": "missing", "sourcePort": "Q", "target": "and", "targetPort": "A0"}]),
])
def test_visual_payload_bounds(mutate):
    v = visual()
    mutate(v)
    with pytest.raises(ValidationError):
        VisualAnswer.model_validate(v)
