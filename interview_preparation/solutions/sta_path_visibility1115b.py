"""Evidence-based toy path visibility, separate from licensed STA tools."""


def explain_visibility(evidence):
    """Evidence booleans describe one selected scenario/check and explicit path."""
    required = (
        "same_design", "start_exists", "end_exists", "physical_route",
        "clocked", "exception_cut", "arc_disabled", "constant_cut",
        "reported",
    )
    if set(evidence) != set(required) or any(type(v) is not bool for v in evidence.values()):
        raise ValueError("all nine explicit boolean observations are required")
    causes = []
    if not evidence["same_design"]:
        causes.append("different_design")
    if not evidence["start_exists"] or not evidence["end_exists"]:
        causes.append("missing_object")
    if not evidence["physical_route"]:
        causes.append("no_data_route")
    if not evidence["clocked"]:
        causes.append("unconstrained_clock_or_io")
    if evidence["exception_cut"]:
        causes.append("timing_exception")
    if evidence["arc_disabled"]:
        causes.append("disabled_timing_arc")
    if evidence["constant_cut"]:
        causes.append("case_or_constant_propagation")
    if not causes and not evidence["reported"]:
        causes.append("report_query_or_coverage")
    return causes
