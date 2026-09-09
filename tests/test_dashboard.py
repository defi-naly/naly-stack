import http.client
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('naly_dashboard', str(ROOT / 'launcher/naly-ui'))
spec = importlib.util.spec_from_loader(loader.name, loader)
ui = importlib.util.module_from_spec(spec)
loader.exec_module(ui)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / '.squad'
        self.env = {**os.environ, 'SQUAD_DIR': str(self.path), 'SQUAD_NAME': 'builder',
                    'PATH': f'{ROOT / "bin"}:{ROOT / "launcher"}:' + os.environ['PATH']}
        self.cli('init')
        (self.path / 'sessions').write_text(f'builder\t{self.temp.name}\tBuild\tcodex\tmodel-example\tdefault\nreviewer\t{self.temp.name}\tReview\tclaude\t\treview\n')
        self.patch = patch.dict(os.environ, {'SQUAD_SESSIONS': str(self.path / 'sessions')})
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.board = ui.Board(self.path)
        self.server = ui.make_server(self.board, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def cli(self, *args):
        return subprocess.run([str(ROOT / 'bin/naly'), *args], env=self.env, text=True,
                              capture_output=True, check=True).stdout

    def request(self, method='GET', path='/api/state', data=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        body = json.dumps(data) if data is not None else None
        defaults = {'Origin': f'http://127.0.0.1:{self.server.server_port}',
                    'Content-Type': 'application/json', 'X-Naly-Token': self.board.token}
        defaults.update(headers or {})
        connection.request(method, path, body, defaults)
        result = connection.getresponse()
        raw = result.read()
        payload = json.loads(raw) if result.getheader('Content-Type') == 'application/json' else raw
        connection.close()
        return result.status, payload

    def action(self, **data):
        return self.request('POST', '/api/action', data)

    def task(self):
        return self.request()[1]['tasks'][0]

    def test_cli_updates_and_configuration_are_visible(self):
        self.cli('add', '<script>alert(1)</script>')
        self.cli('claim', 't1')
        status, state = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(state['tasks'][0]['status'], 'doing')
        self.assertEqual(state['tasks'][0]['title'], '<script>alert(1)</script>')
        self.assertEqual(state['agents'][0]['model'], 'model-example')
        self.assertEqual(state['agents'][0]['tasks'], ['t1'])
        self.assertTrue(state['agents'][0]['last_event'])
        self.assertEqual(state['events'][0]['verb'], 'claim')

    def test_create_routes_and_emits_inbox_event(self):
        status, _ = self.action(action='create', title='Build form', role='default', notes='Keyboard accessible')
        self.assertEqual(status, 200)
        self.assertEqual(self.task()['assigned'], 'builder')
        self.assertIn('Build form', self.cli('inbox'))
        self.assertEqual(self.task()['notes'], 'Keyboard accessible')

    def test_review_actions_preserve_learning(self):
        self.cli('add', 'Build form')
        self.cli('claim', 't1')
        self.cli('handoff', 't1', '--to', 'reviewer', '--review')
        status, _ = self.action(action='fail', id='t1', version=self.task()['version'], reason='Missing keyboard support')
        self.assertEqual(status, 200)
        self.assertEqual(self.task()['status'], 'doing')
        self.cli('handoff', 't1', '--to', 'reviewer', '--review')
        status, _ = self.action(action='pass', id='t1', version=self.task()['version'])
        self.assertEqual(status, 200)
        self.assertEqual(self.task()['status'], 'done')
        self.assertFalse((self.path / 'locks/t1').exists())
        self.assertTrue(list((self.path / 'learning/events').glob('*.json')))

    def test_stale_edits_and_active_handoffs_rejected(self):
        self.cli('add', 'Build form')
        version = self.task()['version']
        self.cli('claim', 't1')
        self.assertEqual(self.action(action='handoff', id='t1', version=version, target='reviewer')[0], 400)
        self.assertEqual(self.action(action='handoff', id='t1', version=self.task()['version'], target='reviewer')[0], 400)
        self.assertEqual(self.task()['owner'], 'builder')

    def test_handoff_notifies_target(self):
        self.cli('add', 'Investigate')
        status, _ = self.action(action='handoff', id='t1', version=self.task()['version'], target='reviewer', notes='Please investigate')
        self.assertEqual(status, 200)
        self.assertEqual(self.task()['assigned'], 'reviewer')
        self.assertEqual(self.request()[1]['events'][0]['target'], 'reviewer')

    def test_origin_token_host_and_path_guards(self):
        for headers in ({'Origin':'https://example.com'}, {'X-Naly-Token':'wrong'}, {'Host':'example.com'}):
            self.assertEqual(self.request('POST','/api/action',{'action':'create','title':'Bad'},headers)[0],403)
        self.assertEqual(self.request(headers={'Host':'example.com'})[0],403)
        self.assertEqual(self.request(path='/../../etc/passwd')[0],404)
        self.assertEqual(self.action(action='pass',id='../../config',version='x')[0],400)
        self.assertEqual(self.action(action='create',title='bad\nstatus=done')[0],400)
        self.assertEqual(self.request('POST','/api/action',[])[0],400)
        self.assertEqual(self.request()[1]['tasks'],[])

    def test_runtime_status_is_separate_from_task_status(self):
        import datetime
        self.cli('add', 'Still needs review')
        folder = self.path / 'runtime/builder'
        folder.mkdir(parents=True)
        record = dict(name='builder', started='2026-01-01T00:00:00+00:00',
                      heartbeat='2026-01-01T00:00:00+00:00', state='running')
        path = folder / 'run.json'
        path.write_text(json.dumps(record))
        state = self.request()[1]
        self.assertEqual(state['agents'][0]['runtime']['state'], 'unknown')
        record['heartbeat'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        path.write_text(json.dumps(record))
        self.assertEqual(self.request()[1]['agents'][0]['runtime']['state'], 'running')
        record.update(state='exited', exit_code=0)
        path.write_text(json.dumps(record))
        state = self.request()[1]
        self.assertEqual(state['agents'][0]['runtime']['state'], 'exited')
        self.assertEqual(state['tasks'][0]['status'], 'backlog')

    def test_assets_and_empty_board(self):
        for path in ('/','/app.js','/style.css'):
            self.assertEqual(self.request(path=path)[0],200)
        self.assertEqual(self.request()[1]['tasks'],[])
        (self.path / 'sessions').write_text('invalid session name\n')
        self.assertTrue(self.request()[1]['warnings'])


if __name__ == '__main__':
    unittest.main()
