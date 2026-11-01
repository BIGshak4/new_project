"""Reproduce the finite logical checks for one intake record."""
import json
from pathlib import Path

from check_batch1101_hardware import CHECKS

if __name__ == '__main__':
    result = CHECKS[233]()
    Path(__file__).with_name('prep-233-verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
