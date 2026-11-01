"""Project the eight authorized compiled extensions onto their exact old hashes.

Only frozen metadata is restored: versions, source digest and invalidated review
attestations. Learner strings and material are taken from current prefixes, and
all old media objects must still exist byte-for-byte in their frozen order.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from tests.preparation_history import BATCH22_BASELINE, _prefix, before_batch1101_record, digest
from tests.preparation_november_compiled_history import before_batch1101_compiled

ROOT = Path(__file__).resolve().parents[2]
PROJECTIONS = json.loads((Path(__file__).parent / 'fixtures/preparation_compiled_before_20261031_batch22.json').read_bytes())['records']


@lru_cache(maxsize=1)
def _raw_archive():
    return {q['id']: q for q in json.loads((ROOT / 'interview_preparation/questions.json').read_bytes())['questions']}


def before_batch22_compiled(question):
    """Require the current compiled provenance, then verify the old full object."""
    question = before_batch1101_compiled(question)
    ident = question['assets']['preparation_id']
    assert ident in BATCH22_BASELINE['records'], ident
    if ident not in PROJECTIONS:
        assert digest(question) == BATCH22_BASELINE['compiled_sha256'][question['key']], ident
        return copy.deepcopy(question)
    frozen = PROJECTIONS[ident]
    assert question['key'] == frozen['key'], ident
    current = copy.deepcopy(question)
    raw = before_batch1101_record(_raw_archive()[ident])
    source_hash = hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert current['assets']['source_sha256'] == source_hash, ident
    current['assets']['source_sha256'] = frozen['source_sha256_before']
    for transition in frozen['transitions']:
        node = current
        for field in transition['path'][:-1]:
            node = node[field]
        field = transition['path'][-1]
        assert node[field] == transition['after'], (ident, transition['path'])
        node[field] = transition['before']
    for field, metadata in frozen['removed_review_metadata'].items():
        assert field not in current['assets'], (ident, field)
        current['assets'][field] = copy.deepcopy(metadata)
    for index, item in enumerate(current['assets']['bank_media'], 1):
        assert item['id'] == f'asset-{index}', (ident, item['path'])
    media = {item['path']: item for item in current['assets']['bank_media']}
    assert len(media) == len(current['assets']['bank_media']), ident
    for path, previous in frozen['media_sha256'].items():
        assert path in media, (ident, path)
        media[path]['id'] = frozen['media_ids'][path]
        assert digest(media[path]) == previous, (ident, path)
    current['assets']['bank_media'] = [media[path] for path in frozen['media_order']]
    restored = _prefix(current, frozen['shape'], ('compiled', ident))
    assert digest(restored) == frozen['sha256'] == BATCH22_BASELINE['compiled_sha256'][question['key']], ident
    return restored
