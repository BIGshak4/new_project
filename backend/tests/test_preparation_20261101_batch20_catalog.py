"""Twenty source questions in21 images; source pairing, preserved history and study gating."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services import question_resources
from tests.preparation_history import (
    BATCH1101_BASELINE,
    assert_pre_batch1101_archive,
    assert_pre_batch1101_assets,
    assert_pre_batch1101_localization,
    digest,
)
from tests.preparation_november_compiled_history import before_batch1101_compiled

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/'interview_preparation'
SEEDS=ROOT/'backend/seeds'
NEW={f'PREP-{n}'for n in range(233,245)}
VARIANTS={'PREP-023','PREP-027','PREP-091','PREP-117','PREP-151'}
SOURCE_ONLY={'PREP-015','PREP-096','PREP-125','PREP-173'}
MAP=((91,),(91,),(27,),(125,),(173,),(237,),(23,),(238,),(239,),(96,),
     (233,),(234,),(235,),(244,),(151,117),(240,),(15,),(241,),(242,),(243,),(236,))


def read(p):
    return json.loads(p.read_bytes())


def test_all21_images_and_first_pair_are_preserved_with_exact_mappings():
    manifest=read(BANK/'intakes/2026-11-01-batch20-sources.json')
    archive={q['id']:q for q in read(BANK/'questions.json')['questions']}
    assert manifest['screenshot_count']==21 and manifest['question_source_count']==20
    assert manifest['first_two_images_same_question'] is True
    for source,numbers in zip(manifest['sources'],MAP,strict=True):
        expected=[f'PREP-{n:03d}'for n in numbers]
        assert source['question_ids']==expected
        assert source['sha256']==BATCH1101_BASELINE['batch1101_source_sha256'][str(source['screenshot'])]
        path=source['archive_paths'][0]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest()==source['sha256']
        for ident in expected:
            q=archive[ident]
            assert any(s.get('path')==path for s in q['sources'])
            assert set(source['source_tags'])<=set(q['source_tags'])
            assert set(source['reported_companies'])<=set(q['reported_companies'])
    assert manifest['sources'][0]['question_ids']==manifest['sources'][1]['question_ids']==['PREP-091']
    assert len({ident for s in manifest['sources']for ident in s['question_ids']})==21


def test_231_old_records_media_and_localizations_remain_hash_bound():
    archive=read(BANK/'questions.json')
    assert len(archive['questions'])==archive['question_count']==270
    assert {q['id']for q in archive['questions']if int(q['id'][5:])<245}-BATCH1101_BASELINE['records'].keys()==NEW
    assert set(BATCH1101_BASELINE['variant_ids'])==VARIANTS
    assert set(BATCH1101_BASELINE['source_only_ids'])==SOURCE_ONLY
    assert_pre_batch1101_archive(archive)
    assert_pre_batch1101_assets(read(SEEDS/'preparation_uploads.json')['files'])
    localized={}
    for p in (SEEDS/'preparation_localization').glob('*.json'):
        rows=read(p)
        assert not localized.keys()&rows.keys()
        localized.update(rows)
    assert localized.keys()=={q['id']for q in archive['questions']}
    assert_pre_batch1101_localization(localized)
    for q in read(SEEDS/'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1101_BASELINE['records']:
            before_batch1101_compiled(q)


def test_bilingual_material_and_three_hints_stay_gated_with_clean_media():
    catalog=load_catalog(SEEDS)
    assert len(catalog.questions)==300
    selected={q.assets.get('preparation_id'):q for q in catalog.questions.values()
              if q.assets.get('preparation_id') in NEW|VARIANTS|SOURCE_ONLY}
    assert set(selected)==NEW|VARIANTS|SOURCE_ONLY
    for ident,q in selected.items():
        for key,pair in q.assets['preparation_resource']['learner_material'].items():
            assert set(pair)=={'he','en'} and pair['he'] and pair['en'],(ident,key)
            assert not any('\u05d0'<=c<='\u05ea'for c in json.dumps(pair['en'],ensure_ascii=False)),(ident,key)
        for lang in ('he','en'):
            text=q.text(lang)
            assert text.prompt and text.reference_solution and len(set(text.hints))==3
            media=question_resources.learner_media(q.assets['bank_media'],lang)
            assert all(not m['source_path'].startswith('sources/')for m in media)
        if ident in NEW|VARIANTS:
            assert solution_review(q).status=='pending_review'
            assert q.status=='trial'and not q.assets['assessment_ready']
        if ident in NEW:
            assert q.assets['difficulty_status']=='unrated'


def test_old_short_cards_quizzes_and_review_registry_remain_exact():
    for name,previous in BATCH1101_BASELINE['short_card_source_sha256'].items():
        assert digest(read(ROOT/'apps/web/src/content'/name))==previous
    assert digest(read(SEEDS/'fundamentals_catalog.json'))==BATCH1101_BASELINE['fundamentals_catalog_sha256']
    assert digest(read(SEEDS/'duel_quiz.json'))==BATCH1101_BASELINE['quiz_bank_sha256']
    assert digest(read(SEEDS/'solution_review_attestations.json'))==BATCH1101_BASELINE['review_registry_canonical_sha256']


@pytest.mark.parametrize('mutation',['title','hint','prompt','version','media','digest'])
def test_frozen_compiled_projection_rejects_old_content_mutations(mutation):
    q=copy.deepcopy(next(q for q in read(SEEDS/'questions/preparation_bank.json')if q['assets']['preparation_id']=='PREP-091'))
    if mutation=='title':
        q['translations']['en']['title']='changed'
    elif mutation=='hint':
        q['translations']['en']['hints'][0]='changed'
    elif mutation=='prompt':
        q['translations']['en']['prompt']='changed'
    elif mutation=='version':
        q['version']+=1
    elif mutation=='media':
        path=read(ROOT/'backend/tests/fixtures/preparation_compiled_before_20261101_batch20.json')['records']['PREP-091']['media_order'][0]
        next(m for m in q['assets']['bank_media'] if m['path']==path)['caption']='changed'
    else:
        q['assets']['source_sha256']='0'*64
    with pytest.raises(AssertionError):
        before_batch1101_compiled(q)
