"""Current intake and frozen historical contracts, without network or learner writes.

Actual C execution has its own persisted, source-bound evidence. Python/HDL model
oracles live in domain tests; these checks cover publication content and gating.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from pathlib import Path

import pytest
from app.api.errors import ApiError
from app.engine import bank
from app.engine.catalog import load_catalog
from app.engine.solution_review import solution_review
from app.repo.questions import LoadedQuestion, summary
from app.services import question_resources
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig

from tests.preparation_history import (
    BATCH20_BASELINE,
    BATCH21_BASELINE,
    assert_pre_batch20_archive,
    assert_pre_batch20_assets,
    assert_pre_batch20_localization,
    before_batch20_record,
    digest,
)
from tests.test_practice_hardening import GOOD, scripted

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / 'interview_preparation'
SEEDS = ROOT / 'backend/seeds'
NEW_IDS = {f'PREP-{number}' for number in range(210, 221)}
VARIANT_IDS = {'PREP-036', 'PREP-070', 'PREP-083', 'PREP-107', 'PREP-110'}
SOURCE_ONLY_IDS = {'PREP-072', 'PREP-106', 'PREP-172'}
AFFECTED_IDS = NEW_IDS | VARIANT_IDS | SOURCE_ONLY_IDS
SOURCE_MAP = dict(enumerate((210, 213, 211, 172, 107, 72, 214, 216, 110, 106,
                             70, 215, 36, 110, 217, 218, 219, 212, 83, 220), 1))
# These original screenshot bytes are independent of generated archive metadata.
SOURCE_SHA256 = dict(enumerate((
    'f05f420e57348726861e4295b75c61e9643c6522fa4305c66b4d106d86217632',
    'accc314219cd55d5adc6372d47db80e9e986e066570646d66d1d8bc3afac9ac0',
    '2b8c8c81162977aef2727ce6f059d68241352abbe7aba48d26d2c061644c8da6',
    '6a02b2f4ff2d21241afaa0b125dc9aba27091d1f307c36a7b413160780060819',
    '5da1d613580bfff976de7ed60042517eb1f5037d26301a30dac2e4b32cfbc4b0',
    '18898bf4bf7fcd0e031cce69b75d041ebde3b982117f4fcdf5443ca83bbeea96',
    'a8fb8d02016f73af4bc0749705beee82ee0df53e77a0f7212fbe25042c1d1585',
    '76ab3fa759152154df6d4f0eebfdffe84425e862da498be0702277647b7bb0a8',
    '0ed9db4a1abb6f23b1d162260b0a2fa66797a3c83365b5ae6fa97a21afc5e51b',
    'ba34c951792edacb21bd92ac13b1b8ad8c96f2626eb674c023e3421a7d5dcd78',
    '431cdfc8c9311801576ef9dfe52a2ddcac5733a960c135fd15c6c07f09b3185e',
    'aed0cfcb8067cd0ec640130840b91145c7c867fc6f17a2907cf7d0004ed5176d',
    'c16ff9da630cbe09ab555e72f1bf45d28ec123f11892d9a55add567482ceb771',
    'f67fd18dfc6fc7bfe2123a59a13ceb1331741db94b09a1666a51eaa3d482b69f',
    'e41d46be11ba1c0f4e325e76605db96a21ee1cf57f45b9a834e1484826fdb461',
    'bc8ae6f682ddfc20fda4887d2b7633acbeaecd9c095bba730d31b2affb339888',
    'f8180c5834b0eba973661172d07069c17c2bc6e63115bca1b3588925e17b7000',
    '877c2b93d5faec43407d9a86f41b045afc0dc9e18e58987160f19653f8a63a7a',
    'c39c9f5453108fd5baa26acf50ebe8db9e4801f6e59710a99607535ed1c7c4b4',
    '9ced64e86e3f86832f878726e0a8b9671866bf1c71868524d9864e20b1051c7c',
), 1))
SOURCE_TAGS = {
    number: set(tags.split()) for number, tags in enumerate((
        'hardware nvidia', 'hardware nvidia', 'hardware apple', 'hardware nvidia',
        'hardware nvidia', 'hardware nvidia verification', 'hardware cisco verification logic',
        'hardware apple', 'hardware intel', 'hardware apple', 'hardware intel',
        'hardware cisco verification', 'hardware apple', 'hardware apple',
        'hardware apple marvell', 'hardware apple', 'hardware apple verification',
        'software apple', 'hardware apple', 'hardware intel verification'), 1)
}
COMPANY_NAMES = {'nvidia': 'NVIDIA', 'apple': 'Apple', 'intel': 'Intel', 'cisco': 'Cisco', 'marvell': 'Marvell'}
MATERIAL_FIELDS = {'assumptions', 'optimality', 'verification', 'edge_cases',
                   'common_mistakes', 'interview_answer', 'solution_extensions', 'source_ambiguities'}


def read(path):
    return json.loads(path.read_bytes())


def no_hebrew(value):
    return not any('\u05d0' <= char <= '\u05ea' for char in json.dumps(value, ensure_ascii=False))


@pytest.fixture(scope='module')
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture(scope='module')
def archive():
    return read(BANK / 'questions.json')


def selected(catalog):
    return {q.assets['preparation_id']: q for q in catalog.questions.values()
            if q.assets.get('preparation_id') in AFFECTED_IDS}


def test_twenty_exact_sources_keep_full_tags_companies_and_nineteen_identities(archive):
    intake = read(BANK / 'intakes/2026-10-31-batch20-sources.json')
    raw = {q['id']: q for q in archive['questions']}
    assert intake['source_count'] == len(intake['sources']) == 20
    assert {source['screenshot'] for source in intake['sources']} == set(SOURCE_MAP)
    assert len(set(SOURCE_MAP.values())) == len(AFFECTED_IDS) == 19
    for source in intake['sources']:
        number = source['screenshot']
        ident = f'PREP-{SOURCE_MAP[number]:03d}'
        path = f'sources/2026-10-31-batch20-{number:02d}.png'
        assert source['archive_paths'] == [path] and source['question_ids'] == [ident]
        assert source['sha256'] == SOURCE_SHA256[number]
        assert hashlib.sha256((BANK / path).read_bytes()).hexdigest() == SOURCE_SHA256[number]
        assert source['original_prompt'].strip()
        assert set(source['source_tags']) == SOURCE_TAGS[number]
        companies = {COMPANY_NAMES[tag] for tag in SOURCE_TAGS[number] if tag in COMPANY_NAMES}
        assert set(source['reported_companies']) == companies
        question = raw[ident]
        assert any(item.get('path') == path for item in question['sources'])
        assert SOURCE_TAGS[number] <= set(question['source_tags'])
        assert companies <= set(question['reported_companies'])
        expected = ('new_manual_question' if ident in NEW_IDS else 'existing_question_source_and_variant'
                    if ident in VARIANT_IDS else 'additional_source_existing_question')
        assert source['decision'] == expected
    incomplete = next(source for source in intake['sources'] if source['screenshot'] == 14)
    authorization = incomplete['editorial_completion_authorization']
    assert authorization['user_text'] == 'האמת שלא כתוב אבל תשלים לבד את השאלה כמו שנראה לך'
    assert 'not recovered from the screenshot' in authorization['added_contract']
    assert incomplete['original_prompt'].endswith('אם A')


def test_all_208_previous_records_and_1141_assets_remain_hash_bound(archive):
    assert len(archive['questions']) == archive['question_count'] == 219
    raw = {q['id']: q for q in archive['questions']}
    assert raw.keys() - BATCH20_BASELINE['records'].keys() == NEW_IDS
    assert len(BATCH20_BASELINE['records']) == 208
    assert BATCH20_BASELINE['canonical_sha256'] == 'ee6a131ca1b39ad067b768017fd69296607a0b5548b1a54420b145139c3e27a7'
    assert_pre_batch20_archive(archive)
    for ident in VARIANT_IDS:
        assert raw[ident]['key'] == before_batch20_record(raw[ident])['key'], ident
    for ident in SOURCE_ONLY_IDS:
        current, previous = raw[ident], before_batch20_record(raw[ident])
        assert current['version'] == previous['version']
        assert current['translations'] == previous['translations']
        assert current.get('prepared_hints') == previous.get('prepared_hints')
    assert_pre_batch20_assets(read(SEEDS / 'preparation_uploads.json')['files'])
    localization = {}
    for path in sorted((SEEDS / 'preparation_localization').glob('*.json')):
        entries = read(path)
        assert not entries.keys() & localization.keys()
        localization.update(entries)
    assert localization.keys() == raw.keys()
    assert localization.keys() - BATCH20_BASELINE['localized_material'].keys() == NEW_IDS
    assert_pre_batch20_localization(localization)
    compiled = read(SEEDS / 'questions/preparation_bank.json')
    assert len(compiled) == 219
    for question in compiled:
        if question['assets']['preparation_id'] not in AFFECTED_IDS:
            assert digest(question) == BATCH20_BASELINE['compiled_sha256'][question['key']]
        if question['assets']['preparation_id'] in VARIANT_IDS:
            ident = question['assets']['preparation_id']
            for language in ('he', 'en'):
                text = question['translations'][language]
                frozen = BATCH20_BASELINE['compiled_variant_prefixes'][ident][language]
                for field in ('prompt', 'reference_solution'):
                    prefix = frozen[field]
                    assert len(text[field]) > prefix['length'], (ident, language, field)
                    assert digest(text[field][:prefix['length']]) == prefix['sha256'], (ident, language, field)
                hint_prefix = frozen['hints']
                assert len(text['hints']) >= hint_prefix['length']
                restored_hints = [hint[:shape['length']] for hint, shape in
                                  zip(text['hints'], hint_prefix['items'], strict=True)]
                assert digest(restored_hints) == hint_prefix['sha256'], (ident, language, 'hints')


def test_all_nineteen_questions_are_bilingual_and_eleven_new_records_are_unrated_pending(catalog, archive):
    questions = selected(catalog)
    raw = {q['id']: q for q in archive['questions']}
    assert len(catalog.questions) == 249 and set(questions) == AFFECTED_IDS
    for ident, question in questions.items():
        source = raw[ident]
        resource = question.assets['preparation_resource']
        material = resource['learner_material']
        assert material.keys() >= MATERIAL_FIELDS
        for field, pair in material.items():
            assert set(pair) == {'he', 'en'} and all(pair[lang] not in (None, '', [], {}) for lang in ('he', 'en'))
            assert no_hebrew(pair['en']), (ident, field)
        assert question.status == 'trial' and not question.assets['assessment_ready']
        assert question.assets['difficulty_status'] == 'unrated'
        if ident in NEW_IDS | VARIANT_IDS:
            assert source['status'] == 'in_review' and source['solution_status'] == 'proposed'
            assert source['ai_assisted'] and source['reviewed_by'] is None
            assert question.reuse_status == 'pending_review'
            assert solution_review(question).status == 'pending_review'
        if ident in NEW_IDS:
            assert source['difficulty'] is source['estimated_minutes'] is None
            assert source['follow_up_integration_status'] == 'prepared_in_archive_not_connected_to_interactive_queue'
            assert (BANK / source['markdown_path']).is_file()
        for language in ('he', 'en'):
            text = question.text(language)
            assert text.prompt and text.reference_solution and len(text.hints) == len(set(text.hints)) == 3
            assert not text.parity_checked
            if language == 'en':
                assert no_hebrew([text.title, text.prompt, text.reference_solution, text.hints]), ident
            public = summary(LoadedQuestion(uuid.uuid4(), question, question.version), language)
            dumped = public.model_dump_json()
            assert public.difficulty is None and not public.assessment_ready
            assert text.reference_solution not in dumped
            assert all(item['path'] not in dumped for item in question.assets['bank_media'])
            assert not bank._servable(question, mode='deep', language=language, allow_in_review=True, require_parity=False)
    for ident in ('PREP-210', 'PREP-211'):
        assert raw[ident]['category'] == 'software'
        assert 'hardware' in raw[ident]['source_topic_tags']
        assert 'software' in raw[ident]['added_topic_tags']


def test_new_private_media_has_exact_paths_hashes_png_bytes_and_protected_code(catalog):
    uploads = read(SEEDS / 'preparation_uploads.json')['files']
    new_paths = uploads.keys() - BATCH20_BASELINE['asset_sha256'].keys()
    assert len(uploads) == 1222 and len(new_paths) == 81
    assert sum(uploads[path]['local_path'].startswith('sources/') for path in new_paths) == 20
    assert sum(uploads[path]['local_path'].startswith('diagrams/') for path in new_paths) == 32
    assert sum(uploads[path]['local_path'].startswith('solutions/') for path in new_paths) == 29
    media_by_path = {item['path']: item for q in selected(catalog).values() for item in q.assets['bank_media']}
    assert new_paths <= media_by_path.keys()
    for path in new_paths:
        item, entry = media_by_path[path], uploads[path]
        local = (BANK / entry['local_path']).resolve()
        assert question_resources.PATH.fullmatch(path)
        assert local.is_relative_to(BANK.resolve()) and local.is_file()
        content = local.read_bytes()
        assert hashlib.sha256(content).hexdigest() == item['sha256'] == entry['sha256']
        assert len(content) == entry['bytes'] and item['source_path'] == entry['local_path']
        if local.suffix == '.png':
            assert content.startswith(b'\x89PNG\r\n\x1a\n')
        if entry['local_path'].startswith('diagrams/'):
            assert item['caption'].strip() and item.get('language') in (None, 'he', 'en')
            if item.get('language') == 'en':
                assert no_hebrew(item['caption'])
        if entry['local_path'].startswith('solutions/'):
            assert item['kind'] == 'file' and item['role'] == 'solution'
    questions = selected(catalog)
    header = next(item for item in questions['PREP-212'].assets['bank_media'] if item['filename'].endswith('.h'))
    assert header['source_path'] == 'solutions/prep_212_linked_list_adt.h'
    assert header['kind'] == 'file' and header['role'] == 'solution'
    for ident in {'PREP-036', *(f'PREP-{number}' for number in range(216, 221))}:
        files = {item['filename']: item for item in questions[ident].assets['bank_media']}
        for filename in ('prep_216_220_sequential.sv', 'prep_216_220_sequential_tb.sv'):
            assert files[filename]['kind'] == 'file' and files[filename]['role'] == 'solution'
    sources = [entry['local_path'] for entry in uploads.values() if entry['local_path'].startswith('sources/')]
    assert len(sources) == 352 and len(set(sources)) == 351
    assert set(read(ROOT / 'apps/web/src/lib/source-screenshots.json')) == {Path(path).name for path in sources}


def test_critical_contracts_keep_source_order_minimum_width_and_authorized_completion(catalog):
    questions = selected(catalog)
    triples = questions['PREP-210'].text('en')
    assert all(value in triples.prompt for value in ('255', '253', '85', 'not necessarily sorted'))
    assert 'globally unique' in triples.reference_solution and '2n−1' in triples.reference_solution
    mode = questions['PREP-211'].text('en')
    assert 'distinct' in mode.prompt and 'smallest' in mode.prompt and 'None' in mode.prompt
    assert 'not a general mode algorithm' in mode.reference_solution
    adder = questions['PREP-215'].text('en').reference_solution
    assert '**5 bits**' in adder and '4 ns' in adder and '2 ns' in adder and '0 ns' in adder
    assert 'not 6' in adder and 'unrestricted model' in adder
    mux = questions['PREP-214'].text('en').reference_solution
    assert all(row in mux for row in ('|0|0|Q3|', '|0|1|Q2|', '|1|0|Q1|', '|1|1|Q0|'))
    comparator = questions['PREP-110'].text('en')
    assert 'editorial completion' in comparator.prompt and 'not a verified reconstruction' in comparator.prompt
    assert 'g[-1]=0' in comparator.reference_solution and 'g[i]=MUX' in comparator.reference_solution
    assert 'X=A AND NOT B' in comparator.reference_solution and 'Y=NOT A AND B' in comparator.reference_solution
    timing = questions['PREP-107'].text('en').reference_solution
    assert '20 ns' in timing and '7 ns' in timing and '10 ns' in timing
    msb = questions['PREP-036'].text('en')
    assert 'N+b·2^k' in msb.prompt and 'old bits do not shift left' in msb.prompt
    assert "s'=2(s+b)" in msb.reference_solution
    assert 'SAME divisibility flag' in msb.reference_solution


async def test_nineteen_resources_require_owned_reveal_and_preserve_language_hints_and_privacy(catalog, monkeypatch):
    signed = []

    async def fake_sign(media, *_):
        assert all(not item['source_path'].startswith('sources/') for item in media)
        signed.append(media)
        return []

    monkeypatch.setattr(question_resources, 'sign_media', fake_sign)
    store = InMemoryStore(catalog)
    service = PracticeService(store, catalog, scripted([]), ServiceConfig())
    owner, stranger = uuid.uuid4(), uuid.uuid4()
    for ident, question in selected(catalog).items():
        started = await service.start(owner, question_key=question.key, mode='deep', language='he')
        attempt_id = uuid.UUID(started.id)
        for language in ('he', 'en'):
            hidden = await service.question_resources(owner, question.key, attempt_id=attempt_id, language=language)
            assert hidden.reference is None and hidden.technical_material is None and not hidden.solution_revealed
            assert all(item['role'] == 'prompt' for item in signed[-1])
        for level in range(1, 4):
            hint, view = await service.next_hint(owner, attempt_id)
            assert hint.level == level and hint.text == question.text('he').hints[level - 1]
            assert len(view.hints) == level and view.hints_remaining == 3 - level
        with pytest.raises(ApiError) as denied:
            await service.question_resources(stranger, question.key, attempt_id=attempt_id)
        assert denied.value.code == 'not_found'
        await service.reveal_reference(owner, attempt_id)
        for language in ('he', 'en'):
            shown = await service.question_resources(owner, question.key, attempt_id=attempt_id, language=language)
            assert shown.solution_revealed and shown.reference == question.text(language).reference_solution
            assert shown.technical_material['id'] == ident
            assert shown.solution_review.status == solution_review(question).status
            assert signed[-1] == question_resources.learner_media(question.assets['bank_media'], language)
            assert all(item.get('language') in (None, language) for item in signed[-1])
        assert store.attempts[attempt_id]['row']['practice_language'] == 'he'
        assert [hint.text for hint in (await service.get(owner, attempt_id)).hints] == question.text('he').hints
    assert not store.metrics


async def test_new_question_feedback_cannot_create_assessment_metrics_or_xp(catalog):
    store = InMemoryStore(catalog)
    provider = scripted([GOOD] * len(NEW_IDS))

    async def images(_):
        return [('image/png', b'offline source fixture')]

    service = PracticeService(store, catalog, provider, ServiceConfig(), question_image_fetcher=images)
    user = uuid.uuid4()
    before = copy.deepcopy(store.profiles)
    for ident, question in selected(catalog).items():
        if ident not in NEW_IDS:
            continue
        started = await service.start(user, question_key=question.key, mode='deep', language='en')
        result, view = await service.submit(user, uuid.UUID(started.id), 'Offline proposed reasoning for content review.',
                                            idempotency_key=ident)
        assert result.status == 'done' and 'content_review_pending' in result.flags
        assert result.xp_earned == 0 and result.next_question is None and view.pending_follow_up is None
    assert store.profiles == before and not store.metrics


def test_short_cards_quiz_and_review_attestations_are_frozen():
    assert digest(read(SEEDS / 'fundamentals_catalog.json')) == BATCH20_BASELINE['fundamentals_sha256']
    assert digest(read(SEEDS / 'duel_quiz.json')) == BATCH20_BASELINE['quiz_sha256']
    assert digest(read(SEEDS / 'solution_review_attestations.json')) == BATCH20_BASELINE['review_registry_sha256']
    content = ROOT / 'apps/web/src/content'
    cards = []
    for name, expected in BATCH21_BASELINE['short_card_source_sha256'].items():
        rows = read(content / name)
        assert digest(rows) == expected
        cards.extend(rows)
    assert len(cards) == len({row['id'] for row in cards}) == 400
    registry = read(SEEDS / 'fundamentals_catalog.json')
    assert read(content / 'fundamentals-revisions.json') == registry['questions']
    quiz = read(SEEDS / 'duel_quiz.json')['questions']
    assert len(quiz) == 2040 and sum(row['status'] == 'approved' for row in quiz) == 2000
