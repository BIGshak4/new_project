"""Independent finite oracles and deterministic subprocess/HTTP-model cases.

No external HTTP requests or live product learner writes. RTL compilation is a
separate check; running this file does not constitute HDL execution.
"""
import ast
import contextlib
import importlib.util
import io
import itertools
import json
import tempfile
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SOL = ROOT / "solutions"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SOL / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fails(function, *args, kind=ValueError, **kwargs):
    try:
        function(*args, **kwargs)
    except kind:
        return
    raise AssertionError("expected exception")


def check_prime():
    module = load("prep_265_primality")
    limit=20000
    sieve=[True]*(limit+1)
    sieve[0]=sieve[1]=False
    for i in range(2,limit+1):
        if sieve[i]:
            for j in range(2*i,limit+1,i):
                sieve[j]=False
    for n,expected in enumerate(sieve):
        assert module.is_prime(n) is expected
    known={2147483647:True,4294967291:True,4294967295:False,
           4294836225:False,65521*65521:False,65537:True}
    for n,expected in known.items():
        assert module.is_prime(n) is expected
    for n in (-1,1.5,True,"2"):
        fails(module.is_prime,n)
    return {"exhaustive_nonnegative_through":limit,"boundary_cases":len(known),
            "invalid_cases":4,"oracle":"independent full-range sieve plus known integer identities",
            "hdl_executed_by_this_check":False}


def check_process():
    module=load("prep_266_script_status")
    with tempfile.TemporaryDirectory(prefix="prep266-") as directory:
        path=Path(directory)/"child.py"
        cases=[("print('product')\n", "exited_zero",0,"product\n"),
               ("print('product')\nraise SystemExit(7)\n","failed",7,"product\n"),
               ("print('product',flush=True)\nraise RuntimeError('boom')\n","failed",1,"product\n"),
               ("print('WRONG')\n","exited_zero",0,"WRONG\n")]
        for source,state,code,stdout in cases:
            path.write_text(source,encoding="utf-8")
            result=module.run_python_file(path)
            assert (result['state'],result['returncode'],result['stdout'])==(state,code,stdout)
        path.write_text("import time\ntime.sleep(5)\n",encoding="utf-8")
        assert module.run_python_file(path,timeout=.1)['state']=='timeout'
        assert module.run_python_file(Path(directory)/'missing.py')['state']=='failed'
    with patch.object(module.subprocess,'run',side_effect=OSError('cannot launch')):
        assert module.run_python_file('x.py')['state']=='launch_error'
    with patch.object(module.subprocess,'run',side_effect=UnicodeDecodeError('utf-8',b'\xff',0,1,'bad')):
        assert module.run_python_file('x.py')['state']=='output_encoding_error'
    return {"real_local_subprocess_cases":6,"mock_launch_failure":1,
            "mock_invalid_utf8":1,
            "semantic_zero_exit_counterexample":True,"external_process_sources":False}


class FakeResponse:
    def __init__(self,body,status=200): self.body,self.status=body,status
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,size): return self.body[:size]


def check_http():
    module=load('prep_267_random_joke')
    successes=0
    for value in ('joke','',"עברית\nsecond line",'quotes " and emoji 😄'):
        body=json.dumps({'value':value,'id':'meta'},ensure_ascii=False).encode()
        def opener(request,timeout,body=body):
            assert request.full_url==module.ENDPOINT and timeout==5
            return FakeResponse(body)
        assert module.fetch_joke(opener)==value
        successes+=1
    failures=0
    for body,status in [(b'no',200),(b'[]',200),(b'{}',200),(b'{"value":7}',200),
                        (b'null',200),(b'{"value":null}',200),(b'\xff',200),
                        (b'{"value":"a"}',503),(b'x'*(module.MAX_BYTES+1),200)]:
        fails(module.fetch_joke,lambda request,timeout,body=body,status=status:FakeResponse(body,status),kind=module.JokeError)
        failures+=1
    for exc in (TimeoutError('deadline'),URLError('offline'),
                HTTPError(module.ENDPOINT,404,'missing',{},None),OSError('read failure'),IncompleteRead(b'partial')):
        def opener(request,timeout,exc=exc): raise exc
        fails(module.fetch_joke,opener,kind=module.JokeError)
        failures+=1
    stdout,stderr=io.StringIO(),io.StringIO()
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        assert module.main(lambda:'just joke')==0
    assert stdout.getvalue()=='just joke\n' and stderr.getvalue()==''
    stdout,stderr=io.StringIO(),io.StringIO()
    def bad(): raise module.JokeError('failed')
    with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
        assert module.main(bad)==1
    assert stdout.getvalue()=='' and stderr.getvalue()=='failed\n'
    return {"fake_transport_successes":successes,"fake_transport_failures":failures,
            "cli_output_contracts":2,"external_http_requests":0}


def check_chat():
    module=load('prep_268_client_server_model')
    model=module.ChatModel()
    fails(model.send,'a','1','hello')
    for user in ('a','b'): model.connect(user)
    for i in range(30):
        user=('a','b')[i%2]
        assert model.send(user,str(i),'m'+str(i))==i+1
        assert model.send(user,str(i),'m'+str(i))==i+1
    assert len(model.events)==30
    for cursor in range(31):
        assert [e[0] for e in model.resume('b',cursor)]==list(range(cursor+1,31))
    model.disconnect('b')
    fails(model.resume,'b',0)
    fails(model.send,'b','x','offline')
    model.connect('b')
    assert len(model.resume('b',20))==10
    fails(model.send,'a','0','changed')
    fails(model.send,'a','new','')
    for cursor in (-1,31,True,'0'): fails(model.resume,'a',cursor)
    return {"new_sends":30,"deduplicated_retries":30,"cursor_snapshots":31,
            "invalid_and_disconnected_cases":9,"scope":"application model only; no socket/browser/load test"}


def check_speed():
    module=load('prep_269_speed_tables')
    for n in range(11):
        assert module.gas(n)==min(n+1,10)
        assert module.brake(n)==max(n-1,0)
    for initial in range(11):
        n=initial
        for _ in range(30): n=module.gas(n)
        assert n==10
        for _ in range(30): n=module.brake(n)
        assert n==0
    tree=ast.parse((SOL/'prep_269_speed_tables.py').read_text('utf-8'))
    assert not any(isinstance(node,(ast.If,ast.IfExp,ast.For,ast.While,ast.Compare)) for node in ast.walk(tree))
    return {"exhaustive_calls":22,"long_saturation_calls":660,
            "ast_forbidden_control_flow_absent":True,"domain":"promised integers 0..10 only"}


def check_binary():
    function=load('prep_019_binary_partition_batch1107').binary_partition
    count=0
    for length in range(13):
        for bits in itertools.product(range(2),repeat=length):
            values=list(bits);identity=id(values)
            assert function(values) is values and id(values)==identity and values==sorted(bits)
            count+=1
    return {"exhaustive_arrays":count,"lengths":"0..12","oracle":"independent sorting; same list identity"}


def check_missing():
    function=load('prep_041_sorted_gap_batch1107').sorted_missing
    count=0
    for n in range(201):
        for missing in range(1,n+2):
            values=[v for v in range(1,n+2) if v!=missing]
            before=values[:]
            assert function(values)==missing and values==before
            count+=1
    return {"exhaustive_domain_sizes":"0..200","omission_cases":count,"input_unchanged":True}


def asm_program():
    lines=(SOL/'prep_035_named_register_multiply_batch1107.asm').read_text('utf-8').splitlines()
    labels,program={},[]
    for raw in lines:
        line=raw.split(';',1)[0].strip()
        if not line: continue
        if line.endswith(':'): labels[line[:-1]]=len(program)
        else: program.append(line.replace(',','').split())
    return program,labels


def run_asm(registers):
    program,labels=asm_program();registers=list(registers);pc=steps=0
    while pc<len(program):
        instruction=program[pc];op=instruction[0];r=int(instruction[1][1:])-1
        if op=='CLEAR': registers[r]=0
        elif op=='INC': registers[r]+=1
        elif op=='DEC':
            assert registers[r]>0
            registers[r]-=1
        elif op=='JUMP_NZ':
            if registers[r]!=0:
                pc=labels[instruction[2]];steps+=1;continue
        else: raise AssertionError('forbidden opcode')
        pc+=1;steps+=1
        assert steps<100000
    return registers,steps


def check_asm():
    count=0
    for a,b,t,r in itertools.product(range(25),range(25),(0,1,17),(0,1,99)):
        result,_=run_asm((a,b,t,r))
        assert result[3]==a*b and result[0]==a
        count+=1
    return {"input_and_dirty_scratch_cases":count,"exact_interpreter":"CLEAR INC DEC named-register JUMP_NZ only",
            "no_negative_decrement":True,"completion":"fall-through END"}


def check_matrix():
    function=load('prep_182_matrix_turtle_batch1107').returns_to_cell
    count=invalid=0
    matrix=[[None]*5 for _ in range(5)]
    for heading in range(4):
        for length in range(8):
            for commands in itertools.product('RLM',repeat=length):
                # Independent complex-plane orientation, row increases down.
                z=0j;direction=(1,1j,-1,-1j)[heading];outside=False
                for command in commands:
                    if command=='R': direction*=1j
                    elif command=='L': direction*=-1j
                    else:
                        z+=direction
                        if not -2<=z.real<=2 or not -2<=z.imag<=2: outside=True
                if outside:
                    fails(function,matrix,2,2,heading,commands);invalid+=1
                else:
                    assert function(matrix,2,2,heading,commands)==(z==0)
                    count+=1
    for args in (([],0,0,0,''),([[0],[0,1]],0,0,0,''),([[0]],0,0,4,''),([[0]],0,0,0,'X')):
        fails(function,*args);invalid+=1
    return {"valid_board_traces":count,"rejected_outside_or_invalid_cases":invalid,
            "headings":4,"command_lengths":"0..7","oracle":"independent complex motion"}


def main():
    results={265:check_prime(),266:check_process(),267:check_http(),268:check_chat(),269:check_speed(),
             19:check_binary(),41:check_missing(),35:check_asm(),182:check_matrix()}
    aggregate={"status":"passed","checked_on":"2026-11-07","evidence_scope":"Executed Python/local processes only; RTL separate","questions":results}
    for number,result in results.items():
        suffix='-batch1107' if number<265 else ''
        path=ROOT/'checks'/f'prep-{number:03d}{suffix}-verification.json'
        path.write_text(json.dumps(dict(status='passed',checked_on='2026-11-07',**result),indent=2)+'\n',encoding='utf-8')
    (ROOT/'checks'/'batch1107-software-verification.json').write_text(json.dumps(aggregate,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(aggregate,indent=2))


if __name__=='__main__': main()
