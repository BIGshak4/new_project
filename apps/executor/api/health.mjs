import { LANGUAGES } from "../lib/job.mjs";
import { verificationFingerprint } from "../lib/auth.mjs";
export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  if (req.method !== "GET") { res.setHeader("Allow", "GET"); return res.status(405).json({ error: "Use GET." }); }
  let fingerprint = null;
  try { fingerprint = verificationFingerprint(process.env.JOBRUN_EXECUTION_PUBLIC_KEY); } catch { /* configuration unavailable */ }
  const available = !!fingerprint && !!process.env.JOBRUN_EXECUTION_SNAPSHOT_ID;
  return res.status(200).json({ status: "ok", available, key_fingerprint: fingerprint, service: "jobrun-executor", revision: process.env.VERCEL_GIT_COMMIT_SHA ?? null, languages: available ? LANGUAGES : [], isolation: "fresh-microvm", network: "deny-all", persistence: false, max_runtime_ms: 45000 });
}
