"""Three-service migration tests: all Docker, network and privileged effects mocked."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from test_pull_release import updater, release, signature, OLD, NEW


SETTINGS = {'APP_DOMAIN': 'example.com', 'API_DOMAIN': 'api.example.com',
            'ACME_EMAIL': 'operator@example.com'}


class TasksContractTests(unittest.TestCase):
    def test_historical_pair_generation_is_unchanged(self):
        old = release(OLD, tasks=False)
        self.assertEqual(old['generation'], OLD+'-'+'1'*12+'-'+'2'*12)
        self.assertEqual(updater.release_roles(old), ('api', 'web'))
        self.assertIs(updater.validate_release(old), old)
        new = release(OLD)
        self.assertNotEqual(old['generation'], new['generation'])

    def test_tasks_cannot_reuse_web_or_api_digest(self):
        for role in updater.PAIR_ROLES:
            candidate = release(NEW)
            candidate['tasks_image'] = updater.REGISTRIES['tasks']+'@'+candidate[role+'_image'].split('@')[1]
            with self.subTest(role=role), self.assertRaisesRegex(updater.DeployError, 'distinct-digest'):
                updater.validate_release(candidate)

    def test_tasks_requires_signed_service_marker_and_all_three_cohorts(self):
        image = release(NEW)['tasks_image']
        for marker in (None, 'web', 'jobrun-tasks'):
            with self.subTest(marker=marker), self.assertRaises(updater.DeployError):
                updater.signature_cohorts([signature(image, NEW, '12/1', marker)], image, NEW, 'tasks')
        self.assertEqual(updater.signature_cohorts([signature(image, NEW, '12/1', 'tasks')],
                                                  image, NEW, 'tasks'), {'12/1'})
        class Remote:
            def resolve(self, role, revision): return release(revision)[role+'_image']
        class Runner:
            count = 0
            def command(self, arguments, label, timeout):
                self.count += 1
                return json.dumps([signature(arguments[-1], NEW,
                    '99/1' if self.count == 3 else '12/1', 'tasks' if self.count == 3 else None)]).encode()
        with self.assertRaisesRegex(updater.DeployError, 'different-release-cohorts'):
            updater.verify_candidate(Remote(), Runner(), NEW)

    def test_tasks_resolves_prefixed_tag_from_existing_web_package(self):
        config = json.dumps({'os': 'linux', 'architecture': 'amd64'}).encode()
        config_digest = 'sha256:'+hashlib.sha256(config).hexdigest()
        manifest = json.dumps({'config': {'digest': config_digest}}).encode()
        remote = updater.Remote()
        with patch.object(remote, 'get', side_effect=[b'{"token":"temporary"}', manifest, config]) as get:
            image = remote.resolve('tasks', NEW)
        self.assertEqual(image, updater.REGISTRIES['web']+'@sha256:'+hashlib.sha256(manifest).hexdigest())
        self.assertIn('repository%3Abigshak4%2Fjobrun-web%3Apull', get.call_args_list[0].args[0])
        self.assertEqual(get.call_args_list[1].args[0],
                         'https://ghcr.io/v2/bigshak4/jobrun-web/manifests/tasks-'+NEW)

    def test_tasks_health_rejects_a_web_response_at_the_correct_revision(self):
        remote = updater.Remote()
        with patch.object(remote, 'get', return_value=json.dumps(
                {'status': 'ok', 'revision': NEW, 'service': 'jobrun-web'}).encode()):
            with self.assertRaisesRegex(updater.DeployError, 'service-mismatch'):
                remote.health('https://tasks.example.com', '/api/health', 'revision', NEW, service='jobrun-tasks')

    def test_tasks_hostname_cannot_overlap_the_api(self):
        with self.assertRaises(updater.DeployError):
            updater.tasks_hostname({**SETTINGS, 'API_DOMAIN': 'tasks.example.com'})


class SnapshotMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)/'controller'
        self.shared = Path(self.temporary.name)/'shared'
        self.root.mkdir()
        self.shared.mkdir()
        (self.root/'releases').mkdir()
        template_root = Path(__file__).parent
        for name in ('compose.yaml', 'Caddyfile'):
            (self.root/name).write_bytes((template_root/name).read_bytes())
        (self.shared/'public-selfhost.env').write_text(''.join(key+'='+value+'\n' for key, value in SETTINGS.items()))
        (self.shared/'backend.env').write_text('FAKE_PRIVATE_SETTING=only-a-test\n')
        self.deployer = updater.Deployer(root=self.root, shared=self.shared)
        self.permissions = patch.object(updater, 'secure_path')
        self.permissions.start()
        self.chmod = patch.object(updater.os, 'fchmod', create=True)
        self.chmod.start()

    def tearDown(self):
        self.chmod.stop()
        self.permissions.stop()
        self.temporary.cleanup()

    def test_pair_snapshot_keeps_no_tasks_container_route_or_environment(self):
        old = release(OLD, tasks=False)
        self.deployer.snapshot(old)
        directory = self.deployer.release_path(old)
        self.assertNotIn('  tasks:', (directory/'compose.yaml').read_text())
        self.assertNotIn('TASKS_', (directory/'compose.yaml').read_text())
        self.assertNotIn('tasks:3000', (directory/'Caddyfile').read_text())
        self.assertNotIn('TASKS_', (directory/'.env').read_text())
        self.assertEqual((directory/'backend.env').read_bytes(), (self.shared/'backend.env').read_bytes())

    def test_triplet_snapshot_pins_tasks_digest_and_domain_and_reuses_it(self):
        candidate = release(NEW)
        self.deployer.snapshot(candidate)
        directory = self.deployer.release_path(candidate)
        self.assertIn('TASKS_IMAGE='+candidate['tasks_image']+'\n', (directory/'.env').read_text())
        self.assertIn('TASKS_DOMAIN=tasks.example.com\n', (directory/'.env').read_text())
        self.assertIn('  tasks:', (directory/'compose.yaml').read_text())
        self.assertIn('reverse_proxy tasks:3000', (directory/'Caddyfile').read_text())
        # Later root-template changes must not rewrite a running/rollback snapshot.
        (self.root/'Caddyfile').write_text('not-installed-now')
        self.deployer.snapshot(candidate)
        self.assertIn('reverse_proxy tasks:3000', (directory/'Caddyfile').read_text())

    def test_historical_snapshot_is_not_rewritten_when_new_templates_install(self):
        old = release(OLD, tasks=False)
        self.deployer.snapshot(old)
        directory = self.deployer.release_path(old)
        before = {path.name: path.read_bytes() for path in directory.iterdir()}
        (self.root/'Caddyfile').write_text('changed-template')
        self.deployer.snapshot(old)
        self.assertEqual(before, {path.name: path.read_bytes() for path in directory.iterdir()})

    def test_partial_template_install_fails_before_snapshot_or_service_mutation(self):
        (self.root/'Caddyfile').write_text('old pair template')
        candidate = release(NEW)
        with self.assertRaisesRegex(updater.DeployError, 'template-not-installed'):
            self.deployer.snapshot(candidate)
        self.assertFalse(self.deployer.release_path(candidate).exists())

    def test_reused_tasks_snapshot_must_still_match_its_full_digest(self):
        candidate = release(NEW)
        self.deployer.snapshot(candidate)
        path = self.deployer.release_path(candidate)/'.env'
        path.write_text(path.read_text().replace(candidate['tasks_image'], candidate['web_image']))
        with self.assertRaisesRegex(updater.DeployError, 'tasks-identity-mismatch'):
            self.deployer.snapshot(candidate)


class MigrationRolloutTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.deployer = updater.Deployer(root=Path(self.temporary.name))
        self.deployer.state.mkdir()
        self.previous, self.candidate = release(OLD, tasks=False), release(NEW)
        self.writes = []
        self.atomic = patch.object(updater, 'atomic_json', side_effect=lambda path, value: self.writes.append((path.name, value)))
        self.atomic.start()

    def tearDown(self):
        self.atomic.stop()
        self.temporary.cleanup()

    def test_same_sha_historical_pair_never_enables_tasks_surprisingly(self):
        with patch.object(updater, 'read_json', side_effect=lambda path, default=None:
                          self.previous if path.name == 'current.json' else default), \
             patch.object(self.deployer, 'observe_revision', return_value=OLD), \
             patch.object(updater, 'verify_candidate') as verify, \
             patch.object(self.deployer, 'compose') as compose:
            self.deployer.poll()
        verify.assert_not_called()
        compose.assert_not_called()

    def test_missing_tasks_publication_leaves_pair_running_without_attempt(self):
        def resolve(role, revision):
            if role == 'tasks': raise updater.NotPublished('tasks-not-ready')
            return self.candidate[role+'_image']
        runner = Mock()
        runner.command.side_effect = lambda arguments, *args, **kwargs: json.dumps(
            [signature(arguments[-1], NEW, '12/1')]).encode()
        with patch.object(updater, 'read_json', side_effect=lambda path, default=None:
                          self.previous if path.name == 'current.json' else default), \
             patch.object(self.deployer, 'observe_revision', return_value=NEW), \
             patch.object(self.deployer.remote, 'resolve', side_effect=resolve), \
             patch.object(self.deployer, 'runner', runner), \
             patch.object(self.deployer, 'compose') as compose, \
             patch.object(self.deployer, 'remember_failure') as failure:
            self.deployer.poll()
        compose.assert_not_called()
        failure.assert_not_called()

    def test_tasks_gate_failure_restores_pair_and_removes_tasks_before_reopening(self):
        events = []
        self.deployer.compose = lambda current, *args: events.append((current, args))
        self.deployer.internal_health = Mock()
        def health(current):
            if current == self.candidate: raise updater.DeployError('tasks-gate-failure')
        self.deployer.public_health = health
        with self.assertRaisesRegex(updater.DeployError, 'previous-restored'):
            self.deployer.deploy(self.previous, self.candidate)
        rollback = [args for current, args in events if current == self.previous]
        self.assertEqual(rollback[0], ('stop', 'caddy'))
        self.assertIn('--remove-orphans', rollback[2])
        self.assertEqual(rollback[2][-2:], ('api', 'web'))
        self.assertEqual(rollback[-1][-1], 'caddy')
        self.assertIn(('current.json', self.previous), self.writes)

    def test_future_triplet_restart_preserves_and_health_checks_tasks(self):
        calls = []
        self.deployer.compose = lambda current, *args: calls.append(args)
        self.deployer.public_health = Mock()
        self.deployer.replace_pair(self.candidate)
        self.assertIn(('stop', 'api', 'web', 'tasks'), calls)
        self.assertEqual(calls[2][-3:], ('api', 'web', 'tasks'))
        probes = [args for args in calls if args[:3] == ('exec', '-T', 'tasks')]
        self.assertEqual(len(probes), 1)
        self.assertEqual(probes[0][-2:], (NEW, 'jobrun-tasks'))

    def test_triplet_public_gate_includes_tasks_but_historical_pair_does_not(self):
        with patch.object(updater, 'public_settings', return_value=SETTINGS), \
             patch.object(self.deployer.remote, 'health') as health:
            self.deployer.public_health(self.previous)
            self.assertEqual(health.call_count, 2)
            health.reset_mock()
            self.deployer.public_health(self.candidate)
            self.assertEqual(health.call_count, 3)
            self.assertEqual(health.call_args.args, ('https://tasks.example.com', '/api/health', 'revision', NEW))
            self.assertEqual(health.call_args.kwargs, {'service': 'jobrun-tasks'})

    def test_mixed_pair_triplet_retention_keeps_current_tasks_digest(self):
        history = [self.candidate, release('c'*40), release('d'*40, tasks=False), self.previous]
        def state(path, default=None):
            if path.name == 'history.json': return history
            if path.name == 'current.json': return self.candidate
            return default
        with patch.object(updater, 'read_json', side_effect=state), \
             patch.object(self.deployer.runner, 'command') as command:
            self.deployer.prune()
        command.assert_not_called()
        self.assertIn(('history.json', history[:3]), self.writes)


if __name__ == '__main__':
    unittest.main()
