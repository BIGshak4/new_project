import test from "node:test";
import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { RequestError, verifyTicket, verificationFingerprint } from "../lib/auth.mjs";
import { LANGUAGES, LIMITS, equalValue, validateJob } from "../lib/job.mjs";
import { CONTROL, executionPlan, RUNNER_USER, WORK } from "../lib/plan.mjs";
import { executeJob, reportSamples, sandboxOptions } from "../lib/runner.mjs";
import { boundedResponse, makeHandler, readEnvelope } from "../api/execute.mjs";

const { privateKey, publicKey } = generateKeyPairSync("ed25519");
const key = publicKey.export({ type: "spki", format: "pem" });
const now = 2000000000;
const job = { language: "python", source: "print('hello')", stdin: "" };
const raw = JSON.stringify(job);
const claim = { aud: "jobrun-executor", iss: "jobrun-api", iat: now, exp: now + 90, jti: "test-request-000000000000", sub: "user-uuid", sha256: createHash("sha256").update(raw).digest("hex") };
function ticket(changes = {}, header = {}) {
  const a = Buffer.from(JSON.stringify({ typ: "JWT", alg: "EdDSA", ...header })).toString("base64url");
  const b = Buffer.from(JSON.stringify({ ...claim, ...changes })).toString("base64url");
  return `${a}.${b}.${sign(null, Buffer.from(`${a}.${b}`), privateKey).toString("base64url")}`;
}
const errorStatus = status => error => error instanceof RequestError && error.status === status;
test("signed exact-byte envelope verifies with PEM and raw public keys", () => {
  assert.equal(verifyTicket(ticket(), raw, key, now).sub, "user-uuid");
  const rawKey = publicKey.export({ type: "spki", format: "der" }).subarray(-32).toString("base64");
  assert.equal(verifyTicket(ticket(), raw, rawKey, now).jti, claim.jti);
  assert.equal(verificationFingerprint(key), createHash("sha256").update(Buffer.from(rawKey, "base64")).digest("hex"));
});
test("changed bytes, wrong key, expired and long-lived signatures fail before execution", () => {
  assert.throws(() => verifyTicket(ticket(), raw + " ", key, now), errorStatus(401));
  const other = generateKeyPairSync("ed25519").publicKey.export({ type: "spki", format: "pem" });
  assert.throws(() => verifyTicket(ticket(), raw, other, now), errorStatus(401));
  for (const change of [{ exp: now }, { exp: now + 91 }, { iat: now + 6 }, { iat: now - 20 }, { iss: "other" }, { aud: "other" }, { jti: "bad" }]) assert.throws(() => verifyTicket(ticket(change), raw, key, now), errorStatus(401));
  assert.throws(() => verifyTicket(ticket({}, { alg: "HS256" }), raw, key, now), errorStatus(401));
  assert.throws(() => verifyTicket(ticket(), raw, "", now), errorStatus(503));
});
test("source, input, language, signature entry and total body limits reject invalid jobs", async () => {
  assert.throws(() => validateJob({ ...job, language: "shell" }), errorStatus(400));
  assert.throws(() => validateJob({ ...job, source: "x".repeat(20001) }), errorStatus(400));
  assert.throws(() => validateJob({ ...job, stdin: "x".repeat(8193) }), errorStatus(400));
  assert.throws(() => validateJob({ ...job, spec: { kind: "function", entry: "f;rm -rf", cases: [{ args: [], expected: 1 }] } }), errorStatus(400));
  assert.throws(() => validateJob({ ...job, spec: { kind: "function", entry: "f", cases: Array.from({ length: 33 }, () => ({ args: [], expected: 1 })) } }), errorStatus(400));
  await assert.rejects(readEnvelope({ headers: { "content-length": LIMITS.body + 1 }, body: {} }), errorStatus(413));
  await assert.rejects(readEnvelope({ headers: {}, body: { job, ticket: ticket() } }), errorStatus(400));
  await assert.rejects(readEnvelope({ headers: {}, body: { job_json: "x".repeat(LIMITS.body), ticket: ticket() } }), errorStatus(413));
});
test("all seven language plans contain only fixed compiler commands and VM-local files", () => {
  for (const language of LANGUAGES) {
    const plan = executionPlan({ ...job, language, source: language === "vhdl" ? "entity tb is end; architecture a of tb is begin end;" : job.source });
    assert.ok(plan.compile.length);
    assert.ok(plan.files.every(f => f.path.startsWith(`${CONTROL}/`)));
    assert.equal(plan.compile.some(arg => arg.includes("/bin/sh")), false);
  }
  const cpp = executionPlan({ ...job, language: "cpp", spec: { kind: "program", driver: '#include "solution.cpp"\nint main(){}', cases: [] } });
  assert.ok(cpp.compile.includes(`${CONTROL}/driver.cpp`));
  assert.equal(cpp.compile.includes(`${CONTROL}/solution.cpp`), false);
  const sv = executionPlan({ ...job, language: "systemverilog", spec: { kind: "hdl", top: "tb", testbench: "module tb; endmodule", expected_stdout: "" } });
  assert.ok(sv.compile.includes("-g2012")); assert.ok(sv.compile.includes("tb"));
});
test("structural comparison respects bool vs number, duplicates and unordered arrays", () => {
  assert.equal(equalValue(false, 0), false);
  assert.equal(equalValue({ a: 1, b: [2] }, { b: [2], a: 1 }), true);
  assert.equal(equalValue([2, 1], [1, 2], true), true);
  assert.equal(equalValue([1, 1], [1, 2], true), false);
});

function fakeVm(outputs = [], failingAt = "") {
  const files = [], calls = [], states = { stopped: false };
  return {
    files, calls, states,
    writeFiles: async fs => { files.push(...fs); if (failingAt === "write") throw new Error("provider secret should not be echoed"); },
    runCommand: async cmd => {
      calls.push(cmd);
      if (cmd.cmd !== "runuser") return { exitCode: 0, stdout: async () => "", stderr: async () => "" };
      if (failingAt === "run") throw new Error("provider secret should not be echoed");
      const next = outputs.shift() ?? {};
      return { exitCode: 0, stdout: async () => JSON.stringify({ exit_code: 0, stdout: "", stderr: "", timed_out: false, output_limited: false, ...next }) };
    },
    stop: async () => { states.stopped = true; },
  };
}
const env = { JOBRUN_EXECUTION_SNAPSHOT_ID: "snapshot-test", JOBRUN_EXECUTION_PUBLIC_KEY: key };
async function mockedRun(theJob, outputs, failingAt) {
  const vm = fakeVm(outputs, failingAt);
  const result = await executeJob(theJob, claim, { env, createSandbox: async options => { assert.equal(options.networkPolicy, "deny-all"); assert.equal(options.persistent, false); assert.equal(options.timeout, 45000); assert.equal("env" in options, false); return vm; } });
  assert.equal(vm.states.stopped, true);
  return { result, vm };
}
test("fresh VM uses no application environment and an independent deadline", () => {
  const options = sandboxOptions(claim, env);
  assert.deepEqual(options.resources, { vcpus: 1 }); assert.equal(options.persistent, false);
  assert.deepEqual(options.source, { type: "snapshot", snapshotId: "snapshot-test" });
  assert.equal(options.name, sandboxOptions(claim, env).name);
  assert.throws(() => sandboxOptions(claim, {}));
});
test("successful standalone execution does not claim question correctness", async () => {
  const { result } = await mockedRun(job, [{}, { stdout: "hello\n" }]);
  assert.equal(result.status, "completed"); assert.equal(result.passed, null); assert.equal(result.compiled, true); assert.equal(result.executed, true); assert.equal(result.stdout, "hello\n");
});
test("compile error never executes the candidate and still stops the VM", async () => {
  const { result, vm } = await mockedRun(job, [{ exit_code: 1, stderr: "syntax error" }]);
  assert.equal(result.status, "compile_error"); assert.equal(result.executed, false); assert.equal(result.compiled, false);
  assert.equal(vm.calls.filter(c => c.cmd === "runuser").length, 1);
});
test("timeouts and output limits are explicit; neither falsely passes", async () => {
  const timeout = await mockedRun(job, [{}, { timed_out: true, exit_code: -9 }]);
  assert.equal(timeout.result.status, "timeout"); assert.equal(timeout.result.passed, null);
  const overflow = await mockedRun(job, [{}, { output_limited: true, exit_code: -9 }]);
  assert.equal(overflow.result.status, "runtime_error"); assert.equal(overflow.result.passed, null);
});
test("expected function values stay outside the VM and are compared in the broker", async () => {
  const expected = "private-oracle-only-do-not-send-to-vm";
  const tested = { ...job, source: "def answer(n): return n", spec: { kind: "function", entry: "answer", cases: [{ args: [7], expected }] } };
  const { result, vm } = await mockedRun(tested, [{}, { stdout: '\n__JOBRUN_VALUE__{"value":7}\n' }]);
  assert.equal(result.status, "failed"); assert.equal(result.passed, false);
  assert.equal(vm.files.some(f => f.content.toString().includes(expected)), false);
  assert.equal(result.cases[0].actual, 7);
  assert.ok(vm.files.every(file => file.path.startsWith(`${CONTROL}/`) && file.mode === 0o644));
  const chown = vm.calls.find(command => command.cmd === "chown");
  assert.deepEqual(chown.args, [`${RUNNER_USER}:${RUNNER_USER}`, WORK]);
  assert.equal(chown.args.some(arg => arg.includes(CONTROL)), false);
  assert.equal(chown.args.includes("-R"), false);
  for (const command of vm.calls.filter(command => command.cmd === "runuser")) {
    assert.equal(command.cwd, CONTROL);
    assert.ok(command.args.includes(`${CONTROL}/process_runner.py`));
    assert.ok(command.args.at(-1).startsWith(`${CONTROL}/command-`));
  }
});
test("late test failures are shown before passing samples and totals cover the full suite", async () => {
  const cases = Array.from({ length: 12 }, (_, n) => ({ args: [n], expected: n }));
  const outputs = [{}, ...cases.map((_, n) => ({ stdout: `__JOBRUN_VALUE__${JSON.stringify({ value: n === 11 ? 99 : n })}\n` }))];
  const { result } = await mockedRun({ ...job, spec: { kind: "function", entry: "f", cases } }, outputs);
  assert.equal(result.status, "failed"); assert.equal(result.test_count, 12); assert.equal(result.passed_count, 11);
  assert.equal(result.cases[0].index, 12); assert.equal(result.cases[0].passed, false);
  assert.deepEqual(reportSamples([{ index: 1, passed: true }, { index: 9, passed: false }]), [{ index: 9, passed: false }]);
});
test("matching JSON values pass, invalid function output does not", async () => {
  const tested = { ...job, source: "def f(): return 7", spec: { kind: "function", entry: "f", cases: [{ args: [], expected: 7 }] } };
  const pass = await mockedRun(tested, [{}, { stdout: '__JOBRUN_VALUE__{"value":7}\n' }]);
  assert.equal(pass.result.status, "passed"); assert.equal(pass.result.passed, true);
  const invalid = await mockedRun(tested, [{}, { stdout: '{"passed":true}\n' }]);
  assert.equal(invalid.result.status, "runtime_error"); assert.equal(invalid.result.passed, null);
});
test("program and HDL tests compare broker-only expected samples", async () => {
  const program = { ...job, language: "c", source: "int f(){return 8;}", spec: { kind: "program", driver: '#include "solution.c"\nint main(){}', cases: [{ stdin: "8\n", expected_stdout: "8\n" }] } };
  const pass = await mockedRun(program, [{}, { stdout: "8\r\n" }]);
  assert.equal(pass.result.passed, true);
  const hdl = { ...job, language: "verilog", source: "module dut; endmodule", spec: { kind: "hdl", top: "tb", testbench: "module tb; endmodule", expected_stdout: "private-sample" } };
  const fail = await mockedRun(hdl, [{}, { stdout: "different-sample" }]);
  assert.equal(fail.result.passed, false); assert.equal(fail.vm.files.some(f => f.content.toString().includes("private-sample")), false);
});
test("provider failure is sanitized and always stops the allocated VM", async () => {
  const { result } = await mockedRun(job, [], "run");
  assert.equal(result.status, "unavailable"); assert.equal(JSON.stringify(result).includes("provider secret"), false);
});
test("transport failure after a program invocation does not assert the program never ran", async () => {
  const vm = fakeVm([{}]); let calls = 0;
  const runCommand = vm.runCommand;
  vm.runCommand = async command => {
    if (command.cmd === "runuser" && ++calls === 2) throw new Error("network transport failed");
    return runCommand(command);
  };
  const result = await executeJob(job, claim, { env, createSandbox: async () => vm });
  assert.equal(result.status, "unavailable"); assert.equal(result.executed, true); assert.equal(result.passed, null);
  assert.equal(vm.states.stopped, true);
});
test("VM timeout errors remain timeout outcomes rather than transport-unavailable", async () => {
  const result = await executeJob(job, claim, { env, createSandbox: async () => { const error = new Error("Sandbox session expired"); error.name = "TimeoutError"; throw error; } });
  assert.equal(result.status, "timeout"); assert.equal(result.passed, null);
});

function response() { return { code: null, headers: {}, payload: null, setHeader(k, v) { this.headers[k] = v; }, status(code) { this.code = code; return this; }, json(payload) { this.payload = payload; return this; } }; }
test("HTTP rejects unsigned or tampered requests before allocating any VM", async () => {
  let called = false;
  const handler = makeHandler({ execute: async () => { called = true; }, env, now: () => now });
  const res = response();
  await handler({ method: "POST", headers: {}, body: { job_json: raw + " ", ticket: ticket() } }, res);
  assert.equal(res.code, 401); assert.equal(called, false);
});
test("HTTP executes once for a valid ticket and rejects immediate replay", async () => {
  let count = 0;
  const handler = makeHandler({ execute: async () => { count++; return { status: "completed" }; }, env, now: () => now });
  const body = { job_json: raw, ticket: ticket({ jti: "unique-http-request-0000001" }) };
  const first = response(), second = response();
  await handler({ method: "POST", headers: {}, body }, first); await handler({ method: "POST", headers: {}, body }, second);
  assert.equal(first.code, 200); assert.equal(second.code, 409); assert.equal(count, 1);
});
test("large diagnostic responses remain below the outer response limit", () => {
  const huge = "\u0000".repeat(16384);
  const result = boundedResponse({ stdout: huge, stderr: huge, compile_output: huge, cases: Array.from({ length: 8 }, (_, index) => ({ index, input: huge, expected: huge, actual: huge })) });
  assert.ok(Buffer.byteLength(JSON.stringify(result)) < LIMITS.body);
});
