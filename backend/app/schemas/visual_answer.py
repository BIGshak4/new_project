"""Bounded, versioned visual answer documents. Storage locators, never URLs or base64."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class CircuitPart(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    kind: Literal["input", "output", "constant", "clock", "and", "nand", "or", "nor", "xor", "xnor", "not", "buffer", "mux", "demux", "encoder", "decoder", "half-adder", "full-adder", "adder", "comparator", "dff", "register", "counter", "splitter", "joiner"]
    label: str = Field(max_length=40)
    x: float = Field(ge=-20000, le=20000)
    y: float = Field(ge=-20000, le=20000)
    count: int = Field(ge=2, le=16)
    bits: int = Field(ge=1, le=16)
    value: int = Field(ge=0, le=65535)

    @model_validator(mode="after")
    def arity(self):
        if self.kind in {"mux", "demux", "encoder", "decoder"} and self.count not in {2, 4, 8, 16}:
            raise ValueError("selector component count must be a power of two")
        return self


class CircuitWire(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    source: str = Field(min_length=1, max_length=64)
    sourcePort: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9]+$")
    target: str = Field(min_length=1, max_length=64)
    targetPort: str = Field(min_length=1, max_length=12, pattern=r"^[A-Za-z0-9]+$")


class Circuit(StrictModel):
    version: Literal[1]
    parts: list[CircuitPart] = Field(max_length=100)
    wires: list[CircuitWire] = Field(max_length=200)

    @model_validator(mode="after")
    def graph(self):
        ids = {p.id for p in self.parts}
        if len(ids) != len(self.parts) or len({w.id for w in self.wires}) != len(self.wires):
            raise ValueError("duplicate circuit IDs")
        targets = set()
        for w in self.wires:
            if w.source not in ids or w.target not in ids:
                raise ValueError("wire references a missing component")
            target = (w.target, w.targetPort)
            if target in targets:
                raise ValueError("an input cannot have multiple drivers")
            targets.add(target)
        return self


class AnswerImage(StrictModel):
    path: str = Field(max_length=180, pattern=r"^[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}\.(jpg|png|webp)$")
    name: str = Field(min_length=1, max_length=160)
    mime: Literal["image/jpeg", "image/png", "image/webp"]
    size: int = Field(ge=1, le=5 * 1024 * 1024)


class VisualAnswer(StrictModel):
    circuit: Circuit | None = None
    images: list[AnswerImage] = Field(default_factory=list, max_length=4)

    @model_validator(mode="after")
    def unique_images(self):
        if len({i.path for i in self.images}) != len(self.images):
            raise ValueError("duplicate image")
        return self

    @property
    def has_content(self) -> bool:
        return bool(self.images or (self.circuit and self.circuit.parts))
