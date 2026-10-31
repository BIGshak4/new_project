// ONE-OFF trusted build task, invoked only by an explicit operator build-command
// override. It creates no HTTP endpoint and never executes candidate code.
// Vercel's build OIDC credential stays in this SDK process, outside the VM.
import { Sandbox } from "@vercel/sandbox";

const baseSnapshot = process.env.JOBRUN_EXECUTION_SNAPSHOT_ID;
if (!baseSnapshot || !/^snap_[A-Za-z0-9]+$/.test(baseSnapshot)) throw new Error("A trusted toolchain base snapshot is required.");
let vm, snapshotted = false;
try {
  vm = await Sandbox.create({
    name: `jobrun-toolchain-seal-${Date.now()}`,
    source: { type: "snapshot", snapshotId: baseSnapshot },
    region: process.env.JOBRUN_EXECUTION_REGION || "iad1",
    persistent: false,
    networkPolicy: "deny-all",
    timeout: 120000,
    resources: { vcpus: 1 },
  });
  // SDK calls POST /v3/sandboxes/sessions/{id}/snapshot with numeric0. The MCP
  // connector's overlapping expiration union rejects numeric inputs, so this
  // supported SDK route avoids that connector serialization defect.
  const snapshot = await vm.snapshot({ expiration: 0 });
  snapshotted = true; // snapshot automatically terminates the source VM
  const expires = snapshot.expiresAt;
  console.log("JOBRUN_SEALED_TOOLCHAIN " + JSON.stringify({
    snapshot_id: snapshot.snapshotId,
    base_snapshot_id: baseSnapshot,
    region: vm.region,
    size_bytes: snapshot.sizeBytes,
    expires_at: expires ? expires.toISOString() : null,
    persistent_vm: false,
    candidate_code_executed: false,
    network: "deny-all",
  }));
  if (expires) throw new Error("The toolchain snapshot unexpectedly has an expiration; do not enable it as permanent.");
} finally {
  if (vm && !snapshotted) {
    try { await vm.stop(); } catch { /* independent two-minute VM deadline */ }
  }
}
