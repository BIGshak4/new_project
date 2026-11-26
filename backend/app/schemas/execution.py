"""Execution facts, kept separate from the AI's assessment of an answer."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ExecutionLanguage = Literal["python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl"]


class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: ExecutionLanguage
    source: str = Field(min_length=1, max_length=20000)
    stdin: str = Field(default="", max_length=8000)
    idempotency_key: str = Field(min_length=1, max_length=128)


class ExecutionCase(BaseModel):
    index: int
    passed: bool
    input: object = None
    expected: object = None
    actual: object = None


def without_nul(value):
    """The same value with every NUL character replaced by U+FFFD, at any depth. Postgres stores a NUL in no text and
    no JSON: a program that printed one (a C loop one past the string) made Run answer 500, lost the output and kept
    one of the user's two run slots for two minutes (bug hunt, 2026-11-26)."""
    if isinstance(value, str):
        return value.replace("\x00", "\ufffd") if "\x00" in value else value
    if isinstance(value, dict):
        return {key: without_nul(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [without_nul(item) for item in value]
    return value


class ExecutionResult(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def _storable(cls, data):
        return without_nul(data) if isinstance(data, dict) else data

    status: Literal["passed", "failed", "compile_error", "runtime_error", "timeout", "completed", "compile_only", "unavailable"]
    language: ExecutionLanguage
    compiled: bool | None = None
    executed: bool = False
    passed: bool | None = None
    stdout: str = ""
    stderr: str = ""
    compile_output: str = ""
    cases: list[ExecutionCase] = Field(default_factory=list, max_length=64)
    test_count: int = Field(default=0, ge=0)
    passed_count: int = Field(default=0, ge=0)
    runtime_ms: int = Field(default=0, ge=0)
    detail: str = ""


class ExecutionCapabilities(BaseModel):
    available: bool
    languages: list[str]
    tested_languages: list[str]
    contract: dict[str, str] | None = None
    starters: dict[str, str] = Field(default_factory=dict)
    reason: str | None = None
