"""Combinational equation models; highest index has highest priority."""
def controller4(word, invalid_code=0):
    if not 0 <= word < 16:
        raise ValueError('Expected four input bits')
    return (1,word.bit_length()-1) if word else (0,invalid_code)

def controller16(word, fifth_controller=False, invalid_code=0):
    if not 0 <= word < 65536:
        raise ValueError('Expected sixteen input bits')
    local=[controller4((word>>(4*g))&15,invalid_code) for g in range(4)]
    v=[pair[0] for pair in local]
    if fifth_controller:
        valid,group=controller4(sum(bit<<i for i,bit in enumerate(v)),invalid_code)
    else:
        valid=v[0]|v[1]|v[2]|v[3]
        g1=v[3]|v[2]
        g0=v[3]|((1-v[2])&v[1])
        group=(g1<<1)|g0
    low=local[group][1]  # two-bit-wide 4:1 mux, not an OR of local codes
    return valid, ((group<<2)|low) if valid else 0

def controller16_gates_only(word):
    if not 0 <= word < 65536:
        raise ValueError('Expected sixteen input bits')
    higher=0; index=0
    for i in range(15,-1,-1):
        bit=(word>>i)&1
        winner=bit&(1-higher)
        # Each code bit is an OR of winner signals whose index has that bit set.
        for k in range(4):
            index |= (winner&((i>>k)&1))<<k
        higher |= bit
    return higher,index
