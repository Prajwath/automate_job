#!/usr/bin/env python3
"""Publish tracker snapshots to the existing GitHub-backed dashboard."""
import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
TRACKER = ROOT / 'job_applications.csv'
SNAPSHOT = ROOT / 'vercel_site/job_applications.csv'
PATHS = ['job_applications.csv', 'vercel_site/job_applications.csv']


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], text=True, capture_output=True, timeout=60)


def publish():
    with open(ROOT / '.dashboard-publish.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        content = TRACKER.read_bytes()
        fd, temporary = tempfile.mkstemp(dir=SNAPSHOT.parent, prefix='.tracker-', suffix='.tmp')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
            os.replace(temporary, SNAPSHOT)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        changed = git('status', '--porcelain', '--', *PATHS)
        if changed.returncode:
            raise RuntimeError(changed.stderr.strip())
        if changed.stdout.strip():
            added = git('add', '--', *PATHS)
            if added.returncode:
                raise RuntimeError(added.stderr.strip())
            committed = git('commit', '-m', 'Update live job application entries', '--', *PATHS)
            if committed.returncode:
                raise RuntimeError(committed.stderr.strip())
        # Push the tracker commits without stashing unrelated in-progress edits.
        pushed = git('push', 'origin', 'HEAD:main')
        if pushed.returncode:
            raise RuntimeError(pushed.stderr.strip()[:500])
        print('Dashboard tracker published.', flush=True)
    return hashlib.sha256(content).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch', action='store_true', help='Publish when tracker content changes')
    args = parser.parse_args()
    previous = None
    while True:
        current = hashlib.sha256(TRACKER.read_bytes()).hexdigest()
        if current != previous:
            try:
                previous = publish()
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                print(f'Dashboard publish failed: {exc}', flush=True)
                if not args.watch:
                    return 1
        if not args.watch:
            return 0
        time.sleep(10)


if __name__ == '__main__':
    raise SystemExit(main())
