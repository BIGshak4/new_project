"""Teaching models, not a process fit, SPICE simulation or cell characterization.

DC: long-channel square-law NMOS/PMOS magnitudes with positive lambda.
The factor (1+lambda*VDS) multiplies BOTH triode and saturation expressions,
giving a continuous empirical CLM extension and a unique inverter DC root.
RC: constant effective resistance, ideal input step, lumped load.
All voltages V, resistance ohms, capacitance F and time seconds.
"""
from math import exp, isfinite, log, sqrt


def mos_current(vgs, vds, beta, vth, channel_lambda=0.15):
    if not all(isfinite(x) for x in (vgs,vds,beta,vth,channel_lambda)):
        raise ValueError('finite parameters required')
    if min(vds,vth,channel_lambda)<0 or beta<=0:
        raise ValueError('require vds/vth/lambda>=0 and beta>0')
    overdrive=vgs-vth
    if overdrive<=0:return 0.0
    core=beta*(overdrive*vds-vds*vds/2) if vds<overdrive else beta*overdrive*overdrive/2
    return core*(1+channel_lambda*vds)


def inverter_dc(vin, beta_n=1.0, beta_p=1.0, vdd=1.0, vth=0.25, channel_lambda=0.15):
    if not all(isfinite(x) for x in (vin,beta_n,beta_p,vdd,vth,channel_lambda)):
        raise ValueError('finite parameters required')
    if not 0<=vin<=vdd or min(beta_n,beta_p,vth,channel_lambda)<=0 or vdd<=2*vth:
        raise ValueError('legal input, positive strengths/threshold/lambda and overlapping conduction required')
    lo,hi=0.0,vdd
    for _ in range(70):
        out=(lo+hi)/2
        net=mos_current(vdd-vin,vdd-out,beta_p,vth,channel_lambda)-mos_current(vin,out,beta_n,vth,channel_lambda)
        if net>0:lo=out
        else:hi=out
    return (lo+hi)/2


def ideal_switching_point(beta_n,beta_p,vdd=1.0,vtn=0.25,vtp_abs=0.25):
    if min(beta_n,beta_p)>0 and vdd>vtn+vtp_abs and min(vtn,vtp_abs)>=0:
        r=sqrt(beta_p/beta_n)
        return (vtn+r*(vdd-vtp_abs))/(1+r)
    raise ValueError('valid overlapping-conduction square-law parameters required')


def off_current_ratio(delta_vth,n=1.5,thermal_voltage=0.02585):
    if not all(isfinite(x) for x in (delta_vth,n,thermal_voltage)) or min(n,thermal_voltage)<=0:
        raise ValueError('finite delta and positive n/thermal voltage required')
    return exp(-delta_vth/(n*thermal_voltage))


def dynamic_power(activity,capacitance,vdd,frequency):
    # activity counts 0->1 charging events per clock cycle, not both edge types.
    if not all(isfinite(x) and x>=0 for x in (activity,capacitance,vdd,frequency)):
        raise ValueError('finite nonnegative parameters required')
    return activity*capacitance*vdd*vdd*frequency


def rc_delay(resistance,capacitance,response_start=0):
    if not all(isfinite(x) for x in (resistance,capacitance,response_start)) or min(resistance,capacitance)<=0 or response_start<0:
        raise ValueError('positive R/C and nonnegative response start required')
    return response_start+log(2)*resistance*capacitance


def output_after_step(time,resistance,capacitance,rising=False,vdd=1.0,response_start=0):
    rc_delay(resistance,capacitance,response_start)
    if not isfinite(time) or not isfinite(vdd) or vdd<=0:raise ValueError('finite time and positive supply required')
    progress=1-exp(-max(0,time-response_start)/(resistance*capacitance))
    return vdd*(progress if rising else 1-progress)
