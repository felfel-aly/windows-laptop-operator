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

    def test_invalid_manifest_is_not_silently_normalized(self):
        with self.assertRaises(ValueError):
            Processes(self.project, [])
        with self.assertRaises(ValueError):
            Processes(self.project, {'blank': []})


if __name__ == '__main__':
    unittest.main()
