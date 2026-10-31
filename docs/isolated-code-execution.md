# Isolated code execution

Implemented 2026-10-31. The application API never executes learner source on its own host. A separate Vercel Function verifies a short-lived, exact-payload Ed25519 ticket and creates a fresh Firecracker microVM per job. The VM has no application secrets or files, denies all networking, does not persist, uses one vCPU and stops within 45 seconds. Compiler setup happens in a separately provisioned, trusted snapshot.

## Learner flow

In a real practice attempt, open the code editor, select a language and use **Run and test**. Python, JavaScript, C, C++, Verilog, SystemVerilog and VHDL have execution adapters. The capability response states whether the isolated provider is currently available and whether this question has tests in the selected language. A starter and a bilingual interface contract appear where tests exist. Other questions can run a complete program or a self-contained HDL testbench with optional stdin; successful execution is not an answer-correctness result.

Running does not submit the answer, call an AI model, earn evidence/coins, or advance progress. A source/input/language change marks previous results stale; a late response cannot replace a newer result. Stop waiting aborts the browser request, not the VM's independent deadline.

On submission, questions with a compatible suite run before the AI assessment, including mock interviews and code duels. Only server-generated facts enter that assessment. An exact recent run for the same user, attempt, source and fixture is reused. Execution is independent of AI-provider readiness. If the AI assessment fails or remains pending, persisted execution facts remain visible without an invented grade or XP. The AI still reviews reasoning, complexity and requirements not covered by execution; this feature does not claim a measured reduction in model tokens. Pure numeric and truth-table checks retain their previous behavior. The legacy Python AST/subprocess runner remains disabled for HTTP input.

## Coverage

`backend/seeds/execution_cases.json` is the server-side manifest; it is not sent as browser-supplied test definitions. The repository is public, so the manifest is not claimed to be secret. It covers **28 existing questions, 67 language specifications** (23 Python, 23 JavaScript, 5 C, 5 C++, 5 Verilog, 5 SystemVerilog, 1 VHDL). All seven pre-existing Python code-test questions are covered. HDL suites include the enabled modulo-six counter, 1101 detector and combinational functions. Multi-part questions explicitly identify which portion is tested. Sampled byte patterns do not claim exhaustive coverage; some small HDL domains are exhaustive. Functional tests do not prove minimum gates, memory bounds, asymptotic complexity or physical timing.

SystemVerilog support is the subset accepted by the provisioned Icarus compiler, not a claim of full language or verification-library support. UVM, vendor IP, synthesis and physical timing verification are outside this execution feature's verified scope.

The learner never supplies a test specification, compiler flag, image, destination or expected result. Expected values remain in the broker, outside the VM. A protected directory owned by the SDK user holds code, wrappers and input files; only scratch/build output belongs to the unprivileged execution user. Later SDK writes never traverse a candidate-writable directory. Diagnostics are bounded and displayed as text. Failure samples are shown first with independent suite totals.

## API and budgets

- `GET /v1/practice/attempts/{id}/execution-capabilities`
- `POST /v1/practice/attempts/{id}/executions` with `language`, `source`, `stdin`, `idempotency_key`
- `GET /execution/verification-key` publishes only the Ed25519 public key and fingerprint for operator pinning.

Both practice routes require the existing paid/pilot access dependency and ownership of the attempt. The backend-only `code_execution_runs` ledger enforces idempotency and a rolling allowance: 60 runs/user/24h, 6/user/minute, 2 concurrent runs globally. A short database advisory lock serializes reservations across API workers; no transaction stays open during execution. Interrupted reservations remain active for 120 seconds. Browser roles cannot read or write the ledger; it contains hashes and results, never source or tickets.

Source is capped at 20,000 characters, stdin at 8,000. The broker caps request/response size, CPU, wall time, file output, process count and output streams. Compiler errors, runtime errors, timeouts, unavailable infrastructure and untested successful runs remain distinct from test pass/fail. No transport failure is presented as a passed check or proof that code never ran.

## Provisioning and deployment

The application is still hosted on Netlify/Render. Only `apps/executor` is a separate Node 24 Vercel project. The connected account remains Hobby; no paid-plan upgrade was made. Included Sandbox quotas stop new creation when exhausted. The earlier team-scope `403` was resolved through owner authorization, and provisioning and real execution have since completed.

Verified broker: `https://jobrun-executor-job-runer.vercel.app`, deployment `dpl_Am5yZpNwdqoGXygRRw613w7gUvBa`. The dedicated toolchain snapshot is `snap_Ja3hGvOlcTr2QfB4k6Qu07XztkkR`, with retention configured without expiry. These identifiers contain no credentials. Revalidate the toolchain and isolation checks whenever replacing the snapshot or deployment.

1. Deploy `apps/executor` as the `jobrun-executor` project with Vercel OIDC enabled. Verify that its production alias matches `CODE_EXECUTION_URL` (default `https://jobrun-executor-job-runer.vercel.app`).
2. Run its trusted provisioning script, or the equivalent authenticated Sandbox API operations. Install and verify Python, Node, GCC/G++, Icarus and GHDL and create the dedicated non-sudo execution user, then snapshot. No learner code runs during setup.
3. Pin `JOBRUN_EXECUTION_PUBLIC_KEY` to the deployed API's `/execution/verification-key`; configure `JOBRUN_EXECUTION_SNAPSHOT_ID` and the matching region. The broker never needs the private key or any Supabase/model credential.
4. Verify `/api/health` reports the matching fingerprint. The API refuses to send jobs to an unconfigured or mismatched broker. Verify real correct/wrong/syntax fixtures in all languages, then the authenticated website flow.
5. Run the live smoke script, timeout/output/control-tamper/network checks, and positive/negative browser submissions. Keep evidence separately from unit-test doubles.

`CODE_EXECUTION_ENABLED=false` stops new execution requests while normal answer saving and AI review continue. An optional independent `CODE_EXECUTION_SIGNING_SEED` can be configured; otherwise the API derives a purpose-separated Ed25519 key from its existing server-only Storage key. Rotating that key requires repinning the public key. Never put the seed, private signing key or an execution ticket in browser configuration or the repository. Reprovision unavailable snapshots and reverify before switching snapshot IDs.

## Verification record and current limits

Verification on 2026-10-31:

- **3,135 offline backend tests passed**, 11 skipped; **322 frontend tests passed**, with production build and TypeScript checks; **19 broker tests passed**. The two backend warnings are recorded in the test log.
- After the final aggregate-quota SQL change, **37 targeted quota/security/interoperability tests passed**. The final Render API revision `2332f30706bee1864d939150698fa2699a4515da` ran the submitted Kernighan Python implementation against **14/14 tests successfully** in 4,833 ms; its response is retained as `live-api-final.json`.
- **94 Linux compiler CI cases passed** in the [compiler verification workflow](https://github.com/BIGshak4/new_project/actions/runs/41193215959/job/124514060452). This executes committed developer fixtures; it does not by itself establish cloud isolation.
- **95 real microVM operator cases passed**: 28 correct, wrong, syntax-error and boundary/security cases, followed by all 67 authored positive language specifications across the 28 covered questions. The live checks exercised Python, JavaScript, C, C++, Verilog, SystemVerilog and VHDL, plus timeout, excessive output, denied networking and protected control-file/write-path behavior.
- **45 interactive UI fixture checks passed** across Hebrew/English, desktop/mobile and light/dark presentations. These use an explicit deferred API double; their cancellation, stale-result, escaping and layout results are separate from actual execution evidence.
- The authenticated live API and website exercised Python success, wrong-answer and compiler-error outcomes, plus a passing SystemVerilog simulation. A live Python API result reported **14/14 configured tests passed** while showing only eight diagnostic samples. At a 390 × 844 viewport, a standalone C++ program compiled and executed with stdin `21` followed by a newline, returned stdout `42`, and correctly displayed that answer correctness was not assessed. Document scroll width was 382 px within the 390 px viewport.

An independent implementation review found and fixed bad-result acceptance, control-file tampering/write permissions, truncated failure reporting and final-code-fence selection. The live website check also caught an OpenAI provider incorrectly classified as demo mode; the provider gate now accepts OpenAI and Anthropic, and execution is enabled explicitly by the authenticated workspace rather than by AI readiness. Tours retain no execution context. New regression tests cover these boundaries.

The new database migration was applied and verified: RLS enabled; anonymous reads and authenticated inserts denied. Security advisor reports the intentionally closed table as RLS-without-policy. An earlier full local command including live database tests recorded 21 setup errors from invalid local database credentials; these are not counted as passing. The offline suite excludes those three live-test files. Live application/database verification is separate.

The real OpenAI-backed submission did **not** complete AI assessment: it returned two retryable evaluator errors, `eval_failed` and `saved_without_evaluation`. Its successful **14/14 execution result persisted**. The deployed frontend revision `a52aa44` was verified in both Hebrew and English to display that result while clearly reporting the AI feedback failure, with no invented model grade or XP. The screenshot `live-ai-outage-preserves-execution.png` records the visible result. This record does not claim the AI provider is healthy.

The manifest covers 28 questions, not the entire interview bank, and tests can cover only part of a multi-part question. Neither passing tests nor compiler success proves a complete solution.

Live QA cleanup completed after signing out. Exact-ID verification found zero remaining rows for the dedicated test account in `auth.users`, `user_profile`, `attempt`, `code_execution_runs` and `jr_members`. Its local temporary credentials file was removed and absence verified. The browser was returned to Hebrew and its viewport reset.

Private operator evidence is under `.impeccable/execution-20261031/`: `backend-final-tests.log`, `frontend-final-all-tests.log`, `frontend-final-build.log`, `compiler-ci.json`, `live-broker-smoke.log`, `live-all-positive.json`, `live-api-positive.json`, `live-api-final.json`, `live-ai-submission.json` and the live screenshots. The evidence directory is not committed; review and sanitize any selected evidence before publishing it.
