"""Ten new sources and explicitly selected completions of older vague tasks."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from tests.copy_november12_history import before_current_copy, before_current_fundamentals_manifest

import pytest

from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_history import (
    BATCH1107B10_BASELINE,
    assert_pre_batch1107b10_archive,
    assert_pre_batch1107b10_assets,
    assert_pre_batch1107b10_localization,
    before_batch1107b20_archive,
    digest,
)
from tests.preparation_november7_batch10_history import before_batch1107b10_compiled

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/'interview_preparation'
SEEDS=ROOT/'backend/seeds'
NEW={f'PREP-{n}' for n in range(272,276)}
VARIANTS={'PREP-018','PREP-040','PREP-050','PREP-067','PREP-095','PREP-133','PREP-206','PREP-271'}
MAP=(95,206,18,67,273,274,50,40,272,275)


def read(path):
    return json.loads(path.read_bytes())


def test_every_original_source_and_reported_attribution_is_preserved():
    manifest=read(BANK/'intakes/2026-11-07-batch10-sources.json')
    archive={q['id']:q for q in read(BANK/'questions.json')['questions']}
    assert manifest['screenshot_count']==manifest['question_source_count']==10
    for source,number in zip(manifest['sources'],MAP,strict=True):
        ident=f'PREP-{number:03d}'
        assert source['question_ids']==[ident]
        assert source['sha256']==BATCH1107B10_BASELINE['batch1107b10_source_sha256'][str(source['screenshot'])]
        path=source['archive_paths'][0]
        assert hashlib.sha256((BANK/path).read_bytes()).hexdigest()==source['sha256']
        q=archive[ident]
        assert any(s.get('path')==path for s in q['sources'])
        assert set(source['source_tags'])<=set(q['source_tags'])
        assert set(source['reported_companies'])<=set(q['reported_companies'])


def test_all270_old_records1557_assets_and_bilingual_content_remain_hash_bound():
    current_archive=read(BANK/'questions.json')
    archive=before_batch1107b20_archive(current_archive)
    assert len(archive['questions'])==archive['question_count']==274
    assert {q['id'] for q in archive['questions']}-BATCH1107B10_BASELINE['records'].keys()==NEW
    assert set(BATCH1107B10_BASELINE['variant_ids'])==VARIANTS
    assert not BATCH1107B10_BASELINE['source_only_ids']
    assert_pre_batch1107b10_archive(current_archive)
    assets=read(SEEDS/'preparation_uploads.json')['files']
    assert len(assets)==1837
    assert_pre_batch1107b10_assets(assets)
    localized={}
    for path in (SEEDS/'preparation_localization').glob('*.json'):
        rows=read(path)
        assert not localized.keys()&rows.keys()
        localized.update(rows)
    assert localized.keys()=={q['id'] for q in current_archive['questions']}
    assert_pre_batch1107b10_localization(localized)
    for q in read(SEEDS/'questions/preparation_bank.json'):
        if q['assets']['preparation_id'] in BATCH1107B10_BASELINE['records']:
            before_batch1107b10_compiled(q)


def test_complete_bilingual_content_and_answer_media_are_still_gated():
    catalog=load_catalog(SEEDS)
    assert len(catalog.questions)== 340
    selected={q.assets.get('preparation_id'):q for q in catalog.questions.values()
              if q.assets.get('preparation_id') in NEW|VARIANTS}
    assert set(selected)==NEW|VARIANTS
    for ident,q in selected.items():
        assert q.status=='trial' and not q.assets['assessment_ready']
        assert solution_review(q).status=='pending_review'
        for lang in ('he','en'):
            text=q.text(lang)
            assert text.prompt and text.reference_solution and len(set(text.hints))==3
            assert all(not m['source_path'].startswith('sources/') for m in learner_media(q.assets['bank_media'],lang))
        for key,pair in q.assets['preparation_resource']['learner_material'].items():
            assert set(pair)=={'he','en'} and pair['he'] and pair['en'],(ident,key)
            assert not any('\u05d0'<=c<='\u05ea' for c in json.dumps(pair['en'],ensure_ascii=False)),(ident,key)


def test_same_day_divisor4_source_does_not_replace_previous_divisor7_variant():
    raw=next(q for q in read(BANK/'questions.json')['questions'] if q['id']=='PREP-206')
    prior=BATCH1107B10_BASELINE['records']['PREP-206']['projection']
    assert raw['version']==prior['version']+1==4
    source=read(BANK/'intakes/2026-11-07-batch10-sources.json')['sources'][1]
    assert 'ב-4' in source['original_prompt']
    for lang in ('he','en'):
        shape=prior['append_shapes']['translations']['items'][lang]['items']['prompt']
        old_prefix=raw['translations'][lang]['prompt'][:shape['length']]
        added=raw['translations'][lang]['prompt'][shape['length']:]
        assert ('בשבע' in old_prefix) if lang=='he' else ('seven' in old_prefix)
        assert ('בארבע' in added or 'ב־4' in added or 'ב-4' in added) if lang=='he' else ('four' in added or 'by4' in added)


def test_completeness_audit_covers_every_prior_record_and_names_only_two_needed_completions():
    audit=read(BANK/'checks/batch1107b10-completeness-audit.json')
    assert audit['reviewed_records']==sum(audit['counts'].values())==270
    assert {item['id'] for item in audit['minimum_targeted_backlog']}=={'PREP-133','PREP-271'}
    assert len(audit['records'])==270


def test_short_banks_and_attestation_registry_are_unchanged():
    baseline=BATCH1107B10_BASELINE
    for name,expected in baseline['short_card_source_sha256'].items():
        assert digest(before_current_copy('fundamentals', name, read(ROOT/'apps/web/src/content'/name)))==expected
    for name,key in [('fundamentals_catalog.json','fundamentals_catalog_sha256'),
                     ('duel_quiz.json','quiz_bank_sha256'),
                     ('solution_review_attestations.json','review_registry_canonical_sha256')]:
        actual = read(SEEDS / name)
        if name == 'fundamentals_catalog.json':
            actual = before_current_fundamentals_manifest(actual)
        elif name == 'duel_quiz.json':
            actual = before_current_copy('quiz', name, actual)
        assert digest(actual) == baseline[key]


@pytest.mark.parametrize('mutation',['title','hint','prompt','version','media','digest','asset_ordinal'])
def test_frozen_prefix_projection_rejects_unauthorized_old_edits(mutation):
    q=copy.deepcopy(next(q for q in read(SEEDS/'questions/preparation_bank.json') if q['assets']['preparation_id']=='PREP-018'))
    if mutation == 'title':
        q['translations']['en']['title'] = 'changed'
    elif mutation == 'hint':
        q['translations']['en']['hints'][0] = 'changed'
    elif mutation == 'prompt':
        q['translations']['en']['prompt'] = 'changed'
    elif mutation == 'version':
        q['version'] += 1
    elif mutation == 'media':
        frozen_media = next(m for m in q['assets']['bank_media']
                            if m['path'] in BATCH1107B10_BASELINE['asset_sha256'])
        frozen_media['caption'] = 'changed'
    elif mutation == 'asset_ordinal':
        q['assets']['bank_media'][0]['id'] = 'asset-999'
    else:
        q['assets']['source_sha256'] = '0' * 64
    with pytest.raises(AssertionError):
        before_batch1107b10_compiled(q)
