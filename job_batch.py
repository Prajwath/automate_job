#!/usr/bin/env python3
"""Prepare, tailor, and submit a private, auditable application batch."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import time
import os
import shutil
import tempfile
import fcntl
from urllib.parse import urlencode

import linkedin_apply as bot
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parent
BATCH=ROOT/'.tailored-applications'/os.environ.get('JOB_APPLICATION_BATCH',datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y%m%d-role-tailored'))
BATCH.mkdir(parents=True,exist_ok=True)


def save(name,data):
    path=BATCH/name
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)


def read(name,default=None):
    path=BATCH/name
    return json.loads(path.read_text()) if path.exists() else default


def jd_text(page):
    body=page.locator('body').inner_text()
    if 'About the job' not in body:
        raise ValueError('Full job description unavailable')
    text=body.split('About the job',1)[1]
    for marker in ('Set alert for similar jobs','About the company','More jobs','Unlock hiring insights'):
        text=text.split(marker,1)[0]
    return text.strip()


def offering(jd,header,workplace):
    lines=[re.sub(r'\s+',' ',line).strip() for line in jd.splitlines() if line.strip()]
    pay=[]
    for line in lines:
        if re.search(r'\b(?:salary|compensation|ctc|pay|package|remuneration|LPA)\b',line,re.I) and re.search(r'\d',line):
            if len(line)<350 and (re.search(r'₹|\bINR\b|\bLPA\b|lakhs?|\$',line,re.I) or re.search(r'(?:salary|ctc|compensation)\s*[:=-]\s*\d',line,re.I)):pay.append(line)
    # A platform pay chip is a listing detail, not a negotiated offer.
    if not pay:
        pay=[line.strip() for line in header.splitlines() if re.search(r'\d.*(?:INR/yr|INR/month|LPA|₹|\$)',line,re.I)][:1]
    perks=[]
    patterns=[('Remote work',r'fully remote|100% remote|work from home|remote[- ]first'),
              ('Flexible working hours',r'flexible (?:working )?hours|flexible schedule'),
              ('Flexible work model',r'flexible work model'),
              ('Health insurance',r'health insurance|medical insurance|healthcare coverage'),
              ('Health care (listed)',r'health care'),
              ('Learning/development support',r'learning (?:budget|allowance)|professional development|training (?:budget|allowance)|budget.{0,50}for training'),
              ('Paid time off',r'paid (?:time off|leave|vacation)|\bPTO\b'),
              ('Equity/stock options',r'stock options|equity (?:grant|package)|\bESOPs?\b'),
              ('Performance bonus',r'performance[- ]based bonus|performance bonus'),
              ('Mentorship and technical guidance',r'mentorship|technical guidance'),
              ('Career development opportunities',r'professional growth|career advancement|career opportunities|opportunities for growth|career development programs'),
              ('AI learning opportunities',r'opportunity to learn and work with rapidly evolving AI'),
              ('Flat hierarchy',r'flat hierarch'),
              ('Well-being assistance programs',r'well-being.{0,100}global assistance program'),
              ('International teams/projects',r'international teams|international company culture|global engineering and product team'),
              ('Bonus mentioned; amount unspecified',r'remuneration package.*bonus')]
    for label,pattern in patterns:
        if re.search(pattern,jd,re.I):perks.append(label)
    if workplace.lower()=='remote' and 'Remote work' not in perks:perks.insert(0,'Listed remote; JD describes hybrid' if re.search('hybrid working',jd,re.I) else 'Remote work (listing)')
    if workplace.lower()=='hybrid':perks.insert(0,'Hybrid arrangement (listing)')
    return {'advertised_ctc':' | '.join(pay[:2]) if pay else 'Not disclosed',
            'perks':'; '.join(perks) if perks else 'Not disclosed in job posting',
            'pay_source':'Job posting / listing; not an offer', 'benefits_source':'Job description; work arrangement from listing'}


def fit(job):
    title=job['Job_Title'];jd=job['jd']
    if 'impactsure' in re.sub(r'[^a-z0-9]','',(job.get('Company','')+' '+jd).lower()):return 'Excluded current employer: Impactsure'
    if bot.TOO_SENIOR.search(title) or re.search(r'\b(intern(?:ship)?|apprentice|research scientist)\b',title,re.I):return 'Excluded seniority / internship / research role'
    if not re.search(r'python|backend|back.end|full.stack|ai\b|ml\b|machine learning|data scien|software engineer|software developer|software development|data engineer|integrations? engineer|application developer|\bsde\b|artificial intelligence|computer vision|forward deployed|deployment engineer|llm|generative',title,re.I):return 'Outside target role family'
    if re.search(r'only IIT|IIT.{0,20}(?:only|mandatory)',title,re.I):return 'Required institution does not match verified education'
    # Read experience requirements in context, including standalone labels and ranges.
    requirement_section=False
    for line in jd.splitlines():
        low=line.strip().lower()
        if re.search(r'^(required|requirements|qualifications|your expertise|minimum requirements|technical skills)',low):requirement_section=True
        if re.search(r'^(preferred|good to have|why join|this is |about the company|benefits)',low):requirement_section=False
        if re.search(r'partnership|founded|global experience',low):continue
        if re.search(r'preferred|nice.to.have|desirable',low) and not re.search(r'minimum|at least|required',low):continue
        numeric_line=re.sub(r'\b(three|four|five|six|seven|eight|nine|ten)(?=\s+(?:or more\s+)?years?\b)',lambda m:str({'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}[m[1].lower()]),line,flags=re.I)
        match=re.search(r'\b(\d+)\s*(?:[-–]\s*\d+|to\s*\d+|\+)?\s*(?:or more\s+)?(?:years?|yrs?)\b',numeric_line,re.I)
        if match and int(match[1])>2 and (requirement_section or re.search(r'\bexperience\b',low) or 'overall' in low or '+' in match[0] or re.search(r'building|developing|minimum|at least|location',low)):
            return f'Explicit experience requirement exceeds 2 years: {line.strip()[:180]}'
        if re.search(r'immediate join(?:ing|ers?)(?: only)?',low) or '15 days to immediate' in low:return 'Requires availability sooner than confirmed 30-day notice'
    if re.search(r'(?:must|required|minimum).{0,50}\bPh\.?D|Ph\.?D.{0,40}(?:required|mandatory)',jd,re.I):return 'PhD required'
    anchors=re.findall(r'\b(?:python|machine learning|rag|llms?|django|ai/ml|generative ai|finbert|ocr|agentic|ai agents)\b',jd,re.I)
    if not anchors:return 'No clear overlap with verified Python / AI experience'
    pay=job['advertised_ctc']
    ranges=re.findall(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?)',pay,re.I)
    lpa=[float(n) for n in re.findall(r'(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?)',pay,re.I)]
    if lpa and max(lpa)<12:return 'Advertised salary is below 12 LPA minimum'
    monthly=re.findall(r'(\d+(?:\.\d+)?)\s*([kK]?)\s*INR/month',pay,re.I)
    if monthly and max(float(n)*(1000 if k else 1)*12 for n,k in monthly)<1200000:return 'Advertised salary is below 12 LPA minimum'
    if ranges and max(float(hi) for _,hi in ranges)<12:return 'Advertised salary is below 12 LPA minimum'
    return ''


def discover(args):
    from playwright.sync_api import sync_playwright
    _,tracked=bot.read_tracker()
    applied={bot.canonical_url(r['Job_URL']) for r in tracked if r['Status'] in ('Applied','Submission uncertain')}
    pairs={(bot.normalize(r['Company']),bot.normalize(r['Job_Title'])) for r in tracked if r['Status']=='Applied'}
    seeds=[]
    for r in tracked:
        match=re.search(r'/jobs/view/(\d+)',r['Job_URL'])
        if match and bot.canonical_url(r['Job_URL']) not in applied and (bot.normalize(r['Company']),bot.normalize(r['Job_Title'])) not in pairs and r['Status'] in ('To Apply','Needs You'):
            seeds.append(match[1])
    candidates=read('candidates.json',[]);known={j['id'] for j in candidates}
    jd_fingerprints={hashlib.sha256(re.sub(r'\s+',' ',j['jd']).lower().encode()).hexdigest() for j in candidates}
    rejected=read('rejected.json',[])
    excluded={r['id'] for r in rejected if 'Explicit experience' in r['reason'] or 'Excluded seniority' in r['reason']}
    with sync_playwright() as p:
        context=p.chromium.launch_persistent_context(str(bot.default_profile()),headless=True,viewport={'width':1280,'height':900})
        context.set_default_timeout(10000)
        try:
            page=context.new_page();page.goto('https://www.linkedin.com/feed/',wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(1000)
            if bot.stop_reason(page):raise RuntimeError(bot.stop_reason(page))
            ids=read('queue.json',[]) if args.queue_only else list(dict.fromkeys(seeds))
            if not (args.seeds_only or args.queue_only):
                for keyword in args.keywords or ['Python Developer','AI Engineer','Backend Engineer Python']:
                    for offset in range(args.pages):
                        params={'keywords':keyword,'geoId':args.geo_id,'f_AL':'true','f_TPR':'r2592000','start':offset*25}
                        params['f_WT']='2' if args.remote_only else '2,3'
                        if args.entry_level:params['f_E']='2,3'
                        print(f'Discovering {keyword}, page {offset+1}',flush=True)
                        try:
                            found=bot.harvest_job_ids(page,'https://www.linkedin.com/jobs/search/?'+urlencode(params),max_scroll=8,location=args.location,workplace='remote' if args.remote_only else 'any')
                            ids.extend(i for i in found if i not in ids)
                        except Exception as exc:
                            if bot.stop_reason(page):raise
                            print('Search skipped:',type(exc).__name__,flush=True)
            save('queue.json',ids)
            for jid in ids:
                if len(candidates)>=args.limit:break
                if jid in known or jid in excluded or f'https://www.linkedin.com/jobs/view/{jid}' in applied:continue
                try:
                    page.goto(f'https://www.linkedin.com/jobs/view/{jid}/',wait_until='domcontentloaded',timeout=35000)
                    page.wait_for_timeout(800)
                    if bot.stop_reason(page):raise RuntimeError(bot.stop_reason(page))
                    job=bot.extract_job(page)
                    if not job or job.get('workplace','').lower() not in ('hybrid','remote'):continue
                    if not bot.location_matches(job['Location'],args.location):continue
                    if args.remote_only and job['workplace'].lower()!='remote':continue
                    if (bot.normalize(job['Company']),bot.normalize(job['Job_Title'])) in pairs:continue
                    if not bot.first_visible(page.get_by_role('button',name=re.compile('easy apply',re.I))):continue
                    text=jd_text(page)
                    header=page.locator('body').inner_text().split('About the job',1)[0]
                    job.update(id=jid,Job_URL=f'https://www.linkedin.com/jobs/view/{jid}',jd=text,header=header[-4000:])
                    job.update(offering(text,header,job['workplace']))
                    reason=fit(job)
                    if reason:
                        rejected.append({'id':jid,'company':job['Company'],'title':job['Job_Title'],'reason':reason})
                        print('Not selected:',job['Company'],job['Job_Title'],'--',reason[:120],flush=True)
                        save('rejected.json',rejected);continue
                    fingerprint=hashlib.sha256(re.sub(r'\s+',' ',job['jd']).lower().encode()).hexdigest()
                    if fingerprint in jd_fingerprints:
                        print('Duplicate description skipped:',jid,job['Company'],flush=True);continue
                    jd_fingerprints.add(fingerprint)
                    candidates.append(job);known.add(jid);save('candidates.json',candidates)
                    print(f'Candidate {len(candidates)}: {jid} | {job["Company"]} | {job["Job_Title"]} | {job["advertised_ctc"][:100]}',flush=True)
                except Exception as exc:
                    if bot.stop_reason(page):raise
                    print(f'Unable to inspect {jid}: {type(exc).__name__}',flush=True)
        finally:context.close()
    print('Candidates saved:',len(candidates),flush=True)


EXTRA=['Batch_ID','Resume_File','JD_File','Advertised_CTC','Perks','Tailored_Keywords']


def ensure_columns():
    fields,rows=bot.read_tracker()
    new=fields+[f for f in EXTRA if f not in fields]
    if new==fields:return
    fd,temporary=tempfile.mkstemp(dir=ROOT,prefix='.tailored-tracker-',suffix='.tmp')
    with os.fdopen(fd,'w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=new,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    Path(temporary).replace(bot.CSV_FILE)


def prepare(args):
    import tailored_resume
    app=bot.load_applicant();manifests=read('manifests.json',{})
    selected=set((args.only or '').split(','))
    finished={j['id'] for j in read('successes.json',[])}
    for job in read('candidates.json',[]):
        if job['id'] in finished:continue
        if args.only and job['id'] not in selected:continue
        reason=fit(job)
        if reason:print('Rejected during JD review:',job['id'],reason,flush=True);continue
        manifest=tailored_resume.generate(job,app,ROOT/'tmp/pdfs/role-tailored')
        manifests[job['id']]=manifest;save('manifests.json',manifests)
        print('Prepared:',job['id'],job['Company'],manifest['pdf'],flush=True)


def apply_approved(args):
    from playwright.sync_api import sync_playwright
    ensure_columns()
    successes=read('successes.json',[])
    approved=read('approved.json',{})
    manifests=read('manifests.json',{})
    jobs={j['id']:j for j in read('candidates.json',[])}
    completed={r['id'] for r in successes}
    starting_count=len(successes)
    only=set((args.only or '').split(','))
    _,rows=bot.read_tracker()
    already={bot.canonical_url(r['Job_URL']) for r in rows if r['Status'] in ('Applied','Submission uncertain')}
    applied_pairs={(bot.normalize(r['Company']),bot.normalize(r['Job_Title'])) for r in rows if r['Status']=='Applied'}
    with open(ROOT/'.linkedin.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        with sync_playwright() as p:
            ctx=p.chromium.launch_persistent_context(str(bot.default_profile()),headless=True,viewport={'width':1280,'height':900})
            ctx.set_default_timeout(10000)
            try:
                page=ctx.new_page()
                for jid,approval in approved.items():
                    if len(successes)>=10 or len(successes)-starting_count>=args.max:break
                    if jid in completed or (args.only and jid not in only):continue
                    job=jobs[jid];manifest=manifests[jid]
                    if (bot.normalize(job['Company']),bot.normalize(job['Job_Title'])) in applied_pairs:continue
                    if bot.canonical_url(job['Job_URL']) in already:continue
                    pdf=Path(manifest['pdf'])
                    digest=hashlib.sha256(pdf.read_bytes()).hexdigest()
                    if digest!=manifest['pdf_sha256'] or digest!=approval['pdf_sha256']:raise RuntimeError('PDF changed after visual approval')
                    if hashlib.sha256(job['jd'].encode()).hexdigest()!=manifest['jd_sha256']:raise RuntimeError('JD changed after tailoring')
                    if fit(job):continue
                    page.goto(job['Job_URL'],wait_until='domcontentloaded',timeout=35000);page.wait_for_timeout(1000)
                    if bot.stop_reason(page):raise RuntimeError(bot.stop_reason(page))
                    live_job=bot.extract_job(page)
                    if not live_job or 'impactsure' in re.sub(r'[^a-z0-9]','',live_job['Company'].lower()):
                        print('Excluded or unverified live employer:',jid,flush=True);continue
                    if bot.normalize(live_job['Company'])!=bot.normalize(job['Company']):
                        print('Employer changed; needs fresh review:',jid,flush=True);continue
                    current_jd=jd_text(page)
                    if re.sub(r'\s+',' ',current_jd)!=re.sub(r'\s+',' ',job['jd']):
                        print('JD changed; needs fresh tailoring:',jid,flush=True);continue
                    app=bot.load_applicant();app['resume path']=str(pdf.resolve())
                    app['current ctc']=''
                    app['_withhold_current_salary']=True
                    answers={k:v for k,v in bot.load_answers(ROOT/'linkedin_answers.json').items() if not re.search(r'(?:current|present|last drawn).*(?:salary|ctc|compensation|package)',k,re.I)}
                    answers.update({bot.normalize(k):v for k,v in read('answers.json',{}).get(jid,{}).items()})
                    jd_file=BATCH/(jid+'-jd.txt');jd_file.write_text(job['jd'])
                    row_job={k:job[k] for k in ('Company','Job_Title','Location','Job_URL')}
                    row_job['Location']+=' ('+job['workplace']+')'
                    row_job.update(Batch_ID=BATCH.name,Resume_File='',JD_File=str(jd_file.relative_to(ROOT)),
                        Advertised_CTC=job['advertised_ctc'],Perks=job['perks'],Tailored_Keywords=', '.join(manifest['matched_keywords']))
                    def before_submit():
                        review=bot.application_modal(page).inner_text()
                        selected=bot.application_modal(page).locator('[role=radio][aria-checked=true],input[type=radio]:checked').evaluate_all("els=>els.map(e=>e.getAttribute('aria-label')||e.closest('[role=radio]')?.getAttribute('aria-label')||'').filter(t=>/\\.pdf$/i.test(t))")
                        if selected and pdf.name not in selected:raise RuntimeError('A different resume is selected; submission blocked')
                        if pdf.name not in review:
                            (BATCH/(jid+'-review.txt')).write_text(review)
                            page.screenshot(path=str(BATCH/(jid+'-review.png')))
                            raise RuntimeError('Tailored resume filename not confirmed on review page; submission blocked')
                        (BATCH/(jid+'-review.txt')).write_text(review)
                        save(jid+'-submission-settings.json',{'notice_period_days':app.get('notice period'),'expected_ctc':app.get('expected ctc'),'resume_sha256':digest,'employer':job['Company']})
                        bot.record_job(row_job,app,'Submission uncertain','Tailored PDF verified on review; submission started')
                    print('Applying tailored:',jid,job['Company'],job['Job_Title'],flush=True)
                    outcome=bot.apply_job(page,app,answers,before_submit=before_submit)
                    print(outcome.status,outcome.reason,flush=True)
                    if outcome.status=='Applied':
                        final=ROOT/'output/pdf'/BATCH.name/pdf.name;final.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(pdf,final)
                        row_job['Resume_File']=str(final.relative_to(ROOT))
                        receipt=BATCH/'receipts';receipt.mkdir(exist_ok=True)
                        page.screenshot(path=str(receipt/(jid+'.png')))
                        row=bot.record_job(row_job,app,'Applied','JD-tailored PDF uploaded and verified; LinkedIn confirmed submission')
                        result={**job,'resume':str(final),'resume_sha256':digest,'Application_ID':row['Application_ID'],'Date_Applied':row['Date_Applied'],'Sender_Email':row['Sender_Email']}
                        successes.append(result);completed.add(jid);already.add(job['Job_URL']);applied_pairs.add((bot.normalize(job['Company']),bot.normalize(job['Job_Title'])));save('successes.json',successes)
                    elif outcome.status!='Skipped':
                        bot.record_job(row_job,app,outcome.status,outcome.reason)
                    if outcome.stop:break
                    time.sleep(2)
            finally:ctx.close()
    print('Confirmed tailored applications in this batch:',len(successes),flush=True)


def summary(args):
    from phone_actions import _server_topic,_ascii
    import urllib.request
    successes=read('successes.json',[])
    notice=bot.load_applicant().get('notice period','Not specified')
    lines=[f'{len(successes)}/10 JD-tailored applications confirmed. Notice period (days): {notice}. Pay below is advertised; unlisted amounts are Not disclosed.']
    for j in successes:
        lines.append(f"{j['Company']} - {j['Job_Title']} | Advertised CTC: {j['advertised_ctc'][:120]} | Perks: {j['perks'][:150]}")
        terms=j.get('terms')
        if terms:lines[-1]+=' | Terms: '+terms
    body='\n\n'.join(lines)
    (BATCH/'ntfy-summary.txt').write_text(body)
    print(body)
    if args.send:
        server,topic=_server_topic()
        if not topic:raise RuntimeError('NTFY_TOPIC is not configured')
        if len(body.encode())>3900:raise RuntimeError('Summary must be shortened before sending')
        request=urllib.request.Request(f'{server}/{topic}',data=body.encode(),headers={'Title':_ascii(f'{len(successes)} tailored applications - companies, roles, pay & perks'),'Tags':'briefcase'})
        with urllib.request.urlopen(request,timeout=30) as response:receipt=json.load(response)
        save('ntfy-receipt.json',{'id':receipt.get('id'),'time':receipt.get('time'),'sent':True,'applications':len(successes)})
        print('ntfy summary delivered; receipt saved.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['discover','prepare','apply','summary'])
    parser.add_argument('--limit',type=int,default=25)
    parser.add_argument('--pages',type=int,default=3)
    parser.add_argument('--max',type=int,default=10)
    parser.add_argument('--only')
    parser.add_argument('--keywords',action='append')
    parser.add_argument('--seeds-only',action='store_true')
    parser.add_argument('--queue-only',action='store_true')
    parser.add_argument('--location',default='Bengaluru')
    parser.add_argument('--geo-id',default='105214831')
    parser.add_argument('--remote-only',action='store_true')
    parser.add_argument('--entry-level',action='store_true')
    parser.add_argument('--send',action='store_true')
    args=parser.parse_args()
    if args.command=='discover':
        with open(ROOT/'.linkedin.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            discover(args)
    else:
        {'prepare':prepare,'apply':apply_approved,'summary':summary}[args.command](args)


if __name__=='__main__':main()
