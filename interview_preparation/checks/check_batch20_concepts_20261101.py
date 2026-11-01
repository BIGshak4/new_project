"""Bounded runtime demonstrations and explicit document-review boundaries."""
from __future__ import annotations

import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / 'solutions' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report(number, cases, method, executed):
    return {'question_id': f'PREP-{number}', 'status': 'pass', 'cases': cases,
            'verification_kind': 'bounded_python_execution' if executed else 'primary_document_review',
            'python_executed': executed, 'c_compiled': False, 'cpp_compiled': False,
            'csharp_executed': False, 'java_executed': False, 'method': method,
            'professional_review': 'pending', 'ai_assisted': True}


def check_240():
    return report(240, 0, 'Reviewed IP/IPv6/FTP RFCs, FTP-security RFC2577 and Cisco LAN definition. '
                  'Personal responses are explicit fill-in structures, not candidate facts or market salary advice. '
                  'No network traffic, credentials, protocol implementation or individual suitability was tested.', False)


def check_241():
    return report(241, 0, 'Reviewed C storage-class documentation and C++ draft sections basic.link, '
                  'basic.stc.static, class.static and stmt.dcl. C17/C++17 listings illustrate scope, duration '
                  'and class data; no native compiler, threading behavior, ABI or physical layout was tested.', False)


def check_242():
    actual = load('prep_242_python_oop_examples').examples()
    expected = {
        'override': 'child', 'duck_without_inheritance': 'duck',
        'class_attribute_shared': ['shared'], 'instance_attribute_separate': [],
        'shadow_does_not_replace_class_attribute': ['shared'], 'mangled_name_accessible': 7,
        'annotation_not_enforced': 'text', 'incompatible_addition': 'TypeError',
        'last_definition_replaces_first': 'TypeError', 'last_definition_works': 3,
        'abstract_instantiation': 'TypeError',
        'concrete_calls_abstract_body': 'base implementation then concrete',
        'mro': ['Diamond', 'First', 'Second', 'Root', 'object'],
    }
    assert actual == expected
    assert load('prep_242_python_oop_examples').examples() == expected
    return report(242, 26, 'Two fresh executions of thirteen Python language-behavior demonstrations, '
                  'with explicit expected values/errors and MRO. Other-language comparisons are document review, '
                  'not execution, static type checking or performance measurement.', True)


def check_243():
    module = load('prep_243_abstract_class_examples')
    cases = 0
    for abstract in (module.Shape, module.StillAbstract):
        try:
            abstract()
        except TypeError:
            cases += 1
        else:
            raise AssertionError('Abstract Python class unexpectedly instantiated')
    assert module.Ordinary().area() == 0
    cases += 1
    for width, height in itertools.product(range(5), repeat=2):
        rectangle = module.Rectangle(width, height)
        assert rectangle.area() == width * height and rectangle.label() == 'shape'
        cases += 1
    return report(243, cases, 'Python ABC analogue: two abstract-instantiation failures, an instantiable ABC '
                  'with no abstract members, and twenty-five concrete rectangles inheriting an implemented method. '
                  'C++/C# claims were checked against primary documents; their snippets were not compiled.', True)


def compositions(total):
    if total == 0:
        yield ()
    else:
        for first in range(1, total + 1):
            for rest in compositions(total - first):
                yield (first, *rest)


def scheduled_distance(count, capacity, rate, removals):
    """Independent ordered batch-removal oracle, rather than harmonic summation."""
    distance, active = Fraction(0), count
    for removed in removals:
        distance += Fraction(removed * capacity, active * rate)
        active -= removed
    assert active == 0
    return distance


def check_244():
    module = load('prep_244_motorcycle_fuel_plan')
    schedules, stage_checks = 0, 0
    for capacity, rate in itertools.product((1, 7, 50), (1, 2)):
        for count in range(10):
            outcomes = [scheduled_distance(count, capacity, rate, removal) for removal in compositions(count)]
            schedules += len(outcomes)
            assert module.max_distance(count, capacity, rate) == max(outcomes)
        for count in range(101):
            distance, stages = module.plan(count, capacity, rate)
            assert distance == module.max_distance(count, capacity, rate)
            consumed = Fraction(0)
            for stage in stages:
                k, d = stage['active'], stage['distance']
                consumed += k * rate * d
                assert d > 0
                assert stage['fuel_before'] - k * rate * d == stage['fuel_after_driving']
                assert stage['fuel_after_driving'] == stage['fuel_after_transfer']
                if k > 1:
                    assert stage['donor_fuel'] == (k - 1) * rate * d
                    assert 0 <= stage['donor_fuel'] < capacity
                stage_checks += 1
            assert consumed == count * capacity
    exact, trace = module.plan()
    assert len(trace) == 100 and trace[0]['distance'] == Fraction(1, 2)
    assert trace[-1]['distance'] == 50
    assert 259.368875881980 < float(exact) < 259.368875881982
    result = report(244, schedules + stage_checks, 'Independent enumeration of all ordered batch-removal '
                    'schedules through n=9 for six capacity/consumption pairs; exact conservation and capacity '
                    'checks for n=0..100. These finite cases support the model; the general optimality claim '
                    'uses the separate written cut-capacity proof. No physical fuel/engine test.', True)
    result.update(ordered_schedules=schedules, exact_stage_checks=stage_checks,
                  distance_metres=str(exact), approximate_distance_metres=float(exact))
    return result


CHECKS = {240: check_240, 241: check_241, 242: check_242, 243: check_243, 244: check_244}


if __name__ == '__main__':
    for number, check in CHECKS.items():
        result = check()
        (BANK / 'checks' / f'prep-{number}-verification.json').write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(result['question_id'], result['verification_kind'], result['cases'], 'PASS')
