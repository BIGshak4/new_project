"""Reverse the Nov 14 additions before running older frozen question checks."""
import copy
import hashlib
import json
from functools import cache
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()).hexdigest()


@cache
def projections():
    return json.loads((Path(__file__).parent / "fixtures/preparation_before_20261114.json").read_bytes())


def before_nov14(key, actual):
    record = projections().get(key)
    if record is None:
        return actual
    assert digest(actual) == record["after"], key
    restored = copy.deepcopy(actual)
    for operation, path, *values in record["edits"]:
        parent = restored
        for part in path[:-1]:
            parent = parent[part]
        field = path[-1]
        if operation == "remove":
            del parent[field]
        elif operation == "prefix":
            parent[field] = parent[field][:values[0]]
        elif operation == "media":
            by_path = {item["path"]: item for item in parent[field]}
            parent[field] = [by_path[prior] for prior in values[0]]
        else:
            assert operation == "set", operation
            parent[field] = values[0]
    assert digest(restored) == record["before"], key
    return restored

