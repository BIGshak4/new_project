# Production publishing and outbound deployment

This route keeps image builds on GitHub's Linux runner and leaves the 2 GB VPS
running prebuilt images. The VPS needs no GitHub personal access token, registry
password, inbound CI SSH access or new public deployment endpoint. Automatic
deployment is active only after the publisher, anonymous pulls and host timer
have all been installed and verified.

## Release authority

Use the dedicated `production` branch of `BIGshak4/new_project`. The existing
`master` branch and its Netlify/Render pair remain separate during the transition.
Changes approved for the new site land on `production`; do not force-push it.
Protect/review that branch where repository permissions allow.

For ordinary updates, synchronize with current production, run the local checks,
review the changes and push the reviewed commit using a normal fast-forward push:

```sh
git push origin HEAD:production
```

A rejected non-fast-forward push must be reconciled with the current branch;
do not bypass it with a force push.

`.github/workflows/selfhost-publish.yml` runs on a push to that branch, or a manual
dispatch explicitly selecting it. It checks out the event's full SHA and checks
that it is still the public production head before publishing. It runs the source
frontend tests/type checks, builds both `linux/amd64` images and performs isolated
runtime/import smoke checks. Database, model and authentication credentials stay
on the VPS.

Push-triggered publication works from `production`. To expose GitHub's manual
dispatch control, the workflow also needs a reviewed workflow-only copy on the
default branch; that copy does not promote the held application runtime.

Required public repository variables:

- `SELFHOST_APP_DOMAIN=muxijobrun.com`
- `SELFHOST_API_DOMAIN=api.muxijobrun.com`
- `NEXT_PUBLIC_SUPABASE_URL`: existing public project URL
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: existing public publishable/anon key

After the pull service is proven, set `SELFHOST_VERIFY_LIVE=true` so publication
also waits for the public web/API health endpoints to report the same SHA.
The pull service gates on verified signed images, not whole-workflow completion;
otherwise this final health check would wait for a deployment that never starts.

## Public registry bootstrap

The publisher uses its short-lived repository `GITHUB_TOKEN` with
`packages: write`, plus `id-token: write` for keyless signing. It does not need a
stored publishing key. OCI source/revision labels link new packages to the repo.

First publication creates these packages privately:

- `ghcr.io/bigshak4/jobrun-api`
- `ghcr.io/bigshak4/jobrun-web`

A package administrator must open each package's **Package settings → Change
visibility → Public** once. A public source repository does not automatically
make its container packages public. GitHub documents this visibility change as
irreversible. Review the concrete packages and confirm that images contain only
repository source/public frontend configuration before making them public.
Repository push access alone does not establish package-admin access; the
`BIGshak4` account owner may need to perform this step.

Confirm anonymous access from the VPS before enabling its deployment timer.
There is no `latest` or `production` image tag to trust, no GitHub Release asset,
and no extra release-metadata package. Public branch head supplies the source SHA;
both corresponding signed images form the release pair.

## Exact publisher/puller contract

For a full 40-character lowercase production SHA `SHA`:

```text
API tag: ghcr.io/bigshak4/jobrun-api:SHA
Web tag: ghcr.io/bigshak4/jobrun-web:SHA
Platform: linux/amd64
OIDC issuer: https://token.actions.githubusercontent.com
Certificate identity: https://github.com/BIGshak4/new_project/.github/workflows/selfhost-publish.yml@refs/heads/production
Signed source_revision annotation: SHA
Signed release_id annotation: GitHub run ID/run attempt, identical for both images
```

Cosign is pinned to `v3.1.4`; signing is keyless by default. Every signature binds
the image digest and the two annotations. Tags and OCI labels alone are not
source verification. The host resolves each SHA tag once and verifies the exact
immutable reference before deploying it:

```sh
cosign verify \
  --certificate-identity 'https://github.com/BIGshak4/new_project/.github/workflows/selfhost-publish.yml@refs/heads/production' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  -a "source_revision=$SHA" \
  ghcr.io/bigshak4/jobrun-api@sha256:THE_RESOLVED_API_DIGEST
```

Repeat for web, require the same verified `release_id`, and apply only the
resolved `@sha256:...` references using a fixed administrator-owned Compose
definition. Never execute a script or Compose file downloaded from an image or
release. Recheck that the production branch has not moved before switching.
If only one image/signature exists, the branch changed, verification fails or
the service is unreachable, retain the current release.

## Host operation and recovery

The implementation under `autodeploy/` supplies the host-side polling and service
definitions. Install/review those files through the existing administrator SSH
connection. Keep application secrets and infrastructure policy outside the
published images. Enable the timer only after a dry run validates the expected
pair and a controlled update/rollback succeeds.

The timer needs outbound HTTPS/public Git access and a pinned verified Cosign
binary. Keep the current SSH firewall restriction. Serialize deployments, retain
the prior successful image digests/configuration and verify both live revisions.
A failed candidate should restore the prior pair; this single-VPS arrangement can
have a short interruption while containers restart. Disk/memory/uptime monitoring
and OS/container security updates remain operational responsibilities.

Publish first, make both packages public once, prove anonymous signature checks,
install/test the puller, then enable live verification. Until all these pass,
manual image transfer remains the working recovery path.

Official references: [GHCR publishing and anonymous public pulls](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
[package visibility and administrator requirements](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility),
[GitHub Actions signing identity](https://docs.sigstore.dev/quickstart/verification-cheat-sheet/),
[Cosign signature/annotation verification](https://docs.sigstore.dev/cosign/verifying/verify/).
