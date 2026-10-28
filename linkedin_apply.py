#!/usr/bin/env python3
"""LinkedIn Easy Apply runner. See --help and README.md for setup and limits.

Uses a saved browser login and explicit applicant answers. A successful click
is not proof of submission: only LinkedIn's confirmation marks a row Applied.
"""

import argparse
import csv
import fcntl
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).resolve().parent
CSV_FILE = ROOT_DIR / "job_applications.csv"
APPLICANT_FILE = ROOT_DIR / "applicant.txt"
LEGACY_PROFILE = Path.home() / ".config/job-tracker-linkedin"
LOG_FILE = ROOT_DIR / "auto_apply.log"
COLUMNS = ["Application_ID", "Company", "Job_Title", "Location", "Target_CTC",
           "Job_URL", "Date_Applied", "Channel", "Sender_Email", "Status",
           "Reverted_Back", "Response_Date", "Notes"]
TARGET_SEARCHES = ["Python Developer", "AI ML Engineer", "Generative AI Engineer",
                   "Backend Engineer Python", "Full Stack Python", "LLM Engineer",
                   "Software Engineer Python"]
TOO_SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|leadership|manager|director|head|architect|vp|chief|cto|ceo|cfo|cio|tl)\b", re.I)
CONFIRMED = re.compile(r"(?:application (?:was |has been )?(?:sent|submitted)|your application (?:was |has been )?sent to)", re.I)
MODAL = ".jobs-easy-apply-modal:visible, dialog[open]:visible, [role=dialog]:visible"


def now():
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def log(message):
    line = f"[{now():%Y-%m-%d %H:%M:%S}] [LinkedIn] {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def setting(key, default=""):
    if key in os.environ:
        return os.environ[key]
    path = ROOT_DIR / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == key:
                return value.strip().strip('"').strip("'")
    return default


def default_profile():
    fallback = LEGACY_PROFILE if LEGACY_PROFILE.exists() else ROOT_DIR / ".linkedin-profile"
    return Path(setting("LINKEDIN_PROFILE_DIR") or fallback).expanduser().resolve()


def load_applicant(path=APPLICANT_FILE):
    path = Path(path)
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep:
            data[key.strip().lower()] = value.strip()
    first, _, last = data.get("full name", "").partition(" ")
    data.setdefault("first name", first)
    data.setdefault("last name", last)
    resume = Path(data.get("resume path") or "Prajwath_resume.pdf").expanduser()
    data["resume path"] = str(resume if resume.is_absolute() else path.parent / resume)
    return data


def normalize(text):
    return re.sub(r"\s+", " ", text.replace("*", "")).strip().casefold()


def load_answers(path):
    if not Path(path).exists():
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in data.items()):
        raise ValueError("Screening answers must be a JSON object mapping question text to strings")
    return {normalize(k): v for k, v in data.items() if v.strip()}


def canonical_url(url):
    parts = urlsplit(url)
    if (parts.hostname or "").lower() in ("linkedin.com", "www.linkedin.com", "in.linkedin.com"):
        match = re.search(r"/jobs/view/(?:[^/?]*-)?(\d+)/?$", parts.path)
        if match:
            return f"https://www.linkedin.com/jobs/view/{match[1]}"
    return url.split("?")[0].rstrip("/")


def read_tracker():
    if not Path(CSV_FILE).exists():
        return COLUMNS[:], []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames or COLUMNS[:], list(reader)


def get_existing_applied_urls():
    # Needs You and uncertain submissions require a human, so don't retry them.
    _, rows = read_tracker()
    return {canonical_url(r.get("Job_URL", "")) for r in rows
            if r.get("Status", "").strip().casefold() != "to apply"}


def record_job(job, app, status, reason):
    fields, rows = read_tracker()
    url = canonical_url(job["Job_URL"])
    row = next((r for r in rows if canonical_url(r.get("Job_URL", "")) == url), None)
    if row is None:
        row = dict.fromkeys(fields, "")
        row["Application_ID"] = str(max([int(r["Application_ID"]) for r in rows if r.get("Application_ID", "").isdigit()] + [0]) + 1)
        row.update(job, Job_URL=url, Channel="LinkedIn Easy Apply", Reverted_Back="No")
        rows.append(row)
    row.update(Status=status, Notes=reason)
    row["Target_CTC"] = app.get("expected ctc", "")
    if status == "Applied":
        row.update(Date_Applied=now().strftime("%Y-%m-%d"), Sender_Email=app.get("_application_email") or app.get("email", ""))
    # Replace atomically so an interrupted write cannot truncate the tracker.
    fd, temporary = tempfile.mkstemp(dir=Path(CSV_FILE).parent, prefix=".linkedin-tracker-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, CSV_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return row


# Collect only the current dialog, including native validity and radio groups.
COLLECT = r"""root => {
 const visible = e => !!e.getClientRects().length;
 const clean = s => (s || '').replace(/\s+/g, ' ').replace(/\*/g, '').trim();
 const label = e => clean(e.getAttribute('aria-label') ||
   (e.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean).map(id => document.getElementById(id)?.innerText || '').join(' ') ||
   (e.labels && [...e.labels].map(l => l.innerText).join(' ')) ||
   e.getAttribute('placeholder') || e.name || 'Unlabelled field');
 const out = [], groups = new Set();
 for (const e of root.querySelectorAll('input,select,textarea,[role=combobox]')) {
   if (!visible(e) || e.disabled || e.type === 'hidden' || ['submit','button','reset','file'].includes(e.type)) continue;
   const kind = e.getAttribute('role') === 'combobox' ? 'combobox' : (e.type || e.tagName.toLowerCase());
   const id = 'li' + out.length;
   if (kind === 'radio') {
     const group = e.closest('fieldset,[role=radiogroup]');
     const key = e.name || group || e;
     if (groups.has(key)) continue;
     groups.add(key);
     const members = e.name ? [...root.querySelectorAll('input[type=radio]')].filter(m => m.name === e.name) : (group ? [...group.querySelectorAll('input[type=radio]')] : [e]);
     if (members.some(m => m.checked)) continue;
     let question = '';
     let ancestor = group || e.parentElement;
     for(let depth=0; depth<6 && ancestor && ancestor!==root.parentElement; depth++,ancestor=ancestor.parentElement) {
       const candidate = [...ancestor.querySelectorAll('legend,label,p')].find(n => {
         const text=clean(n.innerText);
         return text && !n.querySelector('input') && !members.some(m=>[...(m.labels||[])].includes(n)) && /\?|\*/.test(n.innerText);
       });
       if(candidate) {question=clean(candidate.innerText);break;}
     }
     members.forEach((m,i) => m.setAttribute('data-li-option', id + ':' + i));
     out.push({id, kind, label: question || e.closest('[role=radio]')?.getAttribute('aria-label') || clean(group?.querySelector('legend')?.innerText) || label(e), options: members.map(m => clean(m.closest('[role=radio]')?.innerText) || label(m))});
     continue;
   }
   if (kind === 'checkbox' && e.checked) continue;
   if (kind !== 'checkbox' && e.value && !(e.tagName === 'SELECT' && /^(select|choose|--)/i.test(e.selectedOptions[0]?.text || ''))) continue;
   e.setAttribute('data-li-field', id);
   const options = e.tagName === 'SELECT' ? [...e.options].filter(o => !o.disabled && o.value && !/^(select|choose|--)/i.test(o.text.trim())).map(o => o.text.trim()) : [];
   out.push({id, kind, label: label(e), options});
 }
 return out;
}"""

VALIDATE = r"""root => {
 const visible = e => !!e.getClientRects().length;
 const problems = [];
 const seen = new Set();
 for (const e of root.querySelectorAll('input,select,textarea,[role=combobox],[role=radiogroup]')) {
   if (!visible(e) || e.disabled || ['hidden','submit','button','reset'].includes(e.type)) continue;
   const label = e.getAttribute('aria-label') || e.closest('[role=radio]')?.getAttribute('aria-label') || e.labels?.[0]?.innerText || e.name || 'Required field';
   const required = e.required || e.getAttribute('aria-required') === 'true' || /\*/.test(label) || e.type === 'radio';
   const empty = e.type === 'checkbox' ? !e.checked : e.type === 'radio' ? ![...root.querySelectorAll('input[type=radio]')].some(r => r.name === e.name && r.checked) : e.getAttribute('role') === 'radiogroup' ? !e.querySelector('[aria-checked=true],input:checked') : !e.value;
   const placeholder = e.tagName === 'SELECT' && /^(select|choose|--)/i.test(e.selectedOptions[0]?.text || '');
   for(const id of (e.getAttribute('aria-describedby') || '').split(/\s+/)) {
     const error = id && document.getElementById(id);
     if(error && visible(error) && /required|invalid|please enter|must be|select an/i.test(error.innerText)) problems.push(label + ': ' + error.innerText.trim());
   }
   if (e.getAttribute('aria-invalid') === 'true' || (e.validity && !e.validity.valid) || (required && (empty || placeholder))) {
     if (!seen.has(label)) problems.push(label.replace(/\s+/g,' ').trim());
     seen.add(label);
   }
 }
 for (const e of root.querySelectorAll('.artdeco-inline-feedback--error,[role=alert]')) {
   if (visible(e) && e.innerText.trim()) problems.push(e.innerText.trim());
 }
 return problems;
}"""


def answer_for(label, app, answers, kind="text"):
    label = normalize(label)
    if any(normalize(n) in label for n in app.get("never auto-fill", "").split(",") if n.strip()):
        return None
    if label in answers:
        return answers[label]
    if re.search(r"start immediately|immediate joiner|join immediately", label):
        notice = app.get('notice period', '')
        if re.fullmatch(r"0\s*(?:days?)?|immediate", notice, re.I):
            return 'Yes'
        if re.fullmatch(r"[1-9]\d*\s*(?:days?)?", notice, re.I):
            return 'No'
    if re.search(r"by submitting my application i acknowledge and consent to the data privacy policies|i (?:agree|consent) to .*(?:processing|privacy policy)|i certify.*(?:information|accurate)", label) and not re.search(r"marketing|promotional|future opportunit|talent pool", label):
        return 'Yes'
    whole_years = 'whole number' in label
    label = re.sub(r"\s*\(only whole numbers allowed\)\s*$", "", label).strip()
    # Specific skill experience and salary units need an explicit answer.
    rules = [
        (r"\bfirst name\b|given name", "first name"),
        (r"\blast name\b|surname|family name", "last name"),
        (r"^(?:full |legal )?name$", "full name"),
        (r"e-?mail", "email"), (r"phone|mobile", "phone"),
        (r"linkedin", "linkedin"), (r"github", "github"),
        (r"portfolio|personal website", "portfolio"),
        (r"relocat", "willing to relocate"), (r"hybrid|in.office", "hybrid ok"),
        (r"sponsor", "visa sponsorship"),
        (r"engineering graduate", "engineering graduate"),
        (r"authori[sz]ed to work|work authori[sz]ation", "work authorization"),
        (r"^city$|^current city$", "city"),
        (r"^location$|^current location$", "current location"),
        (r"^country(?:/region)?$", "country"),
        (r"^current (?:company|employer)$", "current company"),
        (r"^current (?:title|role|designation)$", "current title"),
        (r"^(?:(?:how many )?years of (?:total |work |professional )?experience(?: do you have)?\??|total experience)$", "total experience"),
        (r"(?:years|yrs).*(?:\bpython\b)|\bpython\b.*(?:years|yrs)", "python experience"),
        (r"(?:years|yrs).*(?:generative ai|genai|ai/ml|machine learning|data science|\bllms?\b|\brag\b)|^what is your experience in ai(?:/ml| automation)\??$", "ai ml experience"),
        (r"notice period|when can you (?:start|join)|(?:how many|how soon|within how many) days?.*(?:start|join)|^what is your np", "notice period"),
        (r"(?:expected|desired|current) (?:ctc|salary)|salary expectation", "expected ctc" if re.search(r"expected|desired|expectation", label) else "current ctc"),
    ]
    for pattern, key in rules:
        if not re.search(pattern, label):
            continue
        value = app.get(key, "")
        if not value:
            return None
        if key == "work authorization" and re.search(r"\bin\s+(?!india\b|the country\b|this country\b)", label):
            return None  # A generic Yes does not establish authorization abroad.
        if key in ("total experience", "python experience", "ai ml experience"):
            match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:years?)?", value, re.I)
            if not match:
                return None
            return str(int(float(match[1]))) if whole_years else match[1]
        if key in ("current ctc", "expected ctc"):
            if re.search(r"lpa|lakhs?|lacs?", label):
                match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lacs?)?", value, re.I)
                return match[1] if match else None
            return None  # Don't guess whether salary means rupees, LPA, monthly, etc.
        if key == "notice period" and (kind in ("number", "text") or re.search(r"\bdays?\b|\bnp\b", label)):
            match = re.fullmatch(r"(\d+)\s*(?:days?)?", value, re.I)
            return match[1] if match else ("0" if value.lower() == "immediate" else None)
        return value
    return None


def first_visible(locator):
    for element in locator.all():
        if element.is_visible():
            return element
    return None


def fill_step(modal, app, answers):
    # LinkedIn may offer only the verified account email. Record the address
    # actually selected rather than claiming the configured address was used.
    for email in modal.locator('input[type=email], select').all():
        label = email.evaluate("e => (e.labels?.[0]?.innerText || e.getAttribute('aria-label') || '').toLowerCase()")
        if 'email' not in label and 'e-mail' not in label:
            continue
        if email.evaluate("e => e.tagName") == "SELECT":
            options = email.evaluate("e => [...e.options].map(o=>({text:o.text.trim(),value:o.value}))")
            option = next((o for o in options if app.get('email') in (o['text'], o['value'])), None)
            if option:
                email.select_option(value=option['value'])
        elif app.get('email'):
            email.fill(app['email'])
        value = email.input_value()
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            app['_application_email'] = value
    uploads = modal.locator('input[type="file"]').all()
    for upload in uploads:
        label = upload.evaluate("e => [e.id, e.name, e.getAttribute('aria-label'), ...(e.labels || [])].map(x => typeof x === 'string' ? x : x?.innerText || '').join(' ')")
        if re.search(r"cover|certificate|photo|additional|supporting", label, re.I):
            continue
        if len(uploads) > 1 and not re.search(r"resume|\bcv\b", label, re.I):
            continue
        if not upload.is_disabled():
            upload.set_input_files(app["resume path"])
            modal = application_modal(modal.page)
    for field in modal.evaluate(COLLECT):
        answer = answer_for(field["label"], app, answers, field["kind"])
        if answer is None:
            continue
        element = modal.locator(f'[data-li-field="{field["id"]}"]')
        kind = field["kind"]
        if kind in ("select-one", "select-multiple", "radio"):
            option = next((i for i, value in enumerate(field["options"]) if normalize(value) == normalize(answer)), None)
            if option is None:
                continue
            if kind == "radio":
                radio = modal.locator(f'[data-li-option="{field["id"]}:{option}"]')
                wrapper = radio.locator('xpath=ancestor::*[@role="radio"][1]')
                if wrapper.count():
                    wrapper.click()
                else:
                    radio.check()
            else:
                element.select_option(label=field["options"][option])
        elif kind == "checkbox":
            if normalize(answer) in ("yes", "true", "checked"):
                element.check()
        elif kind != "combobox":
            if kind == "number" and not re.fullmatch(r"\d+(?:\.\d+)?", answer):
                continue
            element.fill(answer)


def stop_reason(page):
    path = urlsplit(page.url).path.lower()
    if any(s in path for s in ("/login", "/authwall", "/checkpoint", "/challenge")):
        return "Login or security verification required; run --login"
    challenge = first_visible(page.locator('iframe[src*="recaptcha"], iframe[src*="hcaptcha"], iframe[src*="captcha"], #captcha-internal, input#username'))
    if challenge is not None:
        return "Login or CAPTCHA requires your attention"
    limit = page.get_by_text(re.compile(r"(?:reached|exceeded).{0,60}(?:daily|application|easy apply).{0,30}limit|try applying again tomorrow", re.I))
    if first_visible(limit) is not None:
        return "LinkedIn application limit reached"
    return ""


@dataclass
class Outcome:
    status: str
    reason: str = ""
    stop: bool = False


def application_modal(page, timeout=8):
    """Find application controls in native, classic, and portaled dialogs."""
    deadline = time.monotonic() + timeout
    navigation = re.compile(r"^(?:next|review|continue|submit application)(?:\b.*)?$|continue to next step", re.I)
    while time.monotonic() < deadline:
        native = first_visible(page.locator('dialog[open]'))
        if native is not None:
            if first_visible(native.get_by_role('button', name=navigation)) is not None:
                return native
            page.wait_for_timeout(200)
            continue  # Loading a modal must never select a background carousel.
        for modal in page.locator(MODAL).all():
            if first_visible(modal.get_by_role('button', name=navigation)) is not None:
                return modal
        button = first_visible(page.get_by_role('button', name=navigation))
        if button is not None:
            depth = button.evaluate(r"""e => {
                document.querySelectorAll('[data-li-modal]').forEach(n=>n.removeAttribute('data-li-modal'));
                let root=e.parentElement, depth=1;
                while(root && root!==document.body) {
                    if(root.querySelector('input,select,textarea') || /Apply to\s+\S/.test(root.innerText)) {
                        return depth;
                    }
                    root=root.parentElement; depth++;
                }
                return 0;
            }""")
            if depth:
                return button.locator(f'xpath=ancestor::*[{depth}]')
        page.wait_for_timeout(200)
    raise RuntimeError('Application form did not finish loading')


def save_questions(page, modal, problems):
    """Keep unanswered question text locally for factual follow-up, without answers."""
    match = re.search(r'/jobs/view/(\d+)', page.url)
    if not match:
        return
    try:
        directory = ROOT_DIR / '.linkedin-questions'
        directory.mkdir(exist_ok=True, mode=0o700)
        fields = modal.evaluate(COLLECT)
        (directory / (match[1] + '.json')).write_text(json.dumps({'url':page.url,'problems':problems,'fields':fields},indent=2),encoding='utf-8')
    except Exception:
        pass


def apply_job(page, app, answers=None, before_submit=None, confirmation_timeout=12):
    """Never retry Submit. Missing confirmation is an uncertain submission."""
    answers = answers or {}
    clicked_submit = False
    try:
        reason = stop_reason(page)
        if reason:
            return Outcome("Needs You", reason, True)
        button = first_visible(page.get_by_role("button", name=re.compile(r"\beasy apply\b", re.I)))
        if button is None:
            return Outcome("Skipped", "No Easy Apply button")
        button.click()
        for _ in range(12):
            reason = stop_reason(page)
            if reason:
                return Outcome("Needs You", reason, True)
            modal = application_modal(page)
            fill_step(modal, app, answers)
            modal = application_modal(page)
            problems = modal.evaluate(VALIDATE)
            if problems:
                save_questions(page, modal, problems)
                return Outcome("Needs You", "Unanswered or invalid: " + "; ".join(problems)[:500])
            submit = first_visible(modal.get_by_role("button", name=re.compile(r"submit application", re.I)))
            if submit is not None:
                if before_submit:
                    before_submit()  # Persist uncertainty BEFORE clicking, including crash cases.
                clicked_submit = True
                submit.click()
                deadline = time.monotonic() + confirmation_timeout
                while time.monotonic() < deadline:
                    reason = stop_reason(page)
                    if reason:
                        return Outcome("Submission uncertain", reason, True)
                    if first_visible(page.get_by_text(CONFIRMED)) is not None:
                        return Outcome("Applied", "LinkedIn confirmed submission")
                    time.sleep(0.25)
                return Outcome("Submission uncertain", "Submit clicked; LinkedIn confirmation was not observed")
            next_button = first_visible(modal.get_by_role("button", name=re.compile(r"^(?:next|review|continue)(?:\b.*)?$|continue to next step", re.I)))
            if next_button is None or not next_button.is_enabled():
                return Outcome("Needs You", "No enabled Next, Review or Submit button")
            next_button.click()
            page.wait_for_timeout(700)
        save_questions(page, modal, ['Form did not advance after 12 steps'])
        return Outcome("Needs You", "Easy Apply exceeded 12 steps")
    except Exception as exc:
        log(f'Form failure details: {exc}')
        return Outcome("Submission uncertain" if clicked_submit else "Needs You", f"Form error: {type(exc).__name__}: {str(exc).splitlines()[0]}"[:500])
    # Do not discard blocked or uncertain applications; leave LinkedIn's draft intact.


def location_matches(actual, requested):
    city = requested.split(",")[0].strip().casefold()
    cities = ("bengaluru", "bangalore") if city in ("bengaluru", "bangalore") else (city,)
    return any(re.search(r"\b" + re.escape(c) + r"\b", actual, re.I) for c in cities)


def extract_job(page):
    """Read the top section; modern LinkedIn renders its title as a paragraph."""
    page.locator('a[href*="/company/"]').filter(has_text=re.compile(r"\S")).first.wait_for(state="visible", timeout=10000)
    return page.evaluate(r"""() => {
      const visible = e => !!e.getClientRects().length;
      const clean = s => (s || '').replace(/\s+/g,' ').trim();
      const companyLink = [...document.querySelectorAll('a[href*="/company/"]')].find(e => visible(e) && clean(e.innerText));
      if (!companyLink) return null;
      const company = clean(companyLink.innerText);
      let root = companyLink;
      for (let i=0; i<9 && root && ![...root.querySelectorAll('button,a')].some(b => /^(?:easy apply|apply)$/i.test(clean(b.innerText))); i++) root = root.parentElement;
      if (!root || root === document.body || root === document.documentElement) return null;
      const lines = root.innerText.split(/\n+/).map(clean).filter(Boolean);
      const index = lines.indexOf(company);
      if (index < 0 || !lines[index+2]) return null;
      const heading = root.querySelector('h1,.job-details-jobs-unified-top-card__job-title,.jobs-unified-top-card__job-title');
      const workplace = lines.find(s => /^(?:hybrid|remote|on-site)$/i.test(s)) ||
        [...root.querySelectorAll('span,p,button')].map(e => clean(e.innerText)).find(s => /^(?:hybrid|remote|on-site)$/i.test(s)) || '';
      return {Company:company, Job_Title:clean(heading?.innerText) || lines[index+1],
        Location:lines[index+2].split('·')[0].trim(),
        workplace};
    }""")


def harvest_job_ids(page, search_url, max_scroll=12, location="", workplace="any"):
    page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
    if stop_reason(page):
        raise RuntimeError(stop_reason(page))
    cards = '[componentkey^="job-card-component-ref-"][role="button"], [data-job-id], a[href*="/jobs/view/"]'
    page.locator(cards).first.wait_for(timeout=10000)
    ids = []
    for _ in range(max_scroll):
        modern = page.locator('[componentkey^="job-card-component-ref-"][role="button"]')
        source = modern if modern.count() else page.locator(cards)
        found = source.evaluate_all("els => els.map(e => ({key: e.getAttribute('componentkey') || e.getAttribute('href') || '/jobs/view/' + e.getAttribute('data-job-id'), text:e.innerText}))")
        for card in found:
            if modern.count() and ((location and not location_matches(card["text"], location)) or (workplace != "any" and not re.search(r"\(" + workplace + r"\)", card["text"], re.I))):
                continue
            match = re.search(r"(?:job-card-component-ref-|/jobs/view/(?:[^/?]*-)?)(\d+)", card["key"])
            if match and match[1] not in ids:
                ids.append(match[1])
        panel = first_visible(page.locator(".scaffold-layout__list, .jobs-search-results-list"))
        if panel is None and modern.count():
            panel = modern.first
        if panel is None:
            break
        at_end = panel.evaluate("e => {while(e && e.scrollHeight <= e.clientHeight + 2) e=e.parentElement; if(!e)return true; const end=e.scrollTop+e.clientHeight>=e.scrollHeight-2; e.scrollBy(0,800); return end;}")
        if at_end:
            break
        page.wait_for_timeout(700)
    return ids


def notify(row, reason):
    try:
        from phone_actions import send_needs_you
        send_needs_you(row, reason)
    except Exception as exc:
        log(f"Phone hand-off unavailable: {type(exc).__name__}")


def run_linkedin_bot(args, app, answers):
    from playwright.sync_api import sync_playwright
    if args.scheduled and not args.profile_dir.exists():
        log("No saved LinkedIn session; run python3 linkedin_apply.py --login")
        return 0
    args.profile_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    existing = get_existing_applied_urls()
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(str(args.profile_dir), headless=not (args.login or args.headed), viewport={"width": 1280, "height": 900})
        context.set_default_timeout(8000)
        try:
            page = context.new_page()
            page.goto("https://www.linkedin.com/login" if args.login else "https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
            if args.login:
                log("Sign in in the browser, including any security verification. Waiting up to 10 minutes.")
                deadline = time.monotonic() + 600
                while time.monotonic() < deadline:
                    if page.is_closed():
                        raise RuntimeError("Login browser was closed before confirmation")
                    if not stop_reason(page) and first_visible(page.locator(".global-nav__me, #global-nav")) is not None:
                        log("Login confirmed; browser session saved.")
                        return 0
                    page.wait_for_timeout(1000)
                raise RuntimeError("Login timed out; run --login again")
            page.wait_for_timeout(1500)
            reason = stop_reason(page)
            if reason:
                log(reason)
                return 2
            ids = [j.strip() for j in (getattr(args, 'only', '') or '').split(',') if j.strip()]
            searches = [(keyword, offset) for keyword in (args.keywords or TARGET_SEARCHES) for offset in range(0, getattr(args, 'pages', 1) * 25, 25)]
            for keyword, offset in ([] if ids else searches):
                log(f"Searching: {keyword}")
                params = {"keywords": keyword, "location": args.location, "f_AL": "true", "f_TPR": f"r{args.posted_days * 86400}"}
                params["geoId"] = args.geo_id
                params['start'] = offset
                if args.workplace != "any":
                    params["f_WT"] = {"hybrid": "3", "remote": "2"}[args.workplace]
                try:
                    found = harvest_job_ids(page, "https://www.linkedin.com/jobs/search/?" + urlencode(params), location=args.location, workplace=args.workplace)
                    ids.extend(jid for jid in found if jid not in ids and f'https://www.linkedin.com/jobs/view/{jid}' not in existing)
                    log(f"Found {len(found)} matching IDs on page {offset // 25 + 1}")
                except Exception as exc:
                    if stop_reason(page):
                        log(stop_reason(page))
                        return 2
                    log(f"Search unavailable for {keyword}: {type(exc).__name__}")
                if len(ids) >= args.max * 8:
                    break
            counts = {"Applied": 0, "Needs You": 0, "Submission uncertain": 0, "Listed": 0}
            visited = 0
            for jid in ids:
                if counts["Applied"] + counts["Listed"] >= args.max or visited >= max(40, args.max * 8):
                    break
                url = f"https://www.linkedin.com/jobs/view/{jid}"
                if url in existing:
                    continue
                visited += 1
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1000)
                reason = stop_reason(page)
                if reason:
                    log(reason)
                    return 2
                try:
                    job = extract_job(page)
                except Exception:
                    job = None
                if not job or not job["Job_Title"] or not job["Company"]:
                    log(f"Skipping {jid}: could not verify job details")
                    continue
                actual_workplace = job.pop("workplace", "")
                if not location_matches(job["Location"], args.location) or (args.workplace != "any" and actual_workplace.lower() != args.workplace):
                    log(f"Skipping {jid}: actual location/workplace does not match")
                    continue
                years = re.search(r'(\d+)(?:\s*[-–]\s*\d+)?\s*\+?\s*(?:years?|yrs?)\b', job['Job_Title'], re.I)
                if TOO_SENIOR.search(job["Job_Title"]) or re.search(r'\b(intern(?:ship)?|apprentice)\b',job['Job_Title'],re.I) or (years and int(years[1]) > 2):
                    continue
                job["Job_URL"] = url
                if actual_workplace:
                    job["Location"] += f" ({actual_workplace})"
                log(f"{'Listed' if args.dry_run else 'Processing'}: {job['Company']} -- {job['Job_Title']} -- {url}")
                if args.dry_run:
                    counts["Listed"] += 1
                    continue  # Search-only: never open or alter an application draft.
                app = load_applicant()
                answers = load_answers(args.answers)
                app.pop('_application_email', None)
                outcome = apply_job(page, app, answers, before_submit=lambda: record_job(job, app, "Submission uncertain", "Submission started; verify on LinkedIn before retrying"))
                if outcome.status != "Skipped":
                    row = record_job(job, app, outcome.status, outcome.reason)
                    existing.add(url)
                    counts[outcome.status] += 1
                    if outcome.status != "Applied":
                        notify(row, outcome.reason)
                log(f"{outcome.status}: {outcome.reason}")
                if outcome.stop:
                    log("Stopped; resolve the login, verification or limit before another run.")
                    return 2
                page.wait_for_timeout(2000)
            log("Finished: " + ", ".join(f"{key}: {value}" for key, value in counts.items()))
            return 0
        finally:
            context.close()


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--login", action="store_true", help="Save a login using a visible browser")
    mode.add_argument("--dry-run", action="store_true", help="List jobs only; never fill forms or update the tracker")
    mode.add_argument("--check", action="store_true", help="Check local configuration without opening LinkedIn")
    parser.add_argument("--max", type=positive_int, default=10, help="Maximum submissions (default: 10)")
    parser.add_argument("--only", help="Comma-separated LinkedIn job IDs; skips search and keeps all fit checks")
    parser.add_argument("--keywords", action="append", help="Search terms; repeat for multiple searches")
    parser.add_argument("--location", default="Bengaluru, Karnataka, India")
    parser.add_argument("--geo-id", help="LinkedIn location ID; Bengaluru defaults to 105214831")
    parser.add_argument("--workplace", choices=("hybrid", "remote", "any"), default="hybrid")
    parser.add_argument("--posted-days", type=positive_int, default=7)
    parser.add_argument("--pages", type=positive_int, default=2, help="Search result pages per keyword (default: 2)")
    parser.add_argument("--profile-dir", type=Path, default=default_profile())
    parser.add_argument("--answers", type=Path, default=ROOT_DIR / "linkedin_answers.json")
    parser.add_argument("--headed", action="store_true", help="Show the browser during a run")
    parser.add_argument("--scheduled", action="store_true", help="Skip when disabled or no saved browser profile exists")
    args = parser.parse_args(argv)
    if args.only and not all(j.strip().isdigit() for j in args.only.split(',')):
        parser.error('--only must contain numeric job IDs separated by commas')
    if not args.geo_id:
        if location_matches(args.location.split(",")[0], "Bengaluru"):
            args.geo_id = "105214831"
        elif not (args.login or args.check):
            parser.error("--geo-id is required for cities other than Bengaluru; copy geoId from your LinkedIn search URL")
    args.profile_dir = args.profile_dir.expanduser().resolve()
    if args.scheduled and setting("LINKEDIN_ENABLED", "true").lower() != "true":
        log("LinkedIn daily step disabled by LINKEDIN_ENABLED")
        return 0
    try:
        app = {} if args.login else load_applicant()
        answers = load_answers(args.answers)
        if not (args.login or args.dry_run):
            for key in ("full name", "email", "phone"):
                if not app.get(key):
                    raise ValueError(f"Missing {key} in applicant.txt")
            if not Path(app["resume path"]).is_file():
                raise ValueError("Resume not found; check Resume path in applicant.txt")
        if args.check:
            from importlib.util import find_spec
            if find_spec("playwright") is None:
                raise ValueError("Install Playwright: python3 -m pip install playwright")
            log(f"Applicant and resume ready; {len(answers)} explicit screening answers. Saved browser profile exists: {args.profile_dir.exists()}")
            return 0
        # Prevent overlapping manual and scheduled bot runs sharing one session.
        with open(ROOT_DIR / ".linkedin.lock", "a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                log("Another LinkedIn run is already active")
                return 2
            return run_linkedin_bot(args, app, answers)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        log(f"Cannot run: {exc}")
        return 2
    except KeyboardInterrupt:
        log("Stopped by user; check any uncertain submission before retrying")
        return 130
    except Exception as exc:
        log(f"Browser run failed ({type(exc).__name__}): {str(exc).splitlines()[0]}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
