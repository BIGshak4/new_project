# Signed image updates from the host

These are fixed operator-installed files, not scripts downloaded from `production`.
The updater only reads the public branch SHA and signed container metadata. The
VPS needs no GitHub token, Git credentials, registry login, inbound CI SSH, or code
checkout. Both GHCR packages must be public. The executor stays on its isolated
external Vercel Sandbox broker; submitted source never executes on this VPS.

The fixed controller is installed on the VPS. On 12 November 2026 its 23 unit
tests passed on Linux, systemd validation passed, the c3 baseline was adopted,
and anonymous verification of both signed public GHCR images for `1e01ffe`
succeeded. The supervised rollback drill then passed at 18:59 UTC: a candidate
that passed real live gates was intentionally rejected, both c3 services were
restored and verified, and no pending/blocked state remained. Normal deployment
of `1e01ffe` then passed at 18:59:47 UTC. The timer was enabled and active at
19:00:30 UTC, and its first no-change invocation succeeded. See
[the current production record](../PRODUCTION.md) before
operating it. Unit tests mock external effects and do not replace the live gates.

## Trust and publication contract

- Repository/ref: `BIGshak4/new_project`, `refs/heads/production`.
- Images: `ghcr.io/bigshak4/jobrun-api:<full lowercase SHA>` and
  `ghcr.io/bigshak4/jobrun-web:<same SHA>`, with runnable `linux/amd64` configs.
- Both immutable `repo@sha256:...` references must verify with Cosign 3.1.4,
  issuer `https://token.actions.githubusercontent.com`, and exact identity
  `https://github.com/BIGshak4/new_project/.github/workflows/selfhost-publish.yml@refs/heads/production`.
- Each signature must bind `source_revision=<full SHA>`. At least one verified
  `release_id=<GitHub run ID>/<attempt>` must be shared by both images. Cosign's
  transparency/certificate checks remain enabled.

The host resolves tags into digests once, verifies both, then pulls only those
digests. Config bytes are checked against their manifest digest and selected
platform. A changed tag after resolution cannot substitute another image.
OCI indexes are supported only when exactly one runnable Linux amd64 descriptor
is present; its config is checked before any service changes.

## Fixed installation and adoption

An administrator installs a reviewed copy of `pull_release.py`, `compose.yaml`,
`Caddyfile` and the two systemd units. Install Cosign from the verified upstream
release with its published checksum first; its path is `/usr/local/bin/cosign`.
Docker with Compose 2.30+ and Python 3 are required.

From this reviewed directory on the server, as an administrator:

```sh
sudo install -d -o root -g root -m 700 /opt/jobrun/autodeploy
sudo install -d -o root -g root -m 700 /opt/jobrun/autodeploy/state /opt/jobrun/autodeploy/releases
sudo install -o root -g root -m 644 pull_release.py compose.yaml Caddyfile /opt/jobrun/autodeploy/
sudo install -o root -g root -m 644 jobrun-updater.service jobrun-updater.timer /etc/systemd/system/
```

The existing `/opt/jobrun/shared/backend.env` and
`/opt/jobrun/shared/public-selfhost.env` must already contain the reviewed current
configuration. Make them root-owned with mode `600`; their parent must not be
group/other writable. Do not display them, recreate credentials from examples,
or change the execution signing identity. `public-selfhost.env` supplies
`APP_DOMAIN`, `API_DOMAIN` and `ACME_EMAIL`; its old `SOURCE_REVISION` is ignored.
New release snapshots bind the verified SHA and both immutable image references.
Backend environment bytes are copied without shell parsing. Each snapshot is
private, root-owned, and includes its fixed Compose/Caddy configuration.

The already verified c3 release was adopted as the rollback baseline. The command
below records the initial bootstrap procedure; do not rerun it when
`state/current.json` exists. These are the verified Docker 29 immutable manifest
references, not config IDs:

```sh
sudo python3 /opt/jobrun/autodeploy/pull_release.py \
  --adopt c3a2d28a9d9c964325a442d5b642354b862fcec2 \
  --api-image jobrun-api@sha256:02e1ef480e2a165d8400474d7579248bbc37549a448f494b2f87486050cbed46 \
  --web-image jobrun-web@sha256:dbd44171bf83fbd3282644ecade3c8dd0e46f77892a6eae992960eadc421a6f4
```

Adoption checks the running services' internal and public exact-SHA health and
the database probe before recording state. It does not replace containers.
Only explicit bootstrap adoption accepts the existing local image repositories;
all automatically selected candidates require signed GHCR references.

The Compose project remains **`jobrun`**, preserving the existing
`jobrun_caddy_data` and `jobrun_caddy_config` volumes and certificate storage.
The updater does not change SSH or firewall policy. Operator sources are
restricted by the attached DigitalOcean `jobrun-production` Cloud Firewall.
The separately approved Recovery ISO/UFW change was verified. UFW remains active
and SSH key-only; IPv6 SSH is blocked. See [PRODUCTION.md](../PRODUCTION.md) for
the verified recovery and future provider-UI IP-change steps.

The commands below record activation after review and the successful supervised
rollback/normal deployment checks. The timer is already enabled on this server:

```sh
sudo systemctl daemon-reload
sudo systemctl start jobrun-updater.service
sudo systemctl enable --now jobrun-updater.timer
sudo systemctl status jobrun-updater.timer --no-pager
```

The timer waits at least five minutes after each completed invocation. A
persistent rolling counter limits total branch GETs, including pre-switch
rechecks and manual invocations, to thirty per hour. Normal timer polls are at
most twelve per hour; the extra budget avoids starving the final recheck after
an idle hour and remains below GitHub's anonymous sixty-request limit.
Concurrent invocations take a nonblocking lock.
The service uses its own empty Docker configuration and HOME, without operator
registry credentials. Logs contain static result categories and public SHAs.

## Release transaction, retry and recovery

Both images are pulled and validated before the public entry point is touched.
The production ref is rechecked immediately before mutation. A superseded
candidate is skipped. Fixed templates and protected private environment copies
are used; no Compose file, entry-point script or environment is fetched from Git.

The transaction writes an on-disk recovery journal, stops **Caddy**, stops both
old app services, and starts both candidate services. Caddy stays stopped until
both internal SHA checks and the API database round trip pass. It then restarts
and both public HTTPS health checks must pass. Only then is `current.json`
atomically replaced. This intentionally causes a short maintenance window.
Existing browser tabs may still need a refresh after a content revision changes.

A failure replaces **both** services with the previous image/config snapshots.
The entry point reopens only after the previous pair passes the same gates. If
rollback fails, Caddy is stopped and `blocked.json` prevents future automation.
An interrupted transaction is recovered before any new branch candidate is
considered. Root review is required to resolve a blocked journal; do not simply
delete it and restart automation without confirming the actual running pair.

A branch SHA can exist while CI is still building. Unavailable images, missing
or invalid signatures, network errors and other preflight failures stay pending,
keep the current services running and retry on the normal five-minute cadence.
They never bypass verification and never consume rollout attempts. A fixed safe
log category identifies the pending state without dumping external responses.
Only failures after service mutation is attempted consume the rollout budget:
three attempts, at least fifteen minutes apart. Then the same SHA is
quarantined until a different production SHA or an explicit root retry:

```sh
sudo python3 /opt/jobrun/autodeploy/pull_release.py --retry FULL_40_CHARACTER_SHA
```

Review the safe journal/status first. An explicit retry only clears that SHA's
failure counter; it does not remove a blocked recovery state or bypass signatures.
If environment values need correction, review their existing private snapshot
as well: retries reuse that candidate's snapshot. Never weaken a gate to make
the timer green.

The host retains three successful snapshots and two recent failed/superseded
candidate records. Older managed snapshots are removed only when their exact
directory contains the known four controller files. Old signed GHCR image
references are removed only when not retained and not used by any container.
Bootstrap images, arbitrary image repositories, shared environment files,
original release directories, Caddy volumes and database/storage data are never
automatically removed. A retention failure is logged for root review rather than
running a broad image/volume prune. Keep off-server configuration backups and
disk-space monitoring.

## Verification before installation

```sh
python3 -m unittest discover -s deploy/selfhost/autodeploy -p 'test_*.py' -v
```

Run that from the repository root. Tests cover reference allowlists, signature
identity/revision/cohort binding, config-digest integrity, redirect credential
stripping, platform rejection, stopped-entry paired replacement, atomic state,
rollback failure, crash recovery, quarantine, superseded releases and ref budgets.
