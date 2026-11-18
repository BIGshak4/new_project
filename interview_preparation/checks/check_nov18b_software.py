"""Compare the software examples against explicit reference models."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import random
import runpy

BANK = Path(__file__).resolve().parents[1]


def load(number, suffix):
    path = BANK / 'solutions' / f'prep_{number:03d}_{suffix}.py'
    return path, runpy.run_path(str(path))


def report(number, path, counts):
    data = {'status': 'passed', **counts, 'source_sha256': {path.name: sha256(path.read_bytes()).hexdigest()}}
    target = BANK / 'checks' / f'prep-{number:03d}-1118b-verification.json'
    target.write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    print(f'{number}: {counts}')


def median_check():
    path, functions = load(379, 'unsorted_median')
    tested = 0
    def check(values):
        nonlocal tested
        data = sorted(values)
        expected = (data[(len(data)-1)//2] + data[len(data)//2])/2 if data else None
        candidate = list(values)
        actual = functions['median'](candidate)
        assert actual == expected and sorted(candidate) == data, (values, actual, expected)
        tested += 1
    for n in range(8):
        for values in product(range(-2,3), repeat=n):
            check(values)
    for sample in [[-2**31], [2**31-1,-2**31], [2**31-2,2**31-1], [3]*121, list(range(150,0,-1))]:
        check(sample)
    report(379,path,{'reference_sorted_arrays':tested})


def stream_check():
    path, functions = load(380, 'ordered_double_stream')
    checked = 0
    for n in range(10):
        for word in product('xya', repeat=n):
            text = ''.join(word)
            expected = n % 3 == 0 and text == 'x'*(n//3)+'y'*(2*(n//3))
            for transmission, wants in [(text+'\\',expected),(text+'\\y',expected),(text,False)]:
                assert functions['accepts_frame'](transmission) is wants, transmission
                checked += 1
    stack = []
    machine = functions['Receiver'](stack.append,stack.pop,lambda: not stack)
    for symbol, size in zip('xxyyyy',[2,4,3,2,1,0]):
        assert machine.feed(symbol) is None and len(stack)==size
    assert machine.feed('\\') is True
    report(380,path,{'direct_language_comparisons':checked,'event_by_event_trace':True})


def shelf_oracle(width,height,pieces):
    # Retain each row's rectangles explicitly and derive its geometry afresh.
    shelves = [[]]
    placements = []
    occupied = set()
    if width == 0 or height == 0:
        return placements
    for index,(w,h) in enumerate(pieces):
        if not (0 < w <= width and 0 < h <= height):
            continue
        current=shelves[-1]
        base=sum(max(r[1] for r in row) for row in shelves[:-1])
        if h > height-base:
            continue
        x=sum(r[0] for r in current)
        if x+w > width:
            next_base=base+max(r[1] for r in current)
            if next_base+h>height:
                continue
            current=[]
            shelves.append(current)
            x,base=0,next_base
        cells={(a,b) for a in range(x,x+w) for b in range(base,base+h)}
        assert not cells & occupied
        assert all(0<=a<width and 0<=b<height for a,b in cells)
        occupied.update(cells)
        current.append((w,h))
        placements.append([index,x,base])
    return placements


def shelf_check():
    path, functions=load(381,'shelf_rectangles')
    rectangles=[(1,1),(2,1),(1,2),(2,3),(3,1),(4,2),(-1,0)]
    checked=0
    for width,height in product(range(5),repeat=2):
        for pieces in product(rectangles,repeat=4):
            actual=functions['pack_shelves'](width,height,pieces)
            assert actual==shelf_oracle(width,height,pieces), (width,height,pieces,actual)
            checked+=1
    examples=[(6,5,[(2,1),(1,3),(3,2),(4,2)],[[0,0,0],[1,2,0],[2,3,0],[3,0,3]]),
              (8,6,[(2,2),(1,3),(3,1),(1,2),(3,2)],[[0,0,0],[1,2,0],[2,3,0],[3,6,0],[4,0,3]])]
    for w,h,pieces,expected in examples:
        assert functions['pack_shelves'](w,h,pieces)==expected
    report(381,path,{'exhaustive_board_streams':checked,'figure_geometry_cases':len(examples)})


def recursion_check():
    path, functions=load(196,'recursion_nesting_boxes')
    nested=None
    for n in range(100):
        assert functions['count_boxes'](nested)==n
        nested={'inside':nested}
    report(196,path,{'box_chains':100})


if __name__ == '__main__':
    random.seed(1118)
    median_check()
    stream_check()
    shelf_check()
    recursion_check()
