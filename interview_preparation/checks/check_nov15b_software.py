"""Independent finite checks. No learner data or online service is accessed."""
import json
import runpy
from itertools import product
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name):return runpy.run_path(str(ROOT/'solutions'/name))

def main():
    gods=load('prep_346_three_gods_strategy.py')['verify_strategy']()
    assert gods==96
    rows=0
    for p,truth,da_yes in product((False,True),repeat=3):
        statement=(p==truth)==da_yes
        assert ((statement if truth else not statement)==da_yes)==p
        rows+=1
    pyramid=load('prep_347_star_pyramid.py')
    widths=0
    for n in range(1,100,2):
        mid=n//2
        expected='\n'.join(''.join('*' if abs(col-mid)<=row else ' ' for col in range(n)).rstrip()
                           for row in range(mid+1))
        assert pyramid['pyramid'](n)==pyramid['pyramid_by_cells'](n)==expected
        widths+=1
    for bad in (0,-1,2,4,None,True,1.5,'5'):
        for name in ('pyramid','pyramid_by_cells'):
            try:pyramid[name](bad)
            except ValueError:pass
            else:raise AssertionError((name,bad))
    linked=load('prep_348_delete_interior_node.py');deletions=0
    for n in range(3,8):
        for values in product((-1,0,1),repeat=n):
            for index in range(1,n-1):
                assert linked['delete_interior_result'](list(values),index)==list(values[:index]+values[index+1:])
                deletions+=1
    identities=0
    for n in range(3,21):
        for index in range(1,n-1):
            nodes=[linked['Node'](i) for i in range(n)]
            for a,b in zip(nodes,nodes[1:]):a.next=b
            successor=nodes[index+1]
            linked['delete_given'](nodes[index])
            chain=[];node=nodes[0]
            while node is not None:chain.append(node);node=node.next
            assert nodes[index] in chain and successor not in chain and len(chain)==n-1
            assert nodes[index].value==index+1
            identities+=1
    turtle=load('prep_182_turtle_turnback.py')['returns_to_start_with_turnback']
    traces=0
    for n in range(9):
        for commands in product('MRLT',repeat=n):
            pos=0j;heading=1j
            for command in commands:
                if command=='M':pos+=heading
                else:heading*=dict(R=-1j,L=1j,T=-1)[command]
            assert turtle(''.join(commands))==(pos==0)
            traces+=1
    assert traces==87381
    result=dict(passed=True,three_gods_transcripts=gods,wrapper_rows=rows,pyramid_widths=widths,
                deletion_sequences=deletions,deletion_identity_cases=identities,turtle_traces=traces,
                scope='Python finite oracles and identity checks; C native checks recorded separately.')
    (ROOT/'checks/batch1115b-software-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    for number in (346,347,348,182):
        (ROOT/f'checks/prep-{number}-1115b-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result)

if __name__=='__main__':main()
