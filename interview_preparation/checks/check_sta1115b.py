"""Independent schedules, analytic RC crossings and malformed/changed report fixtures."""
import copy
import hashlib
import itertools
import json
import math
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name):return runpy.run_path(str(ROOT/"solutions"/name))
timing=load("three_launch_timing1115b.py")["budgets"]
inverter=load("inverter_step_rc1115b.py")
regression=load("sta_normalized_regression1115b.py")
visibility=load("sta_path_visibility1115b.py")["explain_visibility"]
counts={}


def rejected(function,*args):
    try:function(*args)
    except (ValueError,KeyError,TypeError):return
    raise AssertionError("invalid input was accepted")


cases=0
for launch,capture,cq_min,cq_max,d_min,d_max,period,setup,hold in itertools.product(
        (-.2,0,.3),(-.1,0,.4),(.02,.08),(.1,.2),(.01,.12),(.6,1.4),(1,2),(.05,.15),(.03,.1)):
    path=(launch,cq_min,cq_max,d_min,d_max)
    result=timing(period,capture,setup,hold,[path,path,path])
    latest=launch+cq_max+d_max
    earliest=launch+cq_min+d_min
    for row in result:
        assert math.isclose(row["setup"],(period+capture-setup)-latest,abs_tol=1e-12)
        assert math.isclose(row["hold"],earliest-(capture+hold),abs_tol=1e-12)
    slower=timing(period+.1,capture,setup,hold,[path]*3)[0]
    assert math.isclose(slower["hold"],result[0]["hold"],abs_tol=1e-12)
    assert math.isclose(slower["setup"]-result[0]["setup"],.1,abs_tol=1e-12)
    delayed=(launch,cq_min,cq_max,d_min+.1,d_max+.1)
    after=timing(period,capture,setup,hold,[delayed]*3)[0]
    assert math.isclose(after["hold"]-result[0]["hold"],.1,abs_tol=1e-12)
    assert math.isclose(after["setup"]-result[0]["setup"],-.1,abs_tol=1e-12)
    cases+=1
example=timing(2,.10,.15,.10,[(0,.05,.1,.05,1.4),(.1,.05,.1,.08,1.3),(-.05,.05,.1,.1,1.6)])
assert [round(r["setup"],2) for r in example]==[.45,.45,.30]
assert [round(r["hold"],2) for r in example]==[-.10,.03,-.10]
counts["absolute_schedule_parameter_cases"]=cases

values=[inverter["falling_output"](i/1000) for i in range(6001)]
assert values[0]==1 and values[200]==1
assert all(a>=b>=0 for a,b in zip(values,values[1:]))
for ratio in (.9,.5,.1):
    crossing=inverter["threshold_crossing"](ratio)
    assert math.isclose(inverter["falling_output"](crossing),ratio,abs_tol=1e-12)
assert math.isclose(inverter["threshold_crossing"](.1)-inverter["threshold_crossing"](.9),.5*math.log(9),abs_tol=1e-12)
for i in range(1,101):
    t=.2+i*.01;h=1e-5
    derivative=(inverter["falling_output"](t+h)-inverter["falling_output"](t-h))/(2*h)
    assert math.isclose(derivative,-inverter["falling_output"](t)/.5,rel_tol=1e-7)
rejected(inverter["falling_output"],1,0,0)
counts["rc_curve_samples"]=len(values)
counts["rc_derivative_checks"]=100
counts["rc_threshold_crossings"]=3

fields=("same_design","start_exists","end_exists","physical_route","clocked",
        "exception_cut","arc_disabled","constant_cut","reported")
healthy=dict(zip(fields,(True,True,True,True,True,False,False,False,True)))
assert visibility(healthy)==[]
single={
    "same_design":"different_design","start_exists":"missing_object","end_exists":"missing_object",
    "physical_route":"no_data_route","clocked":"unconstrained_clock_or_io",
    "exception_cut":"timing_exception","arc_disabled":"disabled_timing_arc",
    "constant_cut":"case_or_constant_propagation","reported":"report_query_or_coverage",
}
for field,expected in single.items():
    evidence=healthy|{field:not healthy[field]}
    assert visibility(evidence)==[expected]
for bits in itertools.product((False,True),repeat=9):
    evidence=dict(zip(fields,bits))
    causes=visibility(evidence)
    assert len(causes)==len(set(causes))
    assert bool(causes)==(evidence!=healthy)
    if "report_query_or_coverage" in causes:assert causes==["report_query_or_coverage"]
counts["visibility_observation_vectors"]=512
counts["visibility_single_cause_checks"]=9

def report(check="setup",unit="ps"):
    row=dict(scenario="slow",check=check,startpoint="R0/Q",endpoint="C/D",
             launch_clock="clk",capture_clock="clk",launch_edge="rise_0",
             capture_edge="rise_1" if check=="setup" else "rise_0",transition="rise",
             arrival=1000.0,required=1100.0,slack=100.0 if check=="setup" else -100.0)
    return dict(complete=True,context={k:"frozen-"+k for k in regression["CONTEXT"]},
                unit=unit,paths=[row])

compare=regression["compare_runs"]
checks=0
for check in ("setup","hold"):
    base=report(check)
    assert compare(base,copy.deepcopy(base))["passed"];checks+=1
    ns=copy.deepcopy(base);ns["unit"]="ns"
    for key in regression["METRICS"]:ns["paths"][0][key]/=1000
    assert compare(base,ns)["passed"];checks+=1
    shifted=copy.deepcopy(base)
    shifted["paths"][0]["arrival"]+=20;shifted["paths"][0]["required"]+=20
    delta=compare(base,shifted)
    assert not delta["passed"] and len(delta["changed"])==2;checks+=1
    boundary=copy.deepcopy(base)
    boundary["paths"][0]["arrival"]+=10
    boundary["paths"][0]["slack"]+=-10 if check=="setup" else 10
    assert compare(base,boundary)["passed"];checks+=1
    excessive=copy.deepcopy(boundary)
    excessive["paths"][0]["arrival"]+=.001
    excessive["paths"][0]["slack"]+=-.001 if check=="setup" else .001
    assert not compare(base,excessive)["passed"];checks+=1
    near=copy.deepcopy(base)
    near["paths"][0]["arrival"]=1000
    near["paths"][0]["required"]=1000.001
    near["paths"][0]["slack"]=.001 if check=="setup" else -.001
    other=copy.deepcopy(near)
    other["paths"][0]["required"]=999.999
    other["paths"][0]["slack"]=-.001 if check=="setup" else .001
    assert compare(near,other)["sign_changed"];checks+=1
    empty=copy.deepcopy(base);empty["paths"]=[]
    assert compare(base,empty)["missing"] and compare(empty,base)["added"];checks+=1
    duplicate=copy.deepcopy(base);duplicate["paths"].append(copy.deepcopy(duplicate["paths"][0]))
    rejected(compare,base,duplicate);checks+=1
    invalid=copy.deepcopy(base);invalid["paths"][0]["arrival"]=float("nan")
    rejected(compare,base,invalid);checks+=1
    inconsistent=copy.deepcopy(base);inconsistent["paths"][0]["slack"]+=1
    rejected(compare,base,inconsistent);checks+=1
    incomplete=copy.deepcopy(base);incomplete["complete"]=False
    rejected(compare,base,incomplete);checks+=1
    changed_context=copy.deepcopy(base);changed_context["context"]["libraries"]="different"
    rejected(compare,base,changed_context);checks+=1
    second=copy.deepcopy(base);second["paths"].append(dict(second["paths"][0],endpoint="D/D"))
    reversed_rows=copy.deepcopy(second);reversed_rows["paths"].reverse()
    assert compare(second,reversed_rows)["passed"];checks+=1
counts["normalized_report_regression_checks"]=checks
proof=dict(passed=True,counts=counts,scope="Synthetic normalized reports, absolute-schedule arithmetic, an ideal first-order RC model and explicit evidence fixtures. No licensed STA execution or SPICE.",
           sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (ROOT/"solutions").glob("*1115b.py") if p.name in
                   ("sta_normalized_regression1115b.py","sta_path_visibility1115b.py",
                    "three_launch_timing1115b.py","inverter_step_rc1115b.py")})
(ROOT/"checks/sta1115b-verification.json").write_text(json.dumps(proof,indent=2)+"\n",encoding="utf8")
print(json.dumps(proof["counts"]))
