"""Execution facts, kept separate from the AI's assessment of an answer."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class ExecutionResult(BaseModel):
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
