# JobRun on one VPS

Preparation for a provider-independent Linux VPS deployment. No server, domain,
DNS record, production credential, subscription or running deployment is created
by these files. Docker images and the Compose stack still require a real Linux
Docker build and an end-to-end staging check before production use.

The stack is Caddy (HTTPS), the practice app and the existing FastAPI image.
`compose.tasks.yaml` optionally adds the task board. Supabase remains the existing
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

Use a fresh checkout of a reviewed release. Preserve the current coordinated
question-copy release: do not merge it into `master` just to obtain files, seed
the live database, or update Render while the compatible frontend is not ready.

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
separate from promoting the held application release: bootstrap with an isolated
workflow-only commit, preserving the existing frontend/backend release hold.

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
IDs against the manifest and keep the prior successful images for rollback.
Continue with the server-side Compose and release checks above. This is a manual
staging builder; automatic deployment and production promotion are not wired.

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

Keep the existing Netlify and Render deployments available while testing the new
origins. Add the new root/`www`/optional tasks origins to Supabase Auth redirect
URLs, retaining the old URLs during the transition. Change its production Site
URL when the candidate is ready. Test account login, a new confirmation email,
question loading, saving, Fundamentals completion, a duel link and isolated code
execution; test billing returns/webhooks in the appropriate test environment if
configured. A new origin requires sign-in again and does not transfer browser-only
drafts, so save/copy active drafts before redirecting old URLs.

The new domain can go live independently of Netlify. Redirecting the old Netlify
hostname requires a successful Netlify publication of that redirect; exhausted
deployment credits can still block that separate step.

For the held question-copy release, the VPS frontend and API must come from the
same reviewed commit. Announce or redirect to the new site only after the revision
gate and authenticated functional checks pass. Update payment webhook targets
when moving the API, preserving the provider's verification secret/procedure.

For later releases, build every enabled application service with a **new common SHA tag**,
then run `up --no-build --wait` and the same version/functional checks. This
simple Compose setup can have a short maintenance window while containers are
replaced; it does not implement blue/green or zero-downtime releases. CI/CD wiring
is intentionally not enabled until a server, SSH access and release gates are
chosen and verified. Run independent tests/previews before publishing production.

## Roll back and maintain

Record each successful SHA and keep its local app images plus the release's
configuration snapshot. To roll back, restore that reviewed release's public
configuration and `SOURCE_REVISION`, then run the same `up -d --no-build --wait`
command and verification. Roll back web/API/optional tasks together. Do not
rebuild an old SHA from a different checkout, discard live database changes or
restore a database as part of an ordinary application rollback.

If initial cutover fails, continue using the retained old hosting URLs and
restore prior Supabase/backend Site URLs as needed. Remove old hosting only after
the new host, automatic deployment and restore procedure have been verified.

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
