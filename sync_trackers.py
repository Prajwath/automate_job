#!/usr/bin/env python3
"""
Sync bridge between career-ops markdown tracker and job_applications.csv / dashboard.
"""
import os
import re
import csv
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
CAREER_OPS_TRACKER = os.path.join(ROOT_DIR, "career-ops", "data", "applications.md")
CAREER_OPS_STATUS_LOG = os.path.join(ROOT_DIR, "career-ops", "data", "status-log.tsv")

def parse_markdown_table(md_path):
    if not os.path.exists(md_path):
        return []
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    rows = []
    header_found = False
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if not parts:
            continue
        if parts[0] in ["#", "Num"] or "Date" in parts:
            header_found = True
            continue
        if parts[0].startswith("---"):
            continue
        if header_found and len(parts) >= 6:
            # [# , Date, Company, Role, Score, Status, PDF, Report, Notes]
            num = parts[0]
            date_applied = parts[1] if len(parts) > 1 else ""
            company = parts[2] if len(parts) > 2 else ""
            role = parts[3] if len(parts) > 3 else ""
            score = parts[4] if len(parts) > 4 else ""
            status = parts[5] if len(parts) > 5 else "Applied"
            notes = parts[8] if len(parts) > 8 else ""
            
            reverted = "Yes" if status.lower() in ["interview", "screen", "screening", "offer", "reverted", "accepted"] or "revert" in notes.lower() else "No"
            rows.append({
                "Application_ID": num,
                "Company": company,
                "Job_Title": role,
                "Location": "Remote / India",
                "Job_URL": "",
                "Date_Applied": date_applied,
                "Channel": "career-ops",
                "Sender_Email": "prajwathg@gmail.com",
                "Status": status,
                "Reverted_Back": reverted,
                "Response_Date": date_applied if reverted == "Yes" else "",
                "Notes": f"Score: {score} | {notes}".strip(" |")
            })
    return rows

def sync():
    csv_rows = []
    fieldnames = [
        "Application_ID", "Company", "Job_Title", "Location", "Target_CTC", "Job_URL",
        "Date_Applied", "Channel", "Sender_Email", "Status",
        "Reverted_Back", "Response_Date", "Notes"
    ]
    
    existing_ids = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                csv_rows.append(r)
                existing_ids.add(r.get("Application_ID"))
    
    md_rows = parse_markdown_table(CAREER_OPS_TRACKER)
    added = 0
    updated = 0
    
    for m in md_rows:
        m_id = m["Application_ID"]
        found = False
        for c in csv_rows:
            if c.get("Application_ID") == m_id:
                # Update status if changed
                if c.get("Status") != m["Status"]:
                    c["Status"] = m["Status"]
                    if m["Reverted_Back"] == "Yes":
                        c["Reverted_Back"] = "Yes"
                    updated += 1
                found = True
                break
        if not found:
            csv_rows.append(m)
            added += 1
            
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
        
    print(f"Sync complete: {added} new rows added, {updated} rows updated. Total in CSV: {len(csv_rows)}")

if __name__ == "__main__":
    sync()
