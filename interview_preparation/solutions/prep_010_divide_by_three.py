"""Ideal edge-event model mirroring the stored SystemVerilog equations.

This is a logic/timing model, not an HDL simulator or physical timing analysis.
Input period is one time unit. Values are recorded just after each edge.
"""

def simulate(cycles=12, duty=0.5, initial=(0, 0, 0)):
    if not 0 < duty < 1:
        raise ValueError('Input duty must be strictly between zero and one')
    q1, q0, delayed = initial
    result = []
    for cycle in range(cycles):
        q1, q0 = 1 - (q1 | q0), q1  # simultaneous posedge updates
        result.append(dict(t=float(cycle), clk=1, q1=q1, q0=q0,
                           delayed=delayed, out=q1 | delayed))
        delayed = q1  # negedge occurs duty*T after the posedge
        result.append(dict(t=cycle + duty, clk=0, q1=q1, q0=q0,
                           delayed=delayed, out=q1 | delayed))
    return result
