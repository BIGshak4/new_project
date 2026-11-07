"""Nov7 intake:30screenshots,29source statements,29identities."""
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
    BATCH1107_BASELINE,
    assert_pre_batch1107_archive,
    assert_pre_batch1107_assets,
    assert_pre_batch1107_localization,
    before_batch1107_record,
    digest,
)
from tests.preparation_november7_history import before_batch1107_compiled

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/'interview_preparation'
SEEDS=ROOT/'backend/seeds'
NEW={f'PREP-{n}' for n in range(257,272)}
VARIANTS={'PREP-019','PREP-035','PREP-041','PREP-065','PREP-182','PREP-206'}
SOURCE_ONLY={'PREP-009','PREP-011','PREP-037','PREP-045','PREP-070','PREP-077','PREP-110','PREP-112'}
MAP=tuple((n,) for n in (257,41,65,11,70,35,265,258,19,259,260,112,206,112,266,110,45,37,267,268,269,261,270,9,182,262,263,271,264,77))


def read(path):
    return json.loads(path.read_bytes())


def test_all30_sources_are_preserved_and_duplicate_gate_pair_shares_identity():
    manifest=read(BANK/'intakes/2026-11-07-batch30-sources.json')
    archive={q['id']:q for q in read(BANK/'questions.json')['questions']}
    assert manifest['screenshot_count']==30 and manifest['question_source_count']==29
    assert manifest['duplicate_statement_pairs']==[[12,14]]
    for source,numbers in zip(manifest['sources'],MAP,strict=True):
        expected=[f'PREP-{n:03d}' for n in numbers]
        assert source['question_ids']==expected
        assert source['sha256']==BATCH1107_BASELINE['batch1107_source_sha256'][str(source['screenshot'])]
        path=source['archive_paths'][0]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest()==source['sha256']
        for ident in expected:
            q=archive[ident]
            assert any(s.get('path')==path for s in q['sources'])
            assert set(source['source_tags'])<=set(q['source_tags'])
            assert set(source['reported_companies'])<=set(q['reported_companies'])
    assert manifest['sources'][11]['question_ids']==manifest['sources'][13]['question_ids']==['PREP-112']
    assert len({ident for s in manifest['sources'] for ident in s['question_ids']})==29


def test_source13_divisor_seven_matches_the_new_serial_contract_in_both_banks():
    """The old 2/4/8 base must not overwrite the divisor visible in this source."""
    manifest=read(BANK/'intakes/2026-11-07-batch30-sources.json')
    source=next(s for s in manifest['sources'] if s['screenshot']==13)
    assert source['question_ids']==['PREP-206']
    assert 'ב-7' in source['original_prompt']
    raw=next(q for q in read(BANK/'questions.json')['questions'] if q['id']=='PREP-206')
    compiled=next(q for q in read(SEEDS/'questions/preparation_bank.json')
                  if q['assets']['preparation_id']=='PREP-206')
    assert raw['version']==compiled['version']==3
    for current,previous in ((raw,before_batch1107_record(raw)),
                             (compiled,before_batch1107_compiled(compiled))):
        for language in ('he','en'):
            old=previous['translations'][language]['prompt']
            prompt=current['translations'][language]['prompt']
            assert prompt.startswith(old)
            extension=prompt[len(old):]
            compact=''.join(extension.split()).casefold()
            divisor_markers=('ב־7','ב-7','בשבע') if language=='he' else (
                'divisibleby7','divisiblebyseven','divisibilityby7','divisibilitybyseven')
            assert any(marker in compact for marker in divisor_markers),language
            old_solution=previous['translations'][language]['reference_solution']
            solution=current['translations'][language]['reference_solution']
            assert solution.startswith(old_solution)
            new_solution=solution[len(old_solution):]
            assert 'rnext=(2r+b)%7' in ''.join(new_solution.split()),language


def test_all255_previous_records_assets_translations_and_compiled_values_are_frozen():
    archive=read(BANK/'questions.json')
    assert len(archive['questions'])==archive['question_count']==270
    assert {q['id'] for q in archive['questions']}-BATCH1107_BASELINE['records'].keys()==NEW
    assert set(BATCH1107_BASELINE['variant_ids'])==VARIANTS
    assert set(BATCH1107_BASELINE['source_only_ids'])==SOURCE_ONLY
    assert_pre_batch1107_archive(archive)
    assert_pre_batch1107_assets(read(SEEDS/'preparation_uploads.json')['files'])
    localized={}
    for path in (SEEDS/'preparation_localization').glob('*.json'):
        rows=read(path)
        assert not localized.keys()&rows.keys()
        localized.update(rows)
    assert localized.keys()=={q['id'] for q in archive['questions']}
    assert_pre_batch1107_localization(localized)
    for q in read(SEEDS/'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1107_BASELINE['records']:
            before_batch1107_compiled(q)


def test_bilingual_hints_material_and_protected_media_stay_gated():
    catalog=load_catalog(SEEDS)
    assert len(catalog.questions)==300
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


def test_short_cards_quizzes_and_human_review_registry_are_unchanged():
    for name,previous in BATCH1107_BASELINE['short_card_source_sha256'].items():
        assert digest(read(ROOT/'apps/web/src/content'/name))==previous
    assert digest(read(SEEDS/'fundamentals_catalog.json'))==BATCH1107_BASELINE['fundamentals_catalog_sha256']
    assert digest(read(SEEDS/'duel_quiz.json'))==BATCH1107_BASELINE['quiz_bank_sha256']
    assert digest(read(SEEDS/'solution_review_attestations.json'))==BATCH1107_BASELINE['review_registry_canonical_sha256']


@pytest.mark.parametrize('mutation',['title','hint','prompt','version','media','digest','asset_ordinal'])
def test_frozen_projection_rejects_unauthorized_old_content_edits(mutation):
    q=copy.deepcopy(next(q for q in read(SEEDS/'questions/preparation_bank.json')
                         if q['assets']['preparation_id']=='PREP-065'))
    if mutation=='title':
        q['translations']['en']['title']='changed'
    elif mutation=='hint':
        q['translations']['en']['hints'][0]='changed'
    elif mutation=='prompt':
        q['translations']['en']['prompt']='changed'
    elif mutation=='version':
        q['version']+=1
    elif mutation=='media':
        old_path=read(ROOT/'backend/tests/fixtures/preparation_compiled_before_20261107_batch30.json')['records']['PREP-065']['media_order'][0]
        next(m for m in q['assets']['bank_media'] if m['path']==old_path)['caption']='changed'
    elif mutation=='asset_ordinal':
        q['assets']['bank_media'][0]['id']='asset-999'
    else:
        q['assets']['source_sha256']='0'*64
    with pytest.raises(AssertionError):
        before_batch1107_compiled(q)
