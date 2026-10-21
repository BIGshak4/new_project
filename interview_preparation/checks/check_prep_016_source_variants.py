"""Independent invalid-code coverage for the 2026-10-21 source variants."""
import importlib.util
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('prep016variant', ROOT / 'solutions/prep_016_priority_variants.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def main():
    combinations = 0
    hierarchical_cases = 0
    for word in range(65536):
        expected = (int(word != 0), max(0, word.bit_length() - 1))
        inactive = [g for g in range(4) if ((word >> (4*g)) & 15) == 0]
        for values in itertools.product(range(4), repeat=len(inactive)):
            codes = [0, 0, 0, 0]
            for group, code in zip(inactive, values, strict=True):
                codes[group] = code
            assert model.hierarchy(word, codes, fifth=False) == expected
            # The upper code is invalid only for word zero. Vary it independently.
            for upper in range(4) if word == 0 else (0,):
                assert model.hierarchy(word, codes, fifth=True, upper_invalid=upper) == expected
                hierarchical_cases += 1
            combinations += 1
    assert model.pe4(0b1111) == (1, 3)
    assert model.pe4(0b0101) == (1, 2)
    assert model.hierarchy(0) == (0, 0)
    assert model.hierarchy(1) == (1, 0)
    assert model.hierarchy((1 << 2) | (1 << 6) | (1 << 13)) == (1, 13)
    report = {
        'question_id':'PREP-016', 'checked_on':'2026-10-21', 'status':'passed_python_model',
        'sixteen_bit_input_vectors':65536,
        'independently_varied_inactive_code_combinations':combinations,
        'four_local_plus_gate_model_cases':combinations,
        'five_encoder_model_cases_including_upper_invalid_codes':hierarchical_cases,
        'source_variant_examples_checked':['1111 -> valid=1,index=3','0101 -> valid=1,index=2',
                                          'all-zero -> valid=0,index=0','only bit zero -> valid=1,index=0'],
        'method':'Every input word, every independent two-bit code for each inactive local encoder; independently varied upper invalid code when globally inactive; highest-set-bit integer oracle.',
        'scope':'Python functional model only, not HDL simulation/synthesis, physical timing or professional approval. Existing identity, prompts, hints and review states are preserved.',
    }
    (ROOT / 'checks/prep-016-source-variants-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
