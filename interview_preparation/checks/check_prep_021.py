"""Compare actual frog visits with the mathematical characterization."""
from math import isqrt

def simulate(n):
    lamps=[False]*(n+1)
    for frog in range(1,n+1):
        for lamp in range(frog,n+1,frog):
            lamps[lamp]=not lamps[lamp]
    return [i for i in range(1,n+1) if lamps[i]]

sizes=list(range(201))+[255,256,257,999,1000]
for n in sizes:
    assert simulate(n)==[k*k for k in range(1,isqrt(n)+1)],n
for n in range(1,1001):
    assert sum(n%d==0 for d in range(1,n+1))%2 == (isqrt(n)**2==n),n
assert simulate(100)==[1,4,9,16,25,36,49,64,81,100]
print(f'PASS: {len(sizes)} full frog simulations and 1000 independent divisor-parity checks; N=100 matches the ten specified lamps.')
