"""Archive attribution, authored figures and version boundaries of the 21-image intake."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from app.engine.catalog import load_catalog
from app.engine.question_difficulty import difficulty_fingerprint
from app.engine.solution_review import solution_review
from app.services.question_resources import learner_media
from tests.preparation_november18b_history import before_nov18b


ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
BATCH = '2026-11-18-batch21'
MAP = {
    1: (37,), 2: (385,), 3: (377,), 4: (378,), 6: (379,), 7: (196,),
    8: (22, 162), 9: (382,), 10: (31,), 11: (380,), 12: (119,), 13: (386,),
    14: (115,), 15: (85,), 16: (383,), 17: (381,), 19: (214,), 20: (227,), 21: (384,),
}
COMPANIONS = {4: (5,), 17: (18,)}
NEW = {f'PREP-{number}' for number in range(377, 387)}
EXTENSIONS = {'PREP-031', 'PREP-196', 'PREP-214', 'PREP-227'}
SOURCE_ONLY = {'PREP-022', 'PREP-037', 'PREP-085', 'PREP-115', 'PREP-119', 'PREP-162'}
GIVEN_DIAGRAMS = {'PREP-377', 'PREP-378', 'PREP-381', 'PREP-382'}
# SHA256 over the 21 binary SHA256 digests in the order the attachments were supplied.
ORIGINALS_SHA256 = '50794730bd1dee659d8ec55f60751d0931fe48a6a7d4aad18d675e5c2554f4fc'


def read(path):
    return json.loads(path.read_bytes())


def test_original_files_and_companions_point_to_precisely_the_expected_records():
    manifest = read(BANK / 'intakes' / f'{BATCH}-sources.json')
    assert manifest['screenshot_count'] == 21
    assert len(manifest['sources']) == manifest['source_count'] == 19
    assert (manifest['new_question_count'], manifest['technical_extension_count'],
            manifest['provenance_only_count'], manifest['affected_question_count']) == (10, 4, 6, 20)
    assert [entry['screenshot'] for entry in manifest['sources']] == list(MAP)
    expected_links = Counter()
    original_digests = {}
    for entry in manifest['sources']:
        number = entry['screenshot']
        companions = COMPANIONS.get(number, ())
        ids = [f'PREP-{i:03}' for i in MAP[number]]
        assert entry['question_ids'] == ids
        if set(ids) <= NEW:
            assert entry['decision'] == 'new_question'
        elif set(ids) <= EXTENSIONS:
            assert entry['decision'] == 'technical_extension'
        else:
            assert set(ids) <= SOURCE_ONLY
            assert entry['decision'] == 'additional_source_existing_question'
        assert entry['companion_screenshots'] == list(companions)
        numbers = (number, *companions)
        paths = [f'sources/{BATCH}-{i:02}.png' for i in numbers]
        assert entry['archive_paths'] == paths
        assert set(entry['archive_sha256']) == set(paths)
        for i, path in zip(numbers, paths, strict=True):
            digest = hashlib.sha256((BANK / path).read_bytes())
            assert entry['archive_sha256'][path] == digest.hexdigest()
            original_digests[i] = digest.digest()
            role = 'original_question_screenshot' if i == number else 'original_question_companion_diagram'
            expected_links.update((ident, path, role) for ident in ids)
    assert sorted(original_digests) == list(range(1, 22))
    assert hashlib.sha256(b''.join(original_digests[i] for i in range(1, 22))).hexdigest() == ORIGINALS_SHA256
    archive = read(BANK / 'questions.json')['questions']
    assert len({row['id'] for row in archive}) == len(archive)
    assert len({row['key'] for row in archive}) == len(archive)
    actual_links = Counter(
        (row['id'], source['path'], source['role'])
        for row in archive for source in row['sources']
        if source.get('path', '').startswith(f'sources/{BATCH}-')
    )
    assert actual_links == expected_links


def test_published_questions_keep_images_private_and_ratings_bound_to_the_content():
    catalog = load_catalog(SEEDS)
    compiled = {row['key']: row for row in read(SEEDS / 'questions/preparation_bank.json')}
    ratings = read(SEEDS / 'question_difficulty.json')
    targets = NEW | EXTENSIONS | SOURCE_ONLY
    selected = {q.assets.get('preparation_id'): q for q in catalog.questions.values()
                if q.assets.get('preparation_id') in targets}
    assert selected.keys() == targets
    source_only_material = {}
    for ident, question in selected.items():
        row = compiled[question.key]
        rating = ratings[question.key]
        assert 1 <= question.difficulty == rating['difficulty'] <= 10
        assert rating['reason'].strip()
        assert difficulty_fingerprint(row) == rating['content_sha256']
        if ident in EXTENSIONS:
            previous = before_nov18b('compiled:' + question.key, row)
            assert question.version == previous['version'] + 1
            for lang in ('he', 'en'):
                for field in ('prompt', 'reference_solution'):
                    original = previous['translations'][lang][field]
                    current = row['translations'][lang][field]
                    assert current.startswith(original) and len(current) > len(original)
        elif ident in SOURCE_ONLY:
            source_only_material[ident] = [question.key, question.version, question.difficulty, row['translations']]
        else:
            assert question.version == 1
        if ident in EXTENSIONS | NEW:
            assert question.status == 'trial' and not question.assets['assessment_ready']
            assert solution_review(question).status == 'pending_review'
            for lang in ('he', 'en'):
                assert len(question.text(lang).hints) == len(set(question.text(lang).hints)) == 3
        assets = question.assets['bank_media']
        private_hashes = {item['sha256'] for item in assets if item['source_path'].startswith('sources/')}
        assert private_hashes
        for lang in ('he', 'en'):
            visible = learner_media(assets, lang)
            assert all(not item['source_path'].startswith('sources/') and item['sha256'] not in private_hashes
                       for item in visible)
            if ident in GIVEN_DIAGRAMS:
                given = [item for item in visible if item['kind'] == 'image' and item['role'] == 'prompt'
                         and item.get('language') == lang]
                assert given, (ident, lang)
                for item in given:
                    assert item['source_path'].startswith('diagrams/')
                    assert hashlib.sha256((BANK / item['source_path']).read_bytes()).hexdigest() == item['sha256']
    # These six records gained only provenance. Pin their pre-intake learner copy and version.
    unchanged = json.dumps(source_only_material, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    assert hashlib.sha256(unchanged).hexdigest() == '430a58a154df4081ad678506aee446d928b3383ce6852730619f53102a3a1ddd'
