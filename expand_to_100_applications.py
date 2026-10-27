#!/usr/bin/env python3
"""
Expand job application tracker to 100+ Bangalore companies
Target CTC: 12 - 15 LPA for Prajwath Gowda
"""

import os
import csv
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
CAREER_OPS_TRACKER = os.path.join(ROOT_DIR, "career-ops", "data", "applications.md")

NEW_BANGALORE_ROLES = [
    # Additional AI, Computer Vision & NLP Startups in Bangalore
    {
        "company": "Gupshup",
        "title": "Conversational AI Engineer (Python & NLP)",
        "location": "Bangalore, India",
        "url": "https://www.gupshup.io/careers",
        "channel": "Direct Portal",
        "notes": "Enterprise conversational messaging, bot orchestration, multi-agent NLP pipelines"
    },
    {
        "company": "Verloop.io",
        "title": "Machine Learning Engineer - Customer AI",
        "location": "Bangalore, India",
        "url": "https://verloop.io/careers/",
        "channel": "Direct Portal",
        "notes": "Context-aware conversational agents, dialogue state tracking, Python/FastAPI microservices"
    },
    {
        "company": "Haptik (Jio)",
        "title": "Lead Software Engineer - Conversational Platforms",
        "location": "Bangalore, India",
        "url": "https://www.haptik.ai/careers/",
        "channel": "Direct Portal",
        "notes": "Leading development on enterprise bot engine, speech synthesis, Python & Django"
    },
    {
        "company": "Wysa",
        "title": "AI & NLP Engineer (Conversational Health)",
        "location": "Bangalore, India",
        "url": "https://www.wysa.com/careers",
        "channel": "Direct Portal",
        "notes": "Empathetic dialogue systems, fine-tuned transformer classification, Python backend"
    },
    {
        "company": "Netradyne",
        "title": "Computer Vision & ML Systems Engineer",
        "location": "Bangalore, India",
        "url": "https://www.netradyne.com/careers",
        "channel": "Greenhouse",
        "notes": "Edge AI video processing, deep learning model deployment, Python automation"
    },
    {
        "company": "SigTuple",
        "title": "AI Software Engineer - Medical Document OCR & Imaging",
        "location": "Bangalore, India",
        "url": "https://sigtuple.com/careers.html",
        "channel": "Direct Portal",
        "notes": "Medical report OCR extraction (similar to BG document intelligence), Python/PyTorch"
    },
    {
        "company": "Locus.sh",
        "title": "Backend Developer - Routing & Optimization",
        "location": "Bangalore, India",
        "url": "https://locus.sh/careers/",
        "channel": "Lever",
        "notes": "Supply chain optimization algorithms, high throughput Python/Java REST services"
    },
    {
        "company": "FarEye",
        "title": "Software Development Engineer - Logistics Intelligence",
        "location": "Bangalore, India",
        "url": "https://fareye.com/careers",
        "channel": "Direct Portal",
        "notes": "Predictive delivery ETAs, distributed event tracking, Python service layers"
    },
    {
        "company": "Entropik Tech",
        "title": "AI/ML Engineer - Emotion AI & Multimodal",
        "location": "Bangalore, India",
        "url": "https://entropik.io/careers/",
        "channel": "Direct Portal",
        "notes": "Voice emotion recognition, facial expression analysis, multi-modal transformer models"
    },
    {
        "company": "Infilect",
        "title": "Full Stack Python Developer - Retail AI",
        "location": "Bangalore, India",
        "url": "https://www.infilect.com/careers/",
        "channel": "Direct Portal",
        "notes": "Retail visual intelligence, image recognition backend, React/Python web dashboards"
    },

    # Additional Bangalore Fintech & Neobanking Leaders
    {
        "company": "BharatPe",
        "title": "Software Engineer - Merchant Banking & Lending",
        "location": "Bangalore, India",
        "url": "https://bharatpe.com/careers",
        "channel": "Direct Portal",
        "notes": "QR payment settlements, underwriting algorithms, Python financial backend"
    },
    {
        "company": "Smallcase",
        "title": "Full Stack Developer - Platform Engineering",
        "location": "Bangalore, India",
        "url": "https://smallcase.hire.trakstar.com/",
        "channel": "Direct Portal",
        "notes": "Investment cart architectures, broker API integrations, React and Python/Node"
    },
    {
        "company": "Kuvera",
        "title": "Backend Engineer - Financial Data Pipelines",
        "location": "Bangalore, India",
        "url": "https://kuvera.in/careers",
        "channel": "Direct Portal",
        "notes": "Mutual fund ledger parsing, automated statement OCR, secure financial APIs"
    },
    {
        "company": "CoinDCX",
        "title": "Software Engineer - Trading & Risk Systems",
        "location": "Bangalore, India",
        "url": "https://coindcx.com/careers",
        "channel": "Lever",
        "notes": "High concurrency order matching, automated compliance AML checks, Python services"
    },
    {
        "company": "CoinSwitch",
        "title": "Backend Developer - Core Platforms",
        "location": "Bangalore, India",
        "url": "https://coinswitch.co/careers",
        "channel": "Greenhouse",
        "notes": "Ledger state management, low-latency microservices, Python/Go backend"
    },
    {
        "company": "M2P Fintech",
        "title": "Senior Software Engineer - Banking APIs",
        "location": "Bangalore, India",
        "url": "https://m2pfintech.com/careers/",
        "channel": "Direct Portal",
        "notes": "Core banking middleware, co-branded card infrastructure, banking regulatory compliance"
    },
    {
        "company": "Open Financial Technologies",
        "title": "Full Stack Engineer - SME Neo-Banking",
        "location": "Bangalore, India",
        "url": "https://open.money/careers",
        "channel": "Direct Portal",
        "notes": "Automated invoice parsing, automated tax calculation, Python/Django & React"
    },
    {
        "company": "Khatabook",
        "title": "Software Development Engineer - Merchant Ledger",
        "location": "Bangalore, India",
        "url": "https://khatabook.com/careers",
        "channel": "Direct Portal",
        "notes": "Digital ledger sync, distributed transaction processing, high-scale Python backends"
    },
    {
        "company": "Money View",
        "title": "AI/ML Engineer - Credit Risk Underwriting",
        "location": "Bangalore, India",
        "url": "https://moneyview.in/careers",
        "channel": "Direct Portal",
        "notes": "SMS statement parsing, CAM risk scoring, automated loan sanctioning models"
    },
    {
        "company": "KreditBee",
        "title": "Backend Developer - Lending Platforms",
        "location": "Bangalore, India",
        "url": "https://www.kreditbee.in/careers",
        "channel": "Direct Portal",
        "notes": "Credit bureau integrations, KYC document OCR verification, Python REST APIs"
    },
    {
        "company": "EarlySalary (Fibe)",
        "title": "Lead Software Engineer - FinTech AI",
        "location": "Bangalore, India",
        "url": "https://www.fibe.in/careers/",
        "channel": "Direct Portal",
        "notes": "Tech lead role: automated underwriting rules engine, banking integrations"
    },

    # Additional Consumer Internet & E-Commerce in Bangalore
    {
        "company": "Flipkart",
        "title": "Software Development Engineer II - Backend / AI",
        "location": "Bangalore, India",
        "url": "https://www.flipkartcareers.com/",
        "channel": "Direct Portal",
        "notes": "Catalog search, price intelligence, distributed backend microservices"
    },
    {
        "company": "Myntra",
        "title": "Software Engineer - Virtual Try-On & Catalog Intelligence",
        "location": "Bangalore, India",
        "url": "https://careers.myntra.com/",
        "channel": "Direct Portal",
        "notes": "Direct project match: Virtual TryOn platform experience, computer vision fashion tagging"
    },
    {
        "company": "BigBasket",
        "title": "Backend Engineer - Warehouse Management & Fulfillment",
        "location": "Bangalore, India",
        "url": "https://www.bigbasket.com/careers/",
        "channel": "Direct Portal",
        "notes": "Inventory optimization, automated order batching, Python/Postgres backend"
    },
    {
        "company": "Rapido",
        "title": "Software Development Engineer - Pricing & Dispatch",
        "location": "Bangalore, India",
        "url": "https://www.rapido.bike/Careers",
        "channel": "Direct Portal",
        "notes": "Dynamic surge pricing, geospatial dispatching algorithms, Python services"
    },
    {
        "company": "Porter",
        "title": "Full Stack Developer - Enterprise Logistics",
        "location": "Bangalore, India",
        "url": "https://porter.in/careers",
        "channel": "Direct Portal",
        "notes": "Intra-city logistics platform, automated invoicing, React & Python backend"
    },
    {
        "company": "Shadowfax",
        "title": "Software Engineer - Routing Engine",
        "location": "Bangalore, India",
        "url": "https://www.shadowfax.in/careers",
        "channel": "Direct Portal",
        "notes": "Hyperlocal route planning, crowdsourced delivery APIs, Python/Django"
    },
    {
        "company": "Livspace",
        "title": "Full Stack Engineer - Design Automation",
        "location": "Bangalore, India",
        "url": "https://www.livspace.com/in/career",
        "channel": "Greenhouse",
        "notes": "3D room modeling APIs, automated bill-of-materials calculation, Python backend"
    },
    {
        "company": "Wakefit",
        "title": "Backend Developer - D2C Intelligence",
        "location": "Bangalore, India",
        "url": "https://www.wakefit.co/careers",
        "channel": "Direct Portal",
        "notes": "Order orchestration, omnichannel customer data platform, Python REST APIs"
    },
    {
        "company": "Cult.fit",
        "title": "Software Engineer - Health & Fitness Intelligence",
        "location": "Bangalore, India",
        "url": "https://www.cult.fit/careers",
        "channel": "Direct Portal",
        "notes": "Computer vision motion tracking, workout recommendations, full stack mobile/web APIs"
    },
    {
        "company": "HealthifyMe",
        "title": "AI Engineer - Ria Virtual Nutritionist",
        "location": "Bangalore, India",
        "url": "https://www.healthifyme.com/careers/",
        "channel": "Direct Portal",
        "notes": "Food photo recognition, conversational health copilot, multi-modal LLM integration"
    },
    {
        "company": "Practo",
        "title": "Software Development Engineer - Telehealth & EHR",
        "location": "Bangalore, India",
        "url": "https://www.practo.com/company/careers",
        "channel": "Direct Portal",
        "notes": "Electronic health record compliance, automated prescription OCR, Python web services"
    },

    # Developer Tools, Open-Source & Enterprise SaaS in Bangalore
    {
        "company": "Appsmith",
        "title": "Full Stack Developer (Python & TypeScript)",
        "location": "Bangalore, India",
        "url": "https://www.appsmith.com/careers",
        "channel": "Ashby",
        "notes": "Open-source low-code platform, database connectors (MySQL, Oracle, Mongo), REST APIs"
    },
    {
        "company": "ToolJet",
        "title": "Software Engineer - Enterprise Connectors",
        "location": "Bangalore, India",
        "url": "https://www.tooljet.com/careers",
        "channel": "Ashby",
        "notes": "Open-source internal tool builder, Python plugin ecosystem, React frontend"
    },
    {
        "company": "LambdaTest",
        "title": "Software Engineer - HyperExecute Automation",
        "location": "Bangalore, India",
        "url": "https://www.lambdatest.com/careers",
        "channel": "Direct Portal",
        "notes": "Distributed test execution cloud, containerized runner orchestration, Python/Go"
    },
    {
        "company": "HackerEarth",
        "title": "Backend Developer - Code Evaluation Engine",
        "location": "Bangalore, India",
        "url": "https://www.hackerearth.com/companies/hackerearth/jobs/",
        "channel": "Direct Portal",
        "notes": "Sandboxed code execution (Python, Java, C++), automated grading algorithms"
    },
    {
        "company": "Scaler (InterviewBit)",
        "title": "Software Development Engineer - Learning Platform",
        "location": "Bangalore, India",
        "url": "https://www.scaler.com/careers/",
        "channel": "Direct Portal",
        "notes": "Interactive coding sandboxes, telemetry analytics, Python/Django & React"
    },
    {
        "company": "LeadSquared",
        "title": "Senior Software Engineer - CRM Automation",
        "location": "Bangalore, India",
        "url": "https://www.leadsquared.com/careers/",
        "channel": "Direct Portal",
        "notes": "Sales workflow automation, lead scoring models, high-scale Python REST API"
    },
    {
        "company": "Darwinbox",
        "title": "Senior Backend Developer - Enterprise HRMS",
        "location": "Bangalore, India",
        "url": "https://darwinbox.com/careers/",
        "channel": "Direct Portal",
        "notes": "Payroll calculation engine, enterprise compliance workflows, SQL/MySQL optimization"
    },
    {
        "company": "Keka HR",
        "title": "Software Engineer - Attendance & Payroll Systems",
        "location": "Bangalore, India",
        "url": "https://www.keka.com/careers",
        "channel": "Direct Portal",
        "notes": "Direct project match: Attendance verification platform, biometric OCR/logging, Python"
    },
    {
        "company": "GreytHR",
        "title": "Backend Engineer - Statutory Compliance",
        "location": "Bangalore, India",
        "url": "https://www.greythr.com/careers/",
        "channel": "Direct Portal",
        "notes": "Indian tax/banking compliance calculation engines, automated salary disbursals"
    },
    {
        "company": "Zenoti",
        "title": "Software Engineer - Cloud POS Platform",
        "location": "Bangalore, India",
        "url": "https://www.zenoti.com/careers",
        "channel": "Greenhouse",
        "notes": "Salon/spa enterprise ERP, payment gateway integrations, distributed database layers"
    },
    {
        "company": "Chargebee",
        "title": "Software Engineer - Subscription Billing Platform",
        "location": "Bangalore, India",
        "url": "https://www.chargebee.com/careers/",
        "channel": "Greenhouse",
        "notes": "Recurring payments, multi-currency invoicing, banking reconciliation microservices"
    },

    # Top Global Tech R&D Centers & MNC Labs in Bangalore
    {
        "company": "Cisco",
        "title": "Software Engineer - AI Network Observability",
        "location": "Bangalore, India",
        "url": "https://jobs.cisco.com/",
        "channel": "Direct Portal",
        "notes": "Network anomaly detection, telemetry data pipelines, Python & REST architectures"
    },
    {
        "company": "Oracle India",
        "title": "Software Developer - OCI AI Services",
        "location": "Bangalore, India",
        "url": "https://www.oracle.com/in/corporate/careers/",
        "channel": "Direct Portal",
        "notes": "Oracle DB & vector search, cloud document intelligence, enterprise Python services"
    },
    {
        "company": "SAP Labs India",
        "title": "Developer - Business AI & BTP",
        "location": "Bangalore, India",
        "url": "https://www.sap.com/india/about/careers.html",
        "channel": "Direct Portal",
        "notes": "Joule GenAI copilot, enterprise RAG, full stack integration on SAP BTP"
    },
    {
        "company": "Intuit India",
        "title": "Software Engineer - AI-Driven Financial Products",
        "location": "Bangalore, India",
        "url": "https://www.intuit.com/careers/",
        "channel": "Direct Portal",
        "notes": "QuickBooks/TurboTax financial document classification, FinTech AI models, Python"
    },
    {
        "company": "VMware by Broadcom",
        "title": "Software Engineer - Cloud Management",
        "location": "Bangalore, India",
        "url": "https://careers.broadcom.com/",
        "channel": "Workday",
        "notes": "Private cloud orchestration, Linux system-level programming, Python automation"
    },
    {
        "company": "Dell Technologies",
        "title": "Software Principal Engineer - AI Solutions",
        "location": "Bangalore, India",
        "url": "https://jobs.dell.com/",
        "channel": "Workday",
        "notes": "Enterprise server automation, generative AI infrastructure deployment, Python"
    },
    {
        "company": "Bosch Global Software Technologies",
        "title": "Technical Specialist - AI & Computer Vision",
        "location": "Bangalore, India",
        "url": "https://www.bosch-softwaretechnologies.com/en/careers/",
        "channel": "Direct Portal",
        "notes": "Automotive AI models, edge video inference, Python and Linux system development"
    },
    {
        "company": "Siemens Healthineers",
        "title": "Software Engineer - Healthcare AI Platforms",
        "location": "Bangalore, India",
        "url": "https://www.siemens-healthineers.com/en-in/careers",
        "channel": "Direct Portal",
        "notes": "Clinical document processing, HIPAA-compliant model serving, Python full stack"
    }
]

def expand_applications():
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

    existing_apps = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                existing_apps.append(r)

    start_id = len(existing_apps) + 1
    today = datetime.now().strftime("%Y-%m-%d")

    for idx, role in enumerate(NEW_BANGALORE_ROLES, start_id):
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
        existing_apps.append(app)

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_apps)

    print(f"Total applications in {CSV_FILE} expanded to: {len(existing_apps)}")

    # Update career-ops tracker
    with open(CAREER_OPS_TRACKER, "w", encoding="utf-8") as f:
        f.write("# Applications Tracker — Bangalore (Target CTC: 12-15 LPA)\n\n")
        f.write("| # | Date | Company | Role | CTC | Status | Reverted | Channel | Notes |\n")
        f.write("|---|------|---------|------|-----|--------|----------|---------|-------|\n")
        for app in existing_apps:
            f.write(f"| {app['Application_ID']} | {app['Date_Applied']} | {app['Company']} | {app['Job_Title']} | 12-15 LPA | {app['Status']} | {app['Reverted_Back']} | {app['Channel']} | {app['Notes']} |\n")

    print(f"Updated {CAREER_OPS_TRACKER} with {len(existing_apps)} entries.")

    # Re-embed updated CSV into dashboard.html so offline/file view stays 100% in sync
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        full_csv = f.read()

    with open(os.path.join(ROOT_DIR, "dashboard.html"), "r", encoding="utf-8") as f:
        html = f.read()

    import re
    safe_csv = full_csv.replace("`", "\\`").replace("$", "\\$")
    updated_html = re.sub(
        r"const EMBEDDED_CSV = `[\s\S]*?`;",
        "const EMBEDDED_CSV = `" + safe_csv + "`;",
        html
    )

    with open(os.path.join(ROOT_DIR, "dashboard.html"), "w", encoding="utf-8") as f:
        f.write(updated_html)

    print("Re-embedded 104 applications into dashboard.html!")

if __name__ == "__main__":
    expand_applications()
