"""Independent checks for 500 new bounded cases, plus exhaustive small domains.

Oracles consume the recorded inputs, never the author model or answer index.
Electrical checks solve the stated ideal equations only. No HDL is compiled and
no physical circuit, metastability, SPICE or silicon behavior is asserted here.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import re
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / 'apps/web/src/content'
SHARDS = ROOT / 'backend/seeds/duel_quiz_batches'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


CARDS = read(CONTENT / 'fundamentals-hardware-700.json')
QUIZ = read(SHARDS / 'hardware_700.json')
CHECKS = read(SHARDS / 'hardware_700.checks.json')
BY_KEY = {q['key']: q for q in QUIZ}


def norm(v):
    if isinstance(v, F): return v.numerator if v.denominator == 1 else str(v)
    return v


def unsigned_bits(x, width):
    return [(x // (2 ** i)) % 2 for i in range(width)]


def parallel(*resistors):
    return 1 / sum((F(1, r) for r in resistors), F(0))


def product_by_addition(values):
    result = 1
    for v in values:
        result = sum(result for _ in range(v))
    return result


def oracle(n, p):
    if '_query' in p: return alternate_oracle(n, p)
    if n == 251:
        registers = {'S':p['s'],'P':p['p']}
        if p['reset']: return [0,0]
        plus_ready = (p['busy']==0) or (p['done']==p['bypass']==1)
        read_operand = registers['P']
        if p['done'] and p['bypass']: read_operand=p['product']
        if p['done']: registers['P']=p['product']
        if plus_ready: registers['S']+=read_operand
        return [registers['S'],registers['P']]
    if n == 252:
        bits=unsigned_bits(p['initial'],p['w']);flag=p['overflow']
        for reset,term in p['events']:
            if reset:bits=[0]*p['w'];flag=0;continue
            carry=0
            for index,b in enumerate(unsigned_bits(term,p['w'])):
                ones=bits[index]+b+carry
                bits[index]=ones%2;carry=int(ones>=2)
            flag=int(bool(flag or carry))
        return [sum(b*2**i for i,b in enumerate(bits)),flag]
    if n == 253:
        active=[]
        for reset,equal,value in p['events']:
            if reset:active=[]
            elif equal:active.append(value)
        reset,equal,_=p['events'][-1]
        return [active[-1] if active else 0,int(equal and not reset)]
    if n == 254:
        acc = 1
        for factor in p['factors']:
            acc = sum(acc for _ in range(factor))
            acc = sum(bit * 2 ** i for i, bit in enumerate(unsigned_bits(acc, p['w'])))
        return acc
    if n == 255: return len([1 for pair in p['vr'] if pair == [1, 1]])
    if n == 256: return F(p['i']) * F(p['r'], 1000) * 1000
    if n == 257:
        source_ground = 0
        load_ground = source_ground + p['i'] * p['rg']
        load_power = p['vs'] - p['i'] * p['rs']
        return load_power - load_ground
    if n == 258: return p['common'] + parallel(*([p['branch']] * p['paths']))
    if n == 259:
        old_v, old_i = 1, 1
        new_i, new_v = p['factor'] * old_i, p['factor'] * old_v
        return F(new_v * new_i, old_v * old_i)
    if n == 260:
        coulombs = F(p['i'] * p['us'], 1_000_000)
        farads = F(p['uf'], 1_000_000)
        return coulombs / farads * 1000
    if n == 261:
        bits = unsigned_bits(p['x'], 4)
        majority = any(all(bits[i] for i in triple) for triple in itertools.combinations(range(4), 3))
        parity = 0
        for b in bits: parity ^= b
        return [int(0 in bits), int(majority), parity, int(not parity)]
    if n == 262:
        a, b, c = unsigned_bits(p['x'], 3)
        return a + 2 * (b ^ (a & c)) + 4 * c
    if n == 263: return sum(a == 1 and b == 0 for a, b in zip(unsigned_bits(p['a'], p['w']), unsigned_bits(p['b'], p['w']), strict=True))
    if n == 264:
        nand = {(0,0): 1, (0,1): 1, (1,0): 1, (1,1): 0}
        t = nand[p['a'],p['b']]
        return [t, nand[t,t], int(p['a'] == p['b'] == 0)]
    if n == 265:
        forbidden = (1,0)
        a, b, c = p['abc']
        return [int(pair != forbidden) for pair in [(a,b),(b,c),(a,c)]]
    if n == 266:
        groups, joins = p['inputs'], 0
        while groups > 1: groups, joins = groups - 1, joins + 1
        return joins
    if n == 267:
        path = ['final']
        if p['selected'] != 0: path.extend(['tree'] * p['other_depth'])
        return len(path)
    if n == 268: return sum((2 ** k) * int(k == p['select'] and p['enable']) for k in range(8))
    if n == 269:
        broken = list(p['data'])
        broken[p['fault']] = p['stuck']
        return [p['data'][p['select']], broken[p['select']]]
    if n == 270: return len([address for address in range(len(p['data'])) if p['data'][address] == 1])
    if n in {271,272}:
        decimal = str(sum(p['x'] for _ in range(5))).zfill(2)
        return int(decimal[-1] if n == 271 else decimal[-2])
    if n == 273:
        bits = f"{p['x']:08b}"
        return [int(bits[:4],2), int(bits[4:],2)]
    if n == 274:
        digits = str(p['x']).zfill(2)
        return int(''.join(f'{int(d):04b}' for d in digits), 2)
    if n == 275: return len([x for x in range(p['limit']+1) if str(x).zfill(2)[-2] == str(p['tens'])])
    if n == 276:
        gray_bits = f"{p['g']:04b}"
        binary = [int(gray_bits[0])]
        for b in gray_bits[1:]: binary.append(binary[-1] ^ int(b))
        return int(''.join(map(str, binary)),2)
    if n == 277:
        current, count = p['read'], 0
        while current != p['write']: current, count = (current+1) % p['modulus'], count+1
        return count
    if n == 278:
        # Replay old-state sequential updates; acceptance precedes edge updates.
        synchronizer = [0] * p['stages']
        empty = True
        for edge in range(1, 30):
            if not empty: return edge
            old_last = synchronizer[-1]
            synchronizer = [int(edge >= p['capture'])] + synchronizer[:-1]
            empty = not (old_last if p['flag'] else synchronizer[-1])
    if n == 279:
        # Reflected binary Gray sequence constructed by reflection, not b^(b>>1).
        sequence = ['']
        for _ in range(4): sequence = ['0'+s for s in sequence] + ['1'+s for s in reversed(sequence)]
        return sum(a != b for a,b in zip(sequence[p['a']],sequence[p['b']], strict=True))
    if n == 280:
        observed_live = list(range(p['seen_read'], p['write']))
        slots = [None] * p['depth']
        for i, tag in enumerate(observed_live): slots[i] = tag
        return slots.count(None)
    if n == 281:
        history=[]
        for value in p['samples']:
            history.append(value)
            if len(history)>3: history.pop(0)
        return [max(history), sum(history)-min(history)-max(history), min(history)]
    if n == 282: return sum(p['samples'])-min(p['samples'])-max(p['samples'])
    if n == 283:
        last_reset = max([-1] + [i for i,(reset,_) in enumerate(p['rv']) if reset])
        return min(3, len([1 for _, valid in p['rv'][last_reset+1:] if valid]))
    if n == 284:
        values=list(p['samples'])
        for a,b in [(0,1),(1,2)]:
            if values[a]>values[b]: values[a],values[b]=values[b],values[a]
        return values
    if n == 285:
        pairs=list(zip(p['values'],p['tags'],strict=True))
        for a,b in [(0,2),(0,1),(1,2)]:
            if pairs[a][0]>pairs[b][0]: pairs[a],pairs[b]=pairs[b],pairs[a]
        return [tag for _,tag in pairs]
    if n == 286: return next(t for t in range(100) if all(t-d>=p['overhead'] for d in p['delays']))
    if n == 287:
        completions = [i*p['ii']+p['latency'] for i in range(p['count'])]
        return completions[-1] if completions else 0
    if n == 288:
        unpipelined=sum(sum(p['delays']) for _ in range(p['count']))
        last=0
        for i in range(p['count']): last=(i+len(p['delays']))*max(p['delays'])
        return F(unpipelined,last)
    if n == 289:
        registers=[None]*p['stages']; offered='token'
        for edge in range(1,100):
            if edge in p['stalls']: continue
            registers=[offered]+registers[:-1]; offered=None
            if registers[-1]=='token': return edge
    if n == 290: return next(interval for interval in range(1,100) if all(interval>=stage for stage in p['ii']))
    if n == 291:
        transition={(0,1):2,(2,1):0}
        return [transition[(0 if direction=='up' else 2),1] for direction in p['directions']]
    if n == 292:
        phase=p['phase']
        for _ in range(p['edges']): phase={0:1,1:2,2:3,3:0}[phase]
        return {0:0,1:1,2:2,3:1}[phase]
    if n == 293: return sum(oracle(292,dict(phase=0,edges=k))==1 for k in range(1,p['edges']+1))
    if n == 294:
        people=list(range(p['initial'])); rejected=0
        for event in p['events']:
            if event==1 and len(people)<p['capacity']: people.append('person')
            elif event==-1 and people: people.pop()
            elif event!=0: rejected+=1
        return [len(people),rejected]
    if n == 295:
        a,b=p['lower'],p['upper']; exits=0
        while bool(a)==bool(b): a,b,exits=a-1,b-1,exits+1
        return exits
    if n == 296:
        maximum=sum((2**p['w']-1) for _ in range(3))
        return next(w for w in range(32) if all(x<2**w for x in [0,maximum]))
    if n == 297:
        intermediate = unsigned_sum(unsigned_sum(p['x'],p['x'],p['w']),p['x'],p['w'])
        return int(f'{intermediate:b}'+'0000',2)+p['x']
    if n == 298: return next(k for k in range(100) if sum(k for _ in range(16))+1==p['target'])
    if n == 299: return sum(p['x'] for _ in range(49)) & 15
    if n == 300:
        product=sum(p['x'] for _ in range(49))
        return int(f'{product:0{p["w"]+1}b}'[:-p['w']],2)
    if n == 301: return parallel(p['r'],p['r'],p['r'])
    if n == 302:
        vertices=list(itertools.product((0,1),repeat=p['dimension']))
        return sum(sum(a)==p['layer'] and sum(b)==p['layer']+1 and sum(x!=y for x,y in zip(a,b,strict=True))==1
                   for a in vertices for b in vertices)
    if n == 303:
        return parallel(*([p['r']]*3)) + parallel(*([p['r']]*6)) + parallel(*([p['r']]*3))
    if n == 304:
        # Equate unit-source midpoint voltage, then solve the right divider.
        left=F(p['r2'],p['r1']+p['r2'])
        return left*p['r3']/(1-left)
    if n == 305:
        # Unit test current flows from one midpoint to ground and up the other.
        return 1/(F(1,p['r1'])+F(1,p['r2'])) + 1/(F(1,p['r3'])+F(1,p['r4']))
    if n == 306:
        # Unit Vin: current through Rg also traverses Rf by input KCL.
        current=F(1,p['rg'])
        return 1+current*p['rf']
    if n == 307:
        # Unit output needs Vin=feedback+finite differential voltage.
        if p['a']==0:return 0
        return 1/(F(1,p['den'])+F(1,p['a']))
    if n == 308: return F(p['ib'],1_000_000)*p['r']*1000*1000
    if n == 309:
        demand=p['gain']*p['vin']
        if demand<p['low']:return p['low']
        if demand>p['high']:return p['high']
        return demand
    if n == 310:return F(-p['vin'],p['rc'])
    if n == 311:
        v=F(p['start'])
        for vin,duration in p['segments']:
            for _ in range(duration):v-=F(vin,p['rc'])
        return v
    if n == 312:
        error=F(p['initial_error'])
        for _ in range(p['halvings']):error/=2
        return error
    if n == 313:
        current=F(p['vs'],p['top']+p['bottom'])
        return p['vs']-current*p['top']
    if n == 314:
        ratio=F(1)
        for _ in range(abs(p['k'])):ratio*=2 if p['k']>=0 else F(1,2)
        return ratio-1
    if n == 315:
        # Set total depletion width to one and enforce charge neutrality.
        xp=F(p['nd'],p['na']+p['nd']);xn=1-xp
        assert xp*p['na']==xn*p['nd']
        return xp/xn
    if n == 316:
        scan_duration=F(p['channels'],p['aggregate'])
        return 1/scan_duration
    if n == 317:
        sample_times=[k*p['slot'] for k in range(max(p['first'],p['last'])+1)]
        return sample_times[p['last']]-sample_times[p['first']]
    if n == 318:
        bits=[None for _ in range(p['samples']) for _ in range(p['channels']) for _ in range(p['bits'])]
        return len(list(zip(*[iter(bits)]*8)))
    if n == 319:
        error=F(1);limit=F(1,2**p['bits'])/2;steps=0
        while error>limit:error/=2;steps+=1
        return steps
    if n == 320:
        thresholds=[F(k*p['fs'],2**p['bits']) for k in range(1,2**p['bits'])]
        return sum(p['mv']>=t for t in thresholds)
    if n == 321:
        one_sample=F(1,p['fs']);cycle=F(1,p['fout'])
        return int(cycle/one_sample)
    if n == 322:
        phase=p['phase']
        if phase>=p['period']//2:phase-=p['period']//2
        reflected=p['period']//2-phase
        return phase if phase<=reflected else reflected
    if n == 323:
        full=p['first']+[-v for v in p['first']]
        return full[p['phase']]
    if n == 324:
        advances=len([x for x in p['en'] if x==1])
        elapsed=F(len(p['en']),p['clock'])
        return F(advances,p['period'])/elapsed
    if n == 325:return len(range(0,p['period']//4+1))
    if n == 326:return parallel(*[p['r'] for gate in p['gates'] if gate==0])
    if n == 327:return sum(p['r'] for _ in range(p['series']))
    if n == 328:
        charge_ratio=F(p['voltage_num'],p['voltage_den'])
        energy_ratio=charge_ratio*charge_ratio
        events_ratio=F(p['activity_num']*p['freq'],p['activity_den'])
        return energy_ratio*events_ratio
    if n == 329:
        nm,pm=p['corner'];delay={'F':2,'S':5}
        return delay[pm] if p['edge']=='rise' else delay[nm]
    if n == 330:
        return next(t for t in range(2000) if t+p['skew']-p['setup']-p['uncertainty']>=p['cq']+p['data'])
    if n == 331:
        return next(d for d in range(1000) if p['cq']+p['data']+d>=p['skew']+p['hold']+p['uncertainty'])
    if n == 332:
        deadline=p['capture']-p['setup'];arrival=p['launch']+p['cq']+p['data']
        return deadline-arrival
    if n == 333:
        legal=[s for s in range(-1000,1001) if p['cqmax']+p['dmax']<=p['period']+s-p['setup'] and p['cqmin']+p['dmin']>=s+p['hold']]
        return legal[-1]-legal[0] if legal else 0
    if n == 334:return next(delta for delta in range(1000) if all(slack+delta>=0 for slack in p['slacks']))
    if n == 335:return sorted(p['slacks'])[0]
    if n == 336:
        # Incident voltage normalized to 1. Solve load V=I*R and line V=1+b,I=(1-b)/Z0.
        return (F(p['load'],p['z0'])-1)/(F(p['load'],p['z0'])+1)
    if n == 337:
        incident_current=F(p['vs'],p['rs']+p['z0'])
        return p['vs']-incident_current*p['rs']
    if n == 338:return sum([p['flight'],p['flight']])
    if n == 339:
        # Load KCL with available wave source 2A and series impedance Z0.
        current=F(2*p['incident'],p['z0']+p['load'])
        return current*p['load']
    if n == 340:return next(r for r in range(1000) if r-p['z0']==0)
    if n == 341:
        paths=[(v,) for v in range(p['nodes'])]
        for _ in range(p['nodes']):
            paths += [path+(b,) for path in paths[:] for a,b in p['edges'] if path[-1]==a and b not in path]
        return max(map(len,paths))
    if n == 342:
        lengths=[];current=0
        for char in p['kinds']:
            current=current+1 if char=='B' else 0;lengths.append(current)
        return max(lengths,default=0)
    if n == 343:return len([x for x in p['endpoint_lengths'] if x>=p['limit']+1])
    if n == 344:
        excluded=0
        for roles in p['roles']:
            if len(roles)==0:continue
            if all(role=='reset' or role=='clock' for role in roles):excluded+=1
        return excluded
    if n == 345:
        # Remove by indegree queue; descendants of cycles remain as well.
        degree=[sum(b==v for _,b in p['edges']) for v in range(p['nodes'])]
        queue=[v for v,d in enumerate(degree) if d==0];removed=[]
        while queue:
            v=queue.pop(0);removed.append(v)
            for a,b in p['edges']:
                if a==v:
                    degree[b]-=1
                    if degree[b]==0:queue.append(b)
        return p['nodes']-len(removed)
    if n == 346:
        counter=0
        for b in p['bits']:
            if b and counter<3:counter+=1
        return counter
    if n == 347:
        bits=p['bits'][:];changes=0
        while sum(bits)<=2:
            bits[bits.index(0)]=1;changes+=1
        return changes
    if n == 348:return len([d for d in range(2,p['n']+1) if d*d<=p['n']])
    if n == 349:return sum(len([d for d in range(1,x+1) if x%d==0])==2 for x in p['numbers'])
    if n == 350:
        factors=[d for d in range(2,p['n']) if p['n']%d==0 and d*d<=p['n']]
        return min(factors,default=0)
    raise AssertionError(n)


def unsigned_sum(a,b,width):
    carry=0;result=0
    for bit in range(width):
        ones=((a>>bit)&1)+((b>>bit)&1)+carry
        result|=(ones%2)<<bit;carry=int(ones>=2)
    return result


def alternate_oracle(n,p):
    q=p['_query']
    if n==264:
        nand={(0,0):1,(0,1):1,(1,0):1,(1,1):0}
        t=nand[p['a'],p['b']]
        return [t,nand[t,p['a']],int(p['a']==p['b']==0)]
    if n==301:
        if q=='recover_branch':return p['equivalent']/F(1,3)
        if q=='total_current':return sum(F(p['v'],p['r']) for _ in range(3))
        if q=='branch_current':return F(p['total'],3)
        return parallel(p['r'],p['r'])
    if n==302:
        if q=='six_currents':return sum(p['current'] for _ in range(6))
        if q=='recover_six':return p['equivalent']/F(1,6)
        if q=='current_split':return F(p['total'],6)
        return sum(F(1,p['r']) for _ in range(6))
    if n==303:
        if q=='scale':return oracle(303,{'r':p['new']})/oracle(303,{'r':p['old']})
        equivalent=oracle(303,{'r':p['r']})
        if q=='voltage':return equivalent*p['current']
        if q=='current':return F(p['voltage'])/equivalent
        voltage=equivalent*p['current']
        return voltage*p['current']
    if n==319:
        if q=='time_coefficient':return oracle(319,{'bits':p['bits']})*p['tau']
        error=F(1,2**p['initial_power']);target=F(1,2**p['bits'])/(2**p['margin'] if p['margin']>=0 else F(1,2**(-p['margin'])))
        steps=0
        while error>target:error/=2;steps+=1
        return steps
    if n==321:
        if q=='frequency':return 1/(F(p['samples'],p['fs']))
        if q=='sample_rate':return sum(p['samples'] for _ in range(p['fout']))
        if q=='bits':return len([None for _ in range(p['samples']) for _ in range(p['width'])])
        return list(range(p['samples']))[-1]
    if n==325:
        points=list(range(p['period']//4+1))
        if q=='storage':return len(points)*p['width']
        if q=='wired_zero':return len(points[1:])
        if q=='intervals':return len(list(zip(points,points[1:])))
        return points[-1]
    if n==338:
        if q=='infer_flight':return F(p['roundtrip'],2)
        trips={'load_arrival':['out'],'second_load':['out','back','out'],'absolute_return':['out','back']}[q]
        return sum(p['flight'] for _ in trips)+p.get('launch',0)
    if n==340:
        if q=='positive_source_reflection':return next(r for r in range(1000) if F(r-p['z0'],r+p['z0'])==F(1,2))
        refl=(F(p['rs'],p['z0'])-1)/(F(p['rs'],p['z0'])+1)
        if q=='ideal_source':return refl
        if q=='reflected_amplitude':return refl*p['incident']
        return refl*p['incident']+p['incident']
    raise AssertionError((n,q))


@pytest.mark.parametrize('check',CHECKS,ids=lambda row:row['key'])
def test_each_case_against_independent_input_oracle(check):
    expected=norm(oracle(check['task'],check['inputs']))
    assert expected==check['expected']
    assert sum(option==expected for option in check['options'])==1
    question=BY_KEY[check['key']]
    assert check['options'][question['correct']]==expected
    rendered=json.dumps(expected,separators=(',',':')) if isinstance(expected,list) else str(expected)
    assert question['choices'][question['correct']]==dict(he=rendered,en=rendered)


def test_card_schema_provenance_and_brevity():
    interviews={q['id']:q for q in read(ROOT/'interview_preparation/questions.json')['questions']}
    editorial=read(ROOT/'backend/seeds/preparation_editorial.json')
    prior=[row for file in CONTENT.glob('fundamentals-*.json')
           if file.name not in {'fundamentals-hardware-700.json','fundamentals-reasoning-700.json','fundamentals-code-700.json','fundamentals-revisions.json'} for row in read(file)]
    assert len(CARDS)==100
    assert {c['id'] for c in CARDS}=={f'quick-hw-{n}' for n in range(251,351)}
    assert not ({c['id'] for c in CARDS}&{c['id'] for c in prior})
    for card in CARDS:
        assert card['topic'] in {'gates','bits','sequential','states','electronics'}
        assert card['interviewIds']
        for source in card['interviewIds']:
            assert source in interviews and source in editorial
            assert interviews[source]['category']=='hardware'
            assert set(editorial[source]['reference_solution'])=={'he','en'}
        assert not {'difficulty','company','solution_review','release_approval'}&set(card)
        for field,limit in [('title',12),('prompt',50),('answer',65),('takeaway',20)]:
            assert set(card[field])=={'he','en'}
            for lang,text in card[field].items():
                assert text and text==text.strip() and len(text.split())<=limit,(card['id'],field,lang)
                assert '\ufffd' not in text
                if lang=='en':assert not re.search(r'[\u0590-\u05ff]',text)
    for lang,field in itertools.product(('he','en'),('title','prompt')):
        old={c[field][lang].casefold().strip() for c in prior}
        new=[c[field][lang].casefold().strip() for c in CARDS]
        assert len(new)==len(set(new)) and not old.intersection(new)


def test_quiz_shape_drafts_coverage_difficulty_and_answer_balance():
    assert len(QUIZ)==len(CHECKS)==len(BY_KEY)==500
    for card in CARDS:
        qs=[q for q in QUIZ if q['source_key']==card['id']]
        checks=[c for c in CHECKS if c['key'].startswith(card['id']+'-')]
        assert sorted(q['variant'] for q in qs)==[1,2,3,4,5]
        assert len({c['coverage'] for c in checks})==5
        assert len({c['difficulty'] for c in checks})==len({c['difficulty_rationale'] for c in checks})==1
        assert all(type(c['difficulty']) is int and 1<=c['difficulty']<=10 and c['difficulty_rationale'] for c in checks)
        for lang in ('he','en'):
            assert len({q['prompt'][lang] for q in qs})==5
        for q in qs:
            assert q['key']==f"{q['source_key']}-v{q['variant']}"
            assert q['status']=='draft' and q['topic']==card['topic']
            assert len(q['choices'])==4 and type(q['correct']) is int and 0<=q['correct']<4
            for lang in ('he','en'):
                assert len({x[lang] for x in q['choices']})==4
                for text in [q['prompt'][lang],q['explanation'][lang],*(x[lang] for x in q['choices'])]:
                    assert text and text==text.strip() and '\ufffd' not in text
                    if lang=='en':assert not re.search(r'[\u0590-\u05ff]',text)
    assert Counter(q['correct'] for q in QUIZ)=={0:125,1:125,2:125,3:125}


def test_reproducible_generated_artifacts():
    spec=importlib.util.spec_from_file_location('hardware700',ROOT/'backend/scripts/quiz_authoring/hardware_700.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    quiz,checks=module.build()
    assert quiz==QUIZ and checks==CHECKS and module.CARDS==CARDS


def test_small_domain_oracles_and_material_counterexamples():
    for x in range(16):
        predicates=oracle(261,dict(x=x));count=f'{x:04b}'.count('1')
        assert predicates==[int(count<4),int(count>2),count%2,1-count%2]
    for x in range(8):assert oracle(262,dict(x=x))=={5:7,7:5}.get(x,x)
    for triple in itertools.product(range(4),repeat=3):
        assert oracle(282,dict(samples=list(triple)))==sorted(triple)[1]
    assert oracle(278,dict(capture=1,stages=2,flag=1))==4
    assert oracle(278,dict(capture=1,stages=2,flag=0))==3
    assert oracle(294,dict(capacity=1,initial=0,events=[-1,1,1,-1]))==[0,2]
    assert oracle(297,dict(w=4,x=6))==38 and 49*6==294
    assert oracle(345,dict(nodes=3,edges=[[0,1],[1,0],[1,2]]))==3
    assert oracle(348,dict(n=49))==6
    assert oracle(350,dict(n=49))==7
