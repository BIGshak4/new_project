"""The two companion drawings stay with their questions across the archive and study UI."""

import hashlib
import json
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_november18_history import before_nov18


ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
GROUPS = {6: (7,), 16: (17,)}
MAP = {
    1: 374, 2: 140, 3: 22, 4: 371, 5: 332, 6: 366, 8: 15, 9: 1, 10: 119, 11: 309,
    12: 137, 13: 375, 14: 376, 15: 368, 16: 369, 18: 372, 19: 106, 20: 176,
    21: 373, 22: 123, 23: 238, 24: 367, 25: 153, 26: 92, 27: 72, 28: 41, 29: 232,
    30: 370, 31: 64,
}
NEW = {f'PREP-{n}' for n in range(366, 377)}
EXTENDED = {f'PREP-{n:03}' for n in (140, 332, 15, 137, 176, 123, 92, 72)}


def read(path):
    return json.loads(path.read_bytes())


def test_every_original_and_companion_belongs_to_its_expected_question():
    manifest = read(BANK / 'intakes/2026-11-18-batch31-sources.json')
    assert manifest['screenshot_count'] == 31
    assert len(manifest['sources']) == manifest['source_count'] == 29
    assert (manifest['new_question_count'], manifest['technical_extension_count'],
            manifest['provenance_only_count'], manifest['affected_question_count']) == (11, 8, 10, 29)
    archive = {q['id']: q for q in read(BANK / 'questions.json')['questions']}
    assert {row['screenshot'] for row in manifest['sources']} == MAP.keys()
    for row in manifest['sources']:
        primary = row['screenshot']
        companions = GROUPS.get(primary, ())
        assert row['companion_screenshots'] == list(companions)
        ident = f'PREP-{MAP[primary]:03}'
        assert row['question_ids'] == [ident]
        paths = [f'sources/2026-11-18-batch31-{n:02}.png' for n in (primary, *companions)]
        assert row['archive_paths'] == paths
        sources = {s['path']: s['role'] for s in archive[ident]['sources'] if 'path' in s and 'role' in s}
        for index, path in enumerate(paths):
            assert sources[path] == ('original_question_companion_diagram' if index else 'original_question_screenshot')
            assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == row['archive_sha256'][path]


def test_new_material_and_revisions_keep_private_originals_and_public_given_figures():
    catalog = load_catalog(SEEDS)
    compiled = {q['key']: q for q in read(SEEDS / 'questions/preparation_bank.json')}
    ratings = read(SEEDS / 'question_difficulty.json')
    selected = {q.assets.get('preparation_id'): q for q in catalog.questions.values()
                if q.assets.get('preparation_id') in NEW | EXTENDED}
    assert selected.keys() == NEW | EXTENDED
    for ident, q in selected.items():
        row = compiled[q.key]
        if ident in EXTENDED:
            earlier = before_nov18('compiled:' + q.key, row)
            assert q.version == earlier['version'] + 1
            for lang in ('he', 'en'):
                for field in ('prompt', 'reference_solution'):
                    assert row['translations'][lang][field].startswith(earlier['translations'][lang][field])
        else:
            assert q.version == 1
        assert q.status == 'trial' and not q.assets['assessment_ready']
        assert solution_review(q).status == 'pending_review'
        assert q.difficulty == ratings[q.key]['difficulty']
        assert difficulty_fingerprint(row) == ratings[q.key]['content_sha256']
        for lang in ('he', 'en'):
            assert len(set(q.text(lang).hints)) == 3
            media = learner_media(q.assets['bank_media'], lang)
            assert all(not m['source_path'].startswith('sources/') for m in media)
            if ident in {'PREP-366', 'PREP-369'}:
                assert any(m['kind'] == 'image' and m['role'] == 'prompt' and m['language'] == lang for m in media)
