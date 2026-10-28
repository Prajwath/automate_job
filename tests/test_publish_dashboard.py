import contextlib
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import publish_dashboard as publisher


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.tracker=self.root/'job_applications.csv'
        self.snapshot=self.root/'vercel_site/job_applications.csv'
        self.snapshot.parent.mkdir()
        self.tracker.write_text('Application_ID,Status\n1,Applied\n')
        self.patches=patch.multiple(publisher,ROOT=self.root,TRACKER=self.tracker,SNAPSHOT=self.snapshot)
        self.patches.start();self.addCleanup(self.patches.stop)

    def test_publishes_only_tracker_files_and_mirrors_exact_bytes(self):
        def git(*args):
            return subprocess.CompletedProcess(args,0,' M job_applications.csv\n' if args[0]=='status' else '','')
        with patch.object(publisher,'git',side_effect=git) as run, contextlib.redirect_stdout(io.StringIO()):
            publisher.publish()
        self.assertEqual(self.snapshot.read_bytes(),self.tracker.read_bytes())
        self.assertIn(('add','--',*publisher.PATHS),[c.args for c in run.call_args_list])
        self.assertIn(('push','origin','HEAD:main'),[c.args for c in run.call_args_list])
        commit=next(c.args for c in run.call_args_list if c.args[0]=='commit')
        self.assertEqual(commit[-2:],tuple(publisher.PATHS))

    def test_authentication_failure_is_reported_not_claimed_published(self):
        def git(*args):
            return subprocess.CompletedProcess(args,128 if args[0]=='push' else 0,'','Authentication required' if args[0]=='push' else '')
        with patch.object(publisher,'git',side_effect=git), self.assertRaisesRegex(RuntimeError,'Authentication required'):
            publisher.publish()
        self.assertEqual(self.snapshot.read_bytes(),self.tracker.read_bytes())
