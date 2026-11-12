"""No Docker, network, credentials, or server operations: all effects are mocked."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pull_release', Path(__file__).with_name('pull_release.py'))
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

OLD = 'a'*40
NEW = 'b'*40


def release(revision, cohort='12/1'):
    return updater.release_record(revision, {
        role: updater.REGISTRIES[role]+'@sha256:'+('1' if role == 'api' else '2')*64
        for role in updater.ROLES
    }, cohort)


def signature(image, revision, cohort):
    return {'critical': {'image': {'docker-manifest-digest': image.split('@')[1]}},
            'optional': {'source_revision': revision, 'release_id': cohort}}


class ReferenceTests(unittest.TestCase):
    def test_mutable_tags_shell_payload_wrong_role_and_registry_fail(self):
        for value in ('ghcr.io/bigshak4/jobrun-api:latest',
                      'ghcr.io/evil/jobrun-api@sha256:'+'1'*64,
                      updater.REGISTRIES['web']+'@sha256:'+'1'*64,
                      updater.REGISTRIES['api']+'@sha256:'+'1'*64+';id'):
            with self.subTest(value=value), self.assertRaises(updater.DeployError):
                updater.immutable_image(value, 'api')

    def test_local_immutable_image_only_for_explicit_bootstrap(self):
        image = 'jobrun-api@sha256:'+'3'*64
        self.assertEqual(updater.immutable_image(image, 'api', bootstrap=True), image)
        with self.assertRaises(updater.DeployError):
            updater.immutable_image(image, 'api')

    def test_release_generation_cannot_escape_root(self):
        value = release(NEW)
        value['generation'] = '../../shared'
        with self.assertRaises(updater.DeployError):
            updater.validate_release(value)


class SignatureTests(unittest.TestCase):
    def candidate(self, cohorts=('12/1', '12/1'), signature_revision=NEW):
        class Remote:
            def resolve(self, role, revision):
                return release(revision)[role+'_image']
        class Runner:
            def __init__(self):
                self.calls = []
            def command(self, arguments, label, timeout):
                self.calls.append(arguments)
                role_index = len(self.calls)-1
                return json.dumps([signature(arguments[-1], signature_revision, cohorts[role_index])]).encode()
        runner = Runner()
        return Remote(), runner

    def test_exact_identity_issuer_revision_and_cohort_required(self):
        remote, runner = self.candidate()
        result = updater.verify_candidate(remote, runner, NEW)
        self.assertEqual(result['revision'], NEW)
        self.assertEqual(len(runner.calls), 2)
        for args in runner.calls:
            self.assertEqual(args[args.index('--certificate-identity')+1], updater.IDENTITY)
            self.assertEqual(args[args.index('--certificate-oidc-issuer')+1], updater.ISSUER)
            self.assertEqual(args[args.index('-a')+1], 'source_revision='+NEW)
            self.assertNotIn('--insecure-ignore-tlog', args)

    def test_mismatched_release_cohort_fails(self):
        remote, runner = self.candidate(('12/1', '13/1'))
        with self.assertRaises(updater.DeployError):
            updater.verify_candidate(remote, runner, NEW)

    def test_wrong_revision_annotation_fails_even_with_successful_cli(self):
        remote, runner = self.candidate(signature_revision=OLD)
        with self.assertRaises(updater.DeployError):
            updater.verify_candidate(remote, runner, NEW)

    def test_forged_critical_digest_fails(self):
        image = release(NEW)['api_image']
        payload = signature(image, NEW, '12/1')
        payload['critical']['image']['docker-manifest-digest'] = 'sha256:'+'9'*64
        with self.assertRaises(updater.DeployError):
            updater.signature_cohorts([payload], image, NEW)


class RegistryTests(unittest.TestCase):
    def test_config_bytes_are_bound_to_manifest_and_platform(self):
        import hashlib
        config = json.dumps({'os': 'linux', 'architecture': 'amd64'}).encode()
        digest = 'sha256:'+hashlib.sha256(config).hexdigest()
        manifest = json.dumps({'schemaVersion': 2, 'config': {'digest': digest}}).encode()
        remote = updater.Remote()
        with patch.object(remote, 'registry_get', side_effect=[manifest, config]):
            self.assertTrue(remote.resolve('api', NEW).startswith(updater.REGISTRIES['api']+'@sha256:'))
        with patch.object(remote, 'registry_get', side_effect=[manifest, config+b' ']):
            with self.assertRaises(updater.DeployError):
                remote.resolve('api', NEW)

    def test_wrong_platform_is_rejected(self):
        import hashlib
        config = json.dumps({'os': 'linux', 'architecture': 'arm64'}).encode()
        manifest = json.dumps({'config': {'digest': 'sha256:'+hashlib.sha256(config).hexdigest()}}).encode()
        remote = updater.Remote()
        with patch.object(remote, 'registry_get', side_effect=[manifest, config]):
            with self.assertRaises(updater.DeployError):
                remote.resolve('api', NEW)

    def test_ambiguous_platform_index_is_rejected(self):
        manifest = json.dumps({'manifests': [
            {'platform': {'os': 'linux', 'architecture': 'amd64'}, 'digest': 'sha256:'+'1'*64},
            {'platform': {'os': 'linux', 'architecture': 'amd64'}, 'digest': 'sha256:'+'2'*64},
        ]}).encode()
        remote = updater.Remote()
        with patch.object(remote, 'registry_get', return_value=manifest):
            with self.assertRaises(updater.DeployError):
                remote.resolve('api', NEW)

    def test_blob_redirect_strips_authorization_and_rejects_foreign_host(self):
        from email.message import Message
        import urllib.error
        headers = Message()
        headers['Location'] = 'https://pkg-containers.githubusercontent.com/ghcr1/blob?signature=opaque'
        redirect = urllib.error.HTTPError('https://ghcr.io/blob', 307, 'redirect', headers, None)
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return b'{}'
        remote = updater.Remote()
        with patch.object(remote.opener, 'open', side_effect=[redirect, Response()]) as request:
            self.assertEqual(remote.get('https://ghcr.io/blob', {'Authorization': 'Bearer temporary'}, blob_redirects=True), b'{}')
            self.assertIsNone(request.call_args_list[1].args[0].get_header('Authorization'))
        headers['Location'] = 'https://attacker.example/blob'
        with patch.object(remote.opener, 'open', side_effect=redirect):
            with self.assertRaises(updater.DeployError):
                remote.get('https://ghcr.io/blob', blob_redirects=True)


class RolloutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.deployer = updater.Deployer(root=Path(self.temporary.name))
        self.deployer.state.mkdir()
        self.previous, self.candidate = release(OLD), release(NEW)
        self.writes = []
        self.atomic = patch.object(updater, 'atomic_json', side_effect=lambda path, value: self.writes.append((path.name, value)))
        self.atomic.start()

    def tearDown(self):
        self.atomic.stop()
        self.temporary.cleanup()

    def test_maintenance_covers_paired_replacement_and_internal_gate(self):
        events = []
        self.deployer.compose = lambda current, *args: events.append(('compose', args))
        self.deployer.internal_health = lambda current: events.append(('internal-health', ()))
        self.deployer.public_health = lambda current: events.append(('public-health', ()))
        self.deployer.replace_pair(self.candidate)
        self.assertEqual(events[0], ('compose', ('stop', 'caddy')))
        self.assertEqual(events[1], ('compose', ('stop', 'api', 'web')))
        self.assertLess(events.index(('internal-health', ())),
                        next(index for index, event in enumerate(events) if event[0] == 'compose' and event[1][-1] == 'caddy' and event[1][0] == 'up'))
        self.assertEqual(events[-1][0], 'public-health')

    def test_current_pointer_only_after_public_success(self):
        def replace(current):
            self.assertFalse(any(name == 'current.json' for name, value in self.writes))
        self.deployer.replace_pair = replace
        self.deployer.deploy(self.previous, self.candidate)
        self.assertEqual(self.writes[-1], ('current.json', self.candidate))
        self.assertEqual(self.writes[0][0], 'pending.json')

    def test_failed_candidate_restores_both_previous_images(self):
        attempted = []
        def replace(current):
            attempted.append(current)
            if current == self.candidate:
                raise updater.DeployError('synthetic-health-failure')
        self.deployer.replace_pair = replace
        with self.assertRaises(updater.DeployError):
            self.deployer.deploy(self.previous, self.candidate)
        self.assertEqual(attempted, [self.candidate, self.previous])
        self.assertEqual([value for name, value in self.writes if name == 'current.json'], [self.previous])

    def test_failed_rollback_closes_public_entry_and_blocks_automation(self):
        calls = []
        self.deployer.replace_pair = lambda current: (_ for _ in ()).throw(updater.DeployError('synthetic-failure'))
        self.deployer.compose = lambda current, *args: calls.append(args)
        with self.assertRaises(updater.DeployError):
            self.deployer.deploy(self.previous, self.candidate)
        self.assertIn(('stop', 'caddy'), calls)
        self.assertTrue(any(name == 'blocked.json' for name, value in self.writes))
        self.assertFalse(any(name == 'current.json' for name, value in self.writes))

    def test_manual_interrupt_preserves_recovery_journal(self):
        journal = self.deployer.state/'pending.json'
        journal.write_text('synthetic-journal')
        self.deployer.replace_pair = lambda current: (_ for _ in ()).throw(KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.deployer.deploy(self.previous, self.candidate)
        self.assertTrue(journal.exists())

    def test_retry_quarantine_does_not_run_signature_or_docker(self):
        self.deployer.remote.production_revision = lambda: NEW
        def state(path, default=None):
            if path.name == 'current.json': return self.previous
            if path.name == 'failures.json': return {NEW: {'attempts': updater.MAX_FAILURES}}
            return default
        with patch.object(updater, 'read_json', side_effect=state), patch.object(updater, 'verify_candidate') as verify:
            self.deployer.poll()
            verify.assert_not_called()

    def test_missing_publication_does_not_consume_failure_or_touch_services(self):
        self.deployer.observe_revision = lambda: NEW
        def state(path, default=None):
            return self.previous if path.name == 'current.json' else default
        with patch.object(updater, 'read_json', side_effect=state), \
             patch.object(updater, 'verify_candidate', side_effect=updater.NotPublished('not-ready')), \
             patch.object(self.deployer, 'remember_failure') as failure, \
             patch.object(self.deployer, 'compose') as compose:
            self.deployer.poll()
            failure.assert_not_called()
            compose.assert_not_called()

    def test_ref_recheck_skips_superseded_candidate_before_maintenance(self):
        def state(path, default=None):
            return self.previous if path.name == 'current.json' else default
        with patch.object(updater, 'read_json', side_effect=state), \
             patch.object(updater, 'verify_candidate', return_value=self.candidate), \
             patch.object(self.deployer, 'observe_revision', side_effect=[NEW, 'c'*40]), \
             patch.object(self.deployer, 'pull'), patch.object(self.deployer, 'snapshot'), \
             patch.object(self.deployer, 'compose'), patch.object(self.deployer, 'prune'), \
             patch.object(self.deployer, 'remember_failure') as failure, \
             patch.object(self.deployer, 'deploy') as deploy:
            self.deployer.poll()
            deploy.assert_not_called()
            failure.assert_called_once_with(NEW, self.candidate, counted=False)

    def test_rolling_ref_budget_includes_rechecks(self):
        import time
        with patch.object(updater, 'read_json', return_value=[time.time()]*updater.MAX_REF_REQUESTS), \
             patch.object(self.deployer.remote, 'production_revision') as request:
            with self.assertRaises(updater.Deferred):
                self.deployer.observe_revision()
            request.assert_not_called()

    def test_full_idle_poll_hour_leaves_budget_for_candidate_and_recheck(self):
        import time
        calls = [time.time()]*12
        def save(path, value):
            calls[:] = value
        with patch.object(updater, 'read_json', side_effect=lambda path, default=None: list(calls)), \
             patch.object(updater, 'atomic_json', side_effect=save), \
             patch.object(self.deployer.remote, 'production_revision', return_value=NEW) as request:
            self.assertEqual(self.deployer.observe_revision(), NEW)
            self.assertEqual(self.deployer.observe_revision(), NEW)
            self.assertEqual(len(calls), 14)
            self.assertEqual(request.call_count, 2)

    def test_signature_preflight_failure_stays_pending_without_rollout_attempt(self):
        import time
        self.deployer.observe_revision = lambda: NEW
        def state(path, default=None):
            if path.name == 'current.json': return self.previous
            if path.name == 'seen.json': return {'revision': NEW, 'first_seen': time.time()-1800}
            return default
        with patch.object(updater, 'read_json', side_effect=state), \
             patch.object(updater, 'verify_candidate', side_effect=updater.DeployError('signature-verification-failure')), \
             patch.object(self.deployer, 'remember_failure') as failure:
            self.deployer.poll()
            failure.assert_not_called()
        self.assertFalse(any(name == 'current.json' for name, value in self.writes))

    def test_interrupted_promotion_recovery_restores_previous_pair(self):
        def state(path, default=None):
            if path.name == 'pending.json': return {'previous': self.previous, 'candidate': self.candidate}
            if path.name == 'current.json': return self.previous
            return default
        with patch.object(updater, 'read_json', side_effect=state), \
             patch.object(self.deployer, 'replace_pair') as replace:
            self.deployer.recover()
            replace.assert_called_once_with(self.previous)
        self.assertIn(('current.json', self.previous), self.writes)


if __name__ == '__main__':
    unittest.main()
