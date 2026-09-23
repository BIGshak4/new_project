"""What a drawing or photos add to an answer, for the evaluator and the checks. Shared by practice and interviews."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from app.engine import circuit_text
from app.schemas.visual_answer import VisualAnswer

log = logging.getLogger("app.engine.visual")

ImageFetcher = Callable[[str], Awaitable[tuple[str, bytes] | None]]


@dataclass
class VisualEvidence:
    circuit: str | None = None                          # netlist text for the evaluator
    images: list[tuple[str, bytes]] = field(default_factory=list)
    missing: int = 0                                    # photos that could not be read
    flags: list[str] = field(default_factory=list)
    check_lines: str = ""                               # "alarm = (A & B) | ..." lines for the deterministic checks

    @property
    def has_content(self) -> bool:
        return self.circuit is not None or bool(self.images)


async def gather(visual: VisualAnswer | None, fetcher: ImageFetcher | None) -> VisualEvidence:
    """A drawn circuit becomes text and derived functions; photos are fetched (never fatal) and counted."""
    evidence = VisualEvidence()
    if visual is None:
        return evidence
    if visual.circuit is not None and visual.circuit.parts:
        evidence.circuit = circuit_text.describe(visual.circuit)
        evidence.check_lines = circuit_text.check_lines(visual.circuit)
        evidence.flags.append("circuit_assessed")
    if visual.images:
        for image in visual.images:
            fetched = None
            if fetcher is not None:
                try:
                    fetched = await fetcher(image.path)
                except Exception as exc:                        # noqa: BLE001 - a photo must never break the evaluation
                    log.warning("image fetch raised path=%s error=%s", image.path, exc)
            if fetched is None:
                evidence.missing += 1
            else:
                evidence.images.append(fetched)
        if evidence.images:
            evidence.flags.append("images_assessed")
        if evidence.missing:
            evidence.flags.append("images_not_assessed" if fetcher is None else "images_unavailable")
    return evidence
