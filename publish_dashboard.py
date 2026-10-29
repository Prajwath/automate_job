#!/usr/bin/env python3
"""Publish a minimized dashboard view from a separate, disposable checkout."""
import argparse
import csv
import fcntl
import hashlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
TRACKER = ROOT / 'job_applications.csv'
CACHE = ROOT / '.dashboard-sync/repo'
REMOTE = 'git@github.com:Prajwath/automate_job.git'
PATHS = ['job_applications.csv', 'vercel_site/job_applications.csv']
MARKER = 'dashboard-publication-cache'
COLUMNS = ['Application_ID','Company','Job_Title','Location','Target_CTC','Job_URL',
           'Date_Applied','Channel','Sender_Email','Status','Reverted_Back',
           'Response_Date','Notes','Batch_ID','Resume_File','JD_File',
           'Advertised_CTC','Perks','Tailored_Keywords']
PUBLIC = {'Application_ID','Company','Job_Title','Location','Job_URL',
          'Date_Applied','Channel','Status','Reverted_Back','Response_Date',
          'Advertised_CTC','Perks'}


def application_completed(row):
    status = (row.get('Status') or '').strip().lower()
    if not status or status in {'to apply', 'needs you', 'skipped', 'submission uncertain'}:
        return False
    return (status == 'applied' or 'reject' in status
            or any(word in status for word in ('interview', 'assessment', 'shortlist', 'offer', 'positive'))
            or (row.get('Reverted_Back') or '').strip().lower() == 'yes')


def public_snapshot(content):
    source=csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    if not source.fieldnames or not {'Application_ID','Company','Job_Title','Status'} <= set(source.fieldnames):
        raise ValueError('Tracker is missing required dashboard columns')
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=COLUMNS,lineterminator='\n');writer.writeheader()
    for row in source:
        if not application_completed(row):
            continue
        item={key:row.get(key,'') if key in PUBLIC else '' for key in COLUMNS}
        prefix=next((label for label in ['Strong fit','Stretch','Weak fit','Good fit'] if row.get('Notes','').lower().startswith(label.lower())),'Good fit')
        status=row.get('Status','').strip().lower()
        note={'applied':'Application submitted.','needs you':'Requires your input.',
              'to apply':'Queued.','skipped':'Skipped.',
              'submission uncertain':'Submission awaiting confirmation.'}.get(status,'Employer response recorded.' if status else 'Queued.')
        item['Notes']=prefix+': '+note;writer.writerow(item)
    return out.getvalue().encode('utf-8')


def git(repo,*args,check=True):
    result=subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,timeout=90)
    if check and result.returncode:raise RuntimeError((result.stderr or result.stdout).strip()[:600])
    return result


def initialize(repo,remote):
    if not (repo/'.git').is_dir():
        if repo.exists() and any(repo.iterdir()):raise RuntimeError('Publication checkout must be empty')
        repo.parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(['git','clone','--single-branch','--branch','main',remote,str(repo)],capture_output=True,text=True,timeout=90)
        if result.returncode:raise RuntimeError(result.stderr.strip()[:600])
        (repo/'.git'/MARKER).write_text('Generated public dashboard checkout.\n')
    if not (repo/'.git'/MARKER).exists():raise RuntimeError('Refusing a checkout not created for dashboard publication')
    git(repo,'config','user.name','Dashboard Sync')
    git(repo,'config','user.email','dashboard-sync@users.noreply.github.com')


def check_pending_history(repo):
    pending=git(repo,'rev-list','origin/main..HEAD').stdout.splitlines()
    for sha in pending:
        paths=git(repo,'diff-tree','--no-commit-id','--name-only','-r',sha).stdout.splitlines()
        if not paths or not set(paths)<=set(PATHS):raise RuntimeError('Refusing to push unrelated local history')
        for path in paths:
            blob=git(repo,'show',sha+':'+path).stdout.encode()
            if public_snapshot(blob)!=blob:raise RuntimeError('Refusing private fields in pending tracker history')
    return pending


def atomic_write(path,content):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(dir=path.parent,prefix='.tracker-',suffix='.tmp')
    try:
        with os.fdopen(fd,'wb') as f:f.write(content)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def publish(source=None,repo=None,remote=REMOTE):
    source=Path(source or TRACKER).resolve();repo=Path(repo or CACHE).resolve()
    if repo==source.parent or repo==ROOT.resolve():raise RuntimeError('Publication checkout must be separate from the private workspace')
    content=public_snapshot(source.read_bytes())
    with open(source.parent/'.dashboard-publish.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        initialize(repo,remote);git(repo,'fetch','origin','main')
        pending=check_pending_history(repo)
        dirty=git(repo,'diff','--name-only').stdout.splitlines()+git(repo,'diff','--cached','--name-only').stdout.splitlines()
        if not set(dirty)<=set(PATHS):raise RuntimeError('Publication checkout contains unrelated edits')
        # Only this marked generated cache can discard its own snapshot edits.
        # The canonical private workspace is never reset, pulled, or rebased.
        if pending or dirty:git(repo,'reset','--hard','origin/main')
        else:git(repo,'merge','--ff-only','origin/main')
        for path in PATHS:atomic_write(repo/path,content)
        if not git(repo,'status','--porcelain','--',*PATHS).stdout.strip():return hashlib.sha256(content).hexdigest()
        git(repo,'add','--',*PATHS)
        if not set(git(repo,'diff','--cached','--name-only').stdout.splitlines())<=set(PATHS):raise RuntimeError('Unexpected publication files')
        git(repo,'-c','commit.gpgsign=false','commit','-m','Sync public dashboard statuses','--',*PATHS)
        git(repo,'push','origin','HEAD:main');print('Dashboard snapshot published.',flush=True)
    return hashlib.sha256(content).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch',action='store_true');parser.add_argument('--source',type=Path,default=TRACKER)
    parser.add_argument('--repo',type=Path,default=CACHE);parser.add_argument('--remote',default=REMOTE)
    parser.add_argument('--interval',type=int,default=10);args=parser.parse_args();previous=None
    while True:
        try:
            current=hashlib.sha256(public_snapshot(args.source.read_bytes())).hexdigest()
            if current!=previous:previous=publish(args.source,args.repo,args.remote)
        except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as exc:
            print('Dashboard sync failed: '+str(exc),flush=True)
            if not args.watch:return 1
        if not args.watch:return 0
        time.sleep(max(5,args.interval))


if __name__=='__main__':raise SystemExit(main())
