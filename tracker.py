#!/usr/bin/env python3
"""
Job Application Tracker CLI
Maintains and displays status of job applications and reverts.
"""
import csv
import sys
import os
import argparse
from datetime import datetime

TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_applications.csv")
FIELDNAMES = [
    "Application_ID",
    "Company",
    "Job_Title",
    "Location",
    "Target_CTC",
    "Job_URL",
    "Date_Applied",
    "Channel",
    "Sender_Email",
    "Status",
    "Reverted_Back",
    "Response_Date",
    "Notes"
]

def ensure_file():
    if not os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def load_applications():
    ensure_file()
    applications = []
    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            applications.append(row)
    return applications

def save_applications(applications):
    with open(TRACKER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(applications)

def add_application(company, title, location="Remote", url="", channel="Direct", notes=""):
    apps = load_applications()
    new_id = str(len(apps) + 1)
    today = datetime.now().strftime("%Y-%m-%d")
    
    app = {
        "Application_ID": new_id,
        "Company": company,
        "Job_Title": title,
        "Location": location,
        "Job_URL": url,
        "Date_Applied": today,
        "Channel": channel,
        "Sender_Email": "prajwathg@gmail.com",
        "Status": "Applied",
        "Reverted_Back": "No",
        "Response_Date": "",
        "Notes": notes
    }
    apps.append(app)
    save_applications(apps)
    print(f"Added #{new_id}: {company} - {title} ({channel})")
    return app

def update_response(app_id, status, reverted="Yes", notes=""):
    apps = load_applications()
    found = False
    for app in apps:
        if app["Application_ID"] == str(app_id):
            app["Status"] = status
            app["Reverted_Back"] = reverted
            app["Response_Date"] = datetime.now().strftime("%Y-%m-%d")
            if notes:
                app["Notes"] = (app["Notes"] + " | " + notes) if app["Notes"] else notes
            found = True
            print(f"Updated #{app_id}: {app['Company']} -> Status: {status}, Reverted: {reverted}")
            break
    if not found:
        print(f"Error: Application ID {app_id} not found.")
    else:
        save_applications(apps)

def summary():
    apps = load_applications()
    total = len(apps)
    reverted_count = sum(1 for a in apps if a.get("Reverted_Back", "").lower() in ["yes", "true", "1"])
    
    status_counts = {}
    for a in apps:
        st = a.get("Status", "Unknown")
        status_counts[st] = status_counts.get(st, 0) + 1

    print("==================================================")
    print("            JOB APPLICATION TRACKER               ")
    print("==================================================")
    print(f" Total Applications Sent:   {total}")
    print(f" Companies Reverted Back:   {reverted_count}")
    if total > 0:
        revert_rate = (reverted_count / total) * 100
        print(f" Response Rate:             {revert_rate:.1f}%")
    print("--------------------------------------------------")
    print(" Status Breakdown:")
    for status, count in status_counts.items():
        print(f"   - {status:<15} : {count}")
    print("==================================================")

    if total > 0:
        print("\nRecent Applications:")
        print(f"{'ID':<4} {'Date':<11} {'Company':<20} {'Role':<22} {'Status':<12} {'Reverted':<8}")
        print("-" * 80)
        for a in apps[-10:]:
            print(f"{a['Application_ID']:<4} {a['Date_Applied']:<11} {a['Company'][:18]:<20} {a['Job_Title'][:20]:<22} {a['Status']:<12} {a['Reverted_Back']:<8}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Job Application Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # summary
    subparsers.add_parser("summary", help="Show summary of applications and reverts")

    # add
    add_p = subparsers.add_parser("add", help="Add a new application")
    add_p.add_argument("--company", required=True, help="Company name")
    add_p.add_argument("--title", required=True, help="Job title")
    add_p.add_argument("--location", default="Remote", help="Location")
    add_p.add_argument("--url", default="", help="Job posting URL")
    add_p.add_argument("--channel", default="Email", help="Application channel (Email, LinkedIn, Greenhouse, etc.)")
    add_p.add_argument("--notes", default="", help="Additional notes")

    # respond
    resp_p = subparsers.add_parser("respond", help="Update response from a company")
    resp_p.add_argument("--id", required=True, help="Application ID")
    resp_p.add_argument("--status", required=True, help="New status (Interview, Screen, Rejected, Offer, etc.)")
    resp_p.add_argument("--reverted", default="Yes", help="Did they revert? (Yes/No)")
    resp_p.add_argument("--notes", default="", help="Notes from conversation/revert")

    args = parser.parse_args()
    if args.command == "add":
        add_application(args.company, args.title, args.location, args.url, args.channel, args.notes)
    elif args.command == "respond":
        update_response(args.id, args.status, args.reverted, args.notes)
    else:
        summary()

if __name__ == "__main__":
    main()
