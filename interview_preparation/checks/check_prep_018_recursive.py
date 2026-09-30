"""Two-bit gate model and recursive unsigned comparator composition."""
def compare(a,b,width):
    if width==1:
        return ((1-a)&b),int(a==b)
    low_width=width//2
    mask=(1<<low_width)-1
    lt_hi,eq_hi=compare(a>>low_width,b>>low_width,width-low_width)
    lt_lo,eq_lo=compare(a&mask,b&mask,low_width)
    return lt_hi|(eq_hi&lt_lo),eq_hi&eq_lo

def two_bit(a,b):
    a1,a0=(a>>1)&1,a&1
    b1,b0=(b>>1)&1,b&1
    e1=1^(a1^b1)
    t1=(1-a1)&b1
    t0=e1&(1-a0)&b0
    s=t1|t0
    m1=(a1&(1-s))|(b1&s)
    m0=(a0&(1-s))|(b0&s)
    eq=e1&(1^(a0^b0))
    return s,eq,(m1<<1)|m0

if __name__=='__main__':
    for a in range(4):
        for b in range(4):
            s,eq,m=two_bit(a,b)
            assert (s,eq)==compare(a,b,2)==(int(a<b),int(a==b))
            assert m==max(a,b)
    count=0
    for width in range(1,9):
        for a in range(1<<width):
            for b in range(1<<width):
                lt,eq=compare(a,b,width)
                assert (lt,eq)==(int(a<b),int(a==b))
                assert (b if lt else a)==max(a,b)
                count+=1
    print(f'PASS: all 16 two-bit gate cases; recursive LT/EQ composition verified on {count} unsigned pairs, widths 1..8.')
