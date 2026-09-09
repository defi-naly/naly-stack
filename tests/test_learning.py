import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='squad learning ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.board = self.root / 'board'
        self.env = {**os.environ, 'SQUAD_DIR': str(self.board), 'SQUAD_NAME': 'builder',
                    'SQUAD_AGENT_KIND': 'codex', 'SQUAD_MODEL': 'test-model',
                    'PATH': f'{ROOT}/bin:{ROOT}/launcher:' + os.environ['PATH']}
        self.cli('init')
        self.skill = self.board / 'skills/design/SKILL.md'
        self.skill.parent.mkdir()
        self.original = '---\nname: design\ndescription: Design the interface.\n---\n\n# Design\n'
        self.skill.write_text(self.original)

    def cli(self, *args, ok=True, env=None):
        result = subprocess.run([str(ROOT / 'bin/squad'), *args], cwd=self.root,
                                env=env or self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def task(self):
        task_id = self.cli('add', 'Settings page', '--skills', 'design').stdout.split()[1]
        self.cli('claim', task_id)
        return task_id

    def events(self, task):
        return json.loads(self.cli('outcome', task).stdout)

    def feedback(self, task, lesson='Keep one primary action per screen.', **options):
        args = ['outcome', task, '--decision', 'revised', '--source', options.get('source', 'human'),
                '--reason', options.get('reason', 'Too many competing primary actions.'),
                '--correction', 'action-hierarchy', '--skill', 'design',
                '--kind', options.get('kind', 'preference')]
        if lesson:
            args += ['--lesson', lesson]
        return self.cli(*args)

    def insights(self, *args):
        return json.loads(self.cli('insights', '--json', *args).stdout)

    def seed_pattern(self):
        for _ in range(3):
            self.feedback(self.task())
        return self.insights('--propose')['proposals'][0]

    def test_attempt_freezes_model_and_skill_hash(self):
        task = self.task()
        self.skill.write_text('changed later')
        changed = {**self.env, 'SQUAD_MODEL': 'different-model'}
        self.cli('pass', task, env=changed)
        events = self.events(task)
        attempt, outcome = events
        self.assertEqual(attempt['model'], 'test-model')
        self.assertEqual(attempt['skills'][0]['sha256'], hashlib.sha256(self.original.encode()).hexdigest())
        self.assertEqual(outcome['attempt'], attempt['id'])
        self.assertEqual(outcome['source'], 'workflow')
        self.assertEqual(outcome['decision'], 'accepted')

    def test_check_executes_and_preserves_failure_exit_code(self):
        task = self.task()
        failed = self.cli('check', task, '--', sys.executable, '-c', 'raise SystemExit(7)', ok=False)
        self.assertEqual(failed.returncode, 7)
        self.cli('check', task, '--', sys.executable, '-c', 'print("checked")')
        checks = [e for e in self.events(task) if e['type'] == 'check']
        self.assertEqual([c['exit_code'] for c in checks], [7, 0])
        self.assertEqual(checks[0]['attempt'], checks[1]['attempt'])
        self.assertEqual(checks[0]['cwd'], str(self.root))

    def test_duplicate_feedback_is_not_three_tasks(self):
        task = self.task()
        for _ in range(4):
            self.feedback(task)
        report = self.insights('--propose')
        self.assertEqual(report['patterns'], [])
        self.assertEqual(report['proposals'], [])
        self.assertEqual(report['task_count'], 1)

    def test_preferences_and_defects_do_not_mix(self):
        self.feedback(self.task(), kind='defect')
        self.feedback(self.task(), kind='preference')
        self.feedback(self.task(), source='agent', kind='preference')
        self.assertEqual(self.insights()['patterns'], [])

    def test_rework_keeps_attempts_but_counts_task_once(self):
        task = self.task()
        self.feedback(task)
        self.cli('release', task)
        self.cli('claim', task)
        self.cli('outcome', task, '--decision', 'accepted', '--source', 'human')
        report = self.insights()
        self.assertEqual(report['task_count'], 1)
        self.assertEqual(report['attempt_count'], 2)
        self.assertEqual(report['summaries'][0]['counts'], {'accepted': 1})

    def test_proposal_is_reviewable_and_does_not_auto_apply(self):
        proposal_id = self.seed_pattern()
        self.assertEqual(self.skill.read_text(), self.original)
        proposal = json.loads(self.cli('proposal', 'show', proposal_id).stdout)
        self.assertEqual(len(proposal['evidence']), 3)
        review = (self.board / 'learning/proposals' / (proposal_id + '.md')).read_text()
        self.assertIn('```diff', review)
        self.assertEqual(self.insights('--propose')['proposals'], [proposal_id])
        self.cli('proposal', 'apply', proposal_id)
        self.assertIn(proposal['lesson'], self.skill.read_text())
        self.assertEqual(self.insights('--propose')['proposals'], [])
        self.cli('proposal', 'apply', proposal_id, ok=False)

    def test_crlf_skill_hash_matches_actual_source_bytes(self):
        self.skill.write_bytes(self.original.replace('\n', '\r\n').encode())
        proposal_id = self.seed_pattern()
        self.cli('proposal', 'apply', proposal_id)
        self.assertIn('Keep one primary action', self.skill.read_text())

    def test_stale_proposal_preserves_updated_skill(self):
        proposal_id = self.seed_pattern()
        self.skill.write_text('new instructions')
        self.cli('proposal', 'apply', proposal_id, ok=False)
        self.assertEqual(self.skill.read_text(), 'new instructions')

    def test_no_proposal_without_three_matching_lessons(self):
        for lesson in ('Rule one.', 'Rule two.', 'Rule three.'):
            self.feedback(self.task(), lesson=lesson)
        report = self.insights('--propose')
        self.assertEqual(len(report['patterns']), 1)
        self.assertEqual(report['proposals'], [])

    def test_human_judgment_not_overwritten_by_workflow_completion(self):
        task = self.task()
        self.cli('outcome', task, '--decision', 'rejected', '--source', 'human', '--reason', 'Wrong behavior')
        self.cli('done', task)
        summary = self.insights()['summaries'][0]
        self.assertEqual(summary['source'], 'human')
        self.assertEqual(summary['counts'], {'rejected': 1})

    def test_unknown_models_and_unassessed_completion_are_explicit(self):
        env = {k: v for k, v in self.env.items() if k not in ('SQUAD_AGENT_KIND', 'SQUAD_MODEL')}
        self.cli('add', 'Legacy-style work', env=env)
        self.cli('claim', 't1', env=env)
        self.cli('done', 't1', env=env)
        summary = self.insights()['summaries'][0]
        self.assertEqual(summary['agent'], 'unknown')
        self.assertEqual(summary['model'], 'unknown (CLI default)')
        self.assertEqual(summary['counts'], {'unassessed': 1})

    def test_bad_feedback_and_paths_leave_no_records(self):
        task = self.task()
        before = self.events(task)
        self.cli('outcome', task, '--decision', 'revised', ok=False)
        self.cli('outcome', '../config', ok=False)
        self.cli('outcome', task, '--decision', 'revised', '--reason', 'Wrong',
                 '--correction', 'tag', '--kind', 'defect', '--skill', 'unlisted', ok=False)
        self.assertEqual(self.events(task), before)

    def test_symlinked_skill_updates_source_without_replacing_link(self):
        external = self.root / 'skillbank-design'
        self.skill.parent.rename(external)
        self.skill.parent.symlink_to(external, target_is_directory=True)
        proposal_id = self.seed_pattern()
        self.cli('proposal', 'apply', proposal_id)
        self.assertTrue(self.skill.parent.is_symlink())
        self.assertIn('Keep one primary action', (external / 'SKILL.md').read_text())

    def test_failed_reclaim_snapshot_does_not_attribute_to_previous_attempt(self):
        task = self.task()
        self.cli('release', task)
        self.cli('set', task, 'skills', '../invalid')
        claim = self.cli('claim', task)
        self.assertIn('learning record failed', claim.stderr)
        self.cli('outcome', task, '--decision', 'accepted', ok=False)
        self.cli('pass', task)
        self.assertEqual(len(self.events(task)), 1)
        self.assertEqual(self.insights()['missing_current_attempts'], [task])

    def test_concurrent_feedback_writes_are_preserved(self):
        task = self.task()
        processes = [subprocess.Popen([str(ROOT / 'bin/squad'), 'outcome', task,
                                      '--decision', 'accepted'], cwd=self.root, env=self.env,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for _ in range(8)]
        for process in processes:
            _, error = process.communicate()
            self.assertEqual(process.returncode, 0, error)
        records = self.events(task)
        self.assertEqual(len(records), 9)
        self.assertEqual(len({e['id'] for e in records}), 9)

    def test_targeting_old_attempt_does_not_relabel_current_attempt(self):
        task = self.task()
        original_attempt = self.events(task)[0]['id']
        self.cli('release', task)
        self.cli('claim', task)
        self.cli('outcome', task, '--attempt', original_attempt, '--decision', 'accepted')
        self.assertEqual(self.insights()['summaries'][0]['counts'], {'unassessed': 1})


if __name__ == '__main__':
    unittest.main()
