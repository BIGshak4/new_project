"""Exhaust stable address maps and inject data/read-path faults independently."""
import itertools
import json
import random
import sys
from pathlib import Path

BANK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BANK / "solutions"))
from prep_076_address_alias import test_address_aliases


class Memory:
    def __init__(self, mapping, width, read_map=None, stuck=None):
        self.mapping = mapping
        self.read_map = mapping if read_map is None else read_map
        self.cells = [0] * len(mapping)
        self.stuck = stuck
        self.operations = 0

    def read(self, address):
        self.operations += 1
        value = self.cells[self.read_map[address]]
        if self.stuck and self.read_map[address] == self.stuck[0]:
            _, bit, force = self.stuck
            value = (value & ~(1 << bit)) | (force << bit)
        return value

    def write(self, address, value):
        self.operations += 1
        self.cells[self.mapping[address]] = value


def main():
    maps = permutations = read_faults = data_faults = random_cases = 0
    for size in range(1, 6):
        for mapping in itertools.product(range(size), repeat=size):
            for width in (1, 3):
                m = Memory(mapping, width)
                passed = test_address_aliases(m.read, m.write, size, width)
                # Independent oracle: stable same-path alias-free iff injective.
                assert passed == (len(set(mapping)) == size)
                maps += 1
        for permutation in itertools.permutations(range(size)):
            m = Memory(permutation, 2)
            assert test_address_aliases(m.read, m.write, size, 2)
            permutations += 1
            m = Memory(tuple(range(size)), 2, read_map=permutation)
            assert test_address_aliases(m.read, m.write, size, 2) == (tuple(range(size)) == permutation)
            read_faults += 1
        for width in range(1, 5):
            for cell, bit, force in itertools.product(range(size), range(width), range(2)):
                m = Memory(tuple(range(size)), width, stuck=(cell, bit, force))
                assert not test_address_aliases(m.read, m.write, size, width)
                data_faults += 1

    rng = random.Random(76021)
    for size in (7, 16, 31, 64):
        for width in (1, 2, 8, 16):
            for _ in range(40):
                mapping = [rng.randrange(size) for _ in range(size)]
                m = Memory(mapping, width)
                assert test_address_aliases(m.read, m.write, size, width) == (len(set(mapping)) == size)
                random_cases += 1
            m = Memory(list(range(size)), width)
            assert test_address_aliases(m.read, m.write, size, width)
            assert m.operations == 4 * size * max(1, (size - 1).bit_length())

    # Immediate write/read incorrectly accepts two logical addresses mapped to one.
    alias = Memory([0, 0], 8)
    for address in range(2):
        alias.write(address, address)
        assert alias.read(address) == address
    assert not test_address_aliases(alias.read, alias.write, 2, 8)
    invalid = 0
    for size, width in ((0, 1), (-1, 1), (1, 0), (1, -1), (True, 1), (1, True)):
        try:
            test_address_aliases(lambda _: 0, lambda *_: None, size, width)
        except ValueError:
            invalid += 1
        else:
            raise AssertionError("bad parameters accepted")
    result = {"question_id": "PREP-076", "status": "passed", "exhaustive_map_width_cases": maps,
              "consistent_physical_permutations_passed": permutations,
              "read_path_permutations_checked": read_faults, "stuck_data_cases": data_faults,
              "seeded_random_map_width_cases": random_cases, "invalid_parameters": invalid,
              "write_then_immediate_read_counterexample": "alias [0,0] passes naive check, fails bit-plane test",
              "scope": "Stable pure logical address mappings and sampled stuck-data faults; no physical, retention or timing verification."}
    (BANK / "checks/prep-076-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
