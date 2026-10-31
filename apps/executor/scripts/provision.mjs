// Trusted operator task, never an HTTP action. Installs compilers in an empty VM,
// verifies tool versions, creates one reusable filesystem snapshot, then stops.
// SDK authentication stays in this local process; it is not added to the VM.
import { Sandbox } from "@vercel/sandbox";

const auth = process.env.VERCEL_TOKEN ? { token: process.env.VERCEL_TOKEN, teamId: process.env.VERCEL_TEAM_ID, projectId: process.env.VERCEL_PROJECT_ID } : {};
let vm, snapshotted = false;
try {
  vm = await Sandbox.create({ ...auth, image: "vercel/sandbox/universal", persistent: false, timeout: 600000, resources: { vcpus: 1 }, ...(process.env.JOBRUN_EXECUTION_REGION ? { region: process.env.JOBRUN_EXECUTION_REGION } : {}) });
  const install = await vm.runCommand({
    cmd: "bash", args: ["-c", "set -eu\ninstall -m 755 \"$(command -v node)\" /usr/local/bin/jobrun-node\nln -sf /usr/local/bin/jobrun-node /usr/local/bin/node\napt-get update -qq\nDEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc g++ iverilog ghdl python3\nuseradd --uid 1100 --create-home --shell /usr/sbin/nologin jobrun-code\napt-get clean\nrm -rf /var/lib/apt/lists/*"], sudo: true, timeoutMs: 480000,
  });
  if (install.exitCode !== 0) throw new Error(`Toolchain installation failed (exit ${install.exitCode}).`);
  const versions = {};
  for (const [name, cmd, args] of [["python", "python3", ["--version"]], ["javascript", "node", ["--version"]], ["c", "gcc", ["--version"]], ["cpp", "g++", ["--version"]], ["verilog", "iverilog", ["-V"]], ["vhdl", "ghdl", ["--version"]]]) {
    const version = await vm.runCommand({ cmd: "runuser", args: ["-u", "jobrun-code", "--", "env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "HOME=/home/jobrun-code", "LANG=C.UTF-8", cmd, ...args], sudo: true });
    if (version.exitCode !== 0) throw new Error(`Toolchain verification failed for ${name}.`);
    versions[name] = ((await version.stdout()) || (await version.stderr())).split("\n")[0];
  }
  const noSudo = await vm.runCommand({ cmd: "runuser", args: ["-u", "jobrun-code", "--", "sudo", "-n", "true"], sudo: true });
  if (noSudo.exitCode === 0) throw new Error("The execution user unexpectedly has sudo access.");
  // No source, candidate data, application credentials or expected tests entered
  // this VM. All request VMs restore only these installed tools and user account.
  const snapshot = await vm.snapshot(); snapshotted = true;
  console.log(JSON.stringify({ snapshot_id: snapshot.snapshotId, region: vm.region, versions, runner_uid: 1100, network_at_execution: "deny-all", persistence_at_execution: false }, null, 2));
} finally { if (vm && !snapshotted) await vm.stop(); }
