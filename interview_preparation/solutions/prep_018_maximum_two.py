"""Fixed-width subtract-and-select combinational model, no floating point."""
def select_max(a,b,width,signed=False):
    if width<1:
        raise ValueError('Positive width required')
    lo=-(1<<(width-1)) if signed else 0
    hi=(1<<(width-1))-1 if signed else (1<<width)-1
    if not lo<=a<=hi or not lo<=b<=hi:
        raise ValueError('Input does not fit the selected format')
    mask=(1<<width)-1; extended_mask=(1<<(width+1))-1
    a_bits=a&mask; b_bits=b&mask
    # Repeat the sign bit for signed inputs; prepend zero for unsigned inputs.
    ae=a_bits|(((a_bits>>(width-1))&1)<<width) if signed else a_bits
    be=b_bits|(((b_bits>>(width-1))&1)<<width) if signed else b_bits
    difference=(ae-be)&extended_mask
    choose_b=(difference>>width)&1
    result_bits=b_bits if choose_b else a_bits
    result=result_bits
    if signed and result_bits&(1<<(width-1)):
        result-=1<<width
    return result,choose_b,difference
