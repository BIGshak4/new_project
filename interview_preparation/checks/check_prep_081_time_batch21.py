"""Reproduce the exact proposed-solution model check."""

import json

from batch21_reasoning_checks import check081, run

verify = check081

if __name__ == "__main__":
    print(json.dumps(run("081-time-batch21"), indent=2))
