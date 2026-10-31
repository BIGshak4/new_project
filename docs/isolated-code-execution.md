# Isolated code execution

Implemented 2026-10-31. The application API never executes learner source on its own host. A separate Vercel Function verifies a short-lived, exact-payload Ed25519 ticket and creates a fresh Firecracker microVM per job. The VM has no application secrets or files, denies all networking, does not persist, uses one vCPU and stops within 45 seconds. Compiler setup happens in a separately provisioned, trusted snapshot.

## Learner flow

In a real practice attempt, open the code editor, select a language and use **Run and test**. Python, JavaScript, C, C++, Verilog, SystemVerilog and VHDL have execution adapters. The capability response states whether the isolated provider is currently available and whether this question has tests in the selected language. A starter and a bilingual interface contract appear where tests exist. Other questions can run a complete program or a self-contained HDL testbench with optional stdin; successful execution is not an answer-correctness result.

Running does not submit the answer, call an AI model, earn evidence/coins, or advance progress. A source/input/language change marks previous results stale; a late response cannot replace a newer result. Stop waiting aborts the browser request, not the VM's independent deadline.

On submission, questions with a compatible suite run before the AI assessment, including mock interviews and code duels. Only server-generated facts enter that assessment. An exact recent run for the same user, attempt, source and fixture is reused. The AI still reviews reasoning, complexity and requirements not covered by execution; this feature does not claim a measured reduction in model tokens. Pure numeric and truth-table checks retain their previous behavior. The legacy Python AST/subprocess runner remains disabled for HTTP input.

## Coverage

`backend/seeds/execution_cases.json` is the private server manifest: **28 existing questions, 67 language specifications** (23 Python, 23 JavaScript, 5 C, 5 C++, 5 Verilog, 5 SystemVerilog, 1 VHDL). All seven pre-existing Python code-test questions are covered. HDL suites include the enabled modulo-six counter, 1101 detector and combinational functions. Multi-part questions explicitly identify which portion is tested. Sampled byte patterns do not claim exhaustive coverage; some small HDL domains are exhaustive. Functional tests do not prove minimum gates, memory bounds, asymptotic complexity or physical timing.

The learner never supplies a test specification, compiler flag, image, destination or expected result. Expected values remain in the broker, outside the VM. A protected directory owned by the SDK user holds code, wrappers and input files; only scratch/build output belongs to the unprivileged execution user. Later SDK writes never traverse a candidate-writable directory. Diagnostics are bounded and displayed as text. Failure samples are shown first with independent suite totals.

## API and budgets

- `GET /v1/practice/attempts/{id}/execution-capabilities`
- `POST /v1/practice/attempts/{id}/executions` with `language`, `source`, `stdin`, `idempotency_key`
- `GET /execution/verification-key` publishes only the Ed25519 public key and fingerprint for operator pinning.

Both practice routes require the existing paid/pilot access dependency and ownership of the attempt. The backend-only `code_execution_runs` ledger enforces idempotency and a rolling allowance: 60 runs/user/24h, 6/user/minute, 2 concurrent runs globally. A short database advisory lock serializes reservations across API workers; no transaction stays open during execution. Interrupted reservations remain active for 120 seconds. Browser roles cannot read or write the ledger; it contains hashes and results, never source or tickets.

Source is capped at 20,000 characters, stdin at 8,000. The broker caps request/response size, CPU, wall time, file output, process count and output streams. Compiler errors, runtime errors, timeouts, unavailable infrastructure and untested successful runs remain distinct from test pass/fail. No transport failure is presented as a passed check or proof that code never ran.

## Provisioning and deployment

The application is still hosted on Netlify/Render. Only `apps/executor` is a separate Node 24 Vercel project. No paid-plan upgrade is required by this implementation. The existing connected Vercel account is Hobby; included Sandbox quotas stop new creation when exhausted. Account/team authorization is required before provisioning.

1. Deploy `apps/executor` as the `jobrun-executor` project with Vercel OIDC enabled. Verify that its production alias matches `CODE_EXECUTION_URL` (default `https://jobrun-executor-job-runer.vercel.app`).
2. Run its trusted provisioning script, or the equivalent authenticated Sandbox API operations. Install and verify Python, Node, GCC/G++, Icarus and GHDL and create the dedicated non-sudo execution user, then snapshot. No learner code runs during setup.
3. Pin `JOBRUN_EXECUTION_PUBLIC_KEY` to the deployed API's `/execution/verification-key`; configure `JOBRUN_EXECUTION_SNAPSHOT_ID` and the matching region. The broker never needs the private key or any Supabase/model credential.
4. Verify `/api/health` reports the matching fingerprint. The API refuses to send jobs to an unconfigured or mismatched broker. Verify real correct/wrong/syntax fixtures in all languages, then the authenticated website flow.
5. Run the live smoke script, timeout/output/control-tamper/network checks, and positive/negative browser submissions. Keep evidence separately from unit-test doubles.

`CODE_EXECUTION_ENABLED=false` stops new execution requests while normal answer saving and AI review continue. An optional independent `CODE_EXECUTION_SIGNING_SEED` can be configured; otherwise the API derives a purpose-separated Ed25519 key from its existing server-only Storage key. Rotating that key requires repinning the public key. Never put the seed, private signing key or an execution ticket in browser configuration or the repository. Reprovision expired snapshots and reverify before switching snapshot IDs.

## Verification record and current limit

Local verification before deployment: 3,087 offline backend tests, 315 frontend tests, frontend production build, 19 broker boundary/auth/adapter tests, and 45 interactive UI checks across Hebrew/English and desktop/mobile. The UI tests use an explicit API double and do not establish real execution. An independent review found and fixed a bad-result acceptance bug, control-file tampering/write permissions, truncated failure reporting and final-code-fence selection. New regression tests cover these boundaries.

The new database migration was applied and verified: RLS enabled; anonymous reads and authenticated inserts denied. Security advisor reports the intentionally closed table as RLS-without-policy. The existing local database password is invalid, so the full command including live database tests had 21 setup errors; these are not counted as passing. The offline suite excludes those three live-test files. Live application/database verification is separate.

At preparation time, Vercel returned `403` for the connected team's scope and required owner approval. Therefore provisioning, real microVM isolation checks and a successful run on the live website are **pending**, not verified by the local results above. The real Linux compiler workflow validates committed developer fixtures and filesystem permissions; it explicitly does not prove cloud isolation or live website integration. Append deployment/compiler/browser evidence only after those checks have actually run.
