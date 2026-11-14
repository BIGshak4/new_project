"""One page to read the checked question drafts on, before they are loaded (Shaked, 2026-11-14: "lets work on the
content").

    uv run python scripts/verify_drafts.py --skills ... --out workdir/drafts.json
    uv run python scripts/drafts_review_page.py --checked workdir/drafts.json --out workdir/drafts-review.html

Takes the result of verify_drafts.py and the drafts themselves and writes a plain HTML page: the drafts that passed
the loader's rules and whose reference the judge called STRONG, grouped by skill, each with its English and Hebrew
prompt, the reference solution, the hints and the rubric; the drafts that did not pass are listed at the end with the
reason. The page holds reference solutions: it is written under workdir/, which is not committed. Nothing is loaded.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engine.catalog import load_catalog  # noqa: E402
from scripts.generate_questions import OUTPUT, SEEDS  # noqa: E402

STYLE = """
:root { --ink:#1d2433; --soft:#5b6478; --line:#dfe3ec; --paper:#fbfbf8; --card:#fff; --mark:#fff3bf; --ok:#2b7a4b; --no:#b3402e; }
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 "Segoe UI", Arial, sans-serif; }
main { max-width: 900px; margin: 0 auto; padding: 24px 16px 80px; }
h1 { font-size: 28px; margin: 8px 0 4px; } h2 { font-size: 21px; margin: 40px 0 8px; border-bottom: 2px solid var(--line); padding-bottom: 6px; }
p.lead { color: var(--soft); margin: 0 0 16px; }
table { border-collapse: collapse; width: 100%; margin: 12px 0 8px; } th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--line); }
th { color: var(--soft); font-weight: 600; font-size: 14px; } td.n { text-align: right; font-variant-numeric: tabular-nums; }
article { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; margin: 14px 0; }
article h3 { margin: 0 0 2px; font-size: 18px; } .he { direction: rtl; text-align: right; }
.meta { color: var(--soft); font-size: 14px; margin-bottom: 10px; } .key { font-family: Consolas, monospace; font-size: 13px; }
.text { white-space: pre-wrap; overflow-wrap: anywhere; margin: 6px 0 10px; }
details { border-top: 1px solid var(--line); padding: 8px 0 2px; } summary { cursor: pointer; color: var(--soft); font-weight: 600; }
.pill { display: inline-block; background: var(--mark); border-radius: 999px; padding: 0 9px; font-size: 13px; margin-right: 6px; }
.no { color: var(--no); } nav a { margin-right: 14px; }
"""


def esc(value) -> str:
    return html.escape(str(value or ""))


def card(question: dict, labels: dict[str, str]) -> str:
    en, he = question["translations"]["en"], question["translations"]["he"]
    def words(item: dict) -> str:
        description = item.get("description")
        return description.get("en", "") if isinstance(description, dict) else (description or item.get("key", ""))
    rubric = "".join(f"<li>{esc(words(r))} <span class='meta'>({r.get('weight')})</span></li>"
                     for r in question.get("rubric", []))
    hints = "".join(f"<li>{esc(h)}</li>" for h in en.get("hints", []))
    check = (question.get("deterministic_check") or {}).get("type")
    return f"""<article id="{esc(question['key'])}">
<h3>{esc(en['title'])}</h3><h3 class="he">{esc(he['title'])}</h3>
<div class="meta"><span class="pill">difficulty {question['difficulty']}</span><span class="pill">{esc(question['format'])}</span>
<span class="pill">{question['estimated_minutes']} min</span>{f'<span class="pill">check: {esc(check)}</span>' if check else ''}
<span class="key">{esc(question['key'])}</span></div>
<div class="text">{esc(en['prompt'])}</div>
<details><summary>The question in Hebrew</summary><div class="text he">{esc(he['prompt'])}</div></details>
<details><summary>Reference solution</summary><div class="text">{esc(en['reference_solution'])}</div>
<div class="text he">{esc(he['reference_solution'])}</div></details>
<details><summary>What a complete answer contains, hints, rubric</summary><div class="text">{esc(en['requirements'])}</div>
<ol>{hints}</ol><ul>{rubric}</ul></details>
</article>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checked", type=Path, required=True, help="the JSON verify_drafts.py wrote")
    parser.add_argument("--drafts", type=Path, default=OUTPUT)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    labels = load_catalog(SEEDS).skill_labels()
    drafts = {q["key"]: q for q in json.loads(args.drafts.read_text(encoding="utf-8"))}
    rows = json.loads(args.checked.read_text(encoding="utf-8"))
    ready = [r for r in rows if not r["problems"] and r["band"] == "STRONG"]
    held = [r for r in rows if r not in ready]
    skills = list(dict.fromkeys(r["skill"] for r in rows))

    summary = "".join(
        f"<tr><td><a href='#skill-{s}'>{esc(labels.get(s, s))}</a></td>"
        f"<td class='n'>{sum(1 for r in ready if r['skill'] == s)}</td>"
        f"<td class='n'>{sum(1 for r in held if r['skill'] == s)}</td>"
        f"<td>{', '.join(str(d) for d in sorted({r['difficulty'] for r in ready if r['skill'] == s}))}</td></tr>" for s in skills)
    sections = []
    for s in skills:
        mine = sorted((r for r in ready if r["skill"] == s), key=lambda r: (r["difficulty"], r["key"]))
        sections.append(f"<h2 id='skill-{s}'>{esc(labels.get(s, s))} <span class='meta'>({len(mine)} ready)</span></h2>"
                        + "".join(card(drafts[r["key"]], labels) for r in mine))
    not_ready = "".join(
        f"<li><span class='key'>{esc(r['key'])}</span> (difficulty {r['difficulty']}, {esc(r['format'])}): "
        f"<span class='no'>{esc('; '.join(r['problems']) or 'the reference solution was graded ' + str(r['band']))}</span>"
        f"{' — ' + esc(r['summary']) if r.get('summary') and r['band'] != 'STRONG' else ''}</li>" for r in held)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Question drafts to review</title>
<style>{STYLE}</style></head><body><main>
<h1>Question drafts to review</h1>
<p class="lead">{len(ready)} drafts passed both checks (the loader's rules, and today's grader calling the draft's own
reference solution strong). {len(held)} did not and are listed at the end. Nothing here is in the question bank yet.</p>
<table><tr><th>Skill</th><th>Ready</th><th>Held back</th><th>Difficulties of the ready ones</th></tr>{summary}</table>
{''.join(sections)}
<h2 id="held">Held back ({len(held)})</h2><ul>{not_ready or '<li>none</li>'}</ul>
</main></body></html>"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    print(f"{len(ready)} ready, {len(held)} held back -> {args.out} ({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
