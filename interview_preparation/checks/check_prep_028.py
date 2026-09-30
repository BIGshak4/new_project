"""Abstract lamp model for one-answer pulse counts and framed binary observations."""
from collections import Counter

# Each switch i is deliberately turned ON then OFF, i complete times.
lit_transitions=Counter()
actions=0
for switch in range(1,101):
    for _ in range(switch):
        lit_transitions[switch]+=1
        actions+=2
assert actions==10100
for connected in range(1,101):
    assert lit_transitions[connected]==connected

# Seven announced, synchronized slots; ON-set encodes one bit of switch number.
on_sets=[{switch for switch in range(1,101) if (switch>>bit)&1} for bit in range(6,-1,-1)]
reports=set()
for connected in range(1,101):
    report=''.join('1' if connected in on_set else '0' for on_set in on_sets)
    assert int(report,2)==connected
    reports.add(report)
assert len(reports)==100
assert 2**6<100<=2**7
print('PASS: all 100 pulse-count identities and 100 seven-slot codewords; 10100 ON/OFF actions in simple plan. Abstract ideal observations only; no physical lamp test.')
