from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'solutions'))
from prep_018_maximum_two import select_max

count=0
for width in range(1,9):
    for signed in (False,True):
        lo=-(1<<(width-1)) if signed else 0
        hi=(1<<(width-1))-1 if signed else (1<<width)-1
        for a in range(lo,hi+1):
            for b in range(lo,hi+1):
                result,choose_b,difference=select_max(a,b,width,signed)
                assert result==max(a,b)
                assert choose_b==int(a<b)
                # Interpret the extended difference as a signed number.
                mathematical=difference-(1<<(width+1)) if difference&(1<<width) else difference
                assert mathematical==a-b
                count+=1
assert select_max(15,1,4)[0]==15  # Truncated 4-bit sign would give a wrong comparison.
assert select_max(7,-8,4,True)[0]==7  # Signed overflow if only four bits are kept.
print(f'PASS: {count} input pairs, all widths 1..8 in unsigned and signed formats; comparison, max and exact extended difference.')
