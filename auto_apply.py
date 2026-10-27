#!/usr/bin/env python3
"""
Fill job applications on Greenhouse, Lever and Ashby from applicant.txt.

Runs on your own computer with a visible browser. For each "To Apply" row in
job_applications.csv on a supported platform, it opens the form, fills your
details, uploads your resume and writes a short tailored answer for free-text
questions. By default it then waits for you to check the form, solve any
captcha and click Submit yourself.

Usage:
    pip install playwright && python3 -m playwright install chromium
    python3 auto_apply.py                   # review each form, you click Submit
    python3 auto_apply.py --auto-submit     # submit when every required field is filled and there is no captcha
    python3 auto_apply.py --dry-run         # list what would be opened, change nothing
    python3 auto_apply.py --include-stretch # also apply to "Stretch" / "Weak fit" roles
    python3 auto_apply.py --only 1,5,9      # only these Application_IDs

Workday, SmartRecruiters, company sites and aggregators are skipped: they need
accounts or redirect elsewhere, so apply to those by hand.
"""

import os
import re
import csv
import sys
import time
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
APPLICANT_FILE = os.path.join(ROOT_DIR, "applicant.txt")
LOG_FILE = os.path.join(ROOT_DIR, "auto_apply.log")

SUPPORTED = {
    "job-boards.greenhouse.io": "greenhouse",
    "boards.greenhouse.io": "greenhouse",
    "jobs.lever.co": "lever",
    "jobs.ashbyhq.com": "ashby",
}

SUBMITTED_TEXT = re.compile(
    r"(thank(s| you) for (applying|your (application|interest))|application (has been )?(submitted|received)|we('ve| have) received your application)",
    re.I,
)


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_applicant(path=APPLICANT_FILE):
    """Read 'Key: value' lines. Keys are lower-cased; markdown ** is ignored."""
    if not os.path.exists(path):
        sys.exit(f"Missing {path}. Copy applicant.example.txt to applicant.txt and fill it in.")
    data = {}
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip().replace("**", "")
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = re.sub(r"\s*\(.*?\)", "", key).strip().lower()
            data[key] = value.strip()
    first, _, last = data.get("full name", "").partition(" ")
    data.setdefault("first name", first)
    data.setdefault("last name", last)
    resume = data.get("resume path", "Prajwath_resume.pdf")
    data["resume path"] = resume if os.path.isabs(resume) else os.path.join(ROOT_DIR, resume)
    if not os.path.exists(data["resume path"]):
        sys.exit(f"Resume not found: {data['resume path']}")
    for key in ("full name", "email", "phone"):
        if not data.get(key):
            sys.exit(f"applicant.txt is missing '{key}'")
    return data


def platform_of(url):
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    return SUPPORTED.get(host)


def apply_url(url, platform):
    """Lever and Ashby put the form on a separate /apply or /application page."""
    url = url.split("?")[0].rstrip("/")
    if platform == "lever" and not url.endswith("/apply"):
        return url + "/apply"
    if platform == "ashby" and not url.endswith("/application"):
        return url + "/application"
    return url


def why_company(app, row):
    """Short tailored answer for 'why this company / cover letter' style questions."""
    template = app.get("why this company") or (
        "I'm a Full Stack Python and AI/ML developer at {current_company}, where I lead an "
        "8-member team building production AI for banks: fine-tuned FinBERT/LLM document "
        "classification, OCR pipelines and RAG-based document analysis. The {title} role at "
        "{company} builds on exactly that work, and I'd like to bring the same hands-on "
        "delivery experience to your team in Bangalore on a hybrid basis."
    )
    notes = re.sub(r"^(strong fit|good fit|stretch|weak fit):\s*", "", row.get("Notes", ""), flags=re.I)
    return template.format(
        company=row["Company"], title=row["Job_Title"], notes=notes.rstrip(".") or "Python and AI",
        current_company=app.get("current company", "my current company"),
    )


def answer_for(label, app, row):
    """Map a form question label to an answer, or None when we shouldn't guess."""
    l = label.lower()
    never = [s.strip().lower() for s in app.get("never auto-fill", "").split(",") if s.strip()]
    if any(n and n in l for n in never):
        return None
    rules = [
        (r"\bfirst name\b|given name", "first name"),
        (r"\blast name\b|surname|family name", "last name"),
        (r"^(full )?name\b|your name|legal name", "full name"),
        (r"e-?mail", "email"),
        (r"phone|mobile|contact number", "phone"),
        (r"linkedin", "linkedin"),
        (r"github", "github"),
        (r"portfolio|website|personal site", "portfolio"),
        (r"current (company|employer)|^company$|^org", "current company"),
        (r"current (title|role|designation)|job title", "current title"),
        (r"(current|present) (location|city)|where are you (based|located)|^location|city", "current location"),
        (r"relocat", "willing to relocate"),
        (r"hybrid|in[- ]office|days .*office|office .*days", "hybrid ok"),
        (r"notice period|earliest .*(start|join)|when can you (start|join)|availability to start", "notice period"),
        (r"expected (ctc|salary|compensation)|salary expectation|desired (salary|compensation)", "expected ctc"),
        (r"current (ctc|salary|compensation)", "current ctc"),
        (r"(years|yrs).*(python|ai|ml|machine learning)|(python|ai|ml).*(years|yrs)", "relevant experience"),
        (r"years of experience|total experience|how many years", "total experience"),
        (r"degree|education|qualification|university|college", "degree"),
        (r"authori[sz]ed to work|work authori[sz]ation|eligible to work|right to work", "work authorization"),
        (r"sponsor", "visa sponsorship"),
        (r"how did you (hear|find|learn)|source", "heard about us"),
        (r"\bgender\b", "gender"),
    ]
    for pattern, key in rules:
        if re.search(pattern, l) and app.get(key):
            return app[key]
    if re.search(r"cover letter|why .*(join|work|interested|company|role)|tell us (about|why)|additional information|anything else", l):
        return why_company(app, row)
    return None


def field_label(page, el):
    """Best-effort visible label for an input element."""
    return page.evaluate(
        """(el) => {
            const clean = s => (s || '').replace(/\\s+/g, ' ').replace(/\\*/g, '').trim();
            if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return clean(l.innerText); }
            const wrap = el.closest('label'); if (wrap) return clean(wrap.innerText);
            if (el.getAttribute('aria-label')) return clean(el.getAttribute('aria-label'));
            const by = el.getAttribute('aria-labelledby');
            if (by) { const l = document.getElementById(by.split(' ')[0]); if (l) return clean(l.innerText); }
            let node = el.parentElement;
            for (let i = 0; i < 4 && node; i++, node = node.parentElement) {
                const l = node.querySelector('label, legend, .application-label, .text');
                if (l && !l.contains(el)) return clean(l.innerText);
            }
            return clean(el.getAttribute('placeholder') || el.name || '');
        }""",
        el,
    )


def pick_option(select_el, answer):
    options = select_el.evaluate("s => [...s.options].map(o => o.text.trim())")
    a = answer.lower()
    yes = a.startswith("yes") or a in ("y", "true")
    no = a.startswith("no") or a in ("n", "false")
    for opt in options:
        o = opt.lower()
        if o and (o == a or (len(a) > 2 and a in o) or (yes and o.startswith("yes")) or (no and o.startswith("no"))):
            return opt
    return None


def fill_form(page, app, row):
    """Fill every recognisable field. Returns labels of required fields left empty."""
    page.wait_for_load_state("domcontentloaded")
    time.sleep(1.5)

    for sel in ['input[type=file][name*=resume i]', 'input[type=file][id*=resume i]', 'input[type=file]']:
        files = page.locator(sel)
        if files.count():
            try:
                files.first.set_input_files(app["resume path"])
            except Exception as e:
                log(f"   resume upload failed: {e}")
            break

    for el in page.query_selector_all("input:not([type=hidden]):not([type=file]):not([type=submit]):not([type=checkbox]):not([type=radio]), textarea, select"):
        try:
            if not el.is_visible() or not el.is_enabled():
                continue
            label = field_label(page, el)
            answer = answer_for(label, app, row)
            if not answer:
                continue
            tag = el.evaluate("e => e.tagName.toLowerCase()")
            if tag == "select":
                opt = pick_option(el, answer)
                if opt:
                    el.select_option(label=opt)
            elif not el.input_value():
                el.fill(answer)
        except Exception:
            continue

    # Yes/No radio groups such as "Are you willing to relocate?"
    for group in page.query_selector_all("fieldset, [role=radiogroup]"):
        try:
            label = group.evaluate("g => (g.querySelector('legend, label, .text') || g).innerText.split('\\n')[0]")
            answer = answer_for(label, app, row)
            if not answer:
                continue
            for radio in group.query_selector_all("input[type=radio]"):
                text = field_label(page, radio).lower()
                if text and (text.startswith(answer.lower()[:3]) or answer.lower().startswith(text[:3])):
                    radio.check()
                    break
        except Exception:
            continue

    return page.evaluate(
        """() => [...document.querySelectorAll('input[required], textarea[required], select[required], [aria-required=true]')]
            .filter(e => e.offsetParent !== null && e.type !== 'hidden' && !e.value && !(e.type === 'file' && e.files && e.files.length))
            .map(e => (e.labels && e.labels[0] ? e.labels[0].innerText : (e.getAttribute('aria-label') || e.name || e.id || '?')).replace(/\\s+/g, ' ').trim())"""
    )


def has_captcha(page):
    return page.locator("iframe[src*=recaptcha], iframe[src*=hcaptcha], iframe[src*=turnstile], .g-recaptcha, .h-captcha").count() > 0


def submitted(page, start_url):
    try:
        text = page.inner_text("body")[:5000]
    except Exception:
        return False
    return bool(SUBMITTED_TEXT.search(text)) or ("/confirmation" in page.url or "thanks" in page.url.lower()) and page.url != start_url


def click_submit(page):
    for sel in ["button[type=submit]", "input[type=submit]", "button:has-text('Submit application')", "button:has-text('Submit')"]:
        btn = page.locator(sel)
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            return True
    return False


def mark_applied(row_id, email):
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames, rows = reader.fieldnames, list(reader)
    for r in rows:
        if r["Application_ID"] == row_id:
            r["Status"] = "Applied"
            r["Date_Applied"] = datetime.now().strftime("%Y-%m-%d")
            r["Sender_Email"] = email
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pick_rows(args):
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    only = None
    if "--only" in args:
        only = set(args[args.index("--only") + 1].split(","))
    out, skipped = [], []
    for r in rows:
        if r["Status"].strip().lower() != "to apply":
            continue
        if only and r["Application_ID"] not in only:
            continue
        notes = r.get("Notes", "").lower()
        if not only and "--include-stretch" not in args and notes.startswith(("stretch", "weak fit")):
            skipped.append((r, "stretch/weak fit"))
            continue
        platform = platform_of(r["Job_URL"])
        if not platform:
            skipped.append((r, "platform not supported, apply by hand"))
            continue
        url_path = re.sub(r"^https?://[^/]+/?", "", r["Job_URL"].split("?")[0]).strip("/")
        if url_path.count("/") < 1:
            skipped.append((r, "board link, not a single posting"))
            continue
        out.append((r, platform))
    return out, skipped


def main():
    args = sys.argv[1:]
    app = load_applicant()
    todo, skipped = pick_rows(args)

    print(f"\n{len(todo)} applications to fill, {len(skipped)} skipped:")
    for r, why in skipped:
        print(f"  - #{r['Application_ID']} {r['Company']} — {r['Job_Title']}: {why}")
    if "--dry-run" in args:
        for r, platform in todo:
            print(f"  + #{r['Application_ID']} {r['Company']} — {r['Job_Title']} [{platform}] {apply_url(r['Job_URL'], platform)}")
        return
    if not todo:
        return

    from playwright.sync_api import sync_playwright

    auto = "--auto-submit" in args
    done = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        for i, (row, platform) in enumerate(todo, 1):
            url = apply_url(row["Job_URL"], platform)
            log(f"[{i}/{len(todo)}] #{row['Application_ID']} {row['Company']} — {row['Job_Title']}")
            try:
                page.goto(url, timeout=45000)
            except Exception as e:
                log(f"   could not open {url}: {e}")
                continue
            if page.locator("form").count() == 0:
                log("   no application form found (posting may be closed) — skipped")
                continue

            missing = fill_form(page, app, row)
            captcha = has_captcha(page)
            if missing:
                log(f"   left for you: {', '.join(missing)[:300]}")

            if auto and not missing and not captcha:
                start = page.url
                click_submit(page)
                time.sleep(5)
                ok = submitted(page, start)
            else:
                if auto:
                    log("   needs you: " + ("captcha" if captcha else "required questions"))
                answer = input("   Check the form and click Submit in the browser, then press Enter (s = skip, q = quit): ").strip().lower()
                if answer == "q":
                    break
                if answer == "s":
                    log("   skipped")
                    continue
                ok = True if submitted(page, url) else input("   Did it submit? [y/N]: ").strip().lower() == "y"

            if ok:
                mark_applied(row["Application_ID"], app["email"])
                done += 1
                log("   ✅ marked Applied")
            else:
                log("   ⚠️  not confirmed as submitted — left as To Apply")
        browser.close()

    log(f"Done: {done} applied.")
    if done:
        try:
            from notify_replies import push_csv_to_github
            push_csv_to_github()
        except Exception as e:
            log(f"Could not push CSV: {e}")


if __name__ == "__main__":
    main()
