"""Isolated security regressions; never interact with the user's Windows session."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import operator_core as core
from operator_runtime import Runtime
from process_manager import Processes


class SecurityHardeningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def test_reserved_or_ambiguous_windows_file_names_refused(self):
        invalid = [
            'CON', 'con.txt', 'PRN.csv', 'AUX', 'NUL.log',
            'COM1', 'LPT9.txt', 'folder/COM3.cfg',
            'COM¹', 'com².log', 'folder/LPT³.cfg', 'LPT².txt',
            'trailing.', 'trailing ', 'odd?name.txt', 'has<angle',
            'tab\tname',
        ]
        for name in invalid:
            with self.subTest(path=name):
                with self.assertRaises(ValueError):
                    core.safe_path(self.project, name)
        self.assertEqual(core.safe_path(self.project, 'ordinary.txt'),
                         self.project.resolve() / 'ordinary.txt')

    def test_pipeline_rejects_untrusted_shell_strings_without_opt_in(self):
        sentinel = self.project / 'shell-was-invoked.txt'
        legacy = 'echo should-not-execute > "' + str(sentinel) + '"'
        args = [sys.executable, str(ROOT / 'scripts' / 'test_pipeline.py'),
                str(self.project), '--commands-json', json.dumps([legacy])]
        result = subprocess.run(args, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(sentinel.exists())

    def test_legacy_shell_execution_requires_explicit_switch(self):
        args = [sys.executable, str(ROOT / 'scripts' / 'test_pipeline.py'),
                str(self.project), '--commands-json', json.dumps(['echo legacy-opt-in']),
                '--allow-shell-strings']
        result = subprocess.run(args, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['passed'])
        self.assertIn('legacy-opt-in', report['results'][0]['output_tail'])

    def test_exact_argv_execution_remains_functional(self):
        argv = [sys.executable, '-c', "print('argv-ok')"]
        args = [sys.executable, str(ROOT / 'scripts' / 'test_pipeline.py'),
                str(self.project), '--commands-json', json.dumps([argv])]
        result = subprocess.run(args, text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['passed'])
        self.assertIn('argv-ok', report['results'][0]['output_tail'])

    def test_invalid_timeouts_fail_before_process_start(self):
        manager = Processes(self.project, {
            'safe': [sys.executable, '-c', "print('safe')"]
        })
        self.addCleanup(manager.close)
        for timeout in ('nan', 'inf', 'not-a-number', 0, -5, None):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    manager.pipeline(['safe'], timeout)
                self.assertEqual(manager.children, {})

    def test_runtime_alias_lookup_cannot_inspect_other_workspace(self):
        bound = self.project / 'bound'
        unrelated = self.project / 'unrelated'
        bound.mkdir()
        unrelated.mkdir()
        with patch.dict(os.environ, {'LOCALAPPDATA': str(self.project / 'private-state')}):
            core.workspace_update('selected', bound)
            core.workspace_update('other', unrelated)
            runtime = Runtime(bound)
            try:
                result = runtime.call('workspace_lookup', {'alias': 'selected'})
                self.assertFalse(result['stale'])
                with self.assertRaises(ValueError):
                    runtime.call('workspace_lookup', {'alias': 'other'})
            finally:
                runtime.processes.close()

    def test_pipeline_does_not_adopt_or_stop_existing_process(self):
        manager = Processes(self.project, {
            'service': [sys.executable, '-c', "import time; time.sleep(30)"]
        })
        self.addCleanup(manager.close)
        token = manager.start('service')['token']
        self.assertTrue(manager.status(token)['alive'])
        with self.assertRaises(ValueError):
            manager.pipeline(['service'], timeout=0.1)
        self.assertTrue(manager.status(token)['alive'])

    def test_context_pack_does_not_expand_selected_subdirectory(self):
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        selected = self.project / 'selected'
        selected.mkdir()
        (self.project / 'package.json').write_text('{"scripts":{"outside":"unused"}}', encoding='utf-8')
        (self.project / 'outside.txt').write_text('scope-marker outside', encoding='utf-8')
        (selected / 'inside.py').write_text('# scope-marker inside', encoding='utf-8')
        runtime = Runtime(selected)
        self.addCleanup(runtime.processes.close)
        result = runtime.call('project_snapshot', {'query': 'scope-marker'})
        self.assertEqual(result['project']['root'], str(selected.resolve()))
        self.assertEqual(result['project']['markers'], [])
        self.assertNotIn('outside.txt', result['project']['top_level'])
        self.assertEqual([m['path'] for m in result['search']['matches']], ['inside.py'])

    def test_workspace_registry_retains_selected_subdirectory(self):
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        selected = self.project / 'selected'
        selected.mkdir()
        (self.project / 'package.json').write_text('{}', encoding='utf-8')
        (selected / 'inside.py').write_text('# selected', encoding='utf-8')
        with patch.dict(os.environ, {'LOCALAPPDATA': str(self.project / 'private-state')}):
            core.workspace_update('selected', selected)
            saved = json.loads(core.registry_path().read_text(encoding='utf-8'))['selected']
            self.assertEqual(saved['root'], str(selected.resolve()))
            result = core.workspace_lookup('selected', expected_root=selected)
            self.assertFalse(result['stale'])
            self.assertEqual(result['project']['root'], str(selected.resolve()))
            self.assertNotIn('package.json', result['project']['fingerprints'])
            (selected / 'requirements.txt').write_text('# selected dependency marker', encoding='utf-8')
            refreshed = core.workspace_lookup('selected', expected_root=selected)
            self.assertTrue(refreshed['stale'])
            self.assertEqual(refreshed['project']['root'], str(selected.resolve()))
            self.assertEqual(set(refreshed['project']['fingerprints']), {'requirements.txt'})

    def test_invalid_manifest_is_not_silently_normalized(self):
        with self.assertRaises(ValueError):
            Processes(self.project, [])
        with self.assertRaises(ValueError):
            Processes(self.project, {'blank': []})


if __name__ == '__main__':
    unittest.main()

