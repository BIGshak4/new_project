"""Source integrity, history and learner boundaries for the twenty-source intake."""
import hashlib
import json
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services import question_resources
from tests.preparation_history import (
    BATCH22_BASELINE,
    BATCH1101_BASELINE,
    assert_pre_batch22_archive,
    assert_pre_batch22_assets,
    assert_pre_batch22_localization,
    digest,
)
from tests.preparation_november_compiled_history import before_batch1101_compiled

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
NEW = {f'PREP-{n}' for n in range(221, 233)}
VARIANTS = {'PREP-015','PREP-017','PREP-025','PREP-094','PREP-151','PREP-160'}
SOURCES = {'PREP-009','PREP-150'}
MAP = (25,221,222,223,9,224,94,225,15,17,226,151,227,228,229,230,160,231,150,232)


def read(path):
    return json.loads(path.read_bytes())


def test_sources_have_exact_bytes_tags_and_twenty_stable_targets():
    intake = read(BANK/'intakes/2026-10-31-batch22-sources.json')
    archive = {q['id']:q for q in read(BANK/'questions.json')['questions']}
    assert len(intake['sources']) == len(set(MAP)) == 20
    for source, number in zip(intake['sources'], MAP, strict=True):
        ident = f'PREP-{number:03d}'
        assert source['question_ids'] == [ident]
        assert source['sha256'] == BATCH22_BASELINE['batch22_source_sha256'][str(source['screenshot'])]
        path = source['archive_paths'][0]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest() == source['sha256']
        q = archive[ident]
        assert any(s.get('path') == path for s in q['sources'])
        assert set(source['source_tags']) <= set(q['source_tags'])
        assert set(source['reported_companies']) <= set(q['reported_companies'])
        assert source['original_prompt'].strip()


def test_all_219_old_records_and_localizations_keep_frozen_prefixes():
    archive = read(BANK/'questions.json')
    assert len(archive['questions']) == archive['question_count'] == 243
    historical_ids = {q['id'] for q in archive['questions']} & BATCH1101_BASELINE['records'].keys()
    assert historical_ids - BATCH22_BASELINE['records'].keys() == NEW
    assert set(BATCH22_BASELINE['variant_ids']) == VARIANTS
    assert set(BATCH22_BASELINE['source_only_ids']) == SOURCES
    assert_pre_batch22_archive(archive)
    assert_pre_batch22_assets(read(SEEDS/'preparation_uploads.json')['files'])
    localized = {}
    for path in (SEEDS/'preparation_localization').glob('*.json'):
        item = read(path)
        assert not item.keys() & localized.keys()
        localized.update(item)
    assert localized.keys() == {q['id'] for q in archive['questions']}
    assert_pre_batch22_localization(localized)
    for q in read(SEEDS/'questions/preparation_bank.json'):
        ident=q['assets']['preparation_id']
        if ident not in BATCH1101_BASELINE['records']:
            continue
        q = before_batch1101_compiled(q)
        if ident in BATCH22_BASELINE['records'] and ident not in VARIANTS|SOURCES:
            assert digest(q) == BATCH22_BASELINE['compiled_sha256'][q['key']]
        if ident in VARIANTS:
            for language in ('he','en'):
                for field,prefix in BATCH22_BASELINE['compiled_variant_prefixes'][ident][language].items():
                    assert digest(q['translations'][language][field][:prefix['length']]) == prefix['sha256']


def test_new_and_expanded_content_is_bilingual_proposed_and_private():
    catalog = load_catalog(SEEDS)
    assert len(catalog.questions) == 273
    selected={q.assets.get('preparation_id'):q for q in catalog.questions.values()
              if q.assets.get('preparation_id') in NEW|VARIANTS|SOURCES}
    assert set(selected) == NEW|VARIANTS|SOURCES
    for ident,q in selected.items():
        material=q.assets['preparation_resource']['learner_material']
        for key,pair in material.items():
            assert set(pair)=={'he','en'} and pair['he'] and pair['en'], (ident,key)
            assert not any('\u05d0'<=c<='\u05ea' for c in json.dumps(pair['en'],ensure_ascii=False)), (ident,key)
        for lang in ('he','en'):
            text=q.text(lang)
            assert text.prompt and text.reference_solution and len(set(text.hints))==3
            media=question_resources.learner_media(q.assets['bank_media'],lang)
            assert all(not m['source_path'].startswith('sources/') for m in media)
        if ident in NEW|VARIANTS:
            assert solution_review(q).status=='pending_review'
            assert q.status=='trial' and not q.assets['assessment_ready']
        if ident in NEW:
            assert q.assets['difficulty_status']=='unrated'


def test_short_cards_quizzes_and_review_registry_are_unchanged():
    for name, previous in BATCH22_BASELINE['short_card_source_sha256'].items():
        assert digest(read(ROOT/'apps/web/src/content'/name))==previous
    assert digest(read(SEEDS/'fundamentals_catalog.json')) == BATCH22_BASELINE['fundamentals_catalog_sha256']
    assert digest(read(SEEDS/'duel_quiz.json')) == BATCH22_BASELINE['quiz_bank_sha256']
    assert digest(read(SEEDS/'solution_review_attestations.json')) == BATCH22_BASELINE['review_registry_canonical_sha256']
