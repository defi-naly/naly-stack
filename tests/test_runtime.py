import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.env = {**os.environ, 'SQUAD_DIR': str(self.path), 'SQUAD_NAME': 'builder'}

    def records(self):
        return [json.loads(p.read_text()) for p in (self.path/'runtime/builder').glob('*.json')]

    def run_worker(self, source, **kwargs):
        return subprocess.run([str(ROOT/'launcher/naly-run'), '--', sys.executable, '-c', source],
                              env=self.env, capture_output=True, text=True, timeout=10, **kwargs)

    def test_records_real_exit_and_preserves_input_output(self):
        result = self.run_worker('print(input()); raise SystemExit(7)', input='terminal input\n')
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout, 'terminal input\n')
        record = self.records()[0]
        self.assertEqual(record['exit_code'], 7)
        self.assertEqual(record['state'], 'failed')
        self.assertIn('ended', record)

    def test_relaunch_keeps_separate_records(self):
        self.run_worker('pass')
        self.run_worker('raise SystemExit(3)')
        records = self.records()
        self.assertEqual(len(records), 2)
        self.assertEqual({r['exit_code'] for r in records}, {0,3})
        self.assertEqual(len({r['run_id'] for r in records}), 2)

    def test_running_heartbeat_and_signal_exit(self):
        process = subprocess.Popen([str(ROOT/'launcher/naly-run'), '--', sys.executable, '-c',
                                    'import time; time.sleep(30)'], env=self.env)
        try:
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                records=self.records()
                if records and records[0]['state']=='running':break
                time.sleep(.05)
            self.assertEqual(records[0]['state'], 'running')
            self.assertIn('pid', records[0])
            process.terminate()
            self.assertEqual(process.wait(timeout=5), 143)
            self.assertEqual(self.records()[0]['exit_code'], -15)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    def test_missing_command_is_recorded(self):
        result=subprocess.run([str(ROOT/'launcher/naly-run'),'--','/nonexistent-naly-worker'],env=self.env,capture_output=True)
        self.assertEqual(result.returncode,127)
        self.assertEqual(self.records()[0]['state'],'failed')
