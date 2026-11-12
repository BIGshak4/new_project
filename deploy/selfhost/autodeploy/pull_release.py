"""Root-installed, outbound-only signed-image updater. Python 3 standard library.

Only fixed installed templates and local private configuration are executed.
Nothing executable is fetched from the watched Git branch. Logs deliberately
exclude subprocess output, HTTP response bodies, tokens and environment values.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import urllib.error

try:
    import fcntl
except ImportError:  # Pure unit tests can also run on Windows.
    fcntl = None

ROOT = Path('/opt/jobrun/autodeploy')
SHARED = Path('/opt/jobrun/shared')
DOCKER = '/usr/bin/docker'
COSIGN = '/usr/local/bin/cosign'
REPOSITORY = 'BIGshak4/new_project'
BRANCH = 'production'
IDENTITY = 'https://github.com/BIGshak4/new_project/.github/workflows/selfhost-publish.yml@refs/heads/production'
ISSUER = 'https://token.actions.githubusercontent.com'
ROLES = ('api', 'web')
REGISTRIES = {role: 'ghcr.io/bigshak4/jobrun-' + role for role in ROLES}
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'sha256:[0-9a-f]{64}\Z')
COHORT = re.compile(r'[1-9][0-9]*/[1-9][0-9]*\Z')
MAX_FAILURES = 3
RETRY_SECONDS = 15 * 60
KEEP_SUCCESS = 3
KEEP_FAILURE = 2
MAX_REF_REQUESTS = 30  # Timer polls <=12/hour; capacity remains for rechecks.


class DeployError(Exception):
    """Messages are fixed operator-safe categories, never raw external text."""


class NotPublished(DeployError):
    pass


class Deferred(DeployError):
    pass


class RemoteHTTPError(DeployError):
    def __init__(self, status):
        super().__init__('remote-http-failure')
        self.status = status


def require(condition, message):
    if not condition:
        raise DeployError(message)


def log(event, revision=None):
    record = {'event': event}
    if revision and SHA.fullmatch(revision):
        record['revision'] = revision
    print(json.dumps(record), flush=True)


def immutable_image(value, role, bootstrap=False):
    require(role in ROLES and isinstance(value, str), 'invalid-image-reference')
    prefixes = [REGISTRIES[role]]
    if bootstrap:
        prefixes.append('jobrun-' + role)
    require(any(value.startswith(prefix + '@') and DIGEST.fullmatch(value[len(prefix)+1:])
                for prefix in prefixes), 'invalid-image-reference')
    return value


def validate_release(release, bootstrap=False):
    require(isinstance(release, dict) and SHA.fullmatch(release.get('revision', '')), 'invalid-release-state')
    for role in ROLES:
        immutable_image(release.get(role + '_image'), role, bootstrap=bootstrap)
    generation = release['revision'] + '-' + release['api_image'].split(':')[-1][:12] + '-' + release['web_image'].split(':')[-1][:12]
    require(release.get('generation') == generation, 'invalid-release-generation')
    return release


def release_record(revision, images, cohort='bootstrap'):
    require(SHA.fullmatch(revision) is not None, 'invalid-revision')
    record = {'revision': revision, **{role+'_image': images[role] for role in ROLES}, 'release_id': cohort}
    record['generation'] = revision + '-' + images['api'].split(':')[-1][:12] + '-' + images['web'].split(':')[-1][:12]
    return validate_release(record, bootstrap=cohort == 'bootstrap')


def secure_path(path, private=False, directory=False):
    info = path.lstat()
    require(info.st_uid == 0 and not stat.S_ISLNK(info.st_mode), 'untrusted-local-path')
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'invalid-local-path-type')
    require(not info.st_mode & (0o077 if private else 0o022), 'unsafe-local-permissions')


def atomic_json(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.state-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(value, output, separators=(',', ':'))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path, default=None):
    if not path.exists():
        return default
    secure_path(path, private=True)
    require(path.stat().st_size <= 128 * 1024, 'oversized-local-state')
    return json.loads(path.read_text())


def public_settings(path):
    secure_path(path, private=True)
    values = {}
    allowed = {'APP_DOMAIN', 'API_DOMAIN', 'ACME_EMAIL'}
    for line in path.read_text().splitlines():
        if '=' not in line or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        if key.strip() in allowed:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key.strip()] = value
    hostname = re.compile(r'(?=.{1,253}\Z)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}\Z')
    require(all(hostname.fullmatch(values.get(key, '')) for key in ('APP_DOMAIN', 'API_DOMAIN')), 'invalid-public-hostname')
    require(values['APP_DOMAIN'] != values['API_DOMAIN'], 'duplicate-public-hostname')
    require(re.fullmatch(r'[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}', values.get('ACME_EMAIL', '')),
            'invalid-certificate-contact')
    return values


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Remote:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())
        self.tokens = {}

    def get(self, url, headers=None, limit=2*1024*1024, blob_redirects=False):
        try:
            request_headers = {'User-Agent': 'JobRun-root-updater', **(headers or {})}
            for attempt in range(4):
                request = urllib.request.Request(url, headers=request_headers)
                try:
                    with self.opener.open(request, timeout=20) as response:
                        require(response.status == 200, 'remote-http-failure')
                        data = response.read(limit+1)
                        require(len(data) <= limit, 'oversized-remote-response')
                        return data
                except urllib.error.HTTPError as error:
                    if not blob_redirects or error.code not in (301, 302, 303, 307, 308):
                        raise
                    target = urllib.parse.urlsplit(error.headers.get('Location', ''))
                    require(target.scheme == 'https' and target.hostname in {
                        'ghcr.io', 'pkg-containers.githubusercontent.com',
                    } and not target.username and not target.password and target.port in (None, 443),
                            'untrusted-registry-blob-redirect')
                    url = target.geturl()
                    # Never forward even anonymous registry bearer tokens to a CDN.
                    request_headers = {'User-Agent': 'JobRun-root-updater'}
            raise DeployError('too-many-registry-blob-redirects')
        except DeployError:
            raise
        except urllib.error.HTTPError as error:
            raise RemoteHTTPError(error.code) from None
        except Exception:
            raise DeployError('remote-http-failure') from None

    def production_revision(self):
        data = json.loads(self.get('https://api.github.com/repos/' + REPOSITORY + '/git/ref/heads/' + BRANCH,
                                   {'Accept': 'application/vnd.github+json'}, limit=65536))
        revision = data.get('object', {}).get('sha', '')
        require(SHA.fullmatch(revision) is not None, 'invalid-production-ref')
        return revision

    def registry_get(self, role, path):
        require(role in ROLES and not path.startswith('/') and '..' not in path, 'invalid-registry-request')
        repository = 'bigshak4/jobrun-' + role
        if role not in self.tokens:
            query = urllib.parse.urlencode({'service': 'ghcr.io', 'scope': 'repository:'+repository+':pull'})
            payload = json.loads(self.get('https://ghcr.io/token?'+query, limit=65536))
            token = payload.get('token') or payload.get('access_token')
            require(isinstance(token, str) and token, 'anonymous-registry-token-failure')
            self.tokens[role] = token
        return self.get('https://ghcr.io/v2/'+repository+'/'+path,
                        {'Authorization': 'Bearer '+self.tokens[role],
                         'Accept': 'application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.docker.distribution.manifest.list.v2+json'},
                        blob_redirects=path.startswith('blobs/'))

    def resolve(self, role, revision):
        require(SHA.fullmatch(revision) is not None, 'invalid-registry-tag')
        try:
            raw = self.registry_get(role, 'manifests/'+revision)
        except RemoteHTTPError as error:
            if error.status == 404:
                raise NotPublished('images-not-published-yet') from None
            raise
        digest = 'sha256:'+hashlib.sha256(raw).hexdigest()
        manifest = json.loads(raw)
        if 'manifests' in manifest:
            choices = [item for item in manifest['manifests'] if item.get('platform', {}).get('os') == 'linux'
                       and item.get('platform', {}).get('architecture') == 'amd64']
            require(len(choices) == 1, 'ambiguous-image-platform')
            child_digest = choices[0].get('digest', '')
            require(DIGEST.fullmatch(child_digest) is not None, 'invalid-platform-digest')
            raw_child = self.registry_get(role, 'manifests/'+child_digest)
            require('sha256:'+hashlib.sha256(raw_child).hexdigest() == child_digest, 'platform-manifest-digest-mismatch')
            manifest = json.loads(raw_child)
        config_digest = manifest.get('config', {}).get('digest', '')
        require(DIGEST.fullmatch(config_digest) is not None, 'invalid-image-config-digest')
        raw_config = self.registry_get(role, 'blobs/'+config_digest)
        require('sha256:'+hashlib.sha256(raw_config).hexdigest() == config_digest, 'image-config-digest-mismatch')
        config = json.loads(raw_config)
        require(config.get('os') == 'linux' and config.get('architecture') == 'amd64', 'unsupported-image-platform')
        return REGISTRIES[role]+'@'+digest

    def health(self, origin, path, field, revision, database=False):
        data = json.loads(self.get(origin+path, limit=65536))
        require(data.get('status') == 'ok' and data.get(field) == revision, 'public-health-revision-mismatch')
        if database:
            require(isinstance(data.get('database'), dict) and 'error' not in data['database']
                    and isinstance(data['database'].get('round_trip_ms'), (int, float)), 'database-health-failure')


class Runner:
    def command(self, arguments, label, timeout=240):
        try:
            result = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        except Exception:
            raise DeployError(label) from None
        require(result.returncode == 0, label)
        return result.stdout


def signature_cohorts(payload, image, revision):
    require(isinstance(payload, list), 'invalid-signature-response')
    matches = set()
    for signature in payload:
        optional = signature.get('optional', {})
        actual_digest = signature.get('critical', {}).get('image', {}).get('docker-manifest-digest')
        cohort = optional.get('release_id', '')
        if optional.get('source_revision') == revision and actual_digest == image.split('@')[1] and COHORT.fullmatch(cohort):
            matches.add(cohort)
    require(matches, 'signed-release-annotations-missing')
    return matches


def verify_candidate(remote, runner, revision):
    images, cohorts = {}, []
    for role in ROLES:
        images[role] = remote.resolve(role, revision)
        immutable_image(images[role], role)
        output = runner.command([COSIGN, 'verify', '--certificate-identity', IDENTITY,
                                 '--certificate-oidc-issuer', ISSUER, '-a', 'source_revision='+revision,
                                 '--output', 'json', images[role]], 'signature-verification-failure', timeout=120)
        cohorts.append(signature_cohorts(json.loads(output), images[role], revision))
    common = cohorts[0] & cohorts[1]
    require(common, 'signed-images-have-different-release-cohorts')
    cohort = max(common, key=lambda value: tuple(int(part) for part in value.split('/')))
    return release_record(revision, images, cohort)


class Deployer:
    def __init__(self, root=ROOT, shared=SHARED, runner=None, remote=None):
        self.root, self.shared = Path(root), Path(shared)
        self.state = self.root/'state'
        self.releases = self.root/'releases'
        self.runner, self.remote = runner or Runner(), remote or Remote()
        self.mutation_attempted = False

    def observe_revision(self):
        # Rechecking just before maintenance also consumes this rolling budget.
        # Across timer ticks, retries and rechecks there are at most 30 ref GETs
        # per hour; this does not rely on the timer being the only caller.
        now = time.time()
        calls = [stamp for stamp in read_json(self.state/'ref-requests.json', []) if now-stamp < 3600]
        if len(calls) >= MAX_REF_REQUESTS:
            raise Deferred('production-ref-poll-budget-wait')
        atomic_json(self.state/'ref-requests.json', calls+[now])
        return self.remote.production_revision()

    def release_path(self, release):
        validate_release(release, bootstrap=release.get('release_id') == 'bootstrap')
        return self.releases/release['generation']

    def compose(self, release, *arguments):
        directory = self.release_path(release)
        return self.runner.command([DOCKER, 'compose', '--project-name', 'jobrun', '--env-file', str(directory/'.env'),
                                    '-f', str(directory/'compose.yaml'), *arguments], 'compose-operation-failure', timeout=360)

    def snapshot(self, release):
        directory = self.release_path(release)
        if directory.exists():
            secure_path(directory, private=True, directory=True)
            for name in ('compose.yaml', 'Caddyfile', '.env', 'backend.env'):
                secure_path(directory/name, private=True)
            identity = dict(line.split('=', 1) for line in (directory/'.env').read_text().splitlines()
                            if '=' in line and not line.startswith('#'))
            require(identity.get('SOURCE_REVISION') == release['revision']
                    and identity.get('API_IMAGE') == release['api_image']
                    and identity.get('WEB_IMAGE') == release['web_image'], 'snapshot-identity-mismatch')
            return
        settings = public_settings(self.shared/'public-selfhost.env')
        secure_path(self.shared/'backend.env', private=True)
        for name in ('compose.yaml', 'Caddyfile'):
            secure_path(self.root/name)
        directory.mkdir(mode=0o700)
        for source, destination in ((self.root/'compose.yaml', directory/'compose.yaml'),
                                    (self.root/'Caddyfile', directory/'Caddyfile'),
                                    (self.shared/'backend.env', directory/'backend.env')):
            with destination.open('xb') as output:
                os.fchmod(output.fileno(), 0o600)
                output.write(source.read_bytes())
        values = {**settings, 'SOURCE_REVISION': release['revision'],
                  'API_IMAGE': release['api_image'], 'WEB_IMAGE': release['web_image']}
        with (directory/'.env').open('x') as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(''.join(key+'='+value+'\n' for key, value in values.items()))

    def pull(self, release):
        for role in ROLES:
            reference = immutable_image(release[role+'_image'], role)
            self.runner.command([DOCKER, 'pull', '--platform', 'linux/amd64', reference], 'image-pull-failure', timeout=420)
            platform = self.runner.command([DOCKER, 'image', 'inspect', '--format', '{{.Os}}/{{.Architecture}}', reference],
                                           'loaded-image-inspection-failure').decode().strip()
            require(platform == 'linux/amd64', 'loaded-image-platform-mismatch')

    def internal_health(self, release):
        node = "fetch('http://127.0.0.1:3000/api/health',{signal:AbortSignal.timeout(6000)}).then(async r=>{const j=await r.json();if(!r.ok||j.status!=='ok'||j.revision!==process.argv[1])process.exit(1)}).catch(()=>process.exit(1))"
        python = "import json,sys,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health?db_check=true',timeout=6); j=json.load(r); d=j.get('database',{}); assert r.status==200 and j.get('status')=='ok' and j.get('source_revision')==sys.argv[1] and 'error' not in d and isinstance(d.get('round_trip_ms'),(int,float))"
        self.compose(release, 'exec', '-T', 'web', 'node', '-e', node, release['revision'])
        self.compose(release, 'exec', '-T', 'api', 'python', '-c', python, release['revision'])

    def public_health(self, release):
        values = public_settings(self.release_path(release)/'.env')
        deadline = time.monotonic()+75
        while True:
            try:
                self.remote.health('https://'+values['APP_DOMAIN'], '/api/health', 'revision', release['revision'])
                self.remote.health('https://'+values['API_DOMAIN'], '/health?db_check=true', 'source_revision',
                                   release['revision'], database=True)
                return
            except Exception:
                if time.monotonic() >= deadline:
                    raise DeployError('public-release-health-failure') from None
                time.sleep(3)

    def replace_pair(self, release):
        # The public entry point remains closed until BOTH services pass the
        # internal revision gate. This deliberately trades a maintenance window
        # for avoiding a mixed frontend/API release.
        self.compose(release, 'stop', 'caddy')
        self.compose(release, 'stop', 'api', 'web')
        self.compose(release, 'up', '-d', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '180', 'api', 'web')
        self.internal_health(release)
        self.compose(release, 'up', '-d', '--no-build', '--pull', 'never', '--no-deps', '--wait', 'caddy')
        self.public_health(release)

    def deploy(self, previous, candidate):
        # Journal before the first service mutation; another timer run rolls
        # back if the process/power dies midway through the maintenance window.
        atomic_json(self.state/'pending.json', {'previous': previous, 'candidate': candidate})
        self.mutation_attempted = True
        settled = False
        try:
            self.replace_pair(candidate)
            atomic_json(self.state/'current.json', candidate)
            settled = True
        except Exception:
            log('candidate-failed-rolling-back', candidate['revision'])
            try:
                self.replace_pair(previous)
                atomic_json(self.state/'current.json', previous)
                settled = True
            except Exception:
                try:
                    self.compose(previous, 'stop', 'caddy')
                finally:
                    atomic_json(self.state/'blocked.json', {'reason': 'rollback-failed', 'revision': candidate['revision']})
                raise DeployError('rollback-failed-updater-blocked') from None
            raise DeployError('candidate-failed-previous-restored') from None
        finally:
            if settled:
                (self.state/'pending.json').unlink(missing_ok=True)

    def recover(self):
        pending = read_json(self.state/'pending.json')
        if not pending:
            return
        previous = validate_release(pending['previous'], bootstrap=pending['previous'].get('release_id') == 'bootstrap')
        current = read_json(self.state/'current.json')
        try:
            if current == pending['candidate']:
                self.internal_health(current)
                self.public_health(current)
            else:
                self.replace_pair(previous)
                atomic_json(self.state/'current.json', previous)
        except Exception:
            try:
                self.replace_pair(previous)
                atomic_json(self.state/'current.json', previous)
            except Exception:
                self.compose(previous, 'stop', 'caddy')
                atomic_json(self.state/'blocked.json', {'reason': 'interrupted-release-recovery-failed'})
                raise DeployError('recovery-failed-updater-blocked') from None
        (self.state/'pending.json').unlink(missing_ok=True)
        log('interrupted-release-recovered')

    def remember_failure(self, revision, candidate=None, counted=True):
        failures = read_json(self.state/'failures.json', {})
        failure = failures.get(revision, {'attempts': 0})
        failure.update(attempts=failure['attempts']+int(counted), next_retry=int(time.time())+(RETRY_SECONDS if counted else 0),
                       observed=int(time.time()))
        if candidate:
            failure['candidate'] = candidate
        failures[revision] = failure
        atomic_json(self.state/'failures.json', failures)

    def prune(self):
        history = read_json(self.state/'history.json', [])
        failures = read_json(self.state/'failures.json', {})
        ordered_failures = sorted(failures, key=lambda sha: failures[sha].get('observed', 0), reverse=True)
        old = history[KEEP_SUCCESS:] + [failures[sha]['candidate'] for sha in ordered_failures[KEEP_FAILURE:]
                                       if failures[sha].get('candidate')]
        history = history[:KEEP_SUCCESS]
        failures = {sha: failures[sha] for sha in ordered_failures[:KEEP_FAILURE]}
        retained = history + [item['candidate'] for item in failures.values() if item.get('candidate')]
        current = read_json(self.state/'current.json')
        if current:
            retained.append(current)
        pending = read_json(self.state/'pending.json')
        if pending:
            retained.extend([pending['previous'], pending['candidate']])
        retained_images = {item[role+'_image'] for item in retained for role in ROLES}
        retained_generations = {item['generation'] for item in retained}
        for release in old:
            validate_release(release, bootstrap=release.get('release_id') == 'bootstrap')
            for role in ROLES:
                image = release[role+'_image']
                # Never delete bootstrap images, arbitrary repositories, volumes,
                # container data, or an image referenced by any container.
                if image in retained_images or not image.startswith(REGISTRIES[role]+'@'):
                    continue
                immutable_image(image, role)
                used = self.runner.command([DOCKER, 'ps', '--all', '--quiet', '--filter', 'ancestor='+image], 'retention-inspection-failure')
                if not used.strip():
                    self.runner.command([DOCKER, 'image', 'rm', image], 'retention-image-removal-failure')
            directory = self.release_path(release)
            if release['generation'] not in retained_generations and directory.exists():
                secure_path(directory, private=True, directory=True)
                require({path.name for path in directory.iterdir()} <= {'compose.yaml', 'Caddyfile', '.env', 'backend.env'},
                        'unexpected-release-snapshot-files')
                shutil.rmtree(directory)
        atomic_json(self.state/'history.json', history)
        atomic_json(self.state/'failures.json', failures)

    def poll(self):
        require(not (self.state/'blocked.json').exists(), 'updater-blocked-root-review-required')
        self.recover()
        current = read_json(self.state/'current.json')
        require(current is not None, 'adopt-current-release-before-enabling-timer')
        validate_release(current, bootstrap=current.get('release_id') == 'bootstrap')
        try:
            revision = self.observe_revision()
        except Deferred:
            return
        if revision == current['revision']:
            return
        failure = read_json(self.state/'failures.json', {}).get(revision, {})
        if failure.get('attempts', 0) >= MAX_FAILURES or failure.get('next_retry', 0) > time.time():
            return
        candidate = None
        try:
            candidate = verify_candidate(self.remote, self.runner, revision)
            self.pull(candidate)
            self.snapshot(candidate)
            self.compose(candidate, 'config', '--quiet')
            if self.observe_revision() != revision:
                self.remember_failure(revision, candidate, counted=False)
                log('candidate-superseded-before-maintenance', revision)
                self.prune()
                return
        except Exception:
            # Publication/signature/network/configuration preflight never
            # consumes a rollout attempt and never closes the public entry.
            # It stays pending and is rechecked on the normal timer cadence.
            if candidate:
                self.remember_failure(revision, candidate, counted=False)
                try:
                    self.prune()
                except Exception:
                    log('retention-needs-root-review')
            log('release-preflight-pending', revision)
            return
        self.mutation_attempted = False
        try:
            self.deploy(current, candidate)
        except Exception:
            if not self.mutation_attempted:
                log('release-preflight-pending', revision)
                return
            self.remember_failure(revision, candidate)
            log('release-failed-retry-limited', revision)
            try:
                self.prune()
            except Exception:
                log('retention-needs-root-review')
            raise DeployError('release-failed-review-safe-local-state') from None
        history = read_json(self.state/'history.json', [])
        atomic_json(self.state/'history.json', [candidate]+[item for item in history if item['generation'] != candidate['generation']])
        log('release-published', revision)
        try:
            self.prune()
        except Exception:
            log('retention-needs-root-review')

    def adopt(self, revision, api_image, web_image):
        require(not (self.state/'current.json').exists(), 'current-release-already-adopted')
        release = release_record(revision, {'api': immutable_image(api_image, 'api', bootstrap=True),
                                            'web': immutable_image(web_image, 'web', bootstrap=True)})
        self.snapshot(release)
        self.internal_health(release)
        self.public_health(release)
        atomic_json(self.state/'current.json', release)
        atomic_json(self.state/'history.json', [release])
        log('current-release-adopted', revision)


@contextmanager
def process_lock(root):
    require(fcntl is not None and os.geteuid() == 0, 'root-linux-execution-required')
    secure_path(root, directory=True)
    for name in ('state', 'releases'):
        (root/name).mkdir(mode=0o700, exist_ok=True)
        secure_path(root/name, private=True, directory=True)
    lock_path = root/'state'/'updater.lock'
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise DeployError('updater-already-running') from None
        yield
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--poll', action='store_true')
    mode.add_argument('--adopt', metavar='FULL_SHA')
    mode.add_argument('--retry', metavar='FULL_SHA')
    parser.add_argument('--api-image')
    parser.add_argument('--web-image')
    args = parser.parse_args()
    try:
        secure_path(Path(__file__))
        with process_lock(ROOT):
            deployer = Deployer()
            if args.poll:
                deployer.poll()
            elif args.adopt:
                deployer.adopt(args.adopt, args.api_image, args.web_image)
            else:
                require(SHA.fullmatch(args.retry) is not None, 'invalid-retry-revision')
                require(not (deployer.state/'blocked.json').exists(), 'resolve-blocked-state-manually-before-retry')
                failures = read_json(deployer.state/'failures.json', {})
                failures.pop(args.retry, None)
                atomic_json(deployer.state/'failures.json', failures)
                log('manual-retry-enabled', args.retry)
    except DeployError as error:
        log(str(error))
        raise SystemExit(1)
    except Exception:
        log('updater-error-root-review-required')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
