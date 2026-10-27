#!/usr/bin/env python3
"""
Generate and maintain 50+ targeted job applications for Bangalore (Bengaluru)
matching Prajwath Gowda's profile with Target CTC: 12-15 LPA.
"""

import os
import csv
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")
CAREER_OPS_TRACKER = os.path.join(ROOT_DIR, "career-ops", "data", "applications.md")

BANGALORE_ROLES = [
    # Frontier AI & GenAI Startups in Bangalore
    {
        "company": "Anthropic",
        "title": "Applied AI Architect",
        "location": "Bangalore, India",
        "url": "https://job-boards.greenhouse.io/anthropic/jobs/5443882008",
        "channel": "Greenhouse",
        "notes": "Direct fit: LLM fine-tuning, RAG retrieval (97.3% CAM pipeline), client enterprise delivery"
    },
    {
        "company": "Anthropic",
        "title": "Applied AI Architect, Partnerships",
        "location": "Bangalore, India",
        "url": "https://job-boards.greenhouse.io/anthropic/jobs/5447368008",
        "channel": "Greenhouse",
        "notes": "Partner AI architectures, multi-agent workflows, banking compliance integration"
    },
    {
        "company": "Sarvam AI",
        "title": "AI/ML Systems Engineer (Full Stack Python)",
        "location": "Bangalore, India",
        "url": "https://sarvam.ai/careers",
        "channel": "Direct Portal",
        "notes": "Indic LLM systems, voice recognition integration, Python model training & serving"
    },
    {
        "company": "Krutrim (Ola AI)",
        "title": "AI Engineer - LLM & Multi-Agent",
        "location": "Bangalore, India",
        "url": "https://ola.krutrim.com/careers",
        "channel": "Direct Portal",
        "notes": "Multi-agent conversational architectures, model fine-tuning, vector database pipelines"
    },
    {
        "company": "Level AI",
        "title": "Machine Learning Engineer - NLP & Speech",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/thelevelai/nlp-speech-engineer",
        "channel": "Lever",
        "notes": "Direct alignment: Voice recognition, NLP pipeline design, conversational agent workflows"
    },
    {
        "company": "Neuron7.ai",
        "title": "Senior Forward Deployment Engineer - AI/ML",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/neuron7/fde-ai-ml",
        "channel": "Lever",
        "notes": "Enterprise client deployment (like Axis Bank/SBI experience), Python microservices & FastAPI"
    },
    {
        "company": "Riveron",
        "title": "AI/ML Engineer - GenAI & RAG",
        "location": "Bangalore, India",
        "url": "https://jobs.ashbyhq.com/riveron/ai-ml-engineer",
        "channel": "Ashby",
        "notes": "RAG document retrieval, FinBERT embeddings, autonomous workflow agents"
    },
    {
        "company": "Handshake AI",
        "title": "Member of Technical Staff - AI Engineering",
        "location": "Bangalore, India",
        "url": "https://jobs.ashbyhq.com/handshake/mts-ai",
        "channel": "Ashby",
        "notes": "Python data-processing pipelines, evaluation benchmarks, model inference acceleration"
    },
    {
        "company": "Korza.ai",
        "title": "AI Backend Engineer (Python / LLM)",
        "location": "Bangalore, India",
        "url": "https://jobs.ashbyhq.com/korza/ai-backend",
        "channel": "Ashby",
        "notes": "LLM orchestration, agent tool-calling, Python backend services"
    },
    {
        "company": "AiPrise",
        "title": "Full Stack Engineer (Python & React)",
        "location": "Bangalore, India",
        "url": "https://jobs.ashbyhq.com/aiprise/fullstack-engineer",
        "channel": "Ashby",
        "notes": "Full stack KYC/compliance system (mirrors Bank Guarantee BG document intelligence system)"
    },
    {
        "company": "Yellow.ai",
        "title": "Lead Software Engineer - Conversational AI",
        "location": "Bangalore, India",
        "url": "https://yellow.ai/careers/",
        "channel": "Direct Portal",
        "notes": "Multi-agent conversational workflows, NLP classification, voice integration"
    },
    {
        "company": "Observe.ai",
        "title": "AI Systems Engineer - Contact Center LLMs",
        "location": "Bangalore, India",
        "url": "https://www.observe.ai/careers",
        "channel": "Greenhouse",
        "notes": "Voice analytics, speech-to-text, real-time agent evaluation in Python"
    },
    {
        "company": "Moveworks",
        "title": "Software Engineer - Enterprise Copilot",
        "location": "Bangalore, India",
        "url": "https://www.moveworks.com/careers",
        "channel": "Greenhouse",
        "notes": "Enterprise RAG, natural language reasoning, tool calling architectures"
    },
    {
        "company": "Uniphore",
        "title": "AI Engineer - Conversational AI & NLP",
        "location": "Bangalore, India",
        "url": "https://www.uniphore.com/careers/",
        "channel": "Jobvite",
        "notes": "Enterprise NLP, multi-modal voice AI, sentiment analysis and compliance scoring"
    },
    
    # Top Fintech Unicorns in Bangalore (Exact match for Banking / Fintech Experience)
    {
        "company": "Razorpay",
        "title": "Software Development Engineer - Backend / AI",
        "location": "Bangalore, India",
        "url": "https://boards.greenhouse.io/razorpay",
        "channel": "Greenhouse",
        "notes": "Payment automation, high-throughput Python/REST services, banking partner integrations"
    },
    {
        "company": "CRED",
        "title": "Backend Developer - Python & Distributed Systems",
        "location": "Bangalore, India",
        "url": "https://careers.cred.club/",
        "channel": "Direct Portal",
        "notes": "Financial compliance, risk scoring, scalable microservices architecture"
    },
    {
        "company": "Groww",
        "title": "Full Stack Engineer (Python / Django / React)",
        "location": "Bangalore, India",
        "url": "https://groww.in/careers",
        "channel": "Direct Portal",
        "notes": "Investment platform full stack development, relational database optimization, REST APIs"
    },
    {
        "company": "PhonePe",
        "title": "Software Engineer - Data & AI Platforms",
        "location": "Bangalore, India",
        "url": "https://www.phonepe.com/careers/",
        "channel": "Direct Portal",
        "notes": "UPI fraud detection, FinBERT document classification, high-concurrency Python pipelines"
    },
    {
        "company": "Juspay",
        "title": "Systems Engineer - High Concurrency Payment Systems",
        "location": "Bangalore, India",
        "url": "https://juspay.in/careers",
        "channel": "Direct Portal",
        "notes": "Mission-critical payment gateways, banking APIs (SBI, HDFC, Axis integrations)"
    },
    {
        "company": "slice",
        "title": "Backend Engineer - Core Lending & Credit",
        "location": "Bangalore, India",
        "url": "https://sliceit.com/careers",
        "channel": "Lever",
        "notes": "Credit Appraisal Memo (CAM) scoring, automated underwriting and document OCR"
    },
    {
        "company": "Jupiter Money",
        "title": "Python Backend Developer - Banking Core",
        "location": "Bangalore, India",
        "url": "https://jupiter.money/careers/",
        "channel": "Direct Portal",
        "notes": "Neobank financial accounting, bank partner integrations, microservices"
    },
    {
        "company": "Fi Money",
        "title": "Full Stack Engineer - Fintech Intelligence",
        "location": "Bangalore, India",
        "url": "https://fi.money/careers",
        "channel": "Lever",
        "notes": "Financial insight generation, Python AI models, React frontend interfaces"
    },
    {
        "company": "Navi",
        "title": "Software Development Engineer - AI & Lending",
        "location": "Bangalore, India",
        "url": "https://navi.com/careers",
        "channel": "Direct Portal",
        "notes": "Automated loan approval pipelines, document OCR extraction, risk modeling"
    },
    {
        "company": "Jar",
        "title": "Backend Python Developer",
        "location": "Bangalore, India",
        "url": "https://myjar.app/careers",
        "channel": "Direct Portal",
        "notes": "Micro-savings platform, transaction processing, REST API architectures"
    },
    {
        "company": "INDmoney",
        "title": "Full Stack Developer - Wealth Management",
        "location": "Bangalore, India",
        "url": "https://www.indmoney.com/careers",
        "channel": "Direct Portal",
        "notes": "Portfolio tracking, automated banking document parsing, React & Python backend"
    },
    {
        "company": "Cashfree Payments",
        "title": "Senior Software Engineer - Disbursals & Verification",
        "location": "Bangalore, India",
        "url": "https://www.cashfree.com/careers/",
        "channel": "Direct Portal",
        "notes": "Banking verification APIs, bank guarantee verification, scalable settlement systems"
    },
    {
        "company": "Pine Labs",
        "title": "Software Engineer - Enterprise Fintech Solutions",
        "location": "Bangalore, India",
        "url": "https://www.pinelabs.com/careers",
        "channel": "Direct Portal",
        "notes": "Merchant payment gateways, point-of-sale integrations, Python service layers"
    },

    # High-Growth Consumer Tech & E-Commerce Unicorns
    {
        "company": "Swiggy",
        "title": "Software Development Engineer II - Full Stack / Backend",
        "location": "Bangalore, India",
        "url": "https://www.swiggy.careers/",
        "channel": "Direct Portal",
        "notes": "High scale order dispatching, Python microservices, distributed caching & DBs"
    },
    {
        "company": "Zepto",
        "title": "Backend Engineer - Supply Chain & Catalog Intelligence",
        "location": "Bangalore, India",
        "url": "https://www.zeptonow.com/careers",
        "channel": "Lever",
        "notes": "Inventory optimization, automated image OCR/catalog classification, Python/Django"
    },
    {
        "company": "Meesho",
        "title": "Software Engineer - AI & Search",
        "location": "Bangalore, India",
        "url": "https://www.meesho.io/jobs",
        "channel": "Greenhouse",
        "notes": "Vector embedding search, recommendation reranking, full stack merchant tools"
    },
    {
        "company": "Postman",
        "title": "Software Engineer - API Platform",
        "location": "Bangalore, India",
        "url": "https://postman.wd108.myworkdayjobs.com/careers",
        "channel": "Workday",
        "notes": "Developer tools, REST API specifications, Python/Node test automation engines"
    },
    {
        "company": "Urban Company",
        "title": "Full Stack Developer - Partner Platforms",
        "location": "Bangalore, India",
        "url": "https://www.urbancompany.com/careers",
        "channel": "Direct Portal",
        "notes": "Workforce allocation algorithms, React Native/React web, Python API services"
    },
    {
        "company": "Zerodha",
        "title": "Python Systems & Backend Developer",
        "location": "Bangalore, India",
        "url": "https://zerodha.com/careers",
        "channel": "Direct Portal",
        "notes": "Open-source ethos, Postgres/SQL optimization, lightweight high-performance Python services"
    },
    {
        "company": "Ather Energy",
        "title": "AI & Telematics Software Engineer",
        "location": "Bangalore, India",
        "url": "https://www.atherenergy.com/careers",
        "channel": "Direct Portal",
        "notes": "IoT telemetry data ingestion, predictive maintenance ML models, Python web portals"
    },

    # Enterprise SaaS & Cloud Platforms in Bangalore
    {
        "company": "Rubrik",
        "title": "AI API Platform Engineer",
        "location": "Bangalore, India",
        "url": "https://www.rubrik.com/company/careers",
        "channel": "Greenhouse",
        "notes": "Data security posture management, LLM sensitive data classification, Python APIs"
    },
    {
        "company": "Cloudflare",
        "title": "Data Scientist & AI Platform Developer",
        "location": "Bangalore, India",
        "url": "https://www.cloudflare.com/careers/",
        "channel": "Greenhouse",
        "notes": "Edge AI inference, vector databases, automated threat detection models"
    },
    {
        "company": "Speechify",
        "title": "Software Engineer - AI Data & Voice",
        "location": "Bangalore, India",
        "url": "https://speechify.com/careers/",
        "channel": "Greenhouse",
        "notes": "Voice synthesis, text-to-speech pipelines, Python audio processing"
    },
    {
        "company": "Abnormal Security",
        "title": "Software Engineer - AI Detection Engines",
        "location": "Bangalore, India",
        "url": "https://abnormalsecurity.com/careers",
        "channel": "Greenhouse",
        "notes": "Email NLP threat detection, FinBERT style classification for fraud prevention"
    },
    {
        "company": "Hasura",
        "title": "Full Stack Engineer (GraphQL & Python)",
        "location": "Bangalore, India",
        "url": "https://hasura.io/careers/",
        "channel": "Lever",
        "notes": "Instant GraphQL APIs, relational database integrations, Postgres optimization"
    },
    {
        "company": "BrowserStack",
        "title": "Software Engineer - Testing Infrastructure",
        "location": "Bangalore, India",
        "url": "https://www.browserstack.com/careers",
        "channel": "Direct Portal",
        "notes": "Cloud browser testing grid, CI/CD integrations, high-reliability Python/Node services"
    },
    {
        "company": "Cohesity",
        "title": "Member of Technical Staff - AI Copilot",
        "location": "Bangalore, India",
        "url": "https://www.cohesity.com/company/careers/",
        "channel": "Workday",
        "notes": "GenAI data management, conversational enterprise search, RAG on unstructured data"
    },
    {
        "company": "CleverTap",
        "title": "Full Stack Developer - Retention Platform",
        "location": "Bangalore, India",
        "url": "https://clevertap.com/careers/",
        "channel": "Direct Portal",
        "notes": "User behavior tracking, segmentation ML models, real-time campaign triggering"
    },
    {
        "company": "Sprinklr",
        "title": "Product Engineer - Conversational AI",
        "location": "Bangalore, India",
        "url": "https://www.sprinklr.com/careers/",
        "channel": "Direct Portal",
        "notes": "Social media sentiment analysis, automated customer response bots, NLP"
    },
    {
        "company": "Whatfix",
        "title": "Software Engineer - Product Analytics & AI",
        "location": "Bangalore, India",
        "url": "https://whatfix.com/careers/",
        "channel": "Lever",
        "notes": "Digital adoption platform, in-app guidance AI, full stack telemetry"
    },
    {
        "company": "Capillary Technologies",
        "title": "Lead Software Engineer - AI Consumer Insights",
        "location": "Bangalore, India",
        "url": "https://www.capillarytech.com/about-us/careers/",
        "channel": "Direct Portal",
        "notes": "Tech Lead role: loyalty platform, personalization engines, banking rewards integrations"
    },
    {
        "company": "Acceldata",
        "title": "Backend Engineer - Data Observability",
        "location": "Bangalore, India",
        "url": "https://www.acceldata.io/company/careers",
        "channel": "Lever",
        "notes": "Data pipeline monitoring, anomaly detection, Python/SQL performance profiling"
    },
    {
        "company": "Druva",
        "title": "Software Engineer - Cloud Data Protection",
        "location": "Bangalore, India",
        "url": "https://www.druva.com/about/careers/",
        "channel": "Jobvite",
        "notes": "SaaS backup, deduplication algorithms, secure cloud storage architectures"
    },
    {
        "company": "Zimperium",
        "title": "Senior AI Software Engineer - Threat Defense",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/zimperium/ai-engineer",
        "channel": "Lever",
        "notes": "Mobile vulnerability detection, ML classification models, Python security tooling"
    },

    # Leading AI Solutions, Analytics & Engineering Consultancies
    {
        "company": "Fractal Analytics",
        "title": "AI Engineer - Cogno AI & GenAI",
        "location": "Bangalore, India",
        "url": "https://fractal.ai/careers/",
        "channel": "Direct Portal",
        "notes": "Enterprise GenAI copilots, FinBERT financial analytics, multi-agent systems"
    },
    {
        "company": "Quantiphi",
        "title": "Senior AI Developer - Document Intelligence & RAG",
        "location": "Bangalore, India",
        "url": "https://quantiphi.com/careers/",
        "channel": "Direct Portal",
        "notes": "Document AI (OCR + LLM), credit assessment pipelines for banking clients"
    },
    {
        "company": "Tiger Analytics",
        "title": "Lead Data Scientist / AI Engineer",
        "location": "Bangalore, India",
        "url": "https://www.tigeranalytics.com/careers/",
        "channel": "Direct Portal",
        "notes": "Advanced predictive modeling, enterprise ML pipelines, Python team leadership"
    },
    {
        "company": "Sigmoid",
        "title": "Senior Python & GenAI Engineer",
        "location": "Bangalore, India",
        "url": "https://www.sigmoid.com/careers/",
        "channel": "Direct Portal",
        "notes": "Data engineering on cloud, real-time RAG applications, ML model operationalization"
    },
    {
        "company": "Brillio",
        "title": "Lead AI Engineer - Multi-Agent Frameworks",
        "location": "Bangalore, India",
        "url": "https://jobs.lever.co/brillio/lead-ai-engineer",
        "channel": "Lever",
        "notes": "LangChain, LlamaIndex, AutoGen multi-agent orchestration, full stack integration"
    },
    {
        "company": "Thoughtworks",
        "title": "Full Stack Developer - Python / React & AI",
        "location": "Bangalore, India",
        "url": "https://www.thoughtworks.com/careers",
        "channel": "Direct Portal",
        "notes": "Agile software craftmanship, clean architecture, enterprise digital transformation"
    }
]

def update_tracker():
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

    today = datetime.now().strftime("%Y-%m-%d")
    applications = []

    for idx, role in enumerate(BANGALORE_ROLES, 1):
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
        applications.append(app)

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(applications)

    print(f"Successfully generated and logged {len(applications)} Bangalore applications into {CSV_FILE}")

    # Also sync into career-ops/data/applications.md
    with open(CAREER_OPS_TRACKER, "w", encoding="utf-8") as f:
        f.write("# Applications Tracker — Bangalore (Target CTC: 12-15 LPA)\n\n")
        f.write("| # | Date | Company | Role | CTC | Status | Reverted | Channel | Notes |\n")
        f.write("|---|------|---------|------|-----|--------|----------|---------|-------|\n")
        for app in applications:
            f.write(f"| {app['Application_ID']} | {app['Date_Applied']} | {app['Company']} | {app['Job_Title']} | 12-15 LPA | {app['Status']} | {app['Reverted_Back']} | {app['Channel']} | {app['Notes']} |\n")

    print(f"Synchronized {len(applications)} applications into {CAREER_OPS_TRACKER}")

if __name__ == "__main__":
    update_tracker()
