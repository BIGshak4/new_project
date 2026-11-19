"""Independent finite tables, analytic delay bounds and actual RTL execution."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]
model_path=ROOT/"solutions/hardware1115c_models.py"
spec=importlib.util.spec_from_file_location("hardware1115c_models",model_path)
model=importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


def reference_parking(n,e,x,rst):
    if rst or n>50:
        return 0,False,False
    if n==0:
        return (1 if e else 0),e,False
    if n==50:
        if not x:
            return 50,False,False
        return (50 if e else 49),e,True
    if e and x:
        return n,True,True
    if e:
        return n+1,True,False
    if x:
        return n-1,False,True
    return n,False,False


def main():
    parking_cases=0
    for reset in (False,True):
        for n in range(64):
            for e in (False,True):
                for x in (False,True):
                    assert model.parking_step(n,e,x,reset)==reference_parking(n,e,x,reset)
                    parking_cases+=1
    decode_cases=0
    for n in range(64):
        b=[(n>>i)&1 for i in range(6)]
        decoded=b[5]&b[4]&(b[3]^1)&(b[2]^1)&b[1]&(b[0]^1)
        assert bool(decoded)==(n==50)
        decode_cases+=1
    sizing_cases=0;derivatives=0
    for a in (.25,.5,1.,2.,4.):
        for b in (.25,.5,1.,2.,4.):
            optimum=model.optimum(a,b)
            for c in (0.,1.,5.):
                lower=2*math.sqrt(a*b)+c
                assert math.isclose(model.delay(optimum,a,b,c),lower,rel_tol=1e-12)
                h=optimum*1e-5
                derivative=(model.delay(optimum+h,a,b,c)-model.delay(optimum-h,a,b,c))/(2*h)
                assert abs(derivative)<1e-6
                derivatives+=1
                for tick in range(1,161):
                    size=tick/20
                    assert model.delay(size,a,b,c)>=lower-1e-11
                    sizing_cases+=1
    assert [model.delay(s,1,4,1) for s in (1,2,4)]==[6,5,6]
    assert model.delay(2,1,1,0)>model.delay(1,1,1,0)
    paths=[
        "solutions/prep_001_popcount7_faonly1115c.sv",
        "solutions/prep_356_parking_capacity50_1115c.sv",
        "checks/hardware1115c_tb.sv",
    ]
    binary_dir=Path(os.environ.get("IVERILOG_BIN","C:/Projects/Job_Run/.checks/intake-nov15b/iverilog/ucrt64/bin"))
    stage=Path("C:/Projects/Job_Run/.checks/intake-nov15c/hardware")
    stage.mkdir(parents=True,exist_ok=True)
    executable=stage/"hardware1115c.vvp"
    env={**os.environ,"PATH":str(binary_dir)+os.pathsep+os.environ.get("PATH","")}
    compile_result=subprocess.run([str(binary_dir/"iverilog.exe"),"-g2012","-s","hardware1115c_tb","-o",str(executable),*[str(ROOT/p) for p in paths]],capture_output=True,text=True,env=env)
    assert compile_result.returncode==0,compile_result.stderr
    run=subprocess.run([str(binary_dir/"vvp.exe"),str(executable)],capture_output=True,text=True,env=env,timeout=30)
    assert run.returncode==0 and "PASS popcount=128 parking=512" in run.stdout,(run.stdout,run.stderr)
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths+["solutions/hardware1115c_models.py"]}
    proof={
        "result":"passed",
        "python_parking_cases":parking_cases,
        "exact_fifty_decode_states":decode_cases,
        "sizing_sweep_points":sizing_cases,
        "sizing_stationary_derivatives":derivatives,
        "native_simulator":"Icarus Verilog 13.0, MSYS2 ucrt64 portable package",
        "native_compile_exit_code":compile_result.returncode,
        "native_run_exit_code":run.returncode,
        "native_stdout":run.stdout.strip(),
        "native_popcount_inputs":128,
        "native_parking_cases":512,
        "sha256":hashes,
        "scope":"Compiled two-state RTL event checks and first-order RC-model mathematics. No SPICE, synthesis or physical signoff."
    }
    output=ROOT/"checks/hardware1115c-verification.json"
    output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(proof,ensure_ascii=True))


if __name__=="__main__":
    main()
