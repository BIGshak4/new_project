// Real Linux compiler checks of explicitly committed/reviewed fixtures only.
// This is NOT a sandbox and MUST NOT accept learner/API/generated input. The
// local adapter exercises the same plan/permissions/judge with real subprocesses
// on an ephemeral CI host; it does not validate Firecracker/network isolation.
import { execFile } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";
import { promisify } from "node:util";
import { randomUUID } from "node:crypto";
import { CONTROL, RUNNER_USER, WORK } from "../lib/plan.mjs";
import { executeJob } from "../lib/runner.mjs";
import { CONTROL_TAMPER_FIXTURE } from "./control-tamper-fixture.mjs";

if (process.platform !== "linux" || process.env.CI !== "true" || process.env.JOBRUN_TRUSTED_FIXTURE_CHECK !== "1") {
  throw new Error("This trusted-fixture compiler check is restricted to explicit Linux CI. It is not a submitted-code runner.");
}
const exec = promisify(execFile);
const manifest = JSON.parse(await readFile(new URL("../../../backend/seeds/execution_cases.json", import.meta.url), "utf8"));
const fixtures = JSON.parse(await readFile(new URL("../../../backend/tests/fixtures/execution_smoke.json", import.meta.url), "utf8"));

async function cleanup() {
  // Fixed absolute paths in the ephemeral GitHub host only; never derive a
  // deletion target from fixture source, user data or environment variables.
  if (CONTROL !== "/vercel/sandbox/jobrun-control" || WORK !== "/vercel/sandbox/job") throw new Error("Unexpected fixture workspace.");
  await exec("sudo", ["-n", "rm", "-rf", "--one-file-system", "--", CONTROL, WORK]);
}
async function localFixtureAdapter() {
  await cleanup();
  let stopped = false;
  return {
    async writeFiles(files) {
      for (const file of files) {
        if (!file.path.startsWith(`${CONTROL}/`) || file.mode !== 0o644) throw new Error("A trusted fixture attempted an unsafe SDK write.");
        await writeFile(file.path, file.content, { mode: file.mode });
      }
    },
    async runCommand(command) {
      const argv = command.sudo ? ["sudo", ["-n", command.cmd, ...command.args]] : [command.cmd, command.args];
      try {
        const { stdout, stderr } = await exec(argv[0], argv[1], { cwd: command.cwd, timeout: command.timeoutMs ?? 15000, maxBuffer: 262144 });
        return { exitCode: 0, stdout: async () => stdout, stderr: async () => stderr };
      } catch (error) {
        if (error.killed || error.signal) throw error;
        if (typeof error.code !== "number") throw error;
        return { exitCode: error.code, stdout: async () => error.stdout ?? "", stderr: async () => error.stderr ?? "" };
      }
    },
    async stop() { stopped = true; await cleanup(); },
    get stopped() { return stopped; },
  };
}
const summary = [];
async function check(theJob, name, expected) {
  const adapter = await localFixtureAdapter();
  const result = await executeJob(theJob, { jti: randomUUID() }, { env: { JOBRUN_EXECUTION_SNAPSHOT_ID: "trusted-linux-fixtures-not-a-cloud-sandbox" }, createSandbox: async () => adapter });
  const row = { fixture: name, language: theJob.language, expected, status: result.status, ok: result.status === expected && adapter.stopped, test_count: result.test_count, passed_count: result.passed_count, runtime_ms: result.runtime_ms, ...(result.status === expected ? {} : { detail: result.detail, compile_output: result.compile_output, stderr: result.stderr, cases: result.cases }) };
  summary.push(row); console.log(JSON.stringify(row));
}
for (const fixture of fixtures.cases) {
  const spec = manifest.questions[fixture.question_key]?.languages[fixture.language];
  if (!spec) throw new Error("Fixture specification is missing.");
  for (const kind of ["correct", "wrong", "syntax_error"]) {
    await check({ language: fixture.language, source: fixture[kind], stdin: "", spec }, `${fixture.question_key}/${kind}`, kind === "correct" ? "passed" : kind === "wrong" ? "failed" : "compile_error");
  }
}
// Genuine filesystem permission regression: the first invocation attempts to
// rewrite controls and plant symlinks; the second must still use intact control
// files and SDK-owned argument/config destinations. No host secret is inspected.
await check(CONTROL_TAMPER_FIXTURE, "read-only-controls-and-sdk-write-symlinks", "passed");
await check({ language: "python", source: "while True: pass\n", stdin: "" }, "real-timeout", "timeout");
await check({ language: "python", source: "print('x' * 100000)\n", stdin: "" }, "real-output-limit", "runtime_error");
const result = { kind: "trusted-linux-compiler-validation", real_compilers: true, cloud_isolation_verified: false, runner_user: RUNNER_USER, languages: [...new Set(fixtures.cases.map(f => f.language))], checked: summary.length, passed: summary.filter(row => row.ok).length, failed: summary.filter(row => !row.ok).length };
console.log(JSON.stringify(result));
if (process.env.GITHUB_STEP_SUMMARY) await writeFile(process.env.GITHUB_STEP_SUMMARY, `\n### Real compiler fixtures\n\n${result.passed}/${result.checked} checks passed across ${result.languages.join(", ")}.\n\nThis validates committed fixtures and filesystem permissions on Linux CI, not the deployed microVM provider or live website.\n`, { flag: "a" });
if (result.failed) process.exitCode = 1;
