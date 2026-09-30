"""Unpruned recursive carry-select model; not a synthesized optimal adder."""
def full_adder(a,b,cin):
    return a ^ b ^ cin, (a & b) | (a & cin) | (b & cin)

def ripple(a,b,width,cin=0):
    result=0
    carry=cin
    for i in range(width):
        s,carry=full_adder((a>>i)&1,(b>>i)&1,carry)
        result |= s<<i
    return result,carry

def carry_select(a,b,width,levels,cin=0):
    if levels==0:
        return ripple(a,b,width,cin)
    assert width>=2 and width%2==0
    half=width//2
    mask=(1<<half)-1
    low,select=carry_select(a&mask,b&mask,half,levels-1,cin)
    high0,c0=carry_select(a>>half,b>>half,half,levels-1,0)
    high1,c1=carry_select(a>>half,b>>half,half,levels-1,1)
    high,cout=(high1,c1) if select else (high0,c0)
    return low | (high<<half),cout

def cost(width,levels):
    """Return (full-adder count, one-bit 2:1 mux count)."""
    if levels==0:
        return width,0
    fa,mux=cost(width//2,levels-1)
    return 3*fa,3*mux+width//2+1

def delay(width,levels,fa_delay,mux_delay):
    return (width//(2**levels))*fa_delay+levels*mux_delay

def best_levels(width,fa_delay,mux_delay):
    assert width>0 and width&(width-1)==0
    # Break equal modeled delays in favor of fewer levels / less area.
    return min(range(width.bit_length()),key=lambda n:(delay(width,n,fa_delay,mux_delay),n))
