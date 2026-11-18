import unittest;
import tempfile;
from pathlib import Path;
import sys;
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));
from operator_runtime import Runtime;

class ReadOnlyContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();
        self.addCleanup(self.temp.cleanup);
        self.runtime = Runtime(Path(self.temp.name), allow_writes=False);
        self.addCleanup(self.runtime.processes.close);
    
    def test_hello_writes_disabled(self):
        response = self.runtime.call('hello', {});
        self.assertFalse(response['writes']);
    
    def test_unknown_operation_refused(self):
        with self.assertRaises(ValueError):
            self.runtime.call('unknown', {});
    
    def test_invalid_args_refused(self):
        with self.assertRaises(ValueError):
            self.runtime.call('hello', 123);