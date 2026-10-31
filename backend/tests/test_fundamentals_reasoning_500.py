"""Independent finite worlds, counterexamples and exact oracles for 175 MCQs.

No producer implementation is used to judge an answer. Reproduction is checked
separately after the answer-level checks. These tests do not grant expert review.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import re
from collections import Counter
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "apps/web/src/content"
BATCH = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((CONTENT / "fundamentals-reasoning-500.json").read_bytes())
ROWS = json.loads((BATCH / "reasoning_500.json").read_bytes())
CHECKS = json.loads((BATCH / "reasoning_500.checks.json").read_bytes())
BY_KEY = {q["key"]: q for q in ROWS}


def allowed_assignments(lists):
    """Recursive matching search rather than producer's Cartesian filter."""
    def visit(person, used, assignment):
        if person == len(lists):
            yield assignment
        else:
            for item in lists[person]:
                if item not in used:
                    yield from visit(person+1, used | {item}, (*assignment, item))
    return list(visit(0, set(), ()))


def ferry_oracle(data):
    """Construct all legal worlds, then expand path lengths synchronously."""
    nw, ns = data["w"], data["s"]
    worlds = set()
    for w, s, side in itertools.product(range(nw+1), range(ns+1), (0, 1)):
        banks = [(w, s), (nw-w, ns-s)]
        if all(sheep == 0 or wolves <= sheep for wolves, sheep in banks):
            worlds.add((w, s, side))
    start = (0, 0, 0)
    reached = {start}
    for length in range(len(worlds)+1):
        if any(s == ns for _, s, _ in reached):
            return length
        expanded = set(reached)
        for source in reached:
            for dest in worlds:
                if source[2] == dest[2]:
                    continue
                dw, ds = dest[0]-source[0], dest[1]-source[1]
                if source[2] == 0 and dw >= 0 and ds >= 0 and dw+ds in data["forward"]:
                    expanded.add(dest)
                if source[2] == 1 and dw <= 0 and ds <= 0 and -dw-ds in data["backward"]:
                    expanded.add(dest)
        if expanded == reached:
            return -1
        reached = expanded
    raise AssertionError("Finite graph did not settle")


def oracle(task, d):
    if task in {"nested_joint", "nested_mean", "nested_cdf"}:
        total = F()
        for a in range(d["n"]+1):
            for b in range(a+1):
                weight = F(1, d["n"]+1) / (a+1)
                if task == "nested_mean":
                    total += b*weight
                elif (task == "nested_joint" and (a, b) == (d["a"], d["b"])) or (task == "nested_cdf" and b <= d["k"]):
                    total += weight
        return total
    if task == "modulo_fibers":
        counts = [sum(x % d["m"] == r for x in range(d["base"])) for r in range(d["m"])]
        return max(counts)-min(counts)
    if task == "rejection_cost":
        pairs = list(itertools.product(range(d["base"]), repeat=2))
        accepted = [p for p in pairs if d["base"]*p[0]+p[1] < len(pairs)-len(pairs)%d["m"]]
        # E=2+P(reject)*E, solved directly from the complete one-step space.
        rejected = len(pairs)-len(accepted)
        return F(2, 1-F(rejected,len(pairs)))
    if task in {"right_neighbor", "overlapping_neighbors"}:
        words = list(itertools.permutations(range(d["n"])))
        def good(word):
            adjacent = word.index(1) == word.index(0)+1
            return adjacent and (task == "right_neighbor" or word.index(2) == word.index(1)+1)
        return F(sum(good(word) for word in words), len(words))
    if task == "agenda":
        wins = {(0,1),(1,2),(2,0)}
        if d["reverse"]:
            wins = {(b,a) for a,b in wins}
        def winner(a,b):
            return a if (a,b) in wins else b
        a,b = [x for x in range(3) if x != d["bye"]]
        return winner(winner(a,b),d["bye"])
    if task == "voting_margin":
        counts = [d["x"],d["m"]-d["x"],d["m"]-d["x"],d["x"],d["x"],d["m"]-d["x"]]
        ballots = [ranking for ranking,count in zip(itertools.permutations("ABC"),counts,strict=True) for _ in range(count)]
        return abs(sum(1 if ballot.index("A") < ballot.index("B") else -1 for ballot in ballots))
    if task == "long_cycles":
        # Test feasibility for every possible count, with explicit disjoint-size witnesses.
        feasible = [k for k in range(d["n"]+1) if sum([d["limit"]+1]*k) <= d["n"]]
        return max(feasible)
    if task == "cycle_split":
        return min(max(k,d["length"]-k) for k in range(1,d["length"]))
    if task == "cycle_merge":
        a,b = d["a"],d["b"]
        links = [*range(1,a),0,*range(a+1,a+b),a]
        links[0],links[a] = links[a],links[0]
        current,visited = 0,set()
        while current not in visited:
            visited.add(current)
            current = links[current]
        assert current == 0
        return len(visited)
    if task == "necklaces":
        representatives = set()
        for word in itertools.product((0,1),repeat=d["n"]):
            representatives.add(min(word[i:]+word[:i] for i in range(len(word))))
        return len(representatives)
    if task == "ring_candidates":
        matches = []
        for n in range(1,d["bound"]+1):
            position,returns = 0,set()
            for step in range(1,max(d["distances"])+1):
                position = 0 if position+1 == n else position+1
                if position == 0:
                    returns.add(step)
            if set(d["distances"]) <= returns:
                matches.append(n)
        return len(matches)
    if task == "ferry":
        return ferry_oracle(d)
    if task == "safe_bank":
        return sum(not (s > 0 and w > s) for w,s in itertools.product(range(d["w"]+1),range(d["s"]+1)))
    if task == "box_surface":
        a,b,c = d["a"],d["b"],d["c"]
        return a*a+b*b+c*c+2*min(a*b,a*c,b*c)
    if task == "unseen_target":
        possible = set(range(d["n"]))-set(range(d["misses"]))
        # Every still-possible target has the same likelihood for these misses.
        return F(sum(x == min(possible) for x in possible),len(possible))
    if task == "coupon_remaining":
        n = d["n"]
        expectation = {frozenset(range(n)):F()}
        for size in range(n-1,d["seen"]-1,-1):
            for known in map(frozenset,itertools.combinations(range(n),size)):
                new = [x for x in range(n) if x not in known]
                # One step plus next-state expectations; move self loops to the left.
                expectation[known] = (n+sum(expectation[known|{x}] for x in new))/F(len(new))
        return expectation[frozenset(range(d["seen"]))]
    if task == "linear_orders":
        @lru_cache(None)
        def count(prefix):
            if len(prefix) == d["n"]:
                return 1
            return sum(count((*prefix,x)) for x in range(d["n"]) if x not in prefix and all(a in prefix for a,b in d["edges"] if b == x))
        return count(())
    if task == "elevator_distance":
        low,high,start = d["low"],d["high"],d["start"]
        frontier = {(start,int(start==low)|2*int(start==high))}
        visited = set(frontier)
        for distance in range(2*(max(start,high)-min(start,low))+1):
            if any(mask==3 for _,mask in frontier):
                return distance
            nxt = set()
            for position,mask in frontier:
                for dest in (position-1,position+1):
                    if min(start,low) <= dest <= max(start,high):
                        nxt.add((dest,mask|int(dest==low)|2*int(dest==high)))
            frontier = nxt-visited
            visited |= frontier
        raise AssertionError("No route between integer floors")
    if task == "weighted_completion":
        costs=[]
        for order in itertools.permutations([(d["a"],d["wa"]),(d["b"],d["wb"])]):
            time=cost=0
            for duration,weight in order:
                time += duration
                cost += weight*time
            costs.append(cost)
        return min(costs)
    if task == "set_cover":
        masks=[sum(1<<x for x in set(items)) for items in d["sets"]]
        full=(1<<d["n"])-1
        counts=[]
        for selected in itertools.product((0,1),repeat=len(masks)):
            union=0
            for include,mask in zip(selected,masks,strict=True):
                if include:
                    union |= mask
            if union==full:
                counts.append(sum(selected))
        return min(counts)
    if task == "measurement_cover":
        pairs=set(itertools.combinations(range(len(d["patterns"])),2))
        differences=[{(a,b) for a,b in pairs if d["patterns"][a][i] != d["patterns"][b][i]} for i in range(len(d["patterns"][0]))]
        return min(len(cols) for k in range(len(differences)+1) for cols in itertools.combinations(range(len(differences)),k) if set().union(*(differences[i] for i in cols))==pairs)
    if task == "majority_error":
        p,total=F(d["p"]),F()
        for word in itertools.product((0,1),repeat=d["trials"]):
            if sum(word)>d["trials"]//2:
                weight=F(1)
                for wrong in word:
                    weight *= p if wrong else 1-p
                total += weight
        return total
    if task == "sample_miss":
        samples=list(itertools.combinations(range(d["n"]),d["k"]))
        return F(sum(all(x>=d["d"] for x in sample) for sample in samples),len(samples))
    if task == "first_choices":
        return max(sum(item==d["prefs"][i][0] for i,item in enumerate(assignment)) for assignment in allowed_assignments(d["prefs"]))
    if task == "matching_count":
        return len(allowed_assignments(d["prefs"]))
    if task == "all_visited":
        outcomes=list(itertools.product(range(d["n"]),repeat=d["visits"]))
        return F(sum(len(set(word))==d["n"] for word in outcomes),len(outcomes))
    if task == "hat_expectation":
        # A concrete correlated policy copies the next person's hat. It attains
        # n/k. More generally, fix every visible hat: exactly one of k equally
        # weighted own colors matches ANY deterministic guess at that view.
        words=list(itertools.product(range(d["colors"]),repeat=d["n"]))
        total=sum(sum(hats[i]==hats[(i+1)%d["n"]] for i in range(d["n"])) for hats in words)
        return F(total,len(words))
    if task == "urn_optimum":
        scores=[]
        for red_a in range(d["red"]+1):
            for white_a in range(d["white"]+1):
                red_b,white_b=d["red"]-red_a,d["white"]-white_a
                if red_a+white_a and red_b+white_b:
                    scores.append((F(red_a,red_a+white_a)+F(red_b,red_b+white_b))/2)
        return max(scores)
    if task == "signed_codes":
        predictions=set()
        for counterfeit in range(len(d["vectors"])):
            for deviation in (-1,1):
                predictions.add(tuple(deviation*coefficient for coefficient in d["vectors"][counterfeit]))
        return len(predictions)
    if task == "timed_patterns":
        return len(list(itertools.product(range(d["rounds"]+1),repeat=d["tasters"])))
    if task == "unknown_weight_minimax":
        worst=[]
        for size in range(1,d["n"]//2+1):
            outcomes=Counter()
            for counterfeit,deviation in itertools.product(range(d["n"]),(-1,1)):
                difference=deviation if counterfeit<size else -deviation if counterfeit<2*size else 0
                outcomes[(difference>0)-(difference<0)] += 1
            worst.append(max(outcomes.values()))
        return min(worst)
    if task == "subtraction_game":
        @lru_cache(None)
        def wins(n):
            return any(not wins(n-step) for step in d["moves"] if step<=n)
        return sum(not wins(n) for n in range(1,d["n"]+1))
    raise AssertionError(f"No independent oracle: {task}")


@pytest.mark.parametrize("case",CHECKS,ids=lambda c:c["key"])
def test_each_case_against_independent_oracle(case):
    actual=BY_KEY[case["key"]]
    expected=str(F(oracle(case["task"],case["inputs"])))
    assert case["expected"]==expected
    assert [q["en"] for q in actual["choices"]]==["No winner" if x=="no_winner" else x for x in case["options"]]
    for lang in ("he","en"):
        assert actual["choices"][actual["correct"]][lang]==expected
        assert len([x for x in actual["choices"] if x[lang]==expected])==1
    assert actual["status"]=="draft"
    assert case["method"] and case["professional_review"]=="pending"


def test_content_contract_and_real_interview_links():
    assert len(CARDS)==35 and len(ROWS)==len(CHECKS)==175
    assert {q["id"] for q in CARDS}=={f"quick-sw-{i}" for i in range(201,236)}
    assert len(BY_KEY)==175
    assert {q["task"] for q in CHECKS}.__len__()==35
    old=[]
    for path in CONTENT.glob("fundamentals-*.json"):
        data=json.loads(path.read_bytes())
        if isinstance(data,list):
            old.extend(q for q in data if int(q["id"].split("-")[-1])<=200)
    assert len([q for q in old if q["topic"]=="reasoning"])==140
    for card in CARDS:
        assert card["topic"]=="reasoning" and card["interviewIds"]
        for reference in card["interviewIds"]:
            assert list((ROOT/"interview_preparation/questions").glob(reference.lower()+"-*.md"))
        variants=[row for row in ROWS if row["source_key"]==card["id"]]
        assert sorted(q["variant"] for q in variants)==[1,2,3,4,5]
        assert len({q["correct"] for q in variants})==4
        for lang in ("he","en"):
            assert len({q["prompt"][lang] for q in variants})==5
            for field,limit in (("title",12),("prompt",50),("answer",65),("takeaway",20)):
                text=card[field][lang]
                assert 0<len(text.split())<=limit,(card["id"],lang,field)
                assert text==text.strip() and not re.search(r"\bTODO\b|\ufffd",text)
            for field in ("title","prompt"):
                assert card[field][lang].casefold() not in {q[field][lang].casefold() for q in old}


def test_bilingual_text_and_numbers_are_consistent():
    spec=importlib.util.spec_from_file_location("reasoning500_text_rules",ROOT/"backend/scripts/quiz_authoring/assemble.py")
    assembler=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(assembler)
    for row in ROWS:
        for field,text in [("prompt",row["prompt"]),("explanation",row["explanation"]),*[("choice",x) for x in row["choices"]]]:
            for lang in ("he","en"):
                assert not assembler.text_issues(text[lang],lang,field),(row["key"],field,lang)
            def numbers(s):
                return Counter(re.findall(r"(?<!\w)-?\d+(?:\.\d+)?",s))
            assert numbers(text["he"])==numbers(text["en"]),(row["key"],field,text)


def test_counterexamples_distinguish_neighboring_objectives():
    # Shared-neighbor events are dependent; never silently square 1/n.
    assert oracle("overlapping_neighbors",{"n":5}) != F(1,25)
    # Overall ranking ties can leave a nonzero pairwise margin.
    assert oracle("voting_margin",{"m":5,"x":1})==3
    # The ferry goal requires sheep only, not all animals: two sheep cross once.
    assert ferry_oracle({"w":2,"s":2,"forward":[2],"backward":[1]})==1
    assert ferry_oracle({"w":3,"s":3,"forward":[2],"backward":[1]})==-1
    assert ferry_oracle({"w":3,"s":3,"forward":[1,2],"backward":[1,2]})==7
    # Rotational symmetry: all-equal words have fewer than n representations.
    assert oracle("necklaces",{"n":4})==6
    assert oracle("first_choices",{"prefs":[[0,1],[0,1]]})==1
    assert oracle("matching_count",{"prefs":[[0,1],[0,1]]})==2
    assert oracle("hat_expectation",{"n":5,"colors":2})==F(5,2)


def test_distractors_respect_the_problem_domain_and_address_common_errors():
    for case in CHECKS:
        options=case["options"]
        if case["task"]=="agenda":
            assert set(options)=={"0","1","2","no_winner"}
        elif case["task"]=="nested_mean":
            assert all(0<=F(value)<=case["inputs"]["n"] for value in options)
        elif case["task"]=="overlapping_neighbors":
            assert str(F(1,case["inputs"]["n"]**2)) in options


def test_generation_is_reproducible_without_overwriting_old_content():
    spec=importlib.util.spec_from_file_location("reasoning500_author",ROOT/"backend/scripts/quiz_authoring/reasoning_500.py")
    author=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(author)
    cards,rows,checks=author.build_bundle()
    assert cards==CARDS and rows==ROWS and checks==CHECKS
