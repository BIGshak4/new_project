"""Thirty sources; fourteen new tasks, five variants and preserved old identities."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_history import (
    BATCH1107N30_BASELINE,
    assert_pre_batch1107n30_archive,
    assert_pre_batch1107n30_assets,
    assert_pre_batch1107n30_localization,
    digest,
)
from tests.preparation_november7_night30_history import before_batch1107n30_compiled

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
NEW = {f'PREP-{n}' for n in range(289, 303)}
VARIANTS = {'PREP-001', 'PREP-036', 'PREP-122', 'PREP-194', 'PREP-225'}
SOURCE_ONLY = {'PREP-002', 'PREP-007', 'PREP-010', 'PREP-044', 'PREP-058', 'PREP-092', 'PREP-107', 'PREP-151', 'PREP-162', 'PREP-168'}
MAP = (162,289,290,122,291,36,292,92,293,10,107,294,7,295,296,1,194,168,225,44,297,298,299,58,2,300,301,162,302,151)


def read(path):
    return json.loads(path.read_bytes())


def test_all_thirty_originals_attribution_and_duplicate_decisions_are_preserved():
    manifest = read(BANK / 'intakes/2026-11-07-night30-sources.json')
    records = {q['id']: q for q in read(BANK / 'questions.json')['questions']}
    assert manifest['screenshot_count'] == manifest['question_source_count'] == 30
    assert manifest['new_question_count'] == 14
    assert manifest['technical_extension_count'] == 5
    assert manifest['provenance_only_count'] == 10
    assert len(set(MAP)) == manifest['affected_question_count'] == 29
    for source, number in zip(manifest['sources'], MAP, strict=True):
        ident = f'PREP-{number:03d}'
        assert source['question_ids'] == [ident]
        assert source['sha256'] == BATCH1107N30_BASELINE['batch1107n30_source_sha256'][str(source['screenshot'])]
        path = source['archive_paths'][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source['sha256']
        q = records[ident]
        assert any(s.get('path') == path for s in q['sources'])
        assert set(source['source_tags']) <= set(q['source_tags'])
        assert set(source['reported_companies']) <= set(q['reported_companies'])


def test_every_old_record_asset_localization_and_compiled_prefix_stays_hash_bound():
    archive = read(BANK / 'questions.json')
    assert len(archive['questions']) == archive['question_count'] == 301
    assert {q['id'] for q in archive['questions']} - BATCH1107N30_BASELINE['records'].keys() == NEW
    assert set(BATCH1107N30_BASELINE['variant_ids']) == VARIANTS
    assert set(BATCH1107N30_BASELINE['source_only_ids']) == SOURCE_ONLY
    assert_pre_batch1107n30_archive(archive)
    assets = read(SEEDS / 'preparation_uploads.json')['files']
    assert_pre_batch1107n30_assets(assets)
    localized = {}
    for path in (SEEDS / 'preparation_localization').glob('*.json'):
        values = read(path)
        assert not localized.keys() & values.keys()
        localized.update(values)
    assert localized.keys() == {q['id'] for q in archive['questions']}
    assert_pre_batch1107n30_localization(localized)
    for q in read(SEEDS / 'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1107N30_BASELINE['records']:
            before_batch1107n30_compiled(q)


def test_new_bilingual_tasks_and_variants_remain_proposed_and_media_gated():
    catalog = load_catalog(SEEDS)
    assert len(catalog.questions) == 331
    selected = {q.assets.get('preparation_id'): q for q in catalog.questions.values()
                if q.assets.get('preparation_id') in NEW | VARIANTS}
    assert set(selected) == NEW | VARIANTS
    for ident, q in selected.items():
        assert q.status == 'trial' and not q.assets['assessment_ready']
        assert solution_review(q).status == 'pending_review'
        for language in ('he', 'en'):
            text = q.text(language)
            assert text.prompt and text.reference_solution and len(set(text.hints)) == 3
            assert all(not m['source_path'].startswith('sources/')
                       for m in learner_media(q.assets['bank_media'], language))
        for key, pair in q.assets['preparation_resource']['learner_material'].items():
            assert set(pair) == {'he', 'en'} and pair['he'] and pair['en'], (ident, key)
            assert not any('\u05d0' <= c <= '\u05ea' for c in json.dumps(pair['en'], ensure_ascii=False)), (ident, key)



def test_two_permutation_sources_share_one_existing_identity_without_revision():
    sources = read(BANK / 'intakes/2026-11-07-night30-sources.json')['sources']
    assert sources[0]['question_ids'] == sources[27]['question_ids'] == ['PREP-162']
    assert sources[0]['decision'] == sources[27]['decision'] == 'additional_source_existing_question'
    current = next(q for q in read(BANK / 'questions.json')['questions'] if q['id'] == 'PREP-162')
    baseline = BATCH1107N30_BASELINE['records']['PREP-162']['projection']
    assert current['version'] == baseline['version']


def test_native_evidence_remains_bound_to_the_compiled_sources():
    proof = read(BANK / 'checks/night1107n30-native-verification.json')
    assert proof['result'] == 'passed' and proof['command_exit_code'] == 0
    assert proof['rtl_check_total'] == 21810
    assert proof['cpp_parser']['native_boundary_cases'] == 25
    assert proof['environment']['test_network_policy'] == 'deny-all'
    assert proof['environment']['persistent'] is False
    assert proof['environment']['session_stopped'] is True
    for path, expected in proof['source_sha256'].items():
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == expected, path


def test_existing_fundamentals_quiz_and_human_attestations_are_not_rewritten():
    baseline = BATCH1107N30_BASELINE
    for name, expected in baseline['short_card_source_sha256'].items():
        assert digest(read(ROOT / 'apps/web/src/content' / name)) == expected
    for name, key in [('fundamentals_catalog.json', 'fundamentals_catalog_sha256'),
                      ('duel_quiz.json', 'quiz_bank_sha256'),
                      ('solution_review_attestations.json', 'review_registry_canonical_sha256')]:
        assert digest(read(SEEDS / name)) == baseline[key]


@pytest.mark.parametrize('mutation', ['title','hint','prompt','version','media','digest','asset_ordinal'])
def test_frozen_projection_rejects_old_content_or_asset_mutation(mutation):
    q = copy.deepcopy(next(q for q in read(SEEDS / 'questions/preparation_bank.json')
                           if q['assets']['preparation_id'] == 'PREP-001'))
    if mutation == 'title':
        q['translations']['en']['title'] = 'changed'
    elif mutation == 'hint':
        q['translations']['en']['hints'][0] = 'changed'
    elif mutation == 'prompt':
        q['translations']['en']['prompt'] = 'changed'
    elif mutation == 'version':
        q['version'] += 1
    elif mutation == 'media':
        frozen_path = next(
            m['path'] for m in q['assets']['bank_media'] if '1107n30' not in m['source_path']
            and not m['source_path'].startswith('sources/2026-11-07-night30-'))
        next(m for m in q['assets']['bank_media'] if m['path'] == frozen_path)['caption'] = 'changed'
    elif mutation == 'asset_ordinal':
        q['assets']['bank_media'][0]['id'] = 'asset-999'
    else:
        q['assets']['source_sha256'] = '0' * 64
    with pytest.raises(AssertionError):
        before_batch1107n30_compiled(q)
