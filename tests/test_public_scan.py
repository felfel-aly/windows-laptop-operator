import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from privacy_scan import scan

class PublicScanTests(unittest.TestCase):
    def test_unlisted_private_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'PUBLIC_FILES.json').write_text('["PUBLIC_FILES.json"]')
            (root/'workspace_registry.json').write_text('{}')
            _,findings=scan(root)
            self.assertTrue(any(f[2]=='unlisted file' for f in findings))
    def test_sensitive_text_detected_without_values(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'PUBLIC_FILES.json').write_text(json.dumps(['PUBLIC_FILES.json','example.md']))
            private_path='C:'+chr(92)+'Users'+chr(92)+'synthetic-person'+chr(92)+'file.txt'
            synthetic_token='ghp_'+('A'*36)
            (root/'example.md').write_text(private_path+'\n'+synthetic_token)
            _,findings=scan(root)
            self.assertEqual({f[2] for f in findings},{'personal Windows path','GitHub token'})
            self.assertNotIn(synthetic_token,str(findings))

if __name__=='__main__':unittest.main()
