"""Run finite independent oracles and the actual Icarus HDL simulation."""
from pathlib import Path
from itertools import product
import hashlib,json,os,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]
BIN=Path('C:/Projects/Job_Run/.checks/intake-nov15b/iverilog/ucrt64/bin')
env=dict(os.environ);env['PATH']=str(BIN)+os.pathsep+env.get('PATH','')
def pe4(x):return bool(x),(((x>>3)|(x>>2))&1)*2+(((x>>3)&1)|((1-((x>>2)&1))&((x>>1)&1)))
def pe16(x):
    local=[pe4((x>>(4*g))&15) for g in range(4)]
    valid,group=pe4(sum(int(v)<<(g) for g,(v,c) in enumerate(local)))
    return valid,(4*group+local[group][1]) if valid else 0
def mux(s,a,b):return b if s else a
def compare(a,b):
    low=mux(a&1,0,mux(b&1,1,0))
    return mux(a>>1,mux(b>>1,low,0),mux(b>>1,1,low))
for x in range(65536):assert pe16(x)==(bool(x),max([i for i in range(16) if x&(1<<i)],default=0))
for a,b in product(range(4),repeat=2):assert compare(a,b)==(a>b)
mean_checks=0
for width in range(1,13):
    for a in range(1<<width):
        b=a+2;s=a&1;extended_a=a
        y=(1-s)|(((b>>1) if s else (extended_a>>1))<<1)
        assert y==(a+b)//2
        carry,low=b>>width,b&((1<<width)-1)
        assert (carry<<width)|low==b
        mean_checks+=1
# Each omitted vector has a single-minterm mutant escaping all remaining tests.
vectors=list(product(range(4),repeat=2))
for omitted in vectors:
    def faulty(a,b):return (not (a>b)) if (a,b)==omitted else a>b
    assert all(faulty(a,b)==(a>b) for a,b in vectors if (a,b)!=omitted)
    assert faulty(*omitted)!=(omitted[0]>omitted[1])
paths=[ROOT/'solutions'/p for p in ['prep_349_priority_encoder_1115b.sv','prep_350_programmable_shift_1115b.sv','prep_110_mux_comparator_1115b.sv','prep_058_full_carry_mean_1115b.sv','prep_044_source_fibonacci_1115b.sv']]+[ROOT/'checks/digital1115b_tb.sv']
with tempfile.TemporaryDirectory(prefix='jobrun-digital1115b-') as tmp:
    exe=Path(tmp)/'simulation.vvp'
    compile_result=subprocess.run([str(BIN/'iverilog.exe'),'-g2012','-s','digital1115b_tb','-o',str(exe),*[str(p) for p in paths]],env=env,capture_output=True,text=True)
    if compile_result.returncode:raise RuntimeError(compile_result.stderr)
    result=subprocess.run([str(BIN/'vvp.exe'),str(exe)],env=env,capture_output=True,text=True,timeout=30)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    assert 'PASS pe=65536' in result.stdout
proof=dict(result='passed',python_highest_bit_inputs=65536,python_comparator_inputs=16,python_full_carry_means=mean_checks,omitted_vector_counterexamples=16,native_simulator='Icarus Verilog 13.0 MSYS2 ucrt64',native_exit_code=result.returncode,native_stdout=result.stdout.strip(),native_source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Actual compiled SystemVerilog event simulation plus independent Python models; no physical synthesis or signoff.')
(ROOT/'checks/digital1115b-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(proof,ensure_ascii=False))
