"""Independent finite checks plus native Icarus compile/simulation."""
import hashlib,importlib.util,itertools,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'solutions/digital1115d.sv'
MODEL=ROOT/'solutions/digital1115d_models.py'
BENCH=Path(__file__).with_name('digital1115d_tb.sv')
REPORT=Path(__file__).with_name('digital1115d-verification.json')
spec=importlib.util.spec_from_file_location('m',MODEL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
counts={}
# Value oracle: Python's mathematical highest power of two, independent of DAG.
for x in range(256):
 y,time,arr=m.evaluate_priority_dag(x)
 assert y==(1<<(x.bit_length()-1) if x else 0)
 assert time==1 and arr['y7']==0
 # Uniform delay model is checked separately with the exact same topology.
 uniform=[(name,op,pins,0 if op=='WIRE' else 1) for name,op,pins,_ in m.priority_dag()]
 assert m.evaluate_priority_dag(x,uniform)[1]==8
counts['priority_dag_vectors']=256
counts['priority_dag_nodes']=len(m.priority_dag())
counts['priority_logic_gates']=sum(op!='WIRE' for _,op,_,_ in m.priority_dag())
counts['priority_weighted_max_tau']=1
counts['priority_uniform_same_topology_max_tau']=8
# Compare against suffix slicing of the whole history, not a transition table.
seqsamples=0
for length in range(13):
 for bits in itertools.product((0,1),repeat=length):
  state=0;history=''
  for bit in bits:
   state,hit=m.detector1010_step(state,bit);history+=str(bit)
   assert hit==int(history.endswith('1010'));seqsamples+=1
assert ''.join(str(m.detector1010_step(0,0)[1]) for _ in range(1))=='0'
state=0;example=[]
for b in '0101010001':state,hit=m.detector1010_step(state,int(b));example.append(str(hit))
assert ''.join(example)=='0000101000'
counts['sequence_model_samples']=seqsamples
# Independent last-trigger timestamp oracle; exhaustive traces and full states.
stretches=0
for n in (1,2,3,8,16):
 for bits in itertools.product((0,1),repeat=10):
  p=remaining=0;last=-1000;prior=0
  for t,bit in enumerate(bits):
   if bit and not prior:last=t
   prior=bit;p,remaining,y=m.stretch_step(p,remaining,bit,n)
   assert y==int(t-last<n);assert remaining==max(0,n-(t-last))
   stretches+=1
 for p,rem,b,rst in itertools.product((0,1),range(n+1),(0,1),(False,True)):
  np,nr,y=m.stretch_step(p,rem,b,n,rst)
  oracle=0 if rst else(n if b and not p else(rem-1 if rem else 0))
  assert (np,nr,y)==(0 if rst else b,oracle,int(oracle>0));stretches+=1
counts['stretch_model_steps']=stretches
thermals=0
for on,h,c,r in itertools.product((0,1),repeat=4):
 expected=0 if r or c else(1 if h else on)
 assert m.thermal_step(on,h,c,r)==(expected,h&c);thermals+=1
counts['thermal_full_transition_rows']=thermals
# Independent ring-buffer DUT model: storage/pointers rather than a deque.
class Ring:
 def __init__(self,n):self.n=n;self.a=[None]*n;self.r=self.w=self.count=0
 def signals(self,consumer):
  valid=self.count>0
  return self.count<self.n or(valid and consumer),valid,self.a[self.r] if valid else None
 def step(self,valid,data,consumer,reset=False):
  ready,ov,od=self.signals(consumer);pop=bool(ov and consumer);push=bool(valid and ready)
  if reset:self.r=self.w=self.count=0;return
  if pop:self.r=(self.r+1)%self.n
  if push:self.a[self.w]=data;self.w=(self.w+1)%self.n
  self.count+=push-pop
fifo_samples=0;allcov=set()
for depth in (2,3):
 for choices in itertools.product(range(4),repeat=7):
  dut=Ring(depth);observer=m.FifoObserver(depth)
  for cycle,choice in enumerate(choices):
   iv=choice>>1;orr=choice&1;ready,ov,od=dut.signals(orr)
   observer.sample(iv,ready,cycle,ov,orr,od)
   dut.step(iv,cycle,orr)
   assert len(observer.expected)==dut.count
   fifo_samples+=1
  allcov|=observer.coverage
counts['fifo_ring_model_samples']=fifo_samples
assert all(key in allcov for key in ['accepted_write','accepted_read','blocked_write','blocked_read','simultaneous'])
assert all(('occupancy',i) in allcov for i in range(4))
# Reset with outstanding contents and simultaneous activity is not a transfer.
dut=Ring(2);obs=m.FifoObserver(2)
for cycle in range(3):
 ready,ov,od=dut.signals(False);obs.sample(True,ready,cycle,ov,False,od);dut.step(True,cycle,False)
assert len(obs.expected)==2
ready,ov,od=dut.signals(True);assert obs.sample(True,ready,99,ov,True,od,reset=True)==(False,False)
dut.step(True,99,True,reset=True);assert len(obs.expected)==dut.count==0
# Mutation checks: stale/corrupt data, a false output-valid and incorrect ready.
mutations=[]
def must_fail(name,call):
 try:call()
 except AssertionError:mutations.append(name)
 else:raise AssertionError('mutation survived: '+name)
o=m.FifoObserver(2);o.sample(True,True,10,False,False,None)
must_fail('corrupt_stalled_head',lambda:o.sample(False,True,0,True,False,11))
must_fail('wrong_out_valid',lambda:o.sample(False,True,0,False,False,None))
must_fail('wrong_in_ready',lambda:o.sample(False,False,0,True,False,10))
o.sample(True,True,20,True,False,10)
must_fail('reordered_head',lambda:o.sample(False,True,0,True,True,20))
# Intent can overcount: two accepted writes and a blocked third write.
o=m.FifoObserver(2)
o.sample(True,True,'A',False,False,None);o.sample(True,True,'B',True,False,'A')
o.sample(True,False,'C',True,False,'A');assert list(o.expected)==['A','B']
counts['fifo_fault_mutations_rejected']=mutations
counts['fifo_intent_vs_accepted_example']={'requested_writes':3,'accepted_writes':2}
# Compile the exact archived source and bench in the provided native toolchain.
toolbin=Path('C:/Projects/Job_Run/.checks/intake-nov15b/iverilog/ucrt64/bin')
env=dict(os.environ);env['PATH']=str(toolbin)+os.pathsep+env.get('PATH','')
output=Path('C:/Projects/Job_Run/.checks/intake-nov15d/digital/digital1115d.vvp')
compile_command=[str(toolbin/'iverilog.exe'),'-g2012','-s','digital1115d_tb','-o',str(output),str(SOURCE),str(BENCH)]
c=subprocess.run(compile_command,text=True,capture_output=True,env=env,timeout=30)
assert c.returncode==0,c.stdout+c.stderr
v=subprocess.run([str(toolbin/'vvp.exe'),str(output)],text=True,capture_output=True,env=env,timeout=30)
assert v.returncode==0 and 'PASS digital1115d' in v.stdout,v.stdout+v.stderr
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'status':'passed','kind':'independent Python logical checks and native compiled SystemVerilog simulation',
 'counts':counts,'native':{'compile_command':compile_command,'compile_output':c.stdout+c.stderr,
 'simulation_output':v.stdout.strip(),'source_sha256':sha(SOURCE),'bench_sha256':sha(BENCH),
 'compiled_image_sha256':sha(output),'iverilog_sha256':sha(toolbin/'iverilog.exe'),'vvp_sha256':sha(toolbin/'vvp.exe')},
 'files':{str(p.relative_to(ROOT)):sha(p) for p in (SOURCE,MODEL,BENCH,Path(__file__))},
 'limitations':['No synthesis, analog timing, physical setup/hold closure, hardware execution or UVM run.',
 'Weighted-delay proof uses the explicitly ideal gate library; it is not silicon timing.',
 'Source-only duplicates reuse the checked existing content and do not receive new correctness claims.']}
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'passed','counts':counts,'native':v.stdout.strip()},ensure_ascii=False))
