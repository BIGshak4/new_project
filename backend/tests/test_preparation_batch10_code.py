"""Independent geometric certificate and pixel-level oracles for PREP-108/111."""
from __future__ import annotations

import importlib.util
import itertools
import random
from pathlib import Path

import pytest

BANK = Path(__file__).resolve().parents[2] / "interview_preparation"


def load(name):
    spec = importlib.util.spec_from_file_location(name, BANK / "solutions" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLYGON = load("prep_108_convex_polygon")
BITMAP = load("prep_111_horizontal_bitmap_line")


def convex_certificate(vertices, strict=False):
    """Global half-plane certificate, not the implementation's local turn test."""
    if len(vertices) < 3 or len(set(vertices)) != len(vertices):
        return False
    area = sum(a[0] * b[1] - a[1] * b[0]
               for a, b in zip(vertices, vertices[1:] + vertices[:1], strict=True))
    if area == 0:
        return False
    direction = 1 if area > 0 else -1
    for i in range(len(vertices)):
        a, b = vertices[i], vertices[(i + 1) % len(vertices)]
        for j, point in enumerate(vertices):
            if j in (i, (i + 1) % len(vertices)):
                continue
            side = direction * ((b[0] - a[0]) * (point[1] - a[1])
                                - (b[1] - a[1]) * (point[0] - a[0]))
            if side < 0 or (strict and side == 0):
                return False
    return True


def check_convex_cases():
    grid = tuple(itertools.product(range(3), range(2)))
    checked = 0
    for size in range(3, 7):
        for vertices in itertools.permutations(grid, size):
            for strict in (False, True):
                expected = convex_certificate(vertices, strict)
                assert POLYGON.is_convex_polygon(vertices, strict=strict) == expected
                if POLYGON.is_simple_polygon(vertices):
                    assert POLYGON.is_convex_simple_polygon(vertices, strict=strict) == expected
                checked += 1
    star_outer = [(0, 3), (3, 1), (2, -3), (-2, -3), (-3, 1)]
    star = [star_outer[i] for i in (0, 2, 4, 1, 3)]
    assert POLYGON.is_convex_simple_polygon(star)
    assert not POLYGON.is_simple_polygon(star)
    assert not POLYGON.is_convex_polygon(star)
    collinear = [(0, 0), (1, 0), (2, 0), (2, 2), (0, 2)]
    assert POLYGON.is_convex_polygon(collinear)
    assert not POLYGON.is_convex_polygon(collinear, strict=True)
    for vertices in ([], [(0, 0)], [(0, 0), (1, 1)], [(0, 0)] * 3,
                     [(0, 0), (1, 0), (2, 0)], [(0, 0), (2, 2), (0, 2), (2, 0)]):
        assert not POLYGON.is_convex_polygon(vertices)
    offset = 10**100
    shifted = [(x + offset, y - offset) for x, y in collinear]
    assert POLYGON.is_convex_polygon(shifted)
    assert POLYGON.is_convex_polygon(tuple(reversed(shifted)))
    return checked


def pixel_oracle(buffer, pitch, x, y, length):
    result = bytearray(buffer)
    # Decode individual bits arithmetically; no endpoint byte masks.
    for column in range(x, x + length):
        index = y * pitch + column // 8
        weight = 2 ** (7 - column % 8)
        if (result[index] // weight) % 2 == 0:
            result[index] += weight
    return result


def check_bitmap_cases():
    checked = 0
    for width in range(1, 18):
        for extra_pitch in (0, 1):
            pitch = (width + 7) // 8 + extra_pitch
            for pattern in (0, 255, 0xAA, 0x55):
                for y in range(2):
                    for x in range(width + 1):
                        for length in range(width - x + 1):
                            initial = bytearray([pattern] * (2 * pitch + 3))
                            screen = BITMAP.MonoScreen(initial, width, 2, pitch)
                            assert screen.buffer is initial
                            expected = pixel_oracle(initial, pitch, x, y, length)
                            screen.draw_horizontal(x, y, length)
                            assert initial == expected
                            screen.draw_horizontal(x, y, length)
                            assert initial == expected  # Setting is idempotent, not XOR.
                            checked += 1
    rng = random.Random(111)
    for _ in range(500):
        width, height = rng.randrange(1, 101), rng.randrange(1, 8)
        pitch = (width + 7) // 8 + rng.randrange(4)
        buffer = bytearray(rng.randrange(256) for _ in range(pitch * height + 5))
        x, y = rng.randrange(width + 1), rng.randrange(height)
        length = rng.randrange(width - x + 1)
        expected = pixel_oracle(buffer, pitch, x, y, length)
        BITMAP.MonoScreen(buffer, width, height, pitch).draw_horizontal(x, y, length)
        assert buffer == expected
    buffer = bytearray([0xA5] * 12)
    screen = BITMAP.MonoScreen(buffer, 9, 3, 3)
    for arguments in ((-1, 0, 1), (0, -1, 1), (0, 3, 1), (10, 0, 0),
                      (8, 0, 2), (0, 0, -1), (True, 0, 1), (0, 0, 1.5)):
        before = bytearray(buffer)
        with pytest.raises(ValueError):
            screen.draw_horizontal(*arguments)
        assert buffer == before
    for width, height, pitch, length in ((0, 1, 1, 1), (8, 0, 1, 1), (9, 1, 1, 2), (9, 2, 2, 3)):
        with pytest.raises(ValueError):
            BITMAP.MonoScreen(bytearray(length), width, height, pitch)
    return checked


def test_convexity_against_global_half_planes_including_star_and_collinear_cases():
    assert check_convex_cases() == 3840


def test_horizontal_line_against_pixel_oracle_preserves_every_outside_bit():
    assert check_bitmap_cases() == 18224
