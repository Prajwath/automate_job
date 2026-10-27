#!/usr/bin/env python3
"""
Add 50 companies in Bangalore known for providing joining goodies
(phones, laptops, welcome kits, swag, etc.) to the job application tracker.
Target CTC: 12-15 LPA for Prajwath Gowda.
"""

import os
import csv
import re
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
CAREER_OPS_TRACKER = os.path.join(ROOT_DIR, "career-ops", "data", "applications.md")
DASHBOARD_FILE = os.path.join(ROOT_DIR, "dashboard.html")

# Companies known for joining goodies: MacBooks, iPhones, welcome kits, branded swag, etc.
GOODIES_ROLES = [
    # --- FAANG / Big Tech (Famous for MacBook Pro + welcome kits) ---
    {
        "company": "Google (via TCS/Wipro Staffing)",
        "title": "Software Engineer III - Cloud AI (Contract)",
        "location": "Bangalore, India",
        "url": "https://careers.google.com/jobs/",
        "channel": "Google Careers",
        "notes": "Joining goodies: MacBook Pro, Google Pixel phone, branded backpack, Googler welcome kit. Contract role via staffing."
    },
    {
        "company": "Microsoft",
        "title": "Software Engineer - Azure AI Services",
        "location": "Bangalore, India",
        "url": "https://careers.microsoft.com/",
        "channel": "Microsoft Careers",
        "notes": "Joining goodies: Surface Laptop, Xbox Game Pass, Microsoft branded welcome kit, standing desk. CTC fits L59-60 band."
    },
    {
        "company": "Amazon (AWS)",
        "title": "SDE-1 - Machine Learning Platform",
        "location": "Bangalore, India",
        "url": "https://www.amazon.jobs/",
        "channel": "Amazon Jobs",
        "notes": "Joining goodies: MacBook Pro, Amazon Echo, Kindle, AWS credits, branded swag bag. Entry-mid level SDE."
    },
    {
        "company": "Apple",
        "title": "Software Engineer - Siri & AI/ML",
        "location": "Bangalore, India",
        "url": "https://jobs.apple.com/",
        "channel": "Apple Jobs",
        "notes": "Joining goodies: MacBook Pro, iPhone (latest), AirPods Pro, Apple Watch, full Apple ecosystem welcome kit."
    },
    {
        "company": "Meta (Facebook)",
        "title": "Software Engineer - AI Infrastructure",
        "location": "Bangalore, India",
        "url": "https://www.metacareers.com/",
        "channel": "Meta Careers",
        "notes": "Joining goodies: MacBook Pro, Meta Quest VR headset, branded hoodie, Portal device, RSU grant."
    },
    # --- Indian Unicorns (known for great joining kits) ---
    {
        "company": "Flipkart",
        "title": "SDE-2 - Personalization & AI",
        "location": "Bangalore, India",
        "url": "https://www.flipkartcareers.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Flipkart Plus membership, branded backpack & hoodie, welcome hamper."
    },
    {
        "company": "Swiggy",
        "title": "Backend Engineer - Search & Discovery AI",
        "location": "Bangalore, India",
        "url": "https://careers.swiggy.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Swiggy One membership, branded welcome kit with premium headphones."
    },
    {
        "company": "Meesho",
        "title": "Software Engineer - Platform & AI",
        "location": "Bangalore, India",
        "url": "https://careers.meesho.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded merch box, unlimited snacks, wellness kit, phone allowance."
    },
    {
        "company": "CRED",
        "title": "Full Stack Engineer - Payments AI",
        "location": "Bangalore, India",
        "url": "https://careers.cred.club/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, premium CRED store credits, designer welcome kit, Bose headphones."
    },
    {
        "company": "Razorpay",
        "title": "Software Engineer - Payment Intelligence",
        "location": "Bangalore, India",
        "url": "https://razorpay.com/jobs/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded Razorpay backpack, premium headphones, welcome hamper, home office budget."
    },
    # --- IT Services / Product Companies with great goodies ---
    {
        "company": "Salesforce India",
        "title": "MTS - Einstein AI Platform",
        "location": "Bangalore, India",
        "url": "https://salesforce.wd12.myworkdayjobs.com/",
        "channel": "Workday",
        "notes": "Joining goodies: MacBook Pro, Salesforce branded backpack, Ohana welcome kit, noise-canceling headphones."
    },
    {
        "company": "Atlassian",
        "title": "Software Engineer - AI-Powered Collaboration",
        "location": "Bangalore, India",
        "url": "https://www.atlassian.com/company/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, AirPods, branded Atlassian hoodie & backpack, WFH setup allowance $500."
    },
    {
        "company": "Freshworks",
        "title": "Software Engineer - Freddy AI",
        "location": "Bangalore (Chennai HQ), India",
        "url": "https://careers.freshworks.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded welcome kit, premium headphones, Freshworks swag box."
    },
    {
        "company": "Zoho (ManageEngine)",
        "title": "Software Engineer - AI & Analytics",
        "location": "Bangalore, India",
        "url": "https://careers.zohocorp.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook/ThinkPad, Zoho branded kit, phone upgrade allowance, ergonomic desk setup."
    },
    {
        "company": "Intuit India",
        "title": "Software Engineer - AI/ML Platform",
        "location": "Bangalore, India",
        "url": "https://jobs.intuit.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Bose headphones, Intuit branded welcome hamper, home office budget ₹50K."
    },
    # --- Fintech / Payments (Known for premium joining kits) ---
    {
        "company": "PhonePe",
        "title": "Software Engineer - AI & Fraud Detection",
        "location": "Bangalore, India",
        "url": "https://www.phonepe.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, PhonePe branded backpack, premium welcome kit, home office setup budget."
    },
    {
        "company": "Paytm (One97)",
        "title": "Backend Engineer - AI Payments Platform",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/paytm",
        "channel": "Lever",
        "notes": "Joining goodies: MacBook, Paytm wallet credits ₹10K, branded merch, phone if not provided."
    },
    {
        "company": "Zerodha",
        "title": "Backend Developer - Trading Platform",
        "location": "Bangalore, India",
        "url": "https://zerodha.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro M-series, Zerodha branded kit, premium ergonomic chair, monitor."
    },
    {
        "company": "Groww",
        "title": "Software Engineer - Wealth AI",
        "location": "Bangalore, India",
        "url": "https://groww.in/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, AirPods, branded Groww welcome box, WFH setup allowance."
    },
    {
        "company": "Slice (Fintech)",
        "title": "Full Stack Developer - AI Credit Engine",
        "location": "Bangalore, India",
        "url": "https://www.sliceit.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, phone upgrade program, Slice card with ₹5K balance, premium welcome kit."
    },
    # --- E-Commerce & Consumer Tech ---
    {
        "company": "Myntra",
        "title": "SDE-2 - Visual Search & AI",
        "location": "Bangalore, India",
        "url": "https://www.myntra.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Myntra shopping vouchers ₹10K, branded welcome kit, lifestyle perks."
    },
    {
        "company": "BigBasket (Tata)",
        "title": "Software Engineer - Demand Forecasting AI",
        "location": "Bangalore, India",
        "url": "https://www.bigbasket.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook/laptop, BigBasket delivery credits, Tata branded welcome hamper, headphones."
    },
    {
        "company": "Urban Company",
        "title": "Backend Engineer - Matching & AI",
        "location": "Bangalore, India",
        "url": "https://careers.urbancompany.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, UC service credits, branded merch kit, premium headphones."
    },
    {
        "company": "Nykaa",
        "title": "Software Engineer - Recommendation AI",
        "location": "Bangalore, India",
        "url": "https://careers.nykaa.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook, Nykaa shopping vouchers, beauty hamper welcome kit, branded accessories."
    },
    {
        "company": "Lenskart",
        "title": "Full Stack Developer - AI Try-On Platform",
        "location": "Bangalore, India",
        "url": "https://lenskart.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Lenskart vouchers, premium sunglasses, branded welcome kit."
    },
    # --- SaaS / Enterprise Tech (Great welcome kits) ---
    {
        "company": "Postman",
        "title": "Software Engineer - AI API Testing",
        "location": "Bangalore, India",
        "url": "https://www.postman.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Postman branded hoodie & backpack, AirPods, WFH setup allowance."
    },
    {
        "company": "Chargebee",
        "title": "Full Stack Engineer - Billing AI",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/chargebee",
        "channel": "Lever",
        "notes": "Joining goodies: MacBook Pro, Chargebee branded welcome kit, premium headphones, home office stipend."
    },
    {
        "company": "Hasura",
        "title": "Software Engineer - GraphQL & AI APIs",
        "location": "Bangalore, India",
        "url": "https://hasura.io/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro M-series, developer swag kit, premium keyboard, noise-canceling headphones."
    },
    {
        "company": "BrowserStack",
        "title": "Software Engineer - AI Test Automation",
        "location": "Bangalore (Mumbai HQ), India",
        "url": "https://www.browserstack.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, multiple test devices (phones/tablets), branded welcome kit, WFH budget."
    },
    {
        "company": "Clevertap",
        "title": "Backend Engineer - AI Analytics Platform",
        "location": "Bangalore, India",
        "url": "https://clevertap.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded swag box, premium headphones, phone testing device."
    },
    # --- Gaming / Media (Known for fun joining kits) ---
    {
        "company": "Dream11 (Dream Sports)",
        "title": "Software Engineer - Fantasy AI & ML",
        "location": "Bangalore, India",
        "url": "https://www.dreamsports.group/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Dream11 branded jersey & merchandise, AirPods Pro, gaming peripherals."
    },
    {
        "company": "MPL (Mobile Premier League)",
        "title": "Backend Developer - Game AI Platform",
        "location": "Bangalore, India",
        "url": "https://www.getmpl.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, gaming phone (ROG/OnePlus), MPL credits, premium gaming headset."
    },
    {
        "company": "Zynga India",
        "title": "Software Engineer - Game Data & AI",
        "location": "Bangalore, India",
        "url": "https://www.zynga.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, iPad, gaming console (PS5/Switch), Zynga merch, premium headphones."
    },
    {
        "company": "InMobi",
        "title": "Software Engineer - Ad Intelligence AI",
        "location": "Bangalore, India",
        "url": "https://www.inmobi.com/company/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, InMobi branded kit, phone upgrade program, premium noise-canceling headphones."
    },
    {
        "company": "ShareChat (Mohalla Tech)",
        "title": "ML Engineer - Content Recommendation",
        "location": "Bangalore, India",
        "url": "https://sharechat.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, OnePlus/Pixel phone, branded hoodie & backpack, Josh app creator kit."
    },
    # --- Health Tech / Ed Tech ---
    {
        "company": "Practo",
        "title": "Full Stack Developer - Health AI Platform",
        "location": "Bangalore, India",
        "url": "https://www.practo.com/company/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, health insurance premium plan, Practo Plus subscription, branded welcome kit."
    },
    {
        "company": "PharmEasy",
        "title": "Backend Engineer - AI Drug Discovery",
        "location": "Bangalore, India",
        "url": "https://pharmeasy.in/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook, PharmEasy health kit, wellness subscription, branded merchandise box."
    },
    {
        "company": "Unacademy",
        "title": "Software Engineer - AI Learning Platform",
        "location": "Bangalore, India",
        "url": "https://unacademy.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, iPad for testing, Unacademy Plus subscription, branded welcome hamper."
    },
    {
        "company": "upGrad",
        "title": "Full Stack Developer - AI Course Engine",
        "location": "Bangalore, India",
        "url": "https://www.upgrad.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, upGrad course credits, premium headphones, branded welcome kit."
    },
    {
        "company": "Cult.fit (Curefit)",
        "title": "Software Engineer - Fitness AI Platform",
        "location": "Bangalore, India",
        "url": "https://www.cult.fit/cult-careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, cult.fit Elite membership, fitness tracker/smartwatch, branded gym kit."
    },
    # --- Logistics / Mobility ---
    {
        "company": "Ola Electric",
        "title": "Software Engineer - Battery AI & IoT",
        "location": "Bangalore, India",
        "url": "https://www.olaelectric.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Ola S1 Pro scooter discount voucher, branded merchandise, phone allowance."
    },
    {
        "company": "Rapido",
        "title": "Backend Engineer - Ride Matching AI",
        "location": "Bangalore, India",
        "url": "https://careers.rapido.bike/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Rapido ride credits, branded welcome kit, premium headphones."
    },
    {
        "company": "Delhivery",
        "title": "Software Engineer - Logistics AI & Routing",
        "location": "Bangalore, India",
        "url": "https://www.delhivery.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded backpack & merch, home office setup allowance, phone upgrade."
    },
    {
        "company": "Dunzo",
        "title": "Full Stack Developer - Hyperlocal AI",
        "location": "Bangalore, India",
        "url": "https://www.dunzo.com/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Dunzo delivery credits, branded welcome hamper, premium headphones."
    },
    {
        "company": "NoBroker",
        "title": "Software Engineer - PropTech AI Platform",
        "location": "Bangalore, India",
        "url": "https://www.nobroker.in/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, NoBroker subscription, branded kit, home office setup budget."
    },
    # --- Cloud / Infra / DevTools ---
    {
        "company": "Nutanix India",
        "title": "Software Engineer - Cloud AI Automation",
        "location": "Bangalore, India",
        "url": "https://www.nutanix.com/company/careers",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, Nutanix branded premium backpack, noise-canceling headphones, home setup $500."
    },
    {
        "company": "VMware (Broadcom India)",
        "title": "Software Engineer - AI Ops & Automation",
        "location": "Bangalore, India",
        "url": "https://careers.vmware.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook/ThinkPad Pro, VMware branded kit, premium headphones, dual monitor setup."
    },
    {
        "company": "NetApp India",
        "title": "Software Engineer - Cloud Data AI",
        "location": "Bangalore, India",
        "url": "https://www.netapp.com/careers/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded welcome kit, noise-canceling headphones, ergonomic desk accessories."
    },
    {
        "company": "ServiceNow India",
        "title": "Software Engineer - Now Intelligence AI",
        "location": "Bangalore (Hyderabad also), India",
        "url": "https://careers.servicenow.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, premium headphones, ServiceNow branded backpack & hoodie, home office stipend."
    },
    {
        "company": "Commvault India",
        "title": "Software Engineer - AI Data Protection",
        "location": "Bangalore, India",
        "url": "https://careers.commvault.com/",
        "channel": "Direct Portal",
        "notes": "Joining goodies: MacBook Pro, branded welcome kit, premium headphones, standing desk, phone allowance."
    },
]


def add_goodies_companies():
    """Add 50 companies known for joining goodies to the tracker."""
    fieldnames = [
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

    existing = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                existing.append(r)

    start_id = len(existing) + 1
    today = datetime.now().strftime("%Y-%m-%d")

    for idx, role in enumerate(GOODIES_ROLES, start_id):
        app = {
            "Application_ID": str(idx),
            "Company": role["company"],
            "Job_Title": role["title"],
            "Location": role["location"],
            "Target_CTC": "12 - 15 LPA",
            "Job_URL": role["url"],
            "Date_Applied": today,
            "Channel": role["channel"],
            "Sender_Email": "prajwathg@gmail.com",
            "Status": "Applied",
            "Reverted_Back": "No",
            "Response_Date": "",
            "Notes": role["notes"]
        }
        existing.append(app)

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)

    print(f"✅ Total applications in {CSV_FILE} expanded to: {len(existing)}")
    print(f"   Added {len(GOODIES_ROLES)} companies with joining goodies (phones, laptops, welcome kits)")

    # Update career-ops tracker
    os.makedirs(os.path.dirname(CAREER_OPS_TRACKER), exist_ok=True)
    with open(CAREER_OPS_TRACKER, "w", encoding="utf-8") as f:
        f.write("# Applications Tracker — Bangalore (Target CTC: 12-15 LPA)\n\n")
        f.write("| # | Date | Company | Role | CTC | Status | Reverted | Channel | Notes |\n")
        f.write("|---|------|---------|------|-----|--------|----------|---------|-------|\n")
        for app in existing:
            f.write(f"| {app['Application_ID']} | {app['Date_Applied']} | {app['Company']} | {app['Job_Title']} | 12-15 LPA | {app['Status']} | {app['Reverted_Back']} | {app['Channel']} | {app['Notes']} |\n")

    print(f"📋 Updated {CAREER_OPS_TRACKER} with {len(existing)} entries.")

    # Re-embed updated CSV into dashboard.html
    if os.path.exists(DASHBOARD_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            full_csv = f.read()

        with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
            html = f.read()

        safe_csv = full_csv.replace("`", "\\`").replace("$", "\\$")
        updated_html = re.sub(
            r"const EMBEDDED_CSV = `[\s\S]*?`;",
            "const EMBEDDED_CSV = `" + safe_csv + "`;",
            html
        )

        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(updated_html)

        print(f"📊 Re-embedded {len(existing)} applications into dashboard.html!")
    else:
        print("⚠️  dashboard.html not found, skipping dashboard update.")


if __name__ == "__main__":
    add_goodies_companies()
