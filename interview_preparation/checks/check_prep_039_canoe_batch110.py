"""Reproduce the exact proposed-solution model check."""

import json

from batch110_reasoning_checks import check_039_canoe, run

verify = check_039_canoe

if __name__ == "__main__":
    print(json.dumps(run("039-canoe-batch110"), indent=2))
