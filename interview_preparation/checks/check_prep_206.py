"""Reproduce the exact proposed-solution model check."""

import json

from batch21_reasoning_checks import check206, run

verify = check206

if __name__ == "__main__":
    print(json.dumps(run("206"), indent=2))
