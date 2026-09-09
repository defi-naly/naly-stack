import importlib.machinery
import importlib.util
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('launcher', str(ROOT / 'launcher/squad-up'))
spec = importlib.util.spec_from_loader(loader.name, loader)
launcher = importlib.util.module_from_spec(spec)
loader.exec_module(launcher)


class SquadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='squad tests ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.board = self.root / 'shared board'
        self.front = self.root / 'frontend tree'
        self.back = self.root / 'builder tree'
        self.front.mkdir()
        self.back.mkdir()
        self.env = {**os.environ, 'SQUAD_DIR': str(self.board), 'SQUAD_NAME': 'builder',
                    'PATH': f'{ROOT}/bin:{ROOT}/launcher:' + os.environ['PATH']}
        self.cli('init')
        self.config = self.board / 'sessions'
        self.config.write_text(f'frontend\t{self.front}\tDesign UI\tclaude\tchosen-claude\tfrontend\n'
                               f'builder\t{self.back}\t\tcodex\tchosen-codex\tdefault\n')

    def cli(self, *args, name=None, ok=True):
        env = dict(self.env)
        if name:
            env['SQUAD_NAME'] = name
        result = subprocess.run([str(ROOT / 'bin/squad'), *args], env=env,
                                cwd=self.root, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_role_assignment_and_cross_provider_handoff(self):
        self.cli('add', 'Design page', '--role', 'frontend', '--skills', 'design')
        self.assertIn('assigned=frontend', self.cli('show', 't1').stdout)
        self.cli('claim', 't1', ok=False)
        self.assertIn('CLAIMED', self.cli('claim', 't1', name='frontend').stdout)
        self.cli('claim', 't1', name='frontend', ok=False)
        self.cli('handoff', 't1', '--to', 'builder', '--notes', 'src/a | b & c \\ d', name='frontend')
        self.assertIn('src/a | b & c \\ d', self.cli('show', 't1').stdout)
        self.assertIn('CLAIMED', self.cli('claim', 't1').stdout)
        self.cli('add', 'Other work', '--role', 'backend')
        self.assertIn('assigned=builder', self.cli('show', 't2').stdout)

    def test_init_preserves_events(self):
        self.cli('add', 'First task')
        before = (self.board / 'events.log').read_bytes()
        self.cli('init')
        self.assertEqual((self.board / 'events.log').read_bytes(), before)

    def test_bad_route_does_not_create_task(self):
        self.config.write_text(self.config.read_text() + f'other\t{self.back}\t\tcodex\t\tfrontend\n')
        self.cli('add', 'Ambiguous', '--role', 'frontend', ok=False)
        self.assertEqual(list((self.board / 'tasks').iterdir()), [])

    def test_skill_links_are_shared_idempotent_and_preserve_conflicts(self):
        source = self.board / 'skills/design'
        source.mkdir()
        (source / 'SKILL.md').write_text('original')
        self.cli('skills', 'sync')
        for worktree in (self.front, self.back):
            for scope in ('.agents', '.claude'):
                self.assertEqual((worktree / scope / 'skills/design').resolve(), source)
        (source / 'SKILL.md').write_text('changed once')
        self.assertEqual((self.back / '.agents/skills/design/SKILL.md').read_text(), 'changed once')
        self.cli('skills', 'sync')
        conflict = self.front / '.claude/skills/design'
        conflict.unlink()
        conflict.mkdir()
        (conflict / 'SKILL.md').write_text('local')
        self.cli('skills', 'sync', ok=False)
        self.assertEqual((conflict / 'SKILL.md').read_text(), 'local')

    def test_dry_run_quotes_arguments_and_has_no_side_effects(self):
        marker = self.root / 'injected'
        self.config.write_text(f'frontend\t{self.front}\t$(touch {marker}) `echo bad`\tclaude\tmodel x\tfrontend\n')
        result = self.cli('up', '--dry-run')
        line = result.stdout.splitlines()[0]
        words = shlex.split(line.split(' && ', 1)[1])
        self.assertIn(f'SQUAD_DIR={self.board}', words)
        self.assertIn('model x', words)
        self.assertIn('--add-dir', words)
        self.assertIn(f'$(touch {marker})', words[-1])
        self.assertFalse(marker.exists())
        self.assertFalse((self.front / '.claude').exists())

    def test_old_format_and_empty_columns(self):
        self.config.write_text(f'alice\t{self.front}\tLegacy prompt\nbob\t{self.back}\t\tcodex\t\tdefault\n')
        with patch.dict(os.environ, {'SQUAD_AGENT': 'claude --verbose'}):
            members = launcher.sessions(self.config)
        self.assertEqual(members[0]['command'], ['claude', '--verbose'])
        self.assertEqual(members[1]['command'], ['codex'])
        self.assertEqual(members[1]['role'], 'default')

    def test_custom_sessions_file_is_preserved_for_routing(self):
        custom = self.root / 'custom sessions'
        self.config.rename(custom)
        self.env['SQUAD_SESSIONS'] = str(custom)
        self.cli('add', 'Design', '--role', 'frontend')
        self.assertIn('assigned=frontend', self.cli('show', 't1').stdout)
        self.assertIn(str(custom), self.cli('up', '--dry-run').stdout)

    def test_preflight_failure_creates_no_skill_links(self):
        self.config.write_text(self.config.read_text() + f'missing\t{self.root / "absent"}\t\tcodex\t\treview\n')
        self.cli('skills', 'sync', ok=False)
        self.assertFalse((self.front / '.agents').exists())
        self.assertFalse((self.back / '.claude').exists())

    def test_review_handoff_preserves_builder_assignment(self):
        self.cli('add', 'Design', '--role', 'frontend')
        self.cli('claim', 't1', name='frontend')
        self.cli('handoff', 't1', '--to', 'builder', '--review', name='frontend')
        self.assertIn('for review', self.cli('inbox').stdout)
        self.cli('claim', 'rev:t1')
        self.cli('fail', 't1', 'needs changes')
        self.cli('claim', 't1', name='frontend')
        self.cli('handoff', 't1', '--to', 'builder', '--review', name='frontend')
        self.cli('pass', 't1')
        self.assertIn('status=done', self.cli('show', 't1').stdout)

    def test_yolo_defaults_for_both_agents_and_opt_out(self):
        result = self.cli('up', '--dry-run')
        commands = [shlex.split(line.split(' && ', 1)[1])
                    for line in result.stdout.splitlines() if line.startswith('cd ')]
        for words, flag in zip(commands, ('--dangerously-skip-permissions',
                                          '--dangerously-bypass-approvals-and-sandbox')):
            self.assertIn(flag, words)
            self.assertLess(words.index(flag), words.index('--'))
            self.assertIn('SQUAD_YOLO=1', words)
        result = self.cli('up', '--dry-run', '--no-yolo')
        self.assertNotIn('--dangerously-', result.stdout)
        self.assertIn('SQUAD_YOLO=0', result.stdout)

    def test_custom_wrapper_receives_yolo_setting_without_unknown_flags(self):
        self.config.write_text(f'custom\t{self.front}\tDo work\tmy-wrapper --custom\t\tdefault\n')
        result = self.cli('up', '--dry-run')
        words = shlex.split(result.stdout.splitlines()[0].split(' && ', 1)[1])
        self.assertIn('SQUAD_YOLO=1', words)
        self.assertIn('my-wrapper', words)
        self.assertNotIn('--dangerously-skip-permissions', words)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', words)

    def test_launcher_with_stub_tmux(self):
        fakebin = self.root / 'fakebin'
        fakebin.mkdir()
        logfile = self.root / 'tmux.log'
        tmux = fakebin / 'tmux'
        tmux.write_text('''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['TEST_TMUX_LOG'], 'a') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
if sys.argv[1] == 'has-session': sys.exit(1)
if sys.argv[1] in ('new-session', 'split-window'): print('%1')
''')
        tmux.chmod(0o755)
        for agent in ('claude', 'codex'):
            path = fakebin / agent
            path.write_text('#!/bin/sh\nexit 0\n')
            path.chmod(0o755)
        self.env.update(PATH=str(fakebin) + ':' + self.env['PATH'], TEST_TMUX_LOG=str(logfile))
        self.cli('up')
        import json
        calls = [json.loads(line) for line in logfile.read_text().splitlines()]
        commands = [shlex.split(call[-1]) for call in calls if call[0] == 'send-keys' and '-l' in call]
        self.assertEqual(len(commands), 2)
        self.assertIn('--dangerously-skip-permissions', commands[0])
        self.assertIn('--dangerously-bypass-approvals-and-sandbox', commands[1])
        self.assertIn('claude', commands[0])
        self.assertIn('codex', commands[1])
        for command in commands:
            self.assertIn(f'SQUAD_DIR={self.board}', command)
        self.assertEqual(calls[-1][0], 'attach')


if __name__ == '__main__':
    unittest.main()
