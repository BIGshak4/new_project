import { HDL, LIMITS } from "./job.mjs";

export const WORK = "/vercel/sandbox/job";
// SDK-owned, readable but never writable by the untrusted jobrun-code user.
// All subsequent SDK writes stay here so candidate-created symlinks in WORK
// cannot redirect a privileged write or replace a later resource-control script.
export const CONTROL = "/vercel/sandbox/jobrun-control";
export const RUNNER_USER = "jobrun-code";
export const EXTENSIONS = { python: "py", javascript: "js", c: "c", cpp: "cpp", verilog: "v", systemverilog: "sv", vhdl: "vhd" };
const file = name => `${CONTROL}/${name}`;
const artifact = name => `${WORK}/${name}`;

// This script lives ONLY inside the disposable VM. It bounds child resources and
// stdout before any bytes reach the broker. It is not our isolation boundary:
// the fresh, network-denied microVM is. Nothing in the VM knows expected outputs.
export const PROCESS_RUNNER = String.raw`import json, os, resource, selectors, signal, subprocess, sys, time
cfg = json.load(open(sys.argv[1], encoding="utf8"))
limit = 16384
def restricted():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CPU, (6, 6))
    # V8 reserves a multi-GB virtual address cage. Its heap has a separate 128MB
    # flag; the entire VM still has a provider-enforced 2GB physical memory cap.
    if cfg["argv"][0] != "node": resource.setrlimit(resource.RLIMIT_AS, (768*1024*1024, 768*1024*1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024*1024, 1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
started=time.monotonic()
try:
    p=subprocess.Popen(cfg["argv"], cwd="/vercel/sandbox/job", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=restricted, env={"PATH":"/usr/local/bin:/usr/bin:/bin", "HOME":"/home/jobrun-code", "LANG":"C.UTF-8", "PYTHONIOENCODING":"utf-8"})
except Exception as exc:
    print(json.dumps({"exit_code":127,"stdout":"","stderr":str(exc)[:limit],"timed_out":False,"output_limited":False})); sys.exit(0)
p.stdin.write(cfg.get("stdin", "").encode("utf8")); p.stdin.close()
sel=selectors.DefaultSelector(); sel.register(p.stdout,selectors.EVENT_READ,"stdout"); sel.register(p.stderr,selectors.EVENT_READ,"stderr")
buf={"stdout":bytearray(),"stderr":bytearray()}; timed_out=False; output_limited=False
while sel.get_map():
    if time.monotonic()-started > cfg["timeout_ms"]/1000:
        timed_out=True
        try: os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError: pass
    for key,_ in sel.select(0.02):
        chunk=os.read(key.fileobj.fileno(),4096)
        if not chunk: sel.unregister(key.fileobj); continue
        room=max(0,limit-len(buf[key.data])); buf[key.data].extend(chunk[:room])
        if len(chunk)>room:
            output_limited=True
            try: os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError: pass
    if (timed_out or output_limited) and time.monotonic()-started > cfg["timeout_ms"]/1000+0.5: break
try: code=p.wait(timeout=0.5)
except subprocess.TimeoutExpired:
    try: os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError: pass
    code=-9; timed_out=True
# Kill descendants that deliberately kept no pipe open.
try: os.killpg(p.pid,signal.SIGKILL)
except ProcessLookupError: pass
print(json.dumps({"exit_code":code,"stdout":buf["stdout"].decode("utf8","replace"),"stderr":buf["stderr"].decode("utf8","replace"),"timed_out":timed_out,"output_limited":output_limited},ensure_ascii=False))
`;

export const PYTHON_FUNCTION = String.raw`import json, runpy, sys
ns=runpy.run_path("/vercel/sandbox/jobrun-control/solution.py")
args=json.load(open(sys.argv[1], encoding="utf8"))
fn=ns.get(sys.argv[2])
if not callable(fn): raise ValueError("Required function is not defined: "+sys.argv[2])
value=fn(*args)
print("\n__JOBRUN_VALUE__"+json.dumps({"value":value},ensure_ascii=False,allow_nan=False,separators=(",",":")))
`;

export function executionPlan(job) {
  const { language, spec } = job, extension = EXTENSIONS[language];
  const files = [{ path: file(`solution.${extension}`), content: job.source }, { path: file("process_runner.py"), content: PROCESS_RUNNER }];
  let compile, elaborate, run, compileOnly = false;
  if (language === "python") {
    compile = ["python3", "-I", "-c", `import py_compile; py_compile.compile(${JSON.stringify(file("solution.py"))}, cfile=${JSON.stringify(artifact("solution.pyc"))}, doraise=True)`]; run = ["python3", "-I", file("solution.py")];
    if (spec?.kind === "function") {
      files.push({ path: file("function.py"), content: PYTHON_FUNCTION });
      run = ["python3", "-I", file("function.py")];
    } else if (spec?.driver) {
      files.push({ path: file("driver.py"), content: spec.driver }); run = ["python3", "-I", file("driver.py")];
    }
  } else if (language === "javascript") {
    compile = ["node", "--check", file("solution.js")]; run = ["node", "--max-old-space-size=128", file("solution.js")];
    if (spec?.kind === "function") {
      // Same module preserves ordinary function/const declarations. Caller entry
      // is validated as an identifier; args are data in a separate JSON file.
      files.push({ path: file("function.cjs"), content: `${job.source}\n;Promise.resolve(${spec.entry}(...JSON.parse(require('node:fs').readFileSync(process.argv[2], 'utf8')))).then(value => { console.log('\\n__JOBRUN_VALUE__' + JSON.stringify({value})); }, err => { console.error(String(err)); process.exitCode = 1; });\n` });
      run = ["node", "--max-old-space-size=128", file("function.cjs")];
    } else if (spec?.driver) {
      files.push({ path: file("driver.cjs"), content: `${job.source}\n${spec.driver}` }); run = ["node", "--max-old-space-size=128", file("driver.cjs")];
    }
  } else if (language === "c" || language === "cpp") {
    const name = spec?.driver ? `driver.${extension}` : `solution.${extension}`;
    if (spec?.driver) files.push({ path: file(name), content: spec.driver });
    compile = [language === "c" ? "gcc" : "g++", language === "c" ? "-std=c17" : "-std=c++20", "-O0", "-Wall", "-Wextra", file(name), "-lm", "-o", artifact("program")];
    run = [artifact("program")];
  } else if (language === "vhdl") {
    const source = file("solution.vhd");
    const entities = [...job.source.matchAll(/\bentity\s+([A-Za-z_][A-Za-z0-9_]*)\s+is\b/gi)];
    const top = spec?.top ?? entities.at(-1)?.[1];
    const sources = [source];
    if (spec?.testbench) { files.push({ path: file("tb.vhd"), content: spec.testbench }); sources.push(file("tb.vhd")); }
    compile = ["ghdl", "-a", "--std=08", ...sources];
    elaborate = top ? ["ghdl", "-e", "--std=08", top] : null;
    run = top ? ["ghdl", "-r", "--std=08", top, "--stop-time=1ms", "--assert-level=error"] : null;
    compileOnly = !run;
  } else {
    const sources = [file(`solution.${extension}`)];
    if (spec?.testbench) { files.push({ path: file(`tb.${extension}`), content: spec.testbench }); sources.push(file(`tb.${extension}`)); }
    compile = ["iverilog", language === "systemverilog" ? "-g2012" : "-g2005", ...(spec?.top ? ["-s", spec.top] : []), "-o", artifact("simulation"), ...sources];
    run = ["vvp", artifact("simulation")];
  }
  return { files, compile, elaborate, run, compileOnly, hdl: HDL.has(language), limitMs: spec ? LIMITS.caseMs : LIMITS.runMs };
}
