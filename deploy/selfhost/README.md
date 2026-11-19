# JobRun on one VPS

The practice website and API are live on a DigitalOcean VPS at
[muxijobrun.com](https://muxijobrun.com) and
[api.muxijobrun.com](https://api.muxijobrun.com). See
[PRODUCTION.md](PRODUCTION.md) for the verified deployment, costs, operator access
and remaining checks. The [production publisher](AUTODEPLOY.md) has built and
signed both public GHCR images, and the fixed host updater is installed. Its
supervised rollback drill passed at 18:59 UTC: the signed candidate passed real
live gates before an injected failure, then both prior c3 services were restored
and verified. Normal deployment of `1e01ffe` then passed at 18:59:47 UTC, and
the host timer was enabled and active at 19:00:30 UTC. Its first no-change check
succeeded; `SELFHOST_VERIFY_LIVE=true` is configured for future publications.
The approved Recovery ISO maintenance operation restored operator SSH access on
12 November 2026 at 18:56:48 UTC after about ten minutes. The original host key
and existing login key were verified; website/API c3 and database health passed.
The production runbook records the current availability and access state.

The canonical Tasks hostname is [tasks.muxijobrun.com](https://tasks.muxijobrun.com).
The November 14 extension publishes three signed application images for one SHA;
all three services passed live revision, DNS/TLS/assets and database checks on
November 14. The user's own Tasks login confirmation remains pending. See
the production record for the exact evidence. Accounts,
founder access, tasks and private files stay in the existing Supabase project;
the new browser origin needs its own sign-in and does not inherit local drafts.

The instructions below are the historical manual build/transfer and recovery route.
Ordinary production releases use the dedicated `production` branch and signed
image route. The production runbook labels the dated verified release and checks
the latest branch head dynamically. Do not
use these manual Compose files concurrently with the installed updater.

The automated stack is Caddy (HTTPS), the practice app, existing FastAPI image
and Tasks. The manual files below predate that three-image controller;
`compose.tasks.yaml` optionally adds Tasks only for this manual recovery route.
Do not mix that overlay or manual image tags with the fixed installed controller.
Supabase remains the existing
database, authentication and private storage service. The isolated Vercel Sandbox
execution broker remains external: never run submitted learner code on this VPS.

## Prepare the server and configuration

Use a supported Linux VPS with SSH key access, current OS security updates and
Docker Engine with Compose **2.30+** (`env_file.format: raw` is used). Confirm
actual runtime memory before choosing a permanent size. Build images on a trusted
build machine/CI runner with adequate memory, not on a small 2 GB production VPS.
Docker is installed from its official distribution; there is deliberately no
downloaded bootstrap script here.

At the provider firewall, permit public TCP 80/443 and optionally UDP 443. Limit
SSH to the administrator's source addresses. App ports 3000/8000 are not
published. Configure monitoring, disk-space alerts and off-server configuration
backups; the VPS is a single failure point.

The attached DigitalOcean Cloud Firewall is named `jobrun-production`. The
verified access change places the SSH source allowlist in this provider firewall,
with key-only SSH and no changing source allowlist inside UFW. UFW remains active
with a default-deny policy, IPv4 SSH allowed behind that cloud restriction, and
IPv6 SSH blocked. Future operator IP changes use the provider's
**Networking → Firewalls** rules UI; the steps are
in [PRODUCTION.md](PRODUCTION.md). Do not open SSH to all sources at the provider.

Use a fresh checkout of a reviewed release. Keep the dedicated `production`
branch separate from the retained `master` hosting route; do not merge into
`master` merely to obtain deployment files. Do not seed the live database or
update one service while its compatible frontend/API release is not ready.

From `deploy/selfhost` on that checkout:

```sh
umask 077
cp .env.example .env
cp backend.env.example backend.env
chmod 600 .env backend.env
docker compose version
```

Fill `.env` with the purchased hostnames, a certificate contact email, the existing
public Supabase URL/publishable key, and the **full reviewed Git SHA** as
`SOURCE_REVISION`. Keep it identical across all services and image tags. Confirm
the checkout is at that exact SHA and has no source changes before building.
The files must be committed in the reviewed release before using its SHA.

Transfer the existing backend configuration into `backend.env` securely on the
server. The example lists important keys, not the complete live configuration.
Preserve additional model-role, content, billing, pool and rate-limit settings.
Use the exact existing `CODE_EXECUTION_SIGNING_SEED`: changing it breaks the
broker's pinned identity. Set exact `ALLOWED_ORIGINS` for the new web and optional
task-board URLs, preserving required old origins during cutover. Values in this
raw env file are unquoted; literal `$` characters are preserved. Never pass
database, model, signing or service-role secrets as Docker build arguments.

`NEXT_PUBLIC_*` values are embedded at **build time**; a change to the API domain
or public Supabase configuration requires a new frontend build.

## Build and check the candidate

On a trusted Linux Docker build machine, use `deploy/selfhost` in a clean reviewed
checkout with the completed public `.env` and a placeholder `backend.env` copied
from its example. Builds never read real backend secrets. Build for the server's
architecture and retain the resulting images:

```sh
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml build api web
```

Transfer both exact SHA-tagged images to the server using Docker `save`/`load` or
a chosen private registry, and deploy from the same reviewed Compose checkout.
The server's `backend.env` contains the real configuration. Then run there:

```sh
docker compose -f compose.yaml run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose -f compose.yaml up -d --no-build --wait --wait-timeout 180
docker compose -f compose.yaml ps
```

`config --quiet` validates without printing resolved credentials. Build all
application images before replacing running containers. No `latest` app tag is
used, and the launch command never rebuilds on the production VPS.

### Manual GitHub image builder

`.github/workflows/selfhost-build.yml` provides a manual Linux `amd64` builder.
After this workflow is reviewed and available on the repository's default branch,
choose **Actions → Build self-hosted release images → Run workflow** and supply
the full reviewed release SHA. It checks out that exact commit, which must include
the Docker/Compose preparation. Introducing the builder to the default branch is
separate from approving a runtime release: use a reviewed workflow-only commit
if needed, without inadvertently promoting application changes to old hosting.

Supply website/API hostnames and the **public** Supabase URL/publishable (or legacy
anon) key as inputs, or configure repository variables `SELFHOST_APP_DOMAIN`,
`SELFHOST_API_DOMAIN`, `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`. Optional tasks also need `include_tasks`
and `SELFHOST_TASKS_DOMAIN` or its input. Never supply backend secrets. This job
does not use a registry credential, SSH credential or production environment file.

The builder validates Compose/Caddy, starts the frontend images with networking
disabled to check revision/document/JavaScript assets, and checks API module
imports. API production startup, database, auth and model checks require the real
server configuration and remain staging checks. It packages the exact images,
image IDs, source SHA and checksums as a GitHub artifact retained for **one day**;
normal GitHub Actions/storage limits still apply. Download it before expiry.

Extract the artifact in a separate directory, run `sha256sum -c SHA256SUMS`,
compare `manifest.json` and `SOURCE_REVISION` with the selected reviewed release,
then transfer the archive securely and run
`docker load --input images-linux-amd64.tar.gz` on the server. Verify loaded image
metadata against the archive/manifest and keep the prior successful images for
rollback. Docker 29's containerd image store can expose an OCI manifest digest
as `.Id`, while a classic saved-image manifest records its config digest; raw
string equality between those identifiers is not sufficient verification. Check
the selected Linux amd64 manifest, its config digest, layer chain and source
revision before using the loaded immutable reference. Never waive an unexplained
metadata mismatch.
Continue with the server-side Compose and release checks above. This is a manual
staging builder; it does not publish or promote a production release. The
separate production publisher and host puller are documented in
[AUTODEPLOY.md](AUTODEPLOY.md).

For the optional task board, use both `-f` options **before the subcommand** in
every build/check/start/rollback command, and build `api web tasks`. For example:

```sh
docker compose -f compose.yaml -f compose.tasks.yaml up -d --no-build --wait --wait-timeout 180
```

Point `TASKS_DOMAIN` at this VPS as well. The overlay adds its HTTPS site and waits
for its container to become healthy.

Point the domain's A record to the VPS and its `www` CNAME to the website domain;
point the API (and optional tasks) hostname at the same VPS. Add AAAA records only
when that VPS's IPv6 route has been verified. Caddy obtains and renews HTTPS when
DNS points here and ports 80/443 are reachable. The `caddy_data` and
`caddy_config` volumes persist certificates and configuration across restarts.

From an administrator machine with Node 24, verify the exact live release:

```sh
node verify-release.mjs FULL_40_CHARACTER_SHA https://YOUR_DOMAIN https://YOUR_API_DOMAIN
```

Pass `https://YOUR_TASKS_DOMAIN` as the fourth argument if enabled. Each response
must be HTTP 200, `status: ok`, and the same exact SHA (`revision` for Next.js;
`source_revision` for the API). Redirects fail the check so it cannot silently
verify a different host. This is a runtime/version gate, not an authenticated
database or model test. Inspect protected health details through the normal
operator procedure without printing `HEALTH_KEY`.

## Cut over and subsequent releases

The November 14 cutover is live. Builds are stopped on both old Netlify sites,
and legacy deployment workflows are disabled. Old copies remain temporarily
pending the user's login confirmation; runtime and rollback do not depend on
Netlify. Supabase's Site URL is the canonical main origin and its redirect
allowlist has been cleaned of old Netlify URLs. For a future migration, review
these settings explicitly rather than restoring historical origins. Test account login, a new confirmation email,
question loading, saving, Fundamentals completion, a duel link and isolated code
execution; test billing returns/webhooks in the appropriate test environment if
configured. A new origin requires sign-in again and does not transfer browser-only
drafts, so save/copy active drafts before redirecting old URLs.

The new domain can go live independently of Netlify. Redirecting the old Netlify
hostname requires a successful Netlify publication of that redirect; exhausted
deployment credits can still block that separate step.

For any release, all enabled app images must come from the same reviewed commit.
Announce or redirect to the new site only after the revision
gate and authenticated functional checks pass. Update payment webhook targets
when moving the API, preserving the provider's verification secret/procedure.

For a manual recovery release, build every enabled application service with a
**new common SHA tag**, then run `up --no-build --wait` and the same
version/functional checks. Stop the installed updater timer before a manual
replacement and reconcile its state before enabling it again. Ordinary signed
releases are described in [AUTODEPLOY.md](AUTODEPLOY.md). Both routes can have a
short maintenance window while containers are replaced. Run independent
tests/previews before publishing production.

## Roll back and maintain

Record each successful SHA and keep its local app images plus the release's
configuration snapshot. To roll back, restore that reviewed release's public
configuration and `SOURCE_REVISION`, then run the same `up -d --no-build --wait`
command and verification. Roll back the exact enabled service set together. An
old web/API-only controller snapshot has no Tasks route: its rollback removes
the newer Tasks container. Preserve a prior three-image snapshot when Tasks
must remain available; a pre-Tasks pair is only a historical fallback without
Tasks. No rollback depends on Netlify. Do not retrofit a Tasks digest into old state.
Do not
rebuild an old SHA from a different checkout, discard live database changes or
restore a database as part of an ordinary application rollback.

If a release fails, use the verified prior VPS snapshot and its protected
configuration. Do not restore old hosting URLs or Supabase settings merely to
roll back application code. Retiring old copies and changing billing remain
separate actions; a billing-plan change has not been confirmed.

Back up deployment configuration and Caddy volumes securely off this server.
Continue the existing Supabase database/storage backup policy. Schedule OS,
Docker, Caddy and base-image security updates, monitor service uptime and disk
space, and retain tested rollback images. Do not use `docker compose down -v`
or image/volume pruning as part of the release routine.

## Local checks

```sh
node --test verify-release.test.mjs
```

The health verifier tests mismatched releases and failures without contacting
production. Container build, TLS, resource usage, long-running request behavior,
secrets transfer and actual cutover remain staging checks on the chosen server.
