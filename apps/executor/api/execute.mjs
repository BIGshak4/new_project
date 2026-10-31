import { RequestError, verifyTicket } from "../lib/auth.mjs";
import { baseResult, LIMITS, validateJob } from "../lib/job.mjs";
import { executeJob } from "../lib/runner.mjs";

// Defense in depth within a warm function instance. Durable request ownership,
// daily budgets and duplicate protection are enforced by the signing JobRun API.
const usedTickets = new Map();
let active = 0;
export function boundedResponse(result) {
  if (Buffer.byteLength(JSON.stringify(result), "utf8") <= LIMITS.body) return result;
  const value = v => { const s = JSON.stringify(v); return Buffer.byteLength(s ?? "", "utf8") > 512 ? String(s).slice(0, 128) + "… [truncated]" : v; };
  return { ...result, stdout: result.stdout.slice(0, 4096), stderr: result.stderr.slice(0, 4096), compile_output: result.compile_output.slice(0, 4096), cases: result.cases.slice(0, 4).map(c => ({ ...c, input: value(c.input), expected: value(c.expected), actual: value(c.actual) })) };
}
export async function readEnvelope(req) {
  if (Number(req.headers?.["content-length"] ?? 0) > LIMITS.body) throw new RequestError(413, "Execution request is too large.");
  let body;
  if (req.body !== undefined) {
    const raw = typeof req.body === "string" || Buffer.isBuffer(req.body) ? req.body.toString() : JSON.stringify(req.body);
    if (Buffer.byteLength(raw, "utf8") > LIMITS.body) throw new RequestError(413, "Execution request is too large.");
    try { body = JSON.parse(raw); } catch { throw new RequestError(400, "Invalid execution request."); }
  } else {
    const parts = []; let length = 0;
    for await (const part of req) { const bytes = Buffer.from(part); length += bytes.length; if (length > LIMITS.body) throw new RequestError(413, "Execution request is too large."); parts.push(bytes); }
    try { body = JSON.parse(Buffer.concat(parts).toString("utf8")); } catch { throw new RequestError(400, "Invalid execution request."); }
  }
  if (!body || typeof body !== "object" || typeof body.job_json !== "string" || typeof body.ticket !== "string") throw new RequestError(400, "A signed execution request is required.");
  return body;
}
export function makeHandler({ execute = executeJob, env = process.env, now = () => Math.floor(Date.now() / 1000) } = {}) {
  return async function handler(req, res) {
    res.setHeader("Cache-Control", "no-store"); res.setHeader("X-Content-Type-Options", "nosniff");
    if (req.method !== "POST") { res.setHeader("Allow", "POST"); return res.status(405).json({ error: "Use POST." }); }
    let language = "text", reserved = false;
    try {
      const envelope = await readEnvelope(req);
      const claims = verifyTicket(envelope.ticket, envelope.job_json, env.JOBRUN_EXECUTION_PUBLIC_KEY, now());
      let job;
      try { job = JSON.parse(envelope.job_json); } catch { throw new RequestError(400, "Invalid execution job."); }
      validateJob(job); language = job.language;
      if (!env.JOBRUN_EXECUTION_SNAPSHOT_ID) throw new RequestError(503, "The isolated execution toolchain is not configured.");
      const stamp = now();
      for (const [key, expiry] of usedTickets) if (expiry <= stamp) usedTickets.delete(key);
      if (usedTickets.has(claims.jti)) throw new RequestError(409, "This execution ticket has already been used.");
      if (active >= 2) throw new RequestError(429, "The execution service is busy. Please retry later.");
      usedTickets.set(claims.jti, claims.exp); active++; reserved = true;
      const result = await execute(job, claims, { env });
      return res.status(200).json(boundedResponse(result));
    } catch (error) {
      const status = error instanceof RequestError ? error.status : 503;
      const detail = error instanceof RequestError ? error.message : "The execution service is temporarily unavailable.";
      return res.status(status).json(baseResult(language, { detail }));
    } finally { if (reserved) active--; }
  };
}
export default makeHandler();
