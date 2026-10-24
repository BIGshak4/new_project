"""Compile revision manifests from the actual authored short-card JSON files.

The Render Docker image contains backend/ only. Its small key/hash registry is
therefore generated from the web sources and copied with the ordinary seeds.
The frontend receives the exact same hashes; no learner progress is stored here.
Run --check in CI/tests to reject a stale manifest after content changes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
SOURCES = tuple(CONTENT / name for name in (
    "fundamentals-hardware.json", "fundamentals-code-logic.json",
    "fundamentals-hardware-expansion.json", "fundamentals-reasoning-expansion.json",
    "fundamentals-code-expansion.json",
    "fundamentals-hardware-250.json", "fundamentals-reasoning-250.json",
    "fundamentals-code-250.json",
))
BACKEND_OUTPUT = ROOT / "backend/seeds/fundamentals_catalog.json"
WEB_OUTPUT = CONTENT / "fundamentals-revisions.json"


def revision_for(card: dict) -> str:
    payload = {key: value for key, value in card.items() if key != "revision"}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build(sources: tuple[Path, ...] = SOURCES) -> dict[str, str]:
    revisions = {}
    for path in sources:
        cards = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(cards, list):
            raise ValueError(f"Expected a list of cards: {path.name}")
        for card in cards:
            key = card.get("id")
            if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", key) or key in revisions:
                raise ValueError(f"Invalid or duplicate fundamentals card id: {key!r}")
            revisions[key] = revision_for(card)
    if not revisions:
        raise ValueError("The authored fundamentals catalog is empty")
    return dict(sorted(revisions.items()))


def outputs() -> dict[Path, str]:
    revisions = build()
    return {
        BACKEND_OUTPUT: json.dumps({"schema_version": 1, "questions": revisions}, indent=2, ensure_ascii=False) + "\n",
        WEB_OUTPUT: json.dumps(revisions, indent=2, ensure_ascii=False) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = outputs()
    stale = [path for path, text in rendered.items()
             if not path.is_file() or path.read_text(encoding="utf-8") != text]
    if args.check:
        if stale:
            print("Stale fundamentals manifests: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
            return 1
        print("Fundamentals backend and frontend revision manifests are current.")
        return 0
    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8")
    print(f"Built matching backend and frontend manifests for {len(build())} authored short cards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
