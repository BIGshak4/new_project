"""Independent checks for the November 18 software additions."""
from bisect import bisect_right
from fractions import Fraction
from itertools import combinations, combinations_with_replacement, permutations, product
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys


BANK = Path(__file__).resolve().parents[1]
SOLUTIONS = BANK / 'solutions'
REPORTS = BANK / 'checks'


def load(name):
    return runpy.run_path(str(SOLUTIONS / name))


def report(number, result, *files):
    result['source_sha256'] = {
        name: hashlib.sha256((SOLUTIONS / name).read_bytes()).hexdigest()
        for name in files
    }
    (REPORTS / f'prep-{number:03d}-1118-verification.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(number, result)


def check_clone(compiler, scratch):
    py_name = 'prep_371_clone_random_list.py'
    cc_name = 'prep_371_clone_random_list.cpp'
    module = load(py_name)
    Node, clone = module['Node'], module['clone_list']
    count = 1
    assert clone(None) is None
    for size in range(1,6):
        for destinations in product(range(-1,size), repeat=size):
            source = [Node(index % 2) for index in range(size)]
            for index, node in enumerate(source):
                node.next = source[index+1] if index+1 < size else None
                node.random = source[destinations[index]] if destinations[index] >= 0 else None
            snapshot = [(node.data,node.next,node.random) for node in source]
            copied = []
            node = clone(source[0])
            for _ in range(size):
                assert node is not None and all(node is not old for old in source)
                copied.append(node)
                node = node.next
            assert node is None and len(set(copied)) == size
            for index, node in enumerate(copied):
                target = destinations[index]
                assert node.random is (copied[target] if target >= 0 else None)
                assert node.data == snapshot[index][0]
            copied[0].data += 100
            assert [(node.data,node.next,node.random) for node in source] == snapshot
            count += 1

    harness = scratch/'test_clone_random_list.cpp'
    exe = scratch/'test_clone_random_list.exe'
    harness.write_text(r'''
#include <cassert>
#include <iostream>
#include <unordered_set>
#include "prep_371_clone_random_list.cpp"

int main() {
    const auto empty = clone_list(nullptr);
    assert(empty.head == nullptr && empty.storage.empty());
    int checked = 1;
    for (int n = 1; n <= 5; ++n) {
        int combinations = 1;
        for (int i = 0; i < n; ++i) combinations *= n + 1;
        for (int code = 0; code < combinations; ++code) {
            std::vector<Node> original(n);
            std::vector<int> targets;
            int digits = code;
            for (int i = 0; i < n; ++i) {
                original[i].data = i % 2;
                original[i].next = i + 1 < n ? &original[i+1] : nullptr;
                const int target = digits % (n+1) - 1;
                digits /= n + 1;
                targets.push_back(target);
                original[i].random = target < 0 ? nullptr : &original[target];
            }
            const auto result = clone_list(&original[0]);
            assert(result.storage.size() == original.size());
            std::unordered_set<const Node*> fresh;
            std::vector<Node*> copied;
            Node* current = result.head;
            for (int i = 0; i < n; ++i) {
                assert(current != nullptr);
                for (const auto& node : original) assert(current != &node);
                assert(fresh.insert(current).second);
                assert(current->data == i % 2);
                copied.push_back(current);
                current = current->next;
            }
            assert(current == nullptr);
            copied[0]->data = 99;
            for (int i = 0; i < n; ++i) {
                const int target = targets[i];
                assert(copied[i]->random == (target < 0 ? nullptr : copied[target]));
                assert(original[i].data == i % 2);
                assert(original[i].random == (target < 0 ? nullptr : &original[target]));
                assert(original[i].next == (i+1 < n ? &original[i+1] : nullptr));
            }
            ++checked;
        }
    }
    std::cout << checked << '\n';
}
''',encoding='utf8')
    command=[str(compiler),'c++','-std=c++17','-Wall','-Wextra','-Werror','-O2','-UNDEBUG',
             '-I',str(SOLUTIONS),str(harness),'-o',str(exe)]
    subprocess.run(command,check=True)
    native = int(subprocess.check_output([exe],text=True))
    assert native == count
    report(371,{'status':'passed','python_identity_cases':count,'native_cpp_cases':native,
                'compiler':'Zig C++17 -O2 -UNDEBUG -Wall -Wextra -Werror',
                'compiler_version':subprocess.check_output([compiler,'version'],text=True).strip(),
                'native_harness_sha256':hashlib.sha256(harness.read_bytes()).hexdigest()},py_name,cc_name)


def check_random():
    name = 'prep_372_random_last_five.py'
    module = load(name)
    generator = module['RandomLastFive']
    rank_count = 0
    domain = list(range(-3,6))
    for size in range(6):
        for excluded in combinations(domain,size):
            allowed = [cell for cell in domain if cell not in excluded]
            for rank, expected in enumerate(allowed):
                requested = []
                def draw(low,high):
                    requested.append((low,high))
                    return rank
                instance=generator(domain[0],domain[-1],draw)
                # Reach the history through the public interface in ascending order.
                for cell in excluded:
                    unused_before = [v for v in domain if v not in instance.history]
                    index = unused_before.index(cell)
                    instance.rand=lambda lo,hi,index=index: index
                    assert instance.next()==cell
                instance.rand=draw
                assert instance.next()==expected
                assert requested==[(0,len(allowed)-1)]
                rank_count += 1
    assert module['random_from_ranks'](10,15,[0]*19) == [10+i%6 for i in range(19)]
    snapshots=[]
    for low,high in [(3,2),(1,1),(-4,0)]:
        try:
            generator(low,high,lambda *_: 0)
        except ValueError:
            snapshots.append([low,high])
        else:
            raise AssertionError((low,high))
    first=generator(0,5,lambda *_: 0)
    second=generator(0,5,lambda *_: 0)
    assert [first.next(),first.next(),second.next()]==[0,1,0]
    report(372,{'status':'passed','exhaustive_rank_cases':rank_count,
                'invalid_range_cases':snapshots,'verified_minimum_range_cycle':True,
                'verified_separate_history':True,'sampling_claim':'Bijection, with uniformly generated ranks assumed.'},name)


def check_successor():
    name = 'prep_373_bst_successor.py'
    module=load(name)
    Node, successor=module['Node'],module['successor']
    checked = 0
    for n in range(8):
        keys=list(range(-1,n-1))
        for ordering in permutations(keys):
            nodes = {key:Node(key) for key in ordering}
            if not ordering:
                assert successor(None) is None
                continue
            root=nodes[ordering[0]]
            for key in ordering[1:]:
                current=root
                while True:
                    side='left' if key<current.key else 'right'
                    child=getattr(current,side)
                    if child is None:
                        setattr(current,side,nodes[key])
                        nodes[key].parent=current
                        break
                    current=child
            before=[(u.left,u.right,u.parent) for u in nodes.values()]
            for key in ordering:
                pos=bisect_right(keys,key)
                assert successor(nodes[key]) is (nodes[keys[pos]] if pos<n else None)
                checked+=1
            assert before==[(u.left,u.right,u.parent) for u in nodes.values()]
    report(373,{'status':'passed','direct_node_checks':checked,
                'shape_scope':'All insertion orders through seven distinct keys, plus empty input.',
                'oracle':'Sorted key successor mapped back to original node identity.'},name)


def check_copy():
    name='prep_332_copy_overlapping_slice.py'
    copy=load(name)['copy_within']
    passed=0
    for length in range(20):
        originals=list(range(length))
        for size in range(length+1):
            for source,target in product(range(length-size+1),repeat=2):
                actual=originals.copy()
                expected=originals.copy()
                expected[target:target+size]=originals[source:source+size]
                copy(actual,source,size,target)
                assert actual==expected
                passed+=1
    bad=[(-1,0,0),(0,-1,0),(0,4,0),(0,2,2),(2,2,0),(4,0,0),(0,0,-1)]
    for args in bad:
        actual=[0,1,2]
        try:
            copy(actual,*args)
        except ValueError:
            assert actual==[0,1,2]
        else:
            raise AssertionError(args)
    report(332,{'status':'passed','snapshot_oracle_cases':passed,'unmodified_invalid_cases':len(bad)},name)


def check_partition():
    name='prep_137_sorted_partition_access.py'
    module=load(name)
    random_access,forward=module['boundary_random_access'],module['boundary_forward']

    class ReadCounter:
        def __init__(self,values):
            self.values=values
            self.reads=0
        def __len__(self):
            return len(self.values)
        def __getitem__(self,index):
            assert 0<=index<len(self.values)
            self.reads+=1
            return self.values[index]
        def __iter__(self):
            for value in self.values:
                self.reads+=1
                yield value

    checked=0
    for n in range(10):
        for values in combinations_with_replacement(range(-3,4),n):
            for key in range(-4,5):
                expected=sum(value<key for value in values)
                ram,shift=ReadCounter(values),ReadCounter(values)
                assert random_access(ram,key)==forward(shift,key)==expected
                assert ram.reads<=n.bit_length()
                assert shift.reads==min(n,expected+1)
                checked+=1
    for n in range(129):
        reads=[]
        for boundary in range(n+1):
            values=ReadCounter((0,)*boundary+(1,)*(n-boundary))
            assert random_access(values,1)==boundary
            reads.append(values.reads)
        assert max(reads)==n.bit_length()
    report(137,{'status':'passed','word_boundary_cases':checked,'exhaustive_bit_lengths':129,
                'verified_exact_worst_case_comparisons':True},name)


def check_postfix():
    name='prep_123_postfix_compact_division.py'
    evaluate=load(name)['evaluate_compact_postfix']
    def reference(expression):
        chars=iter(reversed(''.join(expression.split())))
        def parse():
            token=next(chars)
            if token in '+-*/':
                right,left=parse(),parse()
                if token=='+': return left+right
                if token=='-': return left-right
                if token=='*': return left*right
                return int(Fraction(left,right))
            return int(token)
        value=parse()
        if next(chars,None) is not None:
            raise ValueError('unexpected token before completed tree')
        return value
    def outcome(fn,text):
        try:
            return True,fn(text)
        except (StopIteration,ValueError,ZeroDivisionError):
            return False,None
    passed=0
    for length in range(7):
        for symbols in product('025+-*/',repeat=length):
            text=''.join(symbols)
            assert outcome(evaluate,text)==outcome(reference,text),text
            passed+=1
    for example,expected in [('82/',4),('138*+',25),('545*+5/',5),('25-2/',-1),(' 8 2 /\n',4)]:
        assert evaluate(example)==expected
    report(123,{'status':'passed','recursive_parse_comparisons':passed,'explicit_cases':5},name)


def check_prefix():
    name='prep_072_contiguous_prefix_maxima.py'
    stream=load(name)['prefix_max_subarray_sums']
    checked=0
    for size in range(8):
        for data in product(range(-2,3),repeat=size):
            expected=[max(sum(data[a:b]) for a in range(end) for b in range(a+1,end+1))
                      for end in range(1,size+1)]
            assert list(stream(data))==expected
            checked+=1
    allowance=[0]
    def guarded():
        for i in range(4):
            assert i < allowance[0], 'read beyond the requested prefix'
            yield i
    output=stream(guarded())
    for i in range(4):
        allowance[0]+=1
        assert next(output)==i*(i+1)//2
    report(72,{'status':'passed','all_prefixes_exhaustive_arrays':checked,
               'no_lookahead_verified':True},name)


if __name__ == '__main__':
    compiler, scratch = map(Path,sys.argv[1:])
    scratch.mkdir(parents=True,exist_ok=True)
    check_clone(compiler,scratch)
    check_random()
    check_successor()
    check_copy()
    check_partition()
    check_postfix()
    check_prefix()
