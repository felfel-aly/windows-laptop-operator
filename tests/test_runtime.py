"""Synthetic fixtures only. Never use the user's deployed registry or projects."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import operator_core as core
from operator_runtime import Runtime
from process_manager import Processes

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name)
        self.project=self.base/'project';self.project.mkdir()
        self.env=patch.dict(os.environ,{'LOCALAPPDATA':str(self.base/'local')});self.env.start()
    def tearDown(self):
        self.env.stop();self.temp.cleanup()
    def test_non_git_language_context(self):
        for name in ['Main.java','model.m','run.ps1']: (self.project/name).write_text('')
        data=core.context_pack(self.project)
        self.assertFalse(data['git']['is_git'])
        self.assertEqual(set(data['project']['project_types']),{'java','matlab_or_objective_c','powershell'})
    def test_git_error_is_not_non_git(self):
        (self.project/'.git').write_text('gitdir: missing-directory')
        with self.assertRaises(ValueError): core.workspace_snapshot(self.project)
    def test_git_unborn_and_changes(self):
        subprocess.run(['git','init','-q',str(self.project)],check=True)
        (self.project/'demo.py').write_text('VALUE = 1\n')
        snap=core.repo_snapshot(self.project)
        self.assertEqual(snap['head'],'(initial)')
        self.assertIn('demo.py',snap['untracked'])
        subprocess.run(['git','-C',str(self.project),'add','demo.py'],check=True)
        self.assertIn('demo.py',core.repo_snapshot(self.project)['staged'])
    def test_patch_conflict_preserves_original(self):
        p=self.project/'demo.txt';p.write_bytes(b'old\r\n')
        with self.assertRaises(ValueError):
            core.apply_patchset(self.project,[{'path':'demo.txt','expected_sha256':'wrong','text':'new\n'}])
        self.assertEqual(p.read_bytes(),b'old\r\n')
        result=core.apply_patchset(self.project,[{'path':'demo.txt','expected_sha256':core.digest(p.read_bytes()),'text':'new\n'}])
        self.assertTrue(result['verified']);self.assertEqual(p.read_bytes(),b'new\r\n')
    def test_patch_preflight_prevents_partial_write(self):
        p=self.project/'demo.txt';p.write_text('original')
        with self.assertRaises(ValueError):
            core.apply_patchset(self.project,[{'path':'demo.txt','expected_sha256':core.digest(p.read_bytes()),'text':'changed'},
                                             {'path':'../outside.txt','expected_sha256':'absent','text':'bad'}])
        self.assertEqual(p.read_text(),'original')
    def test_readonly_gate_and_path_refusal(self):
        runtime=Runtime(self.project)
        for op in ['workspace_update','apply_patchset']:
            with self.assertRaises(ValueError):runtime.call(op,{})
        for name in ['../outside.txt','.env','.git/config','file.txt:stream']:
            with self.assertRaises(ValueError): core.safe_path(self.project,name)
        runtime.processes.close()
    def test_registry_refresh_and_non_authority(self):
        (self.project/'Main.java').write_text('')
        core.workspace_update('demo',self.project)
        result=core.workspace_lookup('demo')
        self.assertFalse(result['cache_authority']);self.assertFalse(result['stale'])
        (self.project/'pom.xml').write_text('<project/>')
        self.assertTrue(core.workspace_lookup('demo')['stale'])
        self.assertTrue(core.registry_path().is_relative_to(self.base))
    def test_process_manifest_and_pipeline(self):
        manager=Processes(self.project,{'ok':[sys.executable,'-c',"print('operator-process-ok')"],
                                       'fail':[sys.executable,'-c','raise SystemExit(7)']})
        try:
            with self.assertRaises(ValueError):manager.start('unapproved')
            with self.assertRaises(ValueError):manager.stop('unowned')
            passed=manager.pipeline(['ok'])
            self.assertTrue(passed['passed']);self.assertIn('operator-process-ok',passed['results'][0]['output_tail'])
            failed=manager.pipeline(['fail','ok'])
            self.assertFalse(failed['passed']);self.assertEqual(len(failed['results']),1)
        finally:manager.close()
    def test_jsonl_lifecycle(self):
        requests=[{'id':1,'op':'hello'},{'id':2,'op':'project_snapshot'},
                  {'id':3,'op':'workspace_update','args':{'alias':'no-write'}},
                  {'id':4,'op':'health'},{'id':5,'op':'shutdown'}]
        cp=subprocess.run([sys.executable,'-u',str(ROOT/'scripts/operator_runtime.py'),'--root',str(self.project)],
                          input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True,timeout=20)
        self.assertEqual(cp.returncode,0)
        responses=[json.loads(line) for line in cp.stdout.splitlines()]
        self.assertEqual([r['id'] for r in responses],[1,2,3,4,5])
        self.assertFalse(responses[0]['result']['writes']);self.assertFalse(responses[2]['ok'])
        self.assertTrue(responses[3]['ok']);self.assertTrue(responses[4]['result']['shutdown'])
        self.assertFalse(core.registry_path().exists())
    def test_redaction(self):
        value='api_'+'key = "'+('synthetic' * 4)+'"'
        self.assertNotEqual(core.redact(value),value)
        scheme='https://'
        example=scheme+'user:pass'+'@example.com'
        self.assertNotIn('user:pass',core.redact(example))

if __name__=='__main__':unittest.main()
