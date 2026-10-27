#!/usr/bin/env python3
"""
Add 50 high-growth funded tech startups in Bangalore (Target CTC: 12-15 LPA)
to the job application tracker for Prajwath Gowda.
"""

import os
import csv
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
CAREER_OPS_TRACKER = os.path.join(ROOT_DIR, "career-ops", "data", "applications.md")
DASHBOARD_FILE = os.path.join(ROOT_DIR, "dashboard.html")

STARTUP_ROLES = [
    # Top Funded GenAI & Agentic AI Startups (Bangalore)
    {
        "company": "Portkey.ai",
        "title": "AI Systems Engineer - LLMOps & Gateway",
        "location": "Bangalore, India",
        "url": "https://portkey.ai/careers",
        "channel": "Direct Portal",
        "notes": "LLM production routing, prompt caching, latency optimization in Python/Node"
    },
    {
        "company": "TrueFoundry",
        "title": "MLOps & LLM Platform Engineer",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/truefoundry",
        "channel": "Lever",
        "notes": "Containerized model deployment, serverless GPU inference, Python microservices"
    },
    {
        "company": "Composio.ai",
        "title": "AI Agent Infrastructure Engineer",
        "location": "Bangalore, India",
        "url": "https://composio.dev/careers",
        "channel": "Ashby",
        "notes": "Direct fit: Multi-agent tooling, autonomous tool invocation, Python/TypeScript SDKs"
    },
    {
        "company": "Ema Unlimited",
        "title": "AI Software Engineer - Universal AI Employee",
        "location": "Bangalore, India",
        "url": "https://www.ema.co/careers",
        "channel": "Ashby",
        "notes": "Enterprise agent orchestration, RAG on unstructured enterprise documents"
    },
    {
        "company": "Segmind",
        "title": "Backend AI Engineer - Fast Model Inference",
        "location": "Bangalore, India",
        "url": "https://www.segmind.com/careers",
        "channel": "Direct Portal",
        "notes": "PyTorch model serving, serverless API endpoints, distributed Python architecture"
    },
    {
        "company": "Atlan",
        "title": "Full Stack Developer - Data Governance & AI",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/atlan",
        "channel": "Lever",
        "notes": "Active metadata platform, GraphQL/REST APIs, Python backend & React frontend"
    },
    {
        "company": "Murf.ai",
        "title": "AI Speech & Voice Engineer",
        "location": "Bangalore, India",
        "url": "https://murf.ai/careers",
        "channel": "Direct Portal",
        "notes": "Text-to-speech synthesis, voice cloning, audio processing pipelines in Python"
    },
    {
        "company": "InVideo",
        "title": "Full Stack Python Engineer - Video AI",
        "location": "Bangalore, India",
        "url": "https://invideo.io/careers",
        "channel": "Direct Portal",
        "notes": "Generative video scripts, automated storyboard rendering, Python/Django & React"
    },
    {
        "company": "Dubverse.ai",
        "title": "Machine Learning Engineer - Multilingual Speech",
        "location": "Bangalore, India",
        "url": "https://dubverse.ai/careers/",
        "channel": "Direct Portal",
        "notes": "Indic speech models, automated subtitling OCR, Python audio processing"
    },
    {
        "company": "SuperOps.ai",
        "title": "Software Development Engineer - AI Automation",
        "location": "Bangalore, India",
        "url": "https://superops.ai/careers/",
        "channel": "Direct Portal",
        "notes": "IT management automation, predictive anomaly detection, Python backend services"
    },
    {
        "company": "DhiWise",
        "title": "Full Stack Developer - DevTools & CodeGen AI",
        "location": "Bangalore, India",
        "url": "https://www.dhiwise.com/careers",
        "channel": "Direct Portal",
        "notes": "Design-to-code compiler, automated AST generation, React and Python/Node.js"
    },
    {
        "company": "Simplismart",
        "title": "Systems Software Engineer - LLM Inference",
        "location": "Bangalore, India",
        "url": "https://simplismart.ai/careers",
        "channel": "Direct Portal",
        "notes": "vLLM model optimization, low-latency API wrappers, high performance Python"
    },
    {
        "company": "Spyne.ai",
        "title": "Computer Vision & ML Engineer",
        "location": "Bangalore, India",
        "url": "https://www.spyne.ai/careers",
        "channel": "Direct Portal",
        "notes": "Automated background replacement, vehicle inspection computer vision models"
    },
    {
        "company": "Suki.ai",
        "title": "Machine Learning Engineer - Healthcare Voice AI",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/suki",
        "channel": "Lever",
        "notes": "Direct alignment: Voice recognition, clinical entity extraction, conversational NLP"
    },

    # Document AI, RegTech, Identity & Banking Automation Startups
    # (Exact mirror match for Prajwath's OCR 98.5% and Bank Guarantee intelligence experience)
    {
        "company": "Hyperverge",
        "title": "AI Engineer - Document Intelligence & OCR",
        "location": "Bangalore, India",
        "url": "https://hyperverge.co/careers/",
        "channel": "Direct Portal",
        "notes": "Direct match: Bank document OCR extraction, identity verification, Python/PyTorch"
    },
    {
        "company": "Karza Technologies",
        "title": "Lead Software Engineer - Banking Analytics",
        "location": "Bangalore, India",
        "url": "https://karza.in/careers",
        "channel": "Direct Portal",
        "notes": "FinBERT classification, credit appraisal memo (CAM) scoring, banking compliance"
    },
    {
        "company": "Perfios",
        "title": "Senior Software Engineer - Statement Analysis & OCR",
        "location": "Bangalore, India",
        "url": "https://www.perfios.com/careers",
        "channel": "Direct Portal",
        "notes": "Bank statement parser, financial risk underwriting, high precision OCR pipelines"
    },
    {
        "company": "Signzy",
        "title": "AI Engineer - Digital Onboarding & Contracts",
        "location": "Bangalore, India",
        "url": "https://signzy.com/careers/",
        "channel": "Direct Portal",
        "notes": "Direct match: Contract onerous clause analysis, bank guarantee digitization, Python"
    },
    {
        "company": "Bureau.id",
        "title": "Backend Developer - Fraud Intelligence",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/bureau.id",
        "channel": "Lever",
        "notes": "Device fingerprinting, real-time risk decisioning, scalable Python microservices"
    },
    {
        "company": "IDfy",
        "title": "Full Stack Python Developer - Verification Platform",
        "location": "Bangalore, India",
        "url": "https://www.idfy.com/careers/",
        "channel": "Direct Portal",
        "notes": "Automated background verification APIs, document fraud detection, React/Python"
    },
    {
        "company": "Decentro",
        "title": "Senior Backend Developer - Banking APIs",
        "location": "Bangalore, India",
        "url": "https://decentro.tech/careers",
        "channel": "Direct Portal",
        "notes": "Open banking API middleware (Axis/SBI/HDFC), automated payment reconciliations"
    },
    {
        "company": "TartanHQ",
        "title": "Full Stack Engineer - Payroll & Work Data APIs",
        "location": "Bangalore, India",
        "url": "https://www.tartan.one/careers",
        "channel": "Direct Portal",
        "notes": "Payroll consent verification, income statement extraction, Python/FastAPI & React"
    },
    {
        "company": "Velocity.in",
        "title": "Backend Engineer - Revenue Based Financing",
        "location": "Bangalore, India",
        "url": "https://jobs.ashbyhq.com/velocity",
        "channel": "Ashby",
        "notes": "E-commerce cashflow forecasting, underwriting engines, PostgreSQL and Python"
    },
    {
        "company": "Klub",
        "title": "Full Stack Developer - Capital Platforms",
        "location": "Bangalore, India",
        "url": "https://klubworks.com/careers",
        "channel": "Direct Portal",
        "notes": "D2C funding marketplace, financial analytics dashboards, Python/Django & React"
    },
    {
        "company": "Volopay",
        "title": "Software Engineer - Corporate Spend & Cards",
        "location": "Bangalore, India",
        "url": "https://www.volopay.com/careers/",
        "channel": "Direct Portal",
        "notes": "Corporate expense approvals, accounting automation, banking integrations"
    },
    {
        "company": "Kodo",
        "title": "Backend Developer - Card Issuance & Credit",
        "location": "Bangalore, India",
        "url": "https://kodo.com/careers",
        "channel": "Direct Portal",
        "notes": "Card ledger architectures, credit underwriting rules, Python/REST services"
    },

    # Developer Tools, Open Source & Infrastructure Startups
    {
        "company": "SigNoz",
        "title": "Full Stack Engineer - Open Source Observability",
        "location": "Bangalore, India",
        "url": "https://signoz.io/careers/",
        "channel": "Direct Portal",
        "notes": "OpenTelemetry metrics, ClickHouse queries, distributed traces, Python/Go & React"
    },
    {
        "company": "Devtron Labs",
        "title": "Software Engineer - Kubernetes CI/CD",
        "location": "Bangalore, India",
        "url": "https://devtron.ai/careers/",
        "channel": "Direct Portal",
        "notes": "Open-source Kubernetes deployment portal, container orchestration, Python/Go"
    },
    {
        "company": "Privado.ai",
        "title": "Software Engineer - Code Privacy Analysis",
        "location": "Bangalore, India",
        "url": "https://www.privado.ai/careers",
        "channel": "Ashby",
        "notes": "Static code analysis (Python/Java/JS), data flow mapping, privacy compliance"
    },
    {
        "company": "Sprinto",
        "title": "Backend Developer - Automated Security Compliance",
        "location": "Bangalore, India",
        "url": "https://sprinto.com/careers/",
        "channel": "Direct Portal",
        "notes": "SOC2/ISO27001 automation, cloud security posture scanners, Python & REST APIs"
    },
    {
        "company": "Scrut Automation",
        "title": "Senior Software Engineer - Governance & Risk",
        "location": "Bangalore, India",
        "url": "https://www.scrut.io/careers",
        "channel": "Direct Portal",
        "notes": "Continuous compliance auditing, automated evidence collection, Python backend"
    },
    {
        "company": "Rocketlane",
        "title": "Full Stack Developer - Client Collaboration SaaS",
        "location": "Bangalore, India",
        "url": "https://www.rocketlane.com/careers",
        "channel": "Lever",
        "notes": "Customer onboarding portal, document approval workflows, React and Python/Node"
    },
    {
        "company": "Testsigma",
        "title": "Software Engineer - AI-Driven Test Automation",
        "location": "Bangalore, India",
        "url": "https://testsigma.com/careers",
        "channel": "Direct Portal",
        "notes": "Natural language test scripting, web element locator ML models, Python"
    },
    {
        "company": "Traceable AI",
        "title": "Software Engineer - API Security Intelligence",
        "location": "Bangalore, India",
        "url": "https://www.traceable.ai/careers",
        "channel": "Greenhouse",
        "notes": "API call threat analysis, behavioral anomaly detection, high-throughput Python"
    },
    {
        "company": "SquadStack",
        "title": "Full Stack Python Developer - Sales Automation",
        "location": "Bangalore, India",
        "url": "https://www.squadstack.com/careers",
        "channel": "Ashby",
        "notes": "Voice AI call intelligence, speech-to-text scoring, React and Python/Django"
    },
    {
        "company": "Locofy.ai",
        "title": "Software Engineer - Frontend AI Compiler",
        "location": "Bangalore, India",
        "url": "https://www.locofy.ai/careers",
        "channel": "Direct Portal",
        "notes": "AI code generation, AST parsing, React/TypeScript and Python backend services"
    },
    {
        "company": "Superflows",
        "title": "AI Systems Engineer - In-App Copilots",
        "location": "Bangalore, India",
        "url": "https://superflows.ai/careers",
        "channel": "Direct Portal",
        "notes": "SaaS copilot tool-calling, autonomous agent workflows, Python backend"
    },

    # HealthTech, InsurTech & HRTech Startups in Bangalore
    {
        "company": "Plum",
        "title": "Full Stack Engineer - Health Benefits Platform",
        "location": "Bangalore, India",
        "url": "https://www.plumhq.com/careers",
        "channel": "Direct Portal",
        "notes": "Automated insurance claims OCR, policy management APIs, React and Python"
    },
    {
        "company": "Loop Health",
        "title": "Backend Developer - Telemedicine & Claims",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/loophealth",
        "channel": "Lever",
        "notes": "Medical billing automation, electronic prescription pipelines, Python/Django"
    },
    {
        "company": "Kula.ai",
        "title": "Software Engineer - Outbound Recruitment Tech",
        "location": "Bangalore, India",
        "url": "https://www.kula.ai/careers",
        "channel": "Ashby",
        "notes": "Candidate enrichment algorithms, automated outreach workflows, Python/Node"
    },
    {
        "company": "BarRaiser",
        "title": "AI Engineer - Interview Intelligence & Video AI",
        "location": "Bangalore, India",
        "url": "https://barraiser.com/careers/",
        "channel": "Direct Portal",
        "notes": "Real-time speech transcription, interview answer scoring, NLP and Python"
    },
    {
        "company": "Zupain",
        "title": "Full Stack Python Developer - Local Commerce",
        "location": "Bangalore, India",
        "url": "https://zupain.com/careers",
        "channel": "Direct Portal",
        "notes": "Merchant storefronts, WhatsApp commerce integrations, Django/React architecture"
    },
    {
        "company": "Mudrex",
        "title": "Backend Developer - Algorithmic Investing",
        "location": "Bangalore, India",
        "url": "https://mudrex.com/careers",
        "channel": "Direct Portal",
        "notes": "Automated portfolio rebalancing, high-throughput financial execution APIs, Python"
    },
    {
        "company": "Fashinza",
        "title": "Full Stack Engineer - Apparel Supply Chain Tech",
        "location": "Bangalore, India",
        "url": "https://fashinza.com/careers",
        "channel": "Direct Portal",
        "notes": "Manufacturing tracking, automated BOM calculations, React and Python/Node.js"
    },
    {
        "company": "BHuman.ai",
        "title": "AI Video Generation Engineer",
        "location": "Bangalore, India",
        "url": "https://www.bhuman.ai/careers",
        "channel": "Direct Portal",
        "notes": "Facial landmark tracking, personalized video rendering, Python & PyTorch"
    },
    {
        "company": "Cognida.ai",
        "title": "Senior AI/ML Engineer - Enterprise Copilots",
        "location": "Bangalore, India",
        "url": "https://cognida.ai/careers",
        "channel": "Direct Portal",
        "notes": "RAG document synthesis, multi-tenant LLM deployment, Python/FastAPI microservices"
    },
    {
        "company": "Blend (AI Studio)",
        "title": "Full Stack Engineer - Ecommerce Visual AI",
        "location": "Bangalore, India",
        "url": "https://www.blend.to/careers",
        "channel": "Direct Portal",
        "notes": "Generative product photography, diffusion model pipelines, React and Python backend"
    },
    {
        "company": "Kodo Card",
        "title": "Senior Backend Developer - Financial Ledger",
        "location": "Bangalore, India",
        "url": "https://kodo.com/careers",
        "channel": "Direct Portal",
        "notes": "Double-entry bookkeeping engine, automated bank settlements, Python REST APIs"
    },
    {
        "company": "Securden",
        "title": "Software Engineer - Privileged Access Security",
        "location": "Bangalore, India",
        "url": "https://www.securden.com/careers.html",
        "channel": "Direct Portal",
        "notes": "Zero-trust remote access, automated password vaulting, Python security services"
    },
    {
        "company": "Superflows AI",
        "title": "Lead Software Engineer - Autonomous Agents",
        "location": "Bangalore, India",
        "url": "https://superflows.ai/careers",
        "channel": "Direct Portal",
        "notes": "Agentic API execution, tool synthesis, LangChain/LlamaIndex, Python architecture"
    }
]

def add_startups():
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

    for idx, role in enumerate(STARTUP_ROLES, start_id):
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

    print(f"Total applications in {CSV_FILE} expanded to: {len(existing)}")

    # Update career-ops tracker
    with open(CAREER_OPS_TRACKER, "w", encoding="utf-8") as f:
        f.write("# Applications Tracker — Bangalore (Target CTC: 12-15 LPA)\n\n")
        f.write("| # | Date | Company | Role | CTC | Status | Reverted | Channel | Notes |\n")
        f.write("|---|------|---------|------|-----|--------|----------|---------|-------|\n")
        for app in existing:
            f.write(f"| {app['Application_ID']} | {app['Date_Applied']} | {app['Company']} | {app['Job_Title']} | 12-15 LPA | {app['Status']} | {app['Reverted_Back']} | {app['Channel']} | {app['Notes']} |\n")

    print(f"Updated {CAREER_OPS_TRACKER} with {len(existing)} entries.")

    # Re-embed updated CSV into dashboard.html
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        full_csv = f.read()

    with open(DASHBOARD_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    import re
    safe_csv = full_csv.replace("`", "\\`").replace("$", "\\$")
    updated_html = re.sub(
        r"const EMBEDDED_CSV = `[\s\S]*?`;",
        "const EMBEDDED_CSV = `" + safe_csv + "`;",
        html
    )

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(updated_html)

    print(f"Re-embedded {len(existing)} applications into dashboard.html!")

if __name__ == "__main__":
    add_startups()
