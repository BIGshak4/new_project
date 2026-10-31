# JobRun isolated executor

Private server-to-server broker for actual Python, JavaScript, C, C++, Verilog,
SystemVerilog and VHDL execution. The existing JobRun API authenticates the user,
owns the attempt, selects question tests, reserves a durable execution budget and
signs a short-lived Ed25519 ticket. This broker never accepts a browser's test
specification or executes learner code in the Vercel Function itself.

Every accepted job starts a new Firecracker microVM from a compiler snapshot,
with `networkPolicy: deny-all`, `persistent: false`, one vCPU and a 45-second
independent deadline. No application files, tokens, private signing key or
expected test outputs enter that VM. A dedicated `jobrun-code` user has no sudo. Child
commands have wall/CPU/file/process/output limits; Node additionally has a 128MB
heap limit (the VM supplies the physical memory boundary).

SDK-owned control files (sources, test drivers, resource wrapper, invocation data)
stay in a separate directory readable but not writable by `jobrun-code`. Only
build artifacts and scratch data belong to the execution user. SDK writes never
enter candidate-writable directories or follow candidate-created symlinks.

The VM returns actual values/output; **the broker compares expected values
outside the VM**. Compiler success and a standalone program running successfully
do not imply question correctness. Only a completed matching question test suite
can return `passed: true`. Unsupported/missing tests return `passed: null`.

## Configure and deploy

1. Deploy this directory as a Node 24 Vercel project. Keep Vercel OIDC enabled.
   No paid upgrade is required or performed by these scripts.
2. Run `npm ci`, `npm test`, `npm run check`.
3. Run `npm run provision` with operator SDK credentials for that project (OIDC,
   or `VERCEL_TOKEN`, `VERCEL_TEAM_ID`, `VERCEL_PROJECT_ID`). This trusted setup
   VM needs package-download networking; no submitted code runs during setup.
4. Set `JOBRUN_EXECUTION_SNAPSHOT_ID` to the provisioner's snapshot and region.
   Set `JOBRUN_EXECUTION_PUBLIC_KEY` to the API's public Ed25519 key (raw32 base64,
   SPKI DER base64, or PEM). Never configure the private key here.
5. `/api/health` reports `available`, languages and the public-key fingerprint.
   Check both live execution and API health before enabling learner runs.

The Hobby plan stops new sandbox creation at its included quota rather than
charging overages; the broker returns unavailable on provider failures. Budget
limits in the JobRun API remain necessary, independently of provider quotas.
Snapshots can expire after inactivity; reprovision and verify before replacing a
snapshot. The broker fails closed when snapshot/key configuration is missing.

## Wire contract

`POST /api/execute` has JSON `{ "job_json": "<exact UTF-8 job JSON>", "ticket":
"<compact EdDSA JWT>" }`. The signature covers audience `jobrun-executor`, issued
time, expiry (at most 90 seconds), subject, unique `jti`, and SHA256 hex of the
**exact bytes of `job_json`**. This avoids Python/JavaScript float or Unicode
canonicalization ambiguity. Maximum outer request/response size is 128KiB.

Job: `{language, source, stdin?, spec?}`. Source limit 20,000 characters, stdin
8,192 characters; no package installation, custom compiler flags or user-selected
images. Question specs are server selected:

- `function`: Python/JS `{entry, cases:[{args, expected, unordered?}]}`.
- `program`: `{driver?, cases:[{stdin, expected_stdout}]}`. C/C++ drivers include
  `solution.c` / `solution.cpp`. The other program languages can run directly.
- `hdl`: `{top, testbench, expected_stdout}`. Top is an identifier. Icarus compiles
  Verilog/SystemVerilog and runs VVP; GHDL analyzes and simulates VHDL-2008.

Responses report total and passing test counts, and show failures before passing
samples when a suite exceeds the bounded report size. A 40-second overall budget
leaves time to stop the VM before its independent 45-second deadline.

Program/stdout checks normalize CRLF and trailing whitespace only. Function
values use structural JSON equality (bool and number stay distinct); unordered
arrays are compared as multisets. Testbench expected samples never enter the VM.

Tests here are unit tests with a mocked Sandbox boundary, clearly separated from
the live compiler validation the operator must run after provisioning.

`npm run smoke` runs the real deployed compiler fixtures (correct, wrong and
syntax-error submissions for all seven languages, plus bounded timeout, output
and network checks, plus read-only control-file/symlink regression). Set local-only `JOBRUN_EXECUTOR_URL` and the API-derived
32-byte base64 `JOBRUN_EXECUTION_SIGNING_SEED` in the operator process. This does
not update learner records and prints only bounded fixture results.

`npm run check:fixtures` is a separately gated Linux CI task that runs only
committed developer-reviewed fixtures using actual installed compilers and a
dedicated user. It exercises SDK/control-file ownership with real filesystem
permissions, correct/wrong/syntax cases, timeout and output limits. It is **not a
security sandbox**, is never called by HTTP, accepts no learner input, and does
not establish that the cloud provider or live site works. The
`verify-code-execution.yml` workflow runs it on trusted `master` pushes or an
explicit dispatch with no hosting/model/database credentials.

References: [Sandbox SDK](https://vercel.com/docs/sandbox/sdk-reference),
[network isolation](https://vercel.com/docs/sandbox/concepts/firewall),
[pricing](https://vercel.com/docs/sandbox/pricing).
