"""Twenty sources; thirteen new tasks, two variants and preserved old identities."""
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
    BATCH1107B20_BASELINE,
    assert_pre_batch1107b20_archive,
    assert_pre_batch1107b20_assets,
    assert_pre_batch1107b20_localization,
    before_batch1107n30_archive,
    digest,
)
from tests.preparation_november7_batch20_history import before_batch1107b20_compiled

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
NEW = {f'PREP-{n}' for n in range(276, 289)}
VARIANTS = {'PREP-090', 'PREP-151'}
SOURCE_ONLY = {'PREP-022', 'PREP-140', 'PREP-176', 'PREP-204'}
MAP = (276,277,278,279,204,280,22,281,282,176,283,140,284,285,286,287,151,288,151,90)


def read(path):
    return json.loads(path.read_bytes())


def test_all_twenty_originals_attribution_and_duplicate_decisions_are_preserved():
    manifest = read(BANK / 'intakes/2026-11-07-batch20-sources.json')
    records = {q['id']: q for q in read(BANK / 'questions.json')['questions']}
    assert manifest['screenshot_count'] == manifest['question_source_count'] == 20
    assert manifest['new_question_count'] == 13
    assert manifest['technical_extension_count'] == 2
    assert manifest['provenance_only_count'] == 4
    assert len(set(MAP)) == manifest['affected_question_count'] == 19
    for source, number in zip(manifest['sources'], MAP, strict=True):
        ident = f'PREP-{number:03d}'
        assert source['question_ids'] == [ident]
        assert source['sha256'] == BATCH1107B20_BASELINE['batch1107b20_source_sha256'][str(source['screenshot'])]
        path = source['archive_paths'][0]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == source['sha256']
        q = records[ident]
        assert any(s.get('path') == path for s in q['sources'])
        assert set(source['source_tags']) <= set(q['source_tags'])
        assert set(source['reported_companies']) <= set(q['reported_companies'])


def test_every_old_record_asset_localization_and_compiled_prefix_stays_hash_bound():
    current_archive = read(BANK / 'questions.json')
    archive = before_batch1107n30_archive(current_archive)
    assert len(archive['questions']) == archive['question_count'] == 287
    assert {q['id'] for q in archive['questions']} - BATCH1107B20_BASELINE['records'].keys() == NEW
    assert set(BATCH1107B20_BASELINE['variant_ids']) == VARIANTS
    assert set(BATCH1107B20_BASELINE['source_only_ids']) == SOURCE_ONLY
    assert_pre_batch1107b20_archive(current_archive)
    assets = read(SEEDS / 'preparation_uploads.json')['files']
    assert_pre_batch1107b20_assets(assets)
    localized = {}
    for path in (SEEDS / 'preparation_localization').glob('*.json'):
        values = read(path)
        assert not localized.keys() & values.keys()
        localized.update(values)
    assert localized.keys() == {q['id'] for q in current_archive['questions']}
    assert_pre_batch1107b20_localization(localized)
    for q in read(SEEDS / 'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1107B20_BASELINE['records']:
            before_batch1107b20_compiled(q)


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


def test_two_popcount_sources_share_one_canonical_question_and_source_typo_is_preserved():
    sources = read(BANK / 'intakes/2026-11-07-batch20-sources.json')['sources']
    assert sources[16]['question_ids'] == sources[18]['question_ids'] == ['PREP-151']
    assert '3=101' in sources[18]['original_prompt'].replace(' ', '')
    current = next(q for q in read(BANK / 'questions.json')['questions'] if q['id'] == 'PREP-151')
    prior = BATCH1107B20_BASELINE['records']['PREP-151']['projection']
    assert current['version'] == prior['version'] + 1
    for lang in ('he', 'en'):
        length = prior['append_shapes']['translations']['items'][lang]['items']['prompt']['length']
        assert len(current['translations'][lang]['prompt']) > length


def test_existing_fundamentals_quiz_and_human_attestations_are_not_rewritten():
    baseline = BATCH1107B20_BASELINE
    for name, expected in baseline['short_card_source_sha256'].items():
        assert digest(read(ROOT / 'apps/web/src/content' / name)) == expected
    for name, key in [('fundamentals_catalog.json', 'fundamentals_catalog_sha256'),
                      ('duel_quiz.json', 'quiz_bank_sha256'),
                      ('solution_review_attestations.json', 'review_registry_canonical_sha256')]:
        assert digest(read(SEEDS / name)) == baseline[key]


@pytest.mark.parametrize('mutation', ['title','hint','prompt','version','media','digest','asset_ordinal'])
def test_frozen_projection_rejects_old_content_or_asset_mutation(mutation):
    q = copy.deepcopy(next(q for q in read(SEEDS / 'questions/preparation_bank.json')
                           if q['assets']['preparation_id'] == 'PREP-090'))
    if mutation == 'title':
        q['translations']['en']['title'] = 'changed'
    elif mutation == 'hint':
        q['translations']['en']['hints'][0] = 'changed'
    elif mutation == 'prompt':
        q['translations']['en']['prompt'] = 'changed'
    elif mutation == 'version':
        q['version'] += 1
    elif mutation == 'media':
        q['assets']['bank_media'][0]['caption'] = 'changed'
    elif mutation == 'asset_ordinal':
        q['assets']['bank_media'][0]['id'] = 'asset-999'
    else:
        q['assets']['source_sha256'] = '0' * 64
    with pytest.raises(AssertionError):
        before_batch1107b20_compiled(q)
