"""Reproduce the exact proposed-solution model check."""

import json

from batch21_reasoning_checks import check203, run

verify = check203

if __name__ == "__main__":
    print(json.dumps(run("203"), indent=2))
