import { createHash, createPublicKey, verify } from "node:crypto";

export class RequestError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

// Equivalent to Python's sorted compact UTF-8 JSON for JSON data. Normalize whole
// floats before signing: JSON.stringify(1.0) is "1". No NaN/Infinity are allowed.
export function canonicalJson(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number" && Number.isFinite(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    const keys = Object.keys(value).sort((a, b) => {
      const aa = [...a], bb = [...b];
      for (let i = 0; i < Math.min(aa.length, bb.length); i++) {
        const d = aa[i].codePointAt(0) - bb[i].codePointAt(0); if (d) return d;
      }
      return aa.length - bb.length;
    });
    return `{${keys.map(k => `${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(",")}}`;
  }
  throw new RequestError(400, "The job must contain finite JSON values.");
}

export const jobDigest = job => createHash("sha256").update(canonicalJson(job), "utf8").digest("hex");

function publicKey(encoded) {
  if (!encoded) throw new RequestError(503, "The execution verifier is not configured.");
  try {
    if (encoded.includes("BEGIN PUBLIC KEY")) return createPublicKey(encoded.replaceAll("\\n", "\n"));
    const bytes = Buffer.from(encoded, "base64");
    // Ed25519 raw public key -> SubjectPublicKeyInfo. Accept SPKI DER too.
    return createPublicKey({ key: bytes.length === 32 ? Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), bytes]) : bytes, format: "der", type: "spki" });
  } catch { throw new RequestError(503, "The execution verifier is not configured."); }
}

export function verificationFingerprint(encoded) {
  const key = publicKey(encoded);
  if (key.asymmetricKeyType !== "ed25519") throw new RequestError(503, "The execution verifier is not configured.");
  return createHash("sha256").update(key.export({ format: "der", type: "spki" }).subarray(-32)).digest("hex");
}

export function verifyTicket(ticket, jobJson, encodedKey, now = Math.floor(Date.now() / 1000)) {
  if (typeof ticket !== "string" || ticket.length > 8192) throw new RequestError(401, "A signed execution ticket is required.");
  const bits = ticket.split(".");
  if (bits.length !== 3 || bits.some(b => !/^[A-Za-z0-9_-]+$/.test(b))) throw new RequestError(401, "Invalid execution ticket.");
  let header, claims;
  try { header = JSON.parse(Buffer.from(bits[0], "base64url")); claims = JSON.parse(Buffer.from(bits[1], "base64url")); }
  catch { throw new RequestError(401, "Invalid execution ticket."); }
  if (header.alg !== "EdDSA" || header.crit || (header.typ && header.typ !== "JWT")) throw new RequestError(401, "Invalid execution ticket.");
  const key = publicKey(encodedKey);
  if (key.asymmetricKeyType !== "ed25519" || !verify(null, Buffer.from(`${bits[0]}.${bits[1]}`), key, Buffer.from(bits[2], "base64url"))) {
    throw new RequestError(401, "Invalid execution signature.");
  }
  if (claims.iss !== "jobrun-api" || claims.aud !== "jobrun-executor" || !Number.isInteger(claims.exp) || !Number.isInteger(claims.iat)
    || claims.exp <= now || claims.iat > now + 5 || claims.iat < now - 90
    || claims.exp <= claims.iat || claims.exp - claims.iat > 90 || typeof claims.sub !== "string" || !claims.sub || claims.sub.length > 128
    || typeof claims.jti !== "string" || !/^[A-Za-z0-9_-]{16,80}$/.test(claims.jti)) {
    throw new RequestError(401, "Execution ticket expired or invalid.");
  }
  if (typeof jobJson !== "string" || claims.sha256 !== createHash("sha256").update(jobJson, "utf8").digest("hex")) throw new RequestError(401, "The execution ticket does not match this job.");
  return claims;
}
