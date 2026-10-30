"""Executed logical model check; not HDL compilation."""
import json
from pathlib import Path

from batch90_hardware_checks import CHECKS

if __name__ == "__main__":
    result=CHECKS['181']()
    target=Path(__file__).with_name('prep-181-verification.json')
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
