"""Compare complete, tool-adapted timing manifests; this does not invoke an STA tool."""
from math import isfinite


CONTEXT = ("netlist", "constraints", "libraries", "parasitics", "analysis")
IDENTITY = (
    "scenario", "check", "startpoint", "endpoint", "launch_clock",
    "capture_clock", "launch_edge", "capture_edge", "transition",
)
METRICS = ("arrival", "required", "slack")
UNIT_PS = {"ps": 1.0, "ns": 1000.0}


def normalized(run):
    if run.get("complete") is not True:
        raise ValueError("an exhaustive chosen-query manifest is required")
    if set(run.get("context", {})) != set(CONTEXT):
        raise ValueError("all context fingerprints are required")
    if any(not isinstance(v, str) or not v for v in run["context"].values()):
        raise ValueError("context fingerprints must be nonempty strings")
    if run.get("unit") not in UNIT_PS:
        raise ValueError("only explicit ps or ns units are supported")
    scale = UNIT_PS[run["unit"]]
    result = {}
    for row in run["paths"]:
        identity = tuple(row[name] for name in IDENTITY)
        if any(not isinstance(v, str) or not v for v in identity):
            raise ValueError("explicit nonempty path identity fields are required")
        if identity in result:
            raise ValueError("duplicate query identity")
        if row["check"] not in ("setup", "hold"):
            raise ValueError("unsupported check")
        values = {}
        for metric in METRICS:
            value = row[metric]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("numeric finite metrics required")
            value = float(value) * scale
            if not isfinite(value):
                raise ValueError("numeric finite metrics required")
            values[metric] = value
        expected_slack = (values["required"] - values["arrival"]
                          if row["check"] == "setup"
                          else values["arrival"] - values["required"])
        if abs(values["slack"] - expected_slack) > 1e-6:
            raise ValueError("inconsistent arrival/required/slack convention")
        result[identity] = values
    return result


def compare_runs(reference, candidate, tolerance_ps=10.0):
    if (isinstance(tolerance_ps, bool) or not isinstance(tolerance_ps, (int, float))
            or not isfinite(tolerance_ps) or tolerance_ps < 0):
        raise ValueError("nonnegative finite tolerance required")
    left, right = normalized(reference), normalized(candidate)
    if reference["context"] != candidate["context"]:
        raise ValueError("the frozen comparison context differs")
    missing, added = sorted(left.keys() - right.keys()), sorted(right.keys() - left.keys())
    changed, sign_changed = [], []
    for identity in sorted(left.keys() & right.keys()):
        for metric in METRICS:
            difference = right[identity][metric] - left[identity][metric]
            if abs(difference) > tolerance_ps:
                changed.append({"identity": identity, "metric": metric,
                                "delta_ps": difference})
        if (left[identity]["slack"] < 0) != (right[identity]["slack"] < 0):
            sign_changed.append(identity)
    return {"passed": not (missing or added or changed or sign_changed),
            "missing": missing, "added": added, "changed": changed,
            "sign_changed": sign_changed}
