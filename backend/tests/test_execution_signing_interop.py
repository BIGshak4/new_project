"""Real Python Ed25519 -> Node verifier interoperability; no source is executed.

All keys and payloads here are public developer fixtures. No deployment secrets,
network requests, compilers, VMs, or learner answers are used by this test.
"""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from app.services.code_execution import public_key_bytes, signing_key

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")
NOW = 1_800_000_000
PUBLIC_TEST_SEED = "jobrun-public-test-fixture-only-not-a-deployment-key"
PRIVATE_KEY = signing_key(PUBLIC_TEST_SEED)
assert PRIVATE_KEY is not None
PUBLIC_RAW = base64.b64encode(public_key_bytes(PRIVATE_KEY)).decode("ascii")
PUBLIC_PEM = PRIVATE_KEY.public_key().public_bytes(
    serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode("ascii")

# Python emits 1.0/-0.0/1e-07 whereas JSON.stringify normalizes those spellings.
# Signing must bind the exact raw UTF-8 JSON string, not a Node reserialization.
JOB = {
    "language": "python",
    "source": "# שלום 🤖; Unicode é e\u0301\u2028\u2029\n# Literal fences: ```python and ````\ndef f(x):\n    return x\n",
    "stdin": "שורה א\nline two\\literal\\n\n",
    "spec": {"kind": "function", "entry": "f", "cases": [
        {"args": [1.0, -0.0, 1e-7, "שלום 😀"], "expected": {"x": 1.0}},
    ]},
}
JOB_JSON = json.dumps(JOB, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def ticket(*, body=JOB_JSON, claims=None, headers=None):
    data = {"iss": "jobrun-api", "aud": "jobrun-executor", "sub": "public-test-user",
            "jti": "12345678-1234-4234-9234-123456789012", "iat": NOW, "exp": NOW + 90,
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}
    if claims:
        data.update(claims)
    return jwt.encode(data, PRIVATE_KEY, algorithm="EdDSA", headers=headers)


def vectors():
    valid = ticket()
    prefix, signature = valid.rsplit(".", 1)
    signature_bytes = bytearray(base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)))
    signature_bytes[0] ^= 1
    corrupted = prefix + "." + base64.urlsafe_b64encode(signature_bytes).decode("ascii").rstrip("=")
    wrong_key = signing_key("another-public-test-key")
    wrong_public = base64.b64encode(public_key_bytes(wrong_key)).decode("ascii")
    same_object_different_float_spelling = JOB_JSON.replace("1.0", "1").replace("-0.0", "0")
    assert json.loads(same_object_different_float_spelling) == JOB
    result = [
        ("valid_unicode_floats_and_fences", valid, JOB_JSON, PUBLIC_RAW, True),
        ("valid_pem_key", valid, JOB_JSON, PUBLIC_PEM, True),
        ("valid_escaped_pem_key", valid, JOB_JSON, PUBLIC_PEM.replace("\n", "\\n"), True),
        ("tampered_source", valid, JOB_JSON.replace("return x", "return 0"), PUBLIC_RAW, False),
        ("tampered_unicode_normalization", valid, JOB_JSON.replace("é", "e\u0301"), PUBLIC_RAW, False),
        ("same_json_value_different_raw_floats", valid, same_object_different_float_spelling, PUBLIC_RAW, False),
        ("same_json_value_added_whitespace", valid, " " + JOB_JSON, PUBLIC_RAW, False),
        ("wrong_public_key", valid, JOB_JSON, wrong_public, False),
        ("corrupted_signature", corrupted, JOB_JSON, PUBLIC_RAW, False),
        ("unsigned_token", "e30.e30.e30", JOB_JSON, PUBLIC_RAW, False),
        ("malformed_token", "not-a-jwt", JOB_JSON, PUBLIC_RAW, False),
        ("critical_header", ticket(headers={"crit": ["unsupported-extension"]}), JOB_JSON, PUBLIC_RAW, False),
    ]
    for name, override in (
        ("expired", {"iat": NOW - 90, "exp": NOW}),
        ("future_issue", {"iat": NOW + 6, "exp": NOW + 90}),
        ("excess_expiry", {"exp": NOW + 91}),
        ("stale_issue", {"iat": NOW - 91, "exp": NOW + 1}),
        ("nonpositive_window", {"iat": NOW, "exp": NOW}),
        ("wrong_issuer", {"iss": "untrusted-issuer"}),
        ("wrong_audience", {"aud": "other-service"}),
        ("empty_subject", {"sub": ""}),
        ("invalid_job_id", {"jti": "../unsafe"}),
        ("wrong_body_digest", {"sha256": "0" * 64}),
    ):
        result.append((name, ticket(claims=override), JOB_JSON, PUBLIC_RAW, False))
    return result


VECTORS = vectors()
NODE_VERIFIER = """
import fs from 'node:fs';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const {verifyTicket, verificationFingerprint} = await import(input.module);
const results = input.vectors.map(test => {
  try {
    const claims = verifyTicket(test.ticket, test.job_json, test.public_key, input.now);
    return {name:test.name, accepted:true, claims};
  } catch (error) {
    return {name:test.name, accepted:false, status:error.status, error:error.message};
  }
});
process.stdout.write(JSON.stringify({results, fingerprint:verificationFingerprint(input.public_key)}));
"""


@pytest.fixture(scope="module")
def node_verification():
    if NODE is None:
        pytest.skip("Node.js is required for the actual cross-language signature verification test")
    payload = {"module": (ROOT / "apps/executor/lib/auth.mjs").as_uri(), "now": NOW,
               "public_key": PUBLIC_RAW, "vectors": [
                   {"name": name, "ticket": signed, "job_json": body, "public_key": public}
                   for name, signed, body, public, _ in VECTORS]}
    process = subprocess.run([NODE, "--input-type=module", "-e", NODE_VERIFIER],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True, check=False, timeout=15, cwd=ROOT)
    assert process.returncode == 0, process.stderr.decode("utf-8", errors="replace")
    return json.loads(process.stdout)


@pytest.mark.parametrize("name,signed,body,public,accepted", VECTORS, ids=[item[0] for item in VECTORS])
def test_python_eddsa_tickets_are_verified_by_the_real_node_broker(name, signed, body, public, accepted, node_verification):
    outcome = next(item for item in node_verification["results"] if item["name"] == name)
    assert outcome["accepted"] is accepted, outcome
    if accepted:
        assert outcome["claims"]["sha256"] == hashlib.sha256(body.encode("utf-8")).hexdigest()
        assert outcome["claims"]["sub"] == "public-test-user"
    else:
        assert outcome["status"] == 401, outcome


def test_python_and_node_report_the_same_raw_ed25519_key_fingerprint(node_verification):
    assert node_verification["fingerprint"] == hashlib.sha256(public_key_bytes(PRIVATE_KEY)).hexdigest()
