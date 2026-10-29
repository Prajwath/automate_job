import csv
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

import publish_dashboard as publisher


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'private/job_applications.csv'
        self.source.parent.mkdir()
        self.source.write_text('Application_ID,Company,Job_Title,Status,Sender_Email,Notes,Resume_File,Target_CTC\n1,Example,Engineer,Applied,private@example.com,Phone 1234567890,/private/resume.pdf,12 LPA\n')

    def git(self, repo, *args):
        return publisher.git(repo, *args).stdout.strip()

    def origin(self):
        origin = self.root / 'origin.git'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(origin)], check=True, capture_output=True)
        seed = self.root / 'seed'
        subprocess.run(['git', 'clone', str(origin), str(seed)], check=True, capture_output=True)
        self.git(seed, 'config', 'user.name', 'Test')
        self.git(seed, 'config', 'user.email', 'test@example.com')
        (seed / 'index.html').write_text('Public dashboard')
        self.git(seed, 'add', '.')
        self.git(seed, 'commit', '-m', 'Initial public code')
        self.git(seed, 'push', 'origin', 'main')
        return origin, seed

    def test_snapshot_removes_private_fields_and_notes(self):
        result = publisher.public_snapshot(self.source.read_bytes())
        row = next(csv.DictReader(io.StringIO(result.decode())))
        self.assertEqual(row['Status'], 'Applied')
        for key in ('Sender_Email', 'Resume_File', 'Target_CTC', 'JD_File', 'Tailored_Keywords'):
            self.assertEqual(row[key], '')
        self.assertNotIn(b'1234567890', result)
        self.assertNotIn(b'private@', result)
        self.assertEqual(publisher.public_snapshot(result), result)

    def test_separate_checkout_publishes_and_preserves_remote_code(self):
        origin, seed = self.origin()
        cache = self.root / 'cache'
        before = self.source.read_bytes()
        publisher.publish(self.source, cache, str(origin))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(set(self.git(cache, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()), set(publisher.PATHS))
        self.assertEqual((cache / publisher.PATHS[0]).read_bytes(), publisher.public_snapshot(before))
        self.git(seed, 'pull', '--ff-only')
        (seed / 'index.html').write_text('New public code')
        self.git(seed, 'commit', '-am', 'Update code')
        self.git(seed, 'push', 'origin', 'main')
        self.source.write_bytes(before.replace(b'Applied', b'Needs You'))
        publisher.publish(self.source, cache, str(origin))
        self.assertEqual((cache / 'index.html').read_text(), 'New public code')
        self.assertEqual(list(csv.DictReader(io.StringIO((cache / publisher.PATHS[1]).read_text()))), [])
        head = self.git(cache, 'rev-parse', 'HEAD')
        publisher.publish(self.source, cache, str(origin))
        self.assertEqual(head, self.git(cache, 'rev-parse', 'HEAD'))

    def test_public_snapshot_keeps_only_completed_and_preserves_source(self):
        content = b'Application_ID,Company,Job_Title,Status,Reverted_Back\n1,A,Engineer,Applied,No\n2,B,Engineer,Needs You,Yes\n3,C,Engineer,Submission uncertain,Yes\n4,D,Engineer,To Apply,No\n5,E,Engineer,Skipped,No\n6,F,Engineer,Interview,Yes\n7,G,Engineer,Rejected,Yes\n'
        rows = list(csv.DictReader(io.StringIO(publisher.public_snapshot(content).decode())))
        self.assertEqual([row['Application_ID'] for row in rows], ['1', '6', '7'])

    def test_refuses_private_workspace(self):
        with self.assertRaisesRegex(RuntimeError, 'separate'):
            publisher.publish(self.source, self.source.parent)

    def test_refuses_unrelated_pending_history(self):
        origin, _ = self.origin()
        cache = self.root / 'cache'
        publisher.publish(self.source, cache, str(origin))
        (cache / 'secret.txt').write_text('private')
        self.git(cache, 'add', 'secret.txt')
        self.git(cache, 'commit', '-m', 'Private change')
        with self.assertRaisesRegex(RuntimeError, 'unrelated local history'):
            publisher.publish(self.source, cache, str(origin))
        self.assertEqual(self.git(origin, 'log', '-1', '--format=%s'), 'Sync public dashboard statuses')

    def test_refuses_private_csv_pending_history(self):
        origin, _ = self.origin()
        cache = self.root / 'cache'
        publisher.publish(self.source, cache, str(origin))
        (cache / publisher.PATHS[0]).write_bytes(self.source.read_bytes())
        self.git(cache, 'commit', '-am', 'Unsafe snapshot')
        with self.assertRaisesRegex(RuntimeError, 'private fields'):
            publisher.publish(self.source, cache, str(origin))
