"""400 cards and 2,000 quiz variants preserve every previous content identity.

No live DB writes: completion, match snapshots and privacy use existing in-memory
service tests. New technical oracles live in the three domain-specific files.
"""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
CONTENT=ROOT/'apps/web/src/content'
SEEDS=ROOT/'backend/seeds'
NEW_NAMES=('fundamentals-hardware-400.json','fundamentals-reasoning-400.json','fundamentals-code-400.json')
OLD_FILE_SHA256={'fundamentals-hardware.json': '3d942668f98ce6065d09727f1509c483124a61b46c94ddb3a09407cc67cbe8d0', 'fundamentals-code-logic.json': 'd8012fe97385ec924a0bd31c07bb6fd20a64eb3f39912572fc512f6aa1ad5e1f', 'fundamentals-hardware-expansion.json': 'be5cc9b500f314821accc08172408279572773c50620f2b86c0fcdc9940b4f60', 'fundamentals-reasoning-expansion.json': '507a827ec0e1719209aac9da6f7ed483696bbda454caad8ae2412e1d90cc4e2a', 'fundamentals-code-expansion.json': '16b2ff6a0e2071b0ec92dc526647d8ddd70fe49b2a6296ad223a26ae8c9d1823', 'fundamentals-hardware-250.json': 'd9ea4e135e6ed0e2225c4538228daa2ec59cf0bee8f662057de350ac7f01da8d', 'fundamentals-reasoning-250.json': 'ac1bb8d8f4a06f3a4e2342f87941d0d7b34e45b8b86d2d8c664a5fb20b6229df', 'fundamentals-code-250.json': '7bf15b8e095fd920596724a76db81b7dea7a794ae76c2f963563874f431b7470'}
OLD_REVISIONS_SHA256='8f6055ae85bc6606a04be36eb17486e80dcb39bd6b46dd59eea3c5b0042b4b68'
OLD_QUIZ_SHA256='6a495652ed9c23b591f039e0f5f36d7874319f0df1621e726e10ab331ad56e5d'
OLD_RELEASE_SHA256='098332d7f2cffae68d19843a540ceb8a57024f5052f1b9c71621753d06576822'
ARCHIVE_SHA256='5bae12aa23d16895bb038afbe068f2479c26dbf72048b937a5cb65119a520316'
REVIEW_SHA256='334081f0a306ba1715a585e664935c8de59a9fc2e6f3e517f3a6fa3e239aa678'


def read(path):
    return json.loads(path.read_bytes())


def canonical_digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",", ":")).encode()).hexdigest()


def old_id(key):
    return int(key.rsplit("-",1)[1])<=125


def test_old_250_card_bytes_and_revisions_are_preserved():
    for name,expected in OLD_FILE_SHA256.items():
        assert hashlib.sha256((CONTENT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected,name
    web=read(CONTENT/'fundamentals-revisions.json')
    backend=read(SEEDS/'fundamentals_catalog.json')['questions']
    assert len(web)==len(backend)==400 and web==backend
    original={key:value for key,value in web.items() if old_id(key)}
    assert len(original)==250 and canonical_digest(original)==OLD_REVISIONS_SHA256


def test_all_400_cards_have_distinct_bilingual_objectives_and_exact_mix():
    old=[q for name in OLD_FILE_SHA256 for q in read(CONTENT/name)]
    new=[q for name in NEW_NAMES for q in read(CONTENT/name)]
    assert len(new)==150
    all_cards=old+new
    assert len(all_cards)==len({q['id'] for q in all_cards})==400
    assert Counter('hardware' if q['id'].startswith('quick-hw-') else 'reasoning' if q['topic']=='reasoning' else 'code' for q in all_cards)=={'hardware':200,'reasoning':140,'code':60}
    for lang in ('he','en'):
        for field in ('title','prompt'):
            values=[q[field][lang].strip().casefold() for q in all_cards]
            assert len(set(values))==400
    interview={q['id'] for q in read(ROOT/'interview_preparation/questions.json')['questions']}
    for q in new:
        assert q['topic'] in {'gates','bits','sequential','states','electronics','python','algorithms','reasoning'}
        assert q['interviewIds'] and set(q['interviewIds'])<=interview
        assert len(q['interviewIds'])==len(set(q['interviewIds']))
        assert 'solution_review' not in q and 'company' not in q
        for field,limit in (('title',12),('prompt',50),('answer',65),('takeaway',20)):
            assert set(q[field])=={'he','en'}
            for lang,value in q[field].items():
                assert value.strip()==value and value and len(value.split())<=limit,(q['id'],field,lang)
                if lang=='en':
                    assert not any('\u0590'<=char<='\u05ff' for char in value)
        if 'code' in q:
            assert len(q['code']['text'].splitlines())<=5
    assert {q['id'] for q in new}=={f'quick-hw-{n}' for n in range(126,201)}|{f'quick-sw-{n}' for n in range(126,201)}


def test_every_prior_quiz_object_and_authorization_is_unchanged():
    quiz=read(SEEDS/'duel_quiz.json')['questions']
    original=[q for q in quiz if not q.get('source_key') or old_id(q['source_key'])]
    assert len(original)==1290 and canonical_digest(original)==OLD_QUIZ_SHA256
    manifest=read(SEEDS/'duel_quiz_batches/release-manifest.json')
    preserved=[entry for entry in manifest['questions'] if old_id(entry['key'].rsplit('-v',1)[0])]
    assert len(preserved)==1200 and canonical_digest(preserved)==OLD_RELEASE_SHA256
    new=[q for q in quiz if q.get('source_key') and not old_id(q['source_key'])]
    assert len(new)==750
    assert all(q['status']=='approved' and q['release_approval']['on']=='2026-10-30' and q['release_approval']['professional_review']=='pending' for q in new)
    assert len(quiz)==2040 and sum(q['status']=='approved' for q in quiz)==2000


def test_the_interview_bank_and_its_human_attestations_are_not_rewritten():
    assert hashlib.sha256((ROOT/'interview_preparation/questions.json').read_bytes()).hexdigest()==ARCHIVE_SHA256
    assert hashlib.sha256((SEEDS/'solution_review_attestations.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest()==REVIEW_SHA256


@pytest.mark.parametrize('domain,expected',[('hardware',375),('reasoning',260),('code',115)])
def test_each_expansion_variant_has_its_own_reproducible_evidence(domain,expected):
    path=ROOT/f'backend/scripts/quiz_authoring/{domain}_400.py'
    spec=importlib.util.spec_from_file_location(f'quiz_400_{domain}',path)
    author=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    result=author.build()
    rows=result[0] if isinstance(result,tuple) else result
    stored=read(SEEDS/f'duel_quiz_batches/{domain}_400.json')
    checks=read(SEEDS/f'duel_quiz_batches/{domain}_400.checks.json')
    assert rows==stored and len(rows)==len(checks)==expected
    assert {q['key'] for q in rows}=={q['key'] for q in checks}
    assert all(q['status']=='draft' for q in stored)
    assert all(q.get('method') and 'expected' in q for q in checks)
