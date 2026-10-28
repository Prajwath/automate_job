#!/usr/bin/env python3
"""
Find new hybrid Bangalore roles for 1-4 years of experience and add them to
job_applications.csv as "To Apply".

Reads the public job-board APIs of the companies in companies.txt (Greenhouse,
Lever and Ashby, no login needed), keeps roles that:
  - are in Bangalore / Bengaluru and hybrid,
  - match your target roles (Python, backend, full stack, AI/ML, GenAI, data),
  - ask for at most MAX_YEARS years of experience (and aren't Senior/Staff/Lead),
and skips anything already in the tracker.

Usage:
    python3 discover_jobs.py            # add new roles
    python3 discover_jobs.py --dry-run  # only list what would be added
"""

import os
import re
import csv
import sys
import json
import html
import urllib.request

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
COMPANIES_FILE = os.path.join(ROOT_DIR, "companies.txt")

MIN_YEARS, MAX_YEARS = 1, 4
CITY = re.compile(r"bangalore|bengaluru", re.I)
ROLE = re.compile(r"python|backend|back-end|full[ -]?stack|software (engineer|developer)|\bsde\b|\bai\b|\bml\b|machine learning|"
                  r"\bllm\b|gen ?ai|generative|nlp|data scien|applied scien|automation", re.I)
TOO_SENIOR = re.compile(r"\b(senior|sr\.?|staff|principal|lead|manager|director|head|architect|vp|chief|intern|internship)\b", re.I)
NOT_ROLE = re.compile(r"\b(sales|account executive|recruit|marketing|android|ios|designer|support|finance|legal)\b", re.I)
YEARS_RANGE = re.compile(r"(\d{1,2})\s*(?:\+\s*)?(?:-|–|to)\s*(\d{1,2})\s*\+?\s*(?:years|yrs)", re.I)
YEARS_MIN = re.compile(r"(?:(\d{1,2})\s*\+\s*(?:years|yrs))|(?:(?:at least|minimum of|minimum|min\.?)\s*(\d{1,2})\s*(?:years|yrs))|(?:(\d{1,2})\s*(?:years|yrs)\s*(?:of\s*)?(?:\w+\s){0,4}experience)", re.I)


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "job-tracker/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def plain(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def min_years_required(text):
    """Smallest 'years of experience' the posting asks for, or None if it doesn't say."""
    found = [int(a) for a, _ in YEARS_RANGE.findall(text)]
    for groups in YEARS_MIN.findall(text):
        found += [int(g) for g in groups if g]
    found = [y for y in found if 0 < y < 25]
    return min(found) if found else None


def greenhouse(token):
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    for j in data.get("jobs", []):
        content = plain(j.get("content"))
        location = (j.get("location") or {}).get("name", "")
        yield {
            "company": data.get("name") or token, "title": j.get("title", ""), "url": j.get("absolute_url", ""),
            "location": location, "text": content, "channel": "Greenhouse",
            "hybrid": bool(re.search(r"hybrid", location + " " + content[:3000], re.I)),
        }


def lever(token):
    for j in fetch_json(f"https://api.lever.co/v0/postings/{token}?mode=json"):
        cats = j.get("categories") or {}
        location = " / ".join(cats.get("allLocations") or [cats.get("location", "")])
        yield {
            "company": token, "title": j.get("text", ""), "url": j.get("hostedUrl", ""),
            "location": location, "text": plain(j.get("descriptionPlain") or j.get("description")), "channel": "Lever",
            "hybrid": (j.get("workplaceType") or "").lower() == "hybrid",
        }


def ashby(token):
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{token}")
    for j in data.get("jobs", []):
        locs = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        yield {
            "company": token, "title": j.get("title", ""), "url": j.get("jobUrl", ""),
            "location": " / ".join(l for l in locs if l), "text": plain(j.get("descriptionPlain") or j.get("descriptionHtml")),
            "channel": "Ashby", "hybrid": (j.get("workplaceType") or "").lower() == "hybrid",
        }


SOURCES = {"greenhouse": greenhouse, "lever": lever, "ashby": ashby}


def load_companies():
    """companies.txt lines look like 'greenhouse okta  # Okta'."""
    out = []
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        for line in f:
            line, _, name = line.partition("#")
            if line.strip():
                platform, token = line.split()[:2]
                out.append((platform.lower(), token, name.strip() or token))
    return out


def keep(job):
    """Returns a note for roles that fit, or None."""
    if not CITY.search(job["location"]) or not job["hybrid"]:
        return None
    title = job["title"]
    if not ROLE.search(title) or TOO_SENIOR.search(title) or NOT_ROLE.search(title):
        return None
    years = min_years_required(job["text"])
    if years is not None and not (MIN_YEARS - 1 <= years <= MAX_YEARS):
        return None
    return f"Good fit: {years}+ yrs asked" if years is not None else "Good fit: experience not stated"


def main():
    dry = "--dry-run" in sys.argv
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames, rows = reader.fieldnames, list(reader)
    known_urls = {r["Job_URL"].rstrip("/") for r in rows}
    known_roles = {(r["Company"].lower(), r["Job_Title"].lower()) for r in rows}
    next_id = max([int(r["Application_ID"]) for r in rows] or [0]) + 1

    added = []
    for platform, token, name in load_companies():
        try:
            jobs = list(SOURCES[platform](token))
            for job in jobs:
                job["company"] = name
        except Exception as e:
            print(f"  ! {platform}/{token}: {e}")
            continue
        for job in jobs:
            note = keep(job)
            if not note or job["url"].rstrip("/") in known_urls or (job["company"].lower(), job["title"].lower()) in known_roles:
                continue
            known_urls.add(job["url"].rstrip("/"))
            added.append({
                "Application_ID": str(next_id), "Company": job["company"], "Job_Title": job["title"],
                "Location": "Bangalore, India (Hybrid)", "Target_CTC": "12 - 15 LPA", "Job_URL": job["url"],
                "Date_Applied": "", "Channel": job["channel"], "Sender_Email": "", "Status": "To Apply",
                "Reverted_Back": "No", "Response_Date": "", "Notes": note,
            })
            next_id += 1

    for a in added:
        print(f"  + #{a['Application_ID']} {a['Company']} — {a['Job_Title']} ({a['Notes']})")
    print(f"{len(added)} new role(s) found")
    if added and not dry:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows + added)
    return added


if __name__ == "__main__":
    main()
