import { createHash } from "node:crypto";
import { Sandbox } from "@vercel/sandbox";
import { baseResult, bounded, equalValue, LIMITS, normalizeOutput, validateJob } from "./job.mjs";
import { CONTROL, executionPlan, RUNNER_USER, WORK } from "./plan.mjs";

class ExecutionDeadline extends Error {}
export function reportSamples(reports) {
  const failed = reports.filter(report => !report.passed);
  return (failed.length ? failed : reports).slice(0, 8);
}

const commandOutput = async command => {
  const raw = await command.stdout();
  // Two bounded streams can expand sixfold when JSON escapes control bytes.
  if (Buffer.byteLength(raw, "utf8") > LIMITS.output * 12 + 1024) throw new Error("Invalid runner response.");
  let data;
  try { data = JSON.parse(raw); } catch { throw new Error("Invalid runner response."); }
  if (!Number.isInteger(data.exit_code) || typeof data.stdout !== "string" || typeof data.stderr !== "string") throw new Error("Invalid runner response.");
  return { exitCode: data.exit_code, stdout: bounded(data.stdout), stderr: bounded(data.stderr), timedOut: data.timed_out === true, outputLimited: data.output_limited === true };
};

export function sandboxOptions(claims, env = process.env) {
  if (!env.JOBRUN_EXECUTION_SNAPSHOT_ID) throw new Error("Execution toolchain is not configured.");
  return {
    name: `jr-${createHash("sha256").update(claims.jti).digest("hex").slice(0, 32)}`,
    source: { type: "snapshot", snapshotId: env.JOBRUN_EXECUTION_SNAPSHOT_ID },
    networkPolicy: "deny-all", persistent: false, resources: { vcpus: 1 }, timeout: LIMITS.vmMs,
    ...(env.JOBRUN_EXECUTION_REGION ? { region: env.JOBRUN_EXECUTION_REGION } : {}),
    // Credentials are for the calling SDK process only. Never put any secret in
    // Sandbox.env, files, commands, source repository, or submitted code.
    ...(env.VERCEL_TOKEN ? { token: env.VERCEL_TOKEN, teamId: env.VERCEL_TEAM_ID, projectId: env.VERCEL_PROJECT_ID } : {}),
  };
}

export async function executeJob(job, claims, { env = process.env, createSandbox = opts => Sandbox.create(opts) } = {}) {
  validateJob(job);
  const started = Date.now(), plan = executionPlan(job);
  let vm, compiled = null, executed = false, compileOutput = "", stdout = "", stderr = "", stage = "VM startup";
  const reports = [], testCount = job.spec?.kind === "hdl" ? 1 : job.spec?.cases?.length ?? 0;
  const finish = values => baseResult(job.language, { compiled, executed, compile_output: bounded(compileOutput), stdout: bounded(stdout), stderr: bounded(stderr), runtime_ms: Date.now() - started, ...values, cases: reportSamples(values.cases ?? reports), test_count: testCount, passed_count: reports.filter(report => report.passed).length });
  try {
    vm = await createSandbox(sandboxOptions(claims, env));
    stage = "workspace preparation";
    const directories = await vm.runCommand({ cmd: "mkdir", args: ["-p", CONTROL, WORK] });
    if (directories.exitCode !== 0) throw new Error("Workspace could not be created.");
    const modes = await vm.runCommand({ cmd: "chmod", args: ["755", "/vercel/sandbox", CONTROL] });
    if (modes.exitCode !== 0) throw new Error("Control directory permissions could not be set.");
    await vm.writeFiles(plan.files.map(f => ({ path: f.path, content: Buffer.from(f.content, "utf8"), mode: 0o644 })));
    const ownership = await vm.runCommand({ cmd: "chown", args: [`${RUNNER_USER}:${RUNNER_USER}`, WORK], sudo: true });
    if (ownership.exitCode !== 0) throw new Error("Execution user is not configured.");
    const scratch = await vm.runCommand({ cmd: "chmod", args: ["700", WORK], sudo: true });
    if (scratch.exitCode !== 0) throw new Error("Scratch directory permissions could not be set.");
    let sequence = 0;
    async function run(argv, stdin = "", timeout = LIMITS.caseMs) {
      const remaining = 40000 - (Date.now() - started);
      if (remaining < 1500) throw new ExecutionDeadline();
      const childTimeout = Math.min(timeout, remaining - 1000);
      const configPath = `${CONTROL}/command-${sequence++}.json`;
      await vm.writeFiles([{ path: configPath, content: Buffer.from(JSON.stringify({ argv, stdin, timeout_ms: childTimeout }), "utf8"), mode: 0o644 }]);
      // A transport failure after this call cannot establish that no code ran.
      if (stage === "program execution") executed = true;
      const command = await vm.runCommand({
        cmd: "runuser", args: ["-u", RUNNER_USER, "--", "python3", `${CONTROL}/process_runner.py`, configPath],
        sudo: true, cwd: CONTROL, timeoutMs: Math.min(childTimeout + 2000, remaining),
      });
      return commandOutput(command);
    }
    stage = "compiler invocation";
    const build = await run(plan.compile, "", LIMITS.compileMs);
    compileOutput = `${build.stdout}${build.stderr}`;
    if (build.timedOut) return finish({ status: "timeout", compiled: false, detail: "Compilation exceeded its time limit." });
    if (build.exitCode !== 0 || build.outputLimited) return finish({ status: "compile_error", compiled: false, detail: "The compiler rejected the submitted code." });
    if (plan.elaborate) {
      const elaboration = await run(plan.elaborate, "", LIMITS.compileMs);
      compileOutput += `${elaboration.stdout}${elaboration.stderr}`;
      if (elaboration.timedOut) return finish({ status: "timeout", compiled: false, detail: "HDL elaboration exceeded its time limit." });
      if (elaboration.exitCode !== 0 || elaboration.outputLimited) return finish({ status: "compile_error", compiled: false, detail: "The HDL design could not be elaborated." });
    }
    compiled = true;
    if (plan.compileOnly) return finish({ status: "compile_only", detail: "Compilation succeeded. No executable top or question tests were available; correctness was not assessed." });

    stage = "program execution";
    if (job.spec?.kind === "function") {
      for (let i = 0; i < job.spec.cases.length; i++) {
        const test = job.spec.cases[i], argPath = `${CONTROL}/args-${i}.json`;
        await vm.writeFiles([{ path: argPath, content: Buffer.from(JSON.stringify(test.args), "utf8"), mode: 0o644 }]);
        const result = await run([...plan.run, argPath, ...(job.language === "python" ? [job.spec.entry] : [])]);
        executed = true; stdout = result.stdout; stderr = result.stderr;
        if (result.timedOut) return finish({ status: "timeout", cases: reports, detail: `Test ${i + 1} exceeded its time limit.` });
        if (result.exitCode !== 0 || result.outputLimited) return finish({ status: "runtime_error", cases: reports, detail: result.outputLimited ? "The program exceeded the output limit." : `The program failed while running test ${i + 1}.` });
        const markers = result.stdout.split("\n").filter(line => line.startsWith("__JOBRUN_VALUE__"));
        let value;
        try {
          const envelope = JSON.parse(markers.at(-1)?.slice("__JOBRUN_VALUE__".length));
          if (!envelope || !Object.hasOwn(envelope, "value")) throw new Error();
          value = envelope.value;
        } catch { return finish({ status: "runtime_error", cases: reports, detail: `Test ${i + 1} did not return a serializable value.` }); }
        reports.push({ index: i + 1, passed: equalValue(value, test.expected, test.unordered === true), input: test.args, expected: test.expected, actual: value });
      }
      // Do not present the last harness marker as the learner's console output.
      stdout = stdout.split("\n").filter(line => !line.startsWith("__JOBRUN_VALUE__")).join("\n").trim();
      const passed = reports.every(test => test.passed);
      return finish({ status: passed ? "passed" : "failed", passed, detail: `${reports.filter(t => t.passed).length}/${reports.length} question tests passed.` });
    }

    if (job.spec?.kind === "program") {
      for (let i = 0; i < job.spec.cases.length; i++) {
        const test = job.spec.cases[i], result = await run(plan.run, test.stdin);
        executed = true; stdout = result.stdout; stderr = result.stderr;
        if (result.timedOut) return finish({ status: "timeout", cases: reports, detail: `Test ${i + 1} exceeded its time limit.` });
        if (result.exitCode !== 0 || result.outputLimited) return finish({ status: "runtime_error", cases: reports, detail: result.outputLimited ? "The program exceeded the output limit." : `The program failed while running test ${i + 1}.` });
        reports.push({ index: i + 1, passed: normalizeOutput(result.stdout) === normalizeOutput(test.expected_stdout), input: test.stdin, expected: test.expected_stdout, actual: result.stdout });
      }
      const passed = reports.every(test => test.passed);
      return finish({ status: passed ? "passed" : "failed", passed, detail: `${reports.filter(t => t.passed).length}/${reports.length} question tests passed.` });
    }

    const result = await run(plan.run, job.stdin ?? "", LIMITS.runMs);
    executed = true; stdout = result.stdout; stderr = result.stderr;
    if (result.timedOut) return finish({ status: "timeout", detail: "The program or simulation exceeded its time limit." });
    if (result.exitCode !== 0 || result.outputLimited) return finish({ status: "runtime_error", detail: result.outputLimited ? "The program exceeded the output limit." : "The program or simulation exited with an error." });
    if (job.spec?.kind === "hdl") {
      const passed = normalizeOutput(stdout) === normalizeOutput(job.spec.expected_stdout);
      reports.push({ index: 1, passed, input: "Question testbench", expected: job.spec.expected_stdout, actual: stdout });
      return finish({ status: passed ? "passed" : "failed", passed, detail: passed ? "The simulation matched all expected testbench samples." : "The simulation output did not match the expected testbench samples." });
    }
    return finish({ status: "completed", detail: "The program ran successfully. This question has no automated tests for this language; correctness was not assessed." });
  } catch (error) {
    // Provider responses can contain request/auth details; do not echo them.
    if (error instanceof ExecutionDeadline || Date.now() - started >= 39000 || /timeout|timed.?out|deadline|expired|stopped/i.test(String(error?.name) + " " + String(error?.code) + " " + String(error?.message))) return finish({ status: "timeout", detail: "The execution reached its total time limit. No correctness result was inferred." });
    return finish({ status: "unavailable", detail: `The isolated execution service could not finish ${stage}. Please retry later.` });
  } finally {
    if (vm) { try { await vm.stop(); } catch { /* The VM's independent 45s deadline still applies. */ } }
  }
}
