"""The append-only compiled projection rejects actual old-content regressions."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.preparation_compiled_history import PROJECTIONS, before_batch22_compiled
from tests.preparation_history import BATCH22_BASELINE

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def compiled():
    return {q['assets']['preparation_id']: q for q in json.loads(
        (ROOT / 'backend/seeds/questions/preparation_bank.json').read_bytes())}


def test_all_219_old_compiled_objects_still_match_their_original_full_hashes(compiled):
    assert len(BATCH22_BASELINE['records']) == 219
    assert set(PROJECTIONS) == set(BATCH22_BASELINE['variant_ids']) | set(BATCH22_BASELINE['source_only_ids'])
    for ident in BATCH22_BASELINE['record_order']:
        before_batch22_compiled(compiled[ident])


@pytest.mark.parametrize('mutation', ['prompt', 'hint', 'title', 'version', 'source_digest', 'old_media', 'asset_ordinal'])
def test_the_projection_rejects_old_content_or_unbound_metadata_changes(compiled, mutation):
    question = copy.deepcopy(compiled['PREP-025'])
    if mutation in {'prompt', 'title'}:
        question['translations']['en'][mutation] = 'Altered ' + question['translations']['en'][mutation]
    elif mutation == 'hint':
        question['translations']['en']['hints'][0] = 'Changed original hint'
    elif mutation == 'version':
        question['version'] += 1
    elif mutation == 'source_digest':
        question['assets']['source_sha256'] = '0' * 64
    elif mutation == 'old_media':
        path = PROJECTIONS['PREP-025']['media_order'][0]
        next(m for m in question['assets']['bank_media'] if m['path'] == path)['caption'] = 'Changed original caption'
    else:
        question['assets']['bank_media'][0]['id'] = 'asset-999'
    with pytest.raises(AssertionError):
        before_batch22_compiled(question)
