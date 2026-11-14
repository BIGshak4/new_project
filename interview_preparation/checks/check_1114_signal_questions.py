"""Independent finite checks for the 14 November signal and timing exercises."""
import cmath
import json
import math
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def check_setup():
    expected = {0: 6, 2: 4, 5: 1, 6: 0, 7: -1}
    for clock_to_q, margin in expected.items():
        data_at_b = clock_to_q + 12
        next_capture = 15 + 5
        assert next_capture - 2 - data_at_b == margin
        assert (data_at_b + 2 <= next_capture) == (margin >= 0)
    return len(expected)


def check_rc():
    tau, omega = 0.001, 250
    gain = 1 / math.hypot(1, omega*tau)
    phase = math.atan(omega*tau)
    # Integrate the initial-value problem with a fourth-order solver.
    t, step, v = 0, 1e-5, 0
    for _ in range(5000):
        def deriv(stage_t, stage_v):
            return (math.sin(omega*stage_t) - stage_v) / tau
        k1 = deriv(t, v)
        k2 = deriv(t + step/2, v + step*k1/2)
        k3 = deriv(t + step/2, v + step*k2/2)
        k4 = deriv(t + step, v + step*k3)
        v += step*(k1 + 2*k2 + 2*k3 + k4)/6
        t += step
        solution = gain*(math.sin(omega*t - phase) + math.sin(phase)*math.exp(-t/tau))
        assert abs(v - solution) < 1e-8

    for tau in [0.00025, 0.001, 0.008]:
        q = math.exp(-0.002/tau)
        lo, hi = 0, 0
        for _ in range(300):
            hi = 1 + (lo - 1)*q
            lo = hi*q
        assert abs(hi - 1/(1 + q)) < 1e-12
        assert abs(lo - q/(1 + q)) < 1e-12
    return {'sine_integration_steps': 5000, 'square_tau_cases': 3}


def add_bits(x, y, width):
    carry, out = 0, 0
    for i in range(width):
        a, b = (x >> i) & 1, (y >> i) & 1
        propagate = a ^ b
        out |= (propagate ^ carry) << i
        carry = (a & b) | (propagate & carry)
    return out | (carry << width)


def check_tree():
    for a,b,c,d in product(range(8), repeat=4):
        left, right = add_bits(a,b,3), add_bits(c,d,3)
        result = add_bits(left,right,4) << 1
        assert result == 2*(a+b+c+d) and 0 <= result <= 56
    # Graph arrival times at each sum bit and the final carry; one unit per gate.
    def arrival(inputs):
        carry, sums = 0, []
        for i, start in enumerate(inputs):  # same arrival on the two side buses
            operand_gate = start + 1
            sums.append(operand_gate if i == 0 else max(operand_gate,carry) + 1)
            carry = operand_gate if i == 0 else max(operand_gate,carry) + 2
        return sums + [carry]
    pair = arrival([0]*3)
    assert pair == [1,2,4,5] and arrival(pair) == [2,4,6,8,9]
    assert arrival([0]*4) == [1,2,4,6,7]
    return {'operand_tuples': 4096, 'unregistered_gate_depth': 9,
            'pipelined_gate_depths': [5,7]}


def check_dsp():
    codes = [0]*8
    err_sum = err_square = 0
    for j in range(8192):
        x = (j + 0.5)/8192
        k = min(7,math.floor(8*x))
        err = (k + 0.5)/8 - x
        assert abs(err) <= 1/16
        codes[k] += 1
        err_sum += err
        err_square += err*err
    assert codes == [1024]*8 and err_sum == 0
    assert abs(err_square/8192 - 1/768) < 2e-9
    assert sum((F(1,8)**3)/12 for _ in range(8)) == F(1,768)
    for i in range(9):
        k = min(7,math.floor(8*i/8))
        assert k == min(7,i)
    fs,fc = 1000,100
    g = math.tan(math.pi*fc/fs)
    b,a1 = g/(1+g),(g-1)/(g+1)
    gains = {}
    for f in [0,20,100,300,500]:
        z = cmath.exp(-2j*math.pi*f/fs)
        gains[f] = abs(b*(1+z)/(1+a1*z))
    assert abs(gains[0]-1) < 1e-12 and gains[500] < 1e-12
    assert abs(gains[fc] - 1/math.sqrt(2)) < 1e-12
    assert gains[20] > 0.95 and gains[300] < 0.25
    return {'midpoint_samples':8192, 'edge_samples':9, 'gains':gains}


if __name__ == '__main__':
    report = {'setup': check_setup(), 'rc': check_rc(), 'adder': check_tree(), 'dsp': check_dsp()}
    print(json.dumps(report, indent=2))

