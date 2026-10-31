import { RequestError } from "./auth.mjs";

export const LANGUAGES = Object.freeze(["python", "javascript", "c", "cpp", "verilog", "systemverilog", "vhdl"]);
export const HDL = new Set(["verilog", "systemverilog", "vhdl"]);
export const LIMITS = Object.freeze({ source: 20000, stdin: 8192, output: 16384, body: 131072, cases: 32, vmMs: 45000, compileMs: 10000, runMs: 3000, caseMs: 1000 });
const ident = value => typeof value === "string" && /^[A-Za-z_][A-Za-z0-9_]*$/.test(value) && value.length <= 100;
const plain = value => !!value && typeof value === "object" && !Array.isArray(value);
function text(value, max, field) {
  if (typeof value !== "string" || value.length > max || value.includes("\0")) throw new RequestError(400, `Invalid ${field}.`);
}
function cases(spec) {
  if (!Array.isArray(spec.cases) || spec.cases.length < 1 || spec.cases.length > LIMITS.cases) throw new RequestError(400, "Invalid execution cases.");
}
export function validateJob(job) {
  if (!plain(job) || !LANGUAGES.includes(job.language)) throw new RequestError(400, "Unsupported execution language.");
  text(job.source, LIMITS.source, "source");
  if (!job.source.trim()) throw new RequestError(400, "Source code is empty.");
  text(job.stdin ?? "", LIMITS.stdin, "standard input");
  if (job.spec !== undefined && job.spec !== null) {
    const spec = job.spec;
    if (!plain(spec)) throw new RequestError(400, "Invalid execution specification.");
    if (spec.kind === "function") {
      if (!["python", "javascript"].includes(job.language) || !ident(spec.entry)) throw new RequestError(400, "Invalid function entry.");
      cases(spec);
      for (const item of spec.cases) {
        if (!plain(item) || !Array.isArray(item.args) || !("expected" in item)) throw new RequestError(400, "Invalid function test.");
        if (JSON.stringify(item.args).length > LIMITS.stdin || JSON.stringify(item.expected).length > LIMITS.output) throw new RequestError(400, "Test data is too large.");
      }
    } else if (spec.kind === "program") {
      if (HDL.has(job.language)) throw new RequestError(400, "HDL requires a simulation specification.");
      if (spec.driver !== undefined) text(spec.driver, LIMITS.source, "test driver");
      cases(spec);
      for (const item of spec.cases) {
        if (!plain(item)) throw new RequestError(400, "Invalid program test.");
        text(item.stdin, LIMITS.stdin, "test input"); text(item.expected_stdout, LIMITS.output, "expected output");
      }
    } else if (spec.kind === "hdl") {
      if (!HDL.has(job.language) || !ident(spec.top)) throw new RequestError(400, "Invalid HDL top.");
      text(spec.testbench, 48000, "testbench"); text(spec.expected_stdout, LIMITS.output, "expected output");
    } else throw new RequestError(400, "Unsupported execution specification.");
  }
  return job;
}

export function baseResult(language, values = {}) {
  return { status: "unavailable", language, compiled: null, executed: false, passed: null, stdout: "", stderr: "", compile_output: "", cases: [], test_count: 0, passed_count: 0, runtime_ms: 0, detail: "Execution is unavailable.", ...values };
}
export const bounded = value => String(value ?? "").slice(0, LIMITS.output);
export const normalizeOutput = value => String(value ?? "").replaceAll("\r\n", "\n").trimEnd();
export function equalValue(actual, expected, unordered = false) {
  if (unordered && Array.isArray(actual) && Array.isArray(expected)) {
    const key = v => JSON.stringify(v, (_, x) => x && !Array.isArray(x) && typeof x === "object" ? Object.fromEntries(Object.entries(x).sort()) : x);
    return JSON.stringify(actual.map(key).sort()) === JSON.stringify(expected.map(key).sort());
  }
  if (typeof actual !== typeof expected || actual === null || expected === null) return actual === expected;
  if (Array.isArray(actual) || Array.isArray(expected)) return Array.isArray(actual) && Array.isArray(expected) && actual.length === expected.length && actual.every((v, i) => equalValue(v, expected[i]));
  if (typeof actual === "object") {
    const aa = Object.keys(actual).sort(), bb = Object.keys(expected).sort();
    return equalValue(aa, bb) && aa.every(k => equalValue(actual[k], expected[k]));
  }
  return actual === expected;
}
