"""Exact independent outcome enumeration, plus existing100-hat protocol witnesses."""
import hashlib
import importlib.util
import itertools
import json
from fractions import Fraction
from pathlib import Path
from random import Random

BANK=Path(__file__).resolve().parents[1]
SOURCE=BANK/'solutions/prep_308_factory_posterior_1108b20.py'
spec=importlib.util.spec_from_file_location('factory_posterior_1108b20',SOURCE)
candidate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def enumerate_worlds(pa,pb,q):
    evidence=Fraction(0);both=Fraction(0);a_good=Fraction(0)
    for factory,rate,prior in [('A',pa,q),('B',pb,1-q)]:
        for first,second in itertools.product((0,1),repeat=2):
            mass=prior*(rate if first else 1-rate)*(rate if second else 1-rate)
            if first:
                evidence+=mass
                if second:both+=mass
                if factory=='A':a_good+=mass
    if evidence==0:return None
    return {'first_good':evidence,'factory_a':a_good/evidence,
            'factory_b':1-a_good/evidence,'second_good':both/evidence}


def run():
    counts={'primary_equal_prior_grid':0,'general_prior_grid':0,'zero_evidence_rejections':0,
            'seeded_exact_rationals':0,'invalid_probability_rejections':0,
            'hat_small_worlds':0,'hat_hundred_person_worlds':0}
    rates=[Fraction(i,12) for i in range(13)]
    priors=[Fraction(i,6) for i in range(7)]
    for pa,pb in itertools.product(rates,repeat=2):
        expected=enumerate_worlds(pa,pb,Fraction(1,2))
        if expected is not None:
            got=candidate.posterior_quality(pa,pb)
            assert got==expected['second_good']
            assert got==candidate.posterior_quality(pb,pa)
            assert got>=(pa+pb)/2
            assert min(pa,pb)<=got<=max(pa,pb)
            assert got-(pa+pb)/2==(pa-pb)**2/(2*(pa+pb))
            counts['primary_equal_prior_grid']+=1
        for q in priors:
            expected=enumerate_worlds(pa,pb,q)
            if expected is None:
                try:candidate.posterior_details(pa,pb,q)
                except ValueError:counts['zero_evidence_rejections']+=1
                else:raise AssertionError('impossible evidence accepted')
            else:
                assert candidate.posterior_details(pa,pb,q)==expected
                counts['general_prior_grid']+=1
    rng=Random(308)
    for _ in range(1000):
        pa=Fraction(rng.randrange(101),100);pb=Fraction(rng.randrange(101),100)
        q=Fraction(rng.randrange(101),100)
        expected=enumerate_worlds(pa,pb,q)
        if expected is not None:
            assert candidate.posterior_details(pa,pb,q)==expected
            counts['seeded_exact_rationals']+=1
    assert candidate.posterior_quality(1,0)==1
    assert candidate.posterior_quality(Fraction(3,4),Fraction(1,4))==Fraction(5,8)
    for p in rates[1:]:assert candidate.posterior_quality(p,p)==p
    for invalid in [-1,2,Fraction(-1,2),Fraction(3,2),0.5,True,None,'0.5']:
        try:candidate.posterior_quality(invalid,Fraction(1,2))
        except ValueError:counts['invalid_probability_rejections']+=1
        else:raise AssertionError('invalid probability accepted')

    # Independent sequential parity simulation; replies see only visible hats and heard replies.
    def simulate(hats):
        heard=[]
        for index in range(len(hats)-1,-1,-1):
            visible=hats[:index]
            answer=0
            for bit in (*visible,*heard):answer^=bit
            heard.append(answer)
        correct=[answer==hats[index] for answer,index in zip(heard,range(len(hats)-1,-1,-1))]
        assert all(correct[1:])
        return sum(correct)
    for n in range(1,13):
        for hats in itertools.product((0,1),repeat=n):
            assert simulate(hats)>=n-1
            counts['hat_small_worlds']+=1
    for _ in range(256):
        front=[rng.randrange(2) for _ in range(99)]
        parity=sum(front)%2
        assert simulate((*front,1-parity))==99
        assert simulate((*front,parity))==100
        counts['hat_hundred_person_worlds']+=2
    report={'result':'passed','counts':counts,'exact_case_total':sum(counts.values()),
            'bayes_oracle':'Explicit eight-world factory/first/second outcome enumeration with exact Fraction weights.',
            'hat_scope':'Independent finite protocol checks support the new096 diagram; the old implementation is not replaced.',
            'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'limitations':['Finite grids do not constitute enumeration of all real-valued probabilities; algebra proves the general identity.',
                           'No MonteCarlo or chip manufacturing experiment is claimed.',
                           'Internal difficulty is an editorial estimate; no professional human approval is claimed.']}
    (BANK/'checks/1108b20-reasoning-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':run()
