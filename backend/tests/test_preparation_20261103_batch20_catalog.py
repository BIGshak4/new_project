"""Nov3 intake:21 screenshots,20 source statements,18 preserved/new identities."""
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
    BATCH1103_BASELINE,
    assert_pre_batch1103_archive,
    assert_pre_batch1103_assets,
    assert_pre_batch1103_localization,
    digest,
)
from tests.preparation_november3_compiled_history import before_batch1103_compiled

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/'interview_preparation'
SEEDS=ROOT/'backend/seeds'
NEW={f'PREP-{n}' for n in range(245,257)}
VARIANTS={'PREP-001','PREP-094','PREP-140','PREP-152','PREP-238'}
SOURCE_ONLY={'PREP-045'}
MAP=((254,),(94,),(140,),(152,),(238,),(248,),(238,),(238,),(249,),(245,),
     (250,),(252,),(255,),(256,),(246,),(94,),(1,),(251,),(253,),(247,),(45,))


def read(path):
    return json.loads(path.read_bytes())


def test_all21_sources_are_preserved_and_reversal_pair_shares_identity():
    manifest=read(BANK/'intakes/2026-11-03-batch20-sources.json')
    archive={q['id']:q for q in read(BANK/'questions.json')['questions']}
    assert manifest['screenshot_count']==21 and manifest['question_source_count']==20
    assert manifest['duplicate_image_pairs']==[[7,8]]
    for source,numbers in zip(manifest['sources'],MAP,strict=True):
        expected=[f'PREP-{n:03d}' for n in numbers]
        assert source['question_ids']==expected
        assert source['sha256']==BATCH1103_BASELINE['batch1103_source_sha256'][str(source['screenshot'])]
        path=source['archive_paths'][0]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest()==source['sha256']
        for ident in expected:
            q=archive[ident]
            assert any(s.get('path')==path for s in q['sources'])
            assert set(source['source_tags'])<=set(q['source_tags'])
            assert set(source['reported_companies'])<=set(q['reported_companies'])
    assert manifest['sources'][6]['question_ids']==manifest['sources'][7]['question_ids']==['PREP-238']
    assert len({ident for s in manifest['sources'] for ident in s['question_ids']})==18


def test_all243_previous_records_assets_translations_and_compiled_values_are_frozen():
    archive=read(BANK/'questions.json')
    assert len(archive['questions'])==archive['question_count']==255
    assert {q['id'] for q in archive['questions']}-BATCH1103_BASELINE['records'].keys()==NEW
    assert set(BATCH1103_BASELINE['variant_ids'])==VARIANTS
    assert set(BATCH1103_BASELINE['source_only_ids'])==SOURCE_ONLY
    assert_pre_batch1103_archive(archive)
    assert_pre_batch1103_assets(read(SEEDS/'preparation_uploads.json')['files'])
    localized={}
    for path in (SEEDS/'preparation_localization').glob('*.json'):
        rows=read(path)
        assert not localized.keys()&rows.keys()
        localized.update(rows)
    assert localized.keys()=={q['id'] for q in archive['questions']}
    assert_pre_batch1103_localization(localized)
    for q in read(SEEDS/'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1103_BASELINE['records']:
            before_batch1103_compiled(q)


def test_bilingual_hints_material_and_protected_media_stay_gated():
    catalog=load_catalog(SEEDS)
    assert len(catalog.questions)==285
    selected={q.assets.get('preparation_id'):q for q in catalog.questions.values()
              if q.assets.get('preparation_id') in NEW|VARIANTS|SOURCE_ONLY}
    assert set(selected)==NEW|VARIANTS|SOURCE_ONLY
    for ident,q in selected.items():
        for key,pair in q.assets['preparation_resource']['learner_material'].items():
            assert set(pair)=={'he','en'} and pair['he'] and pair['en'],(ident,key)
            assert not any('\u05d0'<=c<='\u05ea' for c in json.dumps(pair['en'],ensure_ascii=False)),(ident,key)
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
        if ident=='PREP-255':
            for lang in ('he','en'):
                media=question_resources.learner_media(q.assets['bank_media'],lang)
                targets=[m for m in media if m['role']=='prompt']
                answers=[m for m in media if m['role']=='solution' and m['kind']=='image']
                assert [m['source_path'] for m in targets]==[f'diagrams/prep-255-target-waveform-{lang}.png']
                assert len(answers)==2 and all('target-waveform' not in m['source_path'] for m in answers)


def test_short_cards_quizzes_and_human_review_registry_are_unchanged():
    for name,previous in BATCH1103_BASELINE['short_card_source_sha256'].items():
        assert digest(read(ROOT/'apps/web/src/content'/name))==previous
    assert digest(read(SEEDS/'fundamentals_catalog.json'))==BATCH1103_BASELINE['fundamentals_catalog_sha256']
    assert digest(read(SEEDS/'duel_quiz.json'))==BATCH1103_BASELINE['quiz_bank_sha256']
    assert digest(read(SEEDS/'solution_review_attestations.json'))==BATCH1103_BASELINE['review_registry_canonical_sha256']


@pytest.mark.parametrize('mutation',['title','hint','prompt','version','media','digest'])
def test_frozen_projection_rejects_unauthorized_old_content_edits(mutation):
    q=copy.deepcopy(next(q for q in read(SEEDS/'questions/preparation_bank.json')
                         if q['assets']['preparation_id']=='PREP-001'))
    if mutation=='title':
        q['translations']['en']['title']='changed'
    elif mutation=='hint':
        q['translations']['en']['hints'][0]='changed'
    elif mutation=='prompt':
        q['translations']['en']['prompt']='changed'
    elif mutation=='version':
        q['version']+=1
    elif mutation=='media':
        old_path=read(ROOT/'backend/tests/fixtures/preparation_compiled_before_20261103_batch20.json')['records']['PREP-001']['media_order'][0]
        next(m for m in q['assets']['bank_media'] if m['path']==old_path)['caption']='changed'
    else:
        q['assets']['source_sha256']='0'*64
    with pytest.raises(AssertionError):
        before_batch1103_compiled(q)
