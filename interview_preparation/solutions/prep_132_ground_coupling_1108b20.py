"""Ground-biased series capacitor and one inverter: ideal unclamped model."""
import math


def edge_node(old_node, old_input, new_input):
    return old_node+new_input-old_input


def relax_ground(start_node, dt, tau):
    if dt < 0 or tau <= 0:
        raise ValueError('dt>=0 and tau>0 required')
    return start_node*math.exp(-dt/tau)


def first_pulse_width(vdd, threshold, tau):
    if not 0 < threshold < vdd or tau <= 0:
        raise ValueError('Require 0<threshold<VDD and tau>0')
    return tau*math.log(vdd/threshold)
