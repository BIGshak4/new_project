"""Assemble source-linked quiz shards without changing existing pilot approvals.

Run all four authors first, then this file. --check verifies generated artifacts
without writing. Unlinked legacy quiz entries and the original 50 pilot entries
are preserved verbatim.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED = ROOT / "backend/seeds/duel_quiz.json"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"
NAMES = ["hardware_basic", "hardware_advanced", "reasoning", "code",
         "hardware_400", "reasoning_400", "code_400"]
SOURCE_FILES = [
    "fundamentals-hardware.json",
    "fundamentals-code-logic.json",
    "fundamentals-hardware-expansion.json",
    "fundamentals-reasoning-expansion.json",
    "fundamentals-code-expansion.json",
    "fundamentals-hardware-250.json",
    "fundamentals-reasoning-250.json",
    "fundamentals-code-250.json",
    "fundamentals-hardware-400.json",
    "fundamentals-reasoning-400.json",
    "fundamentals-code-400.json",
]
PILOT_SOURCES = {
    "quick-hw-03",
    "quick-hw-05",
    "quick-hw-09",
    "quick-hw-10",
    "quick-hw-15",
    "quick-hw-21",
    "quick-hw-40",
    "quick-sw-02",
    "quick-sw-03",
    "quick-sw-61",
}
PRESERVED_SHA256 = "bf1c0ffaee75881d6f0d7be672d60d76fee30934a49b28a6b7b1d61224d7b206"


def content_digest(question):
    content = {k: v for k, v in question.items() if k not in {"status", "release_approval"}}
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def apply_release(questions, manifest):
    """Explicit pilot authorization is tied to the exact authored content.

    The live game renders plain text; remove inline Markdown delimiters without
    changing any code, formula, bracket example or explanation they enclose.
    """
    entries = {entry["key"]: entry for entry in manifest["questions"]}
    authorized = {key: entry["authored_sha256"] for key, entry in entries.items()}
    assert len(authorized) == len(manifest["questions"])
    assert set(authorized) <= {q["key"] for q in questions}
    out = []
    for original in questions:
        q = copy.deepcopy(original)
        if q["key"] in authorized:
            assert content_digest(q) == authorized[q["key"]], f"Release content changed: {q['key']}"
            for values in [q["prompt"], q["explanation"], *q["choices"]]:
                for lang, value in values.items():
                    assert "```" not in value, "Block code requires a dedicated game renderer"
                    values[lang] = re.sub(r"`([^`]*)`", r"\1", value)
            q["status"] = "approved"
            q["release_approval"] = {
                "basis": manifest["basis"],
                "on": entries[q["key"]].get("on", manifest["on"]),
                "professional_review": "pending",
                "authored_sha256": authorized[q["key"]],
                "content_sha256": content_digest(q),
            }
        out.append(q)
    return out


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_cards():
    cards = {}
    for name in SOURCE_FILES:
        for q in read(ROOT / "apps/web/src/content" / name):
            assert q["id"] not in cards, q["id"]
            cards[q["id"]] = q
    assert len(cards) == 400
    return cards


def strip_code(text):
    return re.sub(r"```[\s\S]*?```|`[^`]*`", "", text)


def text_issues(text, lang, field):
    errors = []
    if not text or text != text.strip():
        errors.append("empty or outer whitespace")
    if any(c in text for c in ("\ufffd", "\ufeff", "\x00")):
        errors.append("invalid/replacement character")
    if re.search(r"\?\?|\b(?:TODO|FIXME|TBD)\b", text):
        errors.append("placeholder or repeated question marks")
    if lang == "en" and re.search(r"[\u0590-\u05ff]", text):
        errors.append("Hebrew in English field")
    if field != "choice" and lang == "he" and not re.search(r"[\u05d0-\u05ea]", text):
        errors.append("missing Hebrew prose")
    prose = strip_code(text)
    if re.search(r"\b([a-zA-Z\u05d0-\u05ea]{2,})\s+\1\b", prose, re.IGNORECASE):
        errors.append("repeated adjacent word")
    stack = []
    for c in prose:
        if c in "([{":
            stack.append(c)
        elif c in ")]}" and (not stack or stack.pop() != {")": "(", "]": "[", "}": "{"}[c]):
            errors.append("unbalanced prose brackets (quote intentional code with backticks)")
            break
    else:
        if stack:
            errors.append("unclosed prose brackets (quote intentional code with backticks)")
    if text.count("```") % 2 or strip_code(text).count("`") % 2:
        errors.append("unbalanced Markdown code delimiters")
    return errors


def validate(questions):
    cards = source_cards()
    groups, issues, numeric_warnings = defaultdict(list), [], []
    keys = set()
    for q in questions:
        key = q["key"]
        assert key not in keys, key
        keys.add(key)
        if not q.get("source_key"):
            continue
        source = q["source_key"]
        assert source in cards, key
        assert type(q["variant"]) is int and q["variant"] in range(1, 6), key
        assert key == f"{source}-v{q['variant']}", key
        assert q["topic"] == cards[source]["topic"], key
        assert len(q["choices"]) == 4 and type(q["correct"]) is int and 0 <= q["correct"] < 4, key
        assert q["status"] in {"draft", "approved"}, key
        if source not in PILOT_SOURCES:
            assert q["status"] == "draft", f"{key}: new AI content cannot inherit pilot approval"
        groups[source].append(q)
        for field, values in [("prompt", q["prompt"]), ("explanation", q["explanation"])] + [
            ("choice", c) for c in q["choices"]
        ]:
            assert set(values) == {"he", "en"}, (key, field)
            for lang, text in values.items():
                for issue in text_issues(text, lang, field):
                    issues.append(dict(key=key, field=field, language=lang, issue=issue))
            # These are flags for bilingual review: a language may spell a number
            # out instead of using digits, so differences are not automatic errors.
            numbers = [Counter(re.findall(r"(?<!\w)-?\d+(?:\.\d+)?", values[lang])) for lang in ("he", "en")]
            if numbers[0] != numbers[1]:
                numeric_warnings.append(dict(key=key, field=field, he=dict(numbers[0]), en=dict(numbers[1])))
        for lang in ("he", "en"):
            assert len({c[lang].strip().casefold() for c in q["choices"]}) == 4, (key, lang)
    assert set(groups) == set(cards), f"Missing sources: {set(cards) - set(groups)}"
    for source, rows in groups.items():
        assert sorted(q["variant"] for q in rows) == [1, 2, 3, 4, 5], source
        for lang in ("he", "en"):
            assert len({q["prompt"][lang] for q in rows}) == 5, (source, lang, "duplicate prompts")
    assert len(groups) == 400 and sum(map(len, groups.values())) == 2000
    return issues, numeric_warnings


def collect():
    existing = read(SEED)
    # Preserve all 40 standalone legacy drafts and all existing pilot entries.
    preserved = [
        q for q in existing["questions"] if not q.get("source_key") or q["source_key"] in PILOT_SOURCES
    ]
    assert len(preserved) == 90
    digest = hashlib.sha256(json.dumps(preserved, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert digest == PRESERVED_SHA256, (
        "Existing pilot/legacy content changed; reconcile explicitly before rebuilding"
    )
    generated, checks = [], []
    for name in NAMES:
        rows = read(SHARDS / f"{name}.json")
        evidence = read(SHARDS / f"{name}.checks.json")
        assert {q["key"] for q in rows} == {c["key"] for c in evidence}, name
        assert len(rows) == len(evidence), name
        assert not any(q["source_key"] in PILOT_SOURCES for q in rows), name
        generated.extend(rows)
        checks.extend(evidence)
    authored = preserved + sorted(generated, key=lambda q: (q["source_key"], q["variant"]))
    assert len(generated) == 1950
    issues, numbers = validate(authored)
    manifest_path = SHARDS / "release-manifest.json"
    released = apply_release(generated, read(manifest_path)) if manifest_path.exists() else generated
    by_key = {q["key"]: q for q in released}
    for old in existing["questions"]:
        if old.get("source_key") not in PILOT_SOURCES and old["status"] == "approved":
            assert by_key.get(old["key"]) == old, (
                "Do not overwrite later approvals or edited released content"
            )
    existing["questions"] = preserved + sorted(released, key=lambda q: (q["source_key"], q["variant"]))
    existing["_about"] = (
        "Quiz-duel content: 400 short-question sources with five authored bilingual variants each (2000), "
        "plus 40 preserved standalone legacy drafts. The existing 50 pilot-approved variants retain their "
        "original release_approval metadata. New variant publication follows the content-bound release manifest; "
        "pilot publication is authorized by Harel and does not assert human professional review. "
        "Every question has four choices, one correct index (0-3), and an explanation in Hebrew and English. "
        "Production serves approved sources only; both players receive the same five distinct sources and variants. "
        "Authoring and validation evidence: scripts/quiz_authoring and seeds/duel_quiz_batches. "
        "Machine and AI checks do not establish human professional review or calibrated difficulty."
    )
    return existing, checks, issues, numbers


def review_html(questions):
    """Plain local editorial proof, with both languages side by side."""
    cards = source_cards()
    sections = []
    for source in sorted(cards):
        rows = [q for q in questions if q.get("source_key") == source]
        blocks = []
        for q in rows:
            languages = []
            for lang in ("he", "en"):
                choices = "".join(
                    f'<li class="{"correct" if i == q["correct"] else ""}">{html.escape(c[lang])}</li>'
                    for i, c in enumerate(q["choices"])
                )
                languages.append(
                    f'<article lang="{lang}" dir="{"rtl" if lang == "he" else "ltr"}"><pre>{html.escape(q["prompt"][lang])}</pre><ol>{choices}</ol><pre>{html.escape(q["explanation"][lang])}</pre></article>'
                )
            blocks.append(
                f'<h3>{html.escape(q["key"])} · {html.escape(q["status"])}</h3><div class="pair">{"".join(languages)}</div>'
            )
        title = html.escape(cards[source]["title"]["he"])
        original = html.escape(cards[source]["prompt"]["he"])
        sections.append(
            f'<details><summary>{source} — {title} · 5</summary><p dir="rtl">מקור: {original}</p>{"".join(blocks)}</details>'
        )
    return (
        """<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><title>בדיקת מאגר החידון</title>
<style>body{font:16px/1.65 system-ui;margin:2rem auto;max-width:1300px;padding:0 1rem;background:#f5f5f2;color:#202420}h1{font-size:1.8rem}input{font:inherit;padding:.6rem;width:90%;margin-bottom:1rem}details{background:white;border:1px solid #d4d8d2;margin:.6rem 0;padding:1rem}summary{cursor:pointer;font-weight:650}.pair{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;border-bottom:1px solid #ddd}article{min-width:0;padding:.5rem}.correct{background:#e0f2df;font-weight:650}pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere}h3{direction:ltr;text-align:left;font-size:1rem}@media(max-width:760px){.pair{grid-template-columns:1fr}}</style>
<h1>מאגר החידון: 400 מקורות · 2,000 גרסאות · עברית ואנגלית</h1><p>האפשרות הנכונה מסומנת בירוק. פרסום בפיילוט אושר על ידי הראל; בדיקת AI וחישובים אינם אישור מומחה אנושי. זהו קובץ בדיקה מקומי המכיל תשובות, ולא מסך למשחק פעיל.</p><input id="filter" aria-label="סינון לפי מזהה או תוכן" placeholder="חיפוש לפי מזהה, נושא או טקסט…">"""
        + "".join(sections)
        + """<script>document.querySelector('#filter').addEventListener('input',e=>{const s=e.target.value.toLowerCase();for(const d of document.querySelectorAll('details'))d.hidden=!d.textContent.toLowerCase().includes(s)});</script></html>"""
    )


def reviewed_number_flags(questions, flags):
    """Content-bound review notes; edits invalidate the earlier equivalence check."""
    reviews = {(r["key"], r["field"]): r for r in read(SHARDS / "numeric-language-review.json")}
    by_key = {q["key"]: q for q in questions}
    # The equivalence review concerns authored wording; the release renderer
    # removes only Markdown delimiters and leaves all numerical data unchanged.
    for name in NAMES:
        by_key.update({q["key"]: q for q in read(SHARDS / f"{name}.json")})
    reviewed = []
    for flag in flags:
        item = reviews.get((flag["key"], flag["field"]))
        value = by_key[flag["key"]][flag["field"]]
        fingerprint = hashlib.sha256(
            json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        assert item and item["text_sha256"] == fingerprint, f"Bilingual numeric flag needs review: {flag}"
        reviewed.append({**flag, "disposition": item["reason"], "review": item["review"]})
    return reviewed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    seed, checks, issues, numbers = collect()
    reviewed = reviewed_number_flags(seed["questions"], numbers)
    report = dict(
        source_count=400,
        linked_variants=2000,
        new_variants=1950,
        expansion_variants=750,
        preserved_legacy=40,
        text_errors=issues,
        number_review_flags=reviewed,
        unresolved_number_flags=0,
        checks_count=len(checks),
        human_review="pending for new variants",
        approved_variants=sum(q["status"] == "approved" for q in seed["questions"]),
        release_authorization="Harel requested the original live publication on 2026-10-29 and expansion under the protocols on 2026-10-30",
        source_sha256={
            name: hashlib.sha256((ROOT / "apps/web/src/content" / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES
        },
    )
    if args.check:
        assert read(SEED) == seed, "Seed differs from authored shards"
    else:
        # Report findings even if assembly is stopped by text errors.
        (SHARDS / "validation-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        assert not issues, f"{len(issues)} text errors; see validation-report.json"
        SEED.write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "docs/game-question-bank-review.html").write_text(
            review_html(seed["questions"]), encoding="utf-8"
        )
    assert not issues, issues[:20]
    print(
        f"400 sources / 2000 linked variants; 750 expansion variants; 40 legacy preserved; {len(reviewed)} numeric-language flags reviewed; zero text errors."
    )


if __name__ == "__main__":
    main()
