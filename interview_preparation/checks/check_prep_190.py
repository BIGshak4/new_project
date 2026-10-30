"""Reproduce the exact proposed-solution model check."""

import json

from batch110_reasoning_checks import check_190, run

verify = check_190

if __name__ == "__main__":
    print(json.dumps(run("190"), indent=2))
