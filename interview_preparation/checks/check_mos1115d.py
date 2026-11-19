"""Independent closed-form/DC charge and RC integration checks; not SPICE."""
import importlib.util,json,math,sys
from pathlib import Path
from decimal import Decimal,localcontext
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mos',ROOT/'solutions/mos1115d_models.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=0
def close(a,b,tol=1e-9):
 global checks
 assert abs(a-b)<=tol,(a,b);checks+=1

# Independent Decimal channel-charge integral and safeguarded secant root.
def reference_dc(vin,bn,bp,vdd=1.0,vt=0.25,lam=0.15):
 if vin<=vt:return vdd
 if vin>=vdd-vt:return 0.0
 # Integrate channel charge analytically using Decimal arithmetic, then solve
 # KCL with a safeguarded secant / Illinois method instead of binary search.
 with localcontext() as ctx:
  ctx.prec=60
  D=Decimal;vn=D(str(vin));supply=D(str(vdd));t=D(str(vt));l=D(str(lam));n=D(str(bn));p=D(str(bp))
  def current(vg,vd,beta):
   upper=min(vd,vg-t)
   if upper<=0:return D(0)
   integral=(vg-t)*upper-upper*upper/D(2)
   return beta*integral*(D(1)+l*vd)
  # Independent secant/regula-falsi with Illinois damping and Decimal charge integral.
  low,high=D(0),supply
  fl=current(supply-vn,supply-low,p)-current(vn,low,n)
  fh=current(supply-vn,supply-high,p)-current(vn,high,n)
  for _ in range(500):
   x=(low*fh-high*fl)/(fh-fl)
   f=current(supply-vn,supply-x,p)-current(vn,x,n)
   if abs(f)<D('1e-45'):return float(x)
   if f>0:low,fl=x,f;fh/=2
   else:high,fh=x,f;fl/=2
  return float(x)

dc_rows=[]
for bn,bp in ((1,1),(1,2),(2,1),(0.5,2),(2,0.5)):
 prev=1.0
 for i in range(201):
  vin=i/200;v=m.inverter_dc(vin,bn,bp)
  close(v,reference_dc(vin,bn,bp),2e-9)
  assert -1e-12<=v<=1+1e-12 and v<=prev+1e-12;checks+=1;prev=v
  if 0.25<vin<0.75:
   close(m.mos_current(1-vin,1-v,bp,.25),m.mos_current(vin,v,bn,.25),1e-12)
 for vin in (.3,.4,.5,.6,.7):
  assert m.inverter_dc(vin,bn,bp*2)>=m.inverter_dc(vin,bn,bp)-1e-12;checks+=1
 lo,hi=0.25,0.75
 for _ in range(60):
  mid=(lo+hi)/2
  if m.inverter_dc(mid,bn,bp)>mid:lo=mid
  else:hi=mid
 dc_rows.append(dict(beta_n=bn,beta_p=bp,vm_clm=(lo+hi)/2,vm_ideal=m.ideal_switching_point(bn,bp)))
for vgs in (.3,.5,.9):
 vov=vgs-.25
 close(m.mos_current(vgs,vov-1e-10,1,.25),m.mos_current(vgs,vov+1e-10,1,.25),1e-9)
for bn,bp in ((1,1),(1,2),(2,1)):
 vm=m.ideal_switching_point(bn,bp)
 close(m.mos_current(vm,vm,bn,.25,0),m.mos_current(1-vm,1-vm,bp,.25,0),1e-14)

# Independent subthreshold ratio: Decimal exponent vs math exponential.
with localcontext() as ctx:
 ctx.prec=60
 exact=(-Decimal('0.1')/(Decimal('1.5')*Decimal('0.02585'))).exp()
close(m.off_current_ratio(.1),float(exact),1e-14)
close(m.dynamic_power(.1,20e-15,1,1e9),2e-6,1e-18)
close(m.dynamic_power(.1,20e-15,.8,1e9)/m.dynamic_power(.1,20e-15,1,1e9),.64,1e-14)

# Integrate normalized capacitor KCL by RK4, independently of exponential formula.
samples=0
for resistance in (500,1000,2000):
 for capacitance in (10e-15,20e-15,40e-15):
  tau=resistance*capacitance;dt=tau/2000
  for rising in (False,True):
   value=0.0 if rising else 1.0;cross=None
   for j in range(1,8001):
    def f(x):return ((1-x) if rising else -x)/tau
    a=f(value);b=f(value+dt*a/2);c=f(value+dt*b/2);d=f(value+dt*c)
    nxt=value+dt*(a+2*b+2*c+d)/6
    if cross is None and (value-.5)*(nxt-.5)<=0:cross=(j-1)*dt+dt*(.5-value)/(nxt-value)
    value=nxt;samples+=1
    if j%100==0:close(value,m.output_after_step(j*dt,resistance,capacitance,rising),2e-12)
   close(cross,m.rc_delay(resistance,capacitance),tau*4e-8)
close(m.rc_delay(1000,20e-15),13.862943611198906e-12,1e-24)
close(m.rc_delay(1000,40e-15),2*m.rc_delay(1000,20e-15),1e-24)
close(m.rc_delay(500,20e-15),m.rc_delay(1000,20e-15)/2,1e-24)
bad=0
for call in (lambda:m.inverter_dc(-.1),lambda:m.inverter_dc(.5,channel_lambda=0),lambda:m.rc_delay(0,1),lambda:m.dynamic_power(-1,1,1,1),lambda:m.off_current_ratio(.1,n=0)):
 try:call()
 except ValueError:bad+=1
assert bad==5
report=dict(status='passed',checks=checks,dc_points=1005,dc_models=5,dc_switching_points=dc_rows,rc_scenarios=18,rc_integration_samples=samples,rejected_inputs=bad,leakage_ratio_for_0_1V_increase=m.off_current_ratio(.1),scope='Independent Decimal channel-charge integration and safeguarded secant solve versus binary-search DC model; analytic ideal switching points; Decimal leakage exponent; energy arithmetic; independent RK4 capacitor KCL against RC waveform and threshold crossing. Educational equations only; no SPICE, characterized process, synthesis, measurement or signoff.')
path=ROOT/'checks/mos1115d-verification.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report,indent=2))
