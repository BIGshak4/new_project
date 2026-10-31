"""Reproduce the exact proposed-solution model check."""

import json

from batch21_reasoning_checks import check162, run

verify = check162

if __name__ == "__main__":
    print(json.dumps(run("162-array-batch21"), indent=2))
