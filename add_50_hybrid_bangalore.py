#!/usr/bin/env python3
"""
Add 50 hybrid Bangalore roles found via web search (Oct 2026) to the tracker.

Rows are added with Status "To Apply": nothing is submitted. Each URL is the
posting (or the company board when no single posting link was found). Postings
close often, so check each one before applying.
"""

import os
import csv

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(ROOT_DIR, "job_applications.csv")

# (company, title, url, channel, notes)
HYBRID_ROLES = [
    ("Okta", "IT Automation and AI Engineer", "https://job-boards.greenhouse.io/okta/jobs/8132173", "Greenhouse", "Strong fit: 2-4 yrs, Python + LangGraph/LangChain + LLMs"),
    ("Alaan", "AI Engineer", "https://www.weekday.works/jobs/ai-jobs-in-bangalore-15", "Weekday (aggregator)", "Strong fit: 2+ yrs; find Alaan listing on page"),
    ("Lookup It Solutions", "AI/ML Engineer - GenAI & LLM", "https://bebee.com/in/jobs/ai-ml-engineer-genai-llm-lookup-it-solutions-bengaluru--t7xk-875437557", "beBee (aggregator)", "Strong fit: LLM apps, RAG, vector DBs, AWS Bedrock; apply by 16 Dec 2026"),
    ("DigitalXNode", "AI Engineer - GenAI, LLM, Python", "https://www.foundit.in/job/artificial-intelligence-engineer-jobs-in-bangalore-bengaluru-genai-llm-python-digitalxnode-india-60066032", "Foundit", "Strong fit: 3-10 yrs, LLMs, RAG, NLP, FastAPI"),
    ("Hiver", "SDE 2 - Backend", "https://jobs.weekday.works/hiver-sde-2-backend-(hybrid)", "Weekday (aggregator)", "3+ yrs, listed 25-40 LPA; confirm stack"),
    ("EarnIn", "Machine Learning Engineer", "https://job-boards.greenhouse.io/earnin/jobs/7093414", "Greenhouse", "Hybrid, 2 days/week in Bengaluru office"),
    ("EarnIn", "Senior Machine Learning Engineer", "https://job-boards.greenhouse.io/earnin/jobs/7017818", "Greenhouse", "Senior ML role, Bengaluru hybrid"),
    ("EarnIn", "Senior Platform Engineer (AI Focused)", "https://job-boards.greenhouse.io/earnin/jobs/7895708", "Greenhouse", "4+ yrs, Python and/or Go; 2 days/week in office"),
    ("Konovo", "Senior Applied AI Engineer", "https://job-boards.greenhouse.io/konovo/jobs/5430560008", "Greenhouse", "Python + modern AI frameworks; 3 days/week Whitefield office"),
    ("ConnectWise", "Sr. Software Engineer - AI", "https://job-boards.greenhouse.io/connectwise/jobs/4703410005", "Greenhouse", "RAG + agentic AI; posting ~141 days old, check it is open"),
    ("OpenAI", "Applied AI Engineer", "https://jobs.ashbyhq.com/openai/bf036b23-cd23-46d0-a02f-4b1483f4698a", "Ashby", "Bengaluru/Delhi/Mumbai, 3 days/week in office; enterprise AI deployments"),
    ("Neuron7", "Senior Forward Deployment Engineer (AI/ML, Python)", "https://jobs.lever.co/neuron7/3c8a38fe-00bf-43cd-9622-1b9e4824775f", "Lever", "5+ yrs Python, FastAPI/Flask/Django; real link for tracker #6"),
    ("Neuron7", "Lead Software Engineer - AI/ML (Implementation)", "https://jobs.lever.co/neuron7/787cf4d2-1ee7-4376-8d63-995f1275df4f", "Lever", "7+ yrs; Python services, LLM/RAG, data pipelines"),
    ("Neuron7", "Solution Architect (GenAI/LLM)", "https://jobs.lever.co/neuron7/334c2ee0-2d8a-4c35-a65b-31b7f1c74fc4", "Lever", "LLMs, RAG, NLP integration with Salesforce Field Service"),
    ("Neuron7", "Staff Data Scientist", "https://jobs.lever.co/neuron7/b11b31fe-bdca-44fc-8bb5-5c4e907d8f89", "Lever", "Stretch: 8+ yrs; NLP and unstructured data"),
    ("Zimperium", "Python Developer", "https://jobs.lever.co/zimperium/62345dc6-5179-4e47-8736-0fb3530f4211", "Lever", "Python infrastructure and automation"),
    ("Zimperium", "Senior AI Engineer / Python Developer", "https://jobs.lever.co/zimperium/6e0239b1-9fa6-4967-89a3-f90889dde23b", "Lever", "5-9 yrs, Django/Flask/FastAPI; posting ~312 days old"),
    ("Level AI", "Senior Backend Engineer - AI Agents", "https://jobs.lever.co/levelai/98f0df69-79f8-4072-b676-19d9eec4df74", "Lever", "Hybrid Noida/Bangalore; AI agents backend"),
    ("Level AI", "Senior Machine Learning Engineer - NLP", "https://jobs.lever.co/levelai/cc04ab77-6ee3-4078-9cfd-110cda0b1438", "Lever", "Hybrid Noida/Bangalore; NLP"),
    ("Level AI", "Machine Learning Engineer (Speech)", "https://jobs.lever.co/levelai", "Lever", "Board link; matches voice recognition experience"),
    ("Brillio", "Lead AI Engineer I (R01571042)", "https://jobs.lever.co/brillio-2/3537f097-0870-434a-90a5-f81742e6ed00", "Lever", "Hybrid Bangalore"),
    ("Brillio", "Lead AI Engineer I (R01571162)", "https://jobs.lever.co/brillio-2/df0baced-8074-4381-b73e-ee029c321739", "Lever", "Hybrid Bangalore"),
    ("Brillio", "Senior AI/ML Engineer (R01563571)", "https://jobs.lever.co/brillio-2/a90c3a95-1f47-4d31-b29a-521b653c6500", "Lever", "Hybrid Bangalore"),
    ("Brillio", "AI/ML Engineer (R01570580)", "https://jobs.lever.co/brillio-2", "Lever", "Board link; search R01570580"),
    ("Bazaarvoice", "Staff Machine Learning Engineer", "https://jobs.lever.co/bazaarvoice?department=Engineering", "Lever", "Stretch: staff level; board link"),
    ("Weekday client (tech & media)", "Data Scientist", "https://jobs.lever.co/weekdayworks/8b29d9b7-0a79-4c17-a7ef-3bc1fe09378e", "Lever", "Stretch: 7+ yrs"),
    ("Cloudflare", "Software Engineer", "https://job-boards.greenhouse.io/cloudflare/jobs/8212060", "Greenhouse", "3-15 yrs; internal platforms, Python accepted"),
    ("Scopely", "Senior Software Engineer - Backend (Python + Django)", "https://job-boards.greenhouse.io/scopely/jobs/5298509008", "Greenhouse", "5+ yrs Python/Django; WWE Champions team"),
    ("Poppulo", "Senior Software Engineer - Full Stack", "https://job-boards.greenhouse.io/poppulo/jobs/6824055", "Greenhouse", "7-12 yrs; Python not confirmed"),
    ("Sigmoid", "Software Development Engineer III (Backend)", "https://job-boards.greenhouse.io/sigmoid/jobs/8086216002", "Greenhouse", "5-8 yrs backend"),
    ("HackerRank", "Senior Machine Learning Engineer", "https://job-boards.greenhouse.io/hackerrank", "Greenhouse", "Board link; hybrid Bangalore"),
    ("Smartsheet", "Senior AI/ML Ops Engineer", "https://job-boards.greenhouse.io/smartsheet", "Greenhouse", "Board link; hybrid Bangalore"),
    ("Smartsheet", "Principal AI Engineer", "https://job-boards.greenhouse.io/smartsheet", "Greenhouse", "Stretch: principal level; board link"),
    ("Zscaler", "Sr. Software Development Engineer", "https://job-boards.greenhouse.io/zscaler/jobs/5202460007", "Greenhouse", "Weak fit: Go/Rust/Python systems role"),
    ("SpotOn", "Senior Software Engineer (Full Stack)", "https://jobs.ashbyhq.com/spoton/483dad25-ec2b-4c28-8749-445b69341ce3", "Ashby", "Full stack, not AI-focused"),
    ("SurveyMonkey", "Staff Software Engineer", "https://jobs.ashbyhq.com/surveymonkey/2a5cdde3-051c-408e-9bd8-e8bebdbdd1d0", "Ashby", "Stretch: staff level, billing/payments; up to 3 days/week in office"),
    ("Reo.Dev", "Backend Engineer", "https://jobs.ashbyhq.com/reo-dev/f3964eba-b346-4ad3-83d8-4774b258a5cf", "Ashby", "Backend; Python not confirmed"),
    ("Ema", "Software Engineer, Backend - India", "https://jobs.ashbyhq.com/ema/eb62df31-0370-447f-8cc6-707e79cbc9fa", "Ashby", "Go and Python; 3 days/week in office"),
    ("Tilt Finance", "Staff Backend Engineer - NIRA", "https://jobs.ashbyhq.com/tilthq/b45f4a2d-78eb-482a-bd5b-119c80599350", "Ashby", "Stretch: staff level"),
    ("Trintech", "Senior Software Engineer (JR100139)", "https://trintech.wd501.myworkdayjobs.com/trintech/job/India---Bangalore/Senior-Software-Engineer_JR100139", "Workday", "Python backend + data pipelines for AI agents (financial close)"),
    ("Synechron", "AI / Generative AI Sr. Associate", "https://synechron.wd1.myworkdayjobs.com/SynechronCareers/job/Bengaluru---Bellandur-GTP/AI---Generative-AI-Sr-Associate_JR1043353-6", "Workday", "6+ yrs GenAI apps"),
    ("GSK", "Senior Lead - AI Engineer", "https://gsk.wd5.myworkdayjobs.com/gskcareers/job/Bengaluru-Luxor-North-Tower/Assistant-Manager--AI-Engineer_438250", "Workday", "5+ yrs Azure web apps, strong Python"),
    ("Freshworks", "Staff Engineer - Machine Learning", "https://jobs.smartrecruiters.com/Freshworks/744000155675855-staff-engineer-machine-learning", "SmartRecruiters", "Stretch: staff level; office Tue-Thu"),
    ("LinkedIn", "Senior Software Engineer, Systems Infrastructure", "https://jobs.smartrecruiters.com/linkedin3/744000149783529-senior-software-engineer-systems-infrastructure", "SmartRecruiters", "Weak fit: infrastructure, Python one of several languages"),
    ("Cognizant", "Gen AI Engineer", "https://careers.cognizant.com/india-en/jobs/00065735601/gen-ai-engineer/", "Direct Portal", "4-13 yrs"),
    ("Cognizant", "AI Engineer (Python, LangChain, LangGraph, Agentic AI)", "https://careers.cognizant.com/global-en/jobs/00068075031/ai-engineer-python-langchain-langgraph-agentic-ai-api-llms/", "Direct Portal", "7-13 yrs; one copy says remote, confirm work mode"),
    ("PayPal", "Senior Software Engineer - Backend (Python)", "https://jointaro.com/jobs/paypal/senior-software-engineer-backend-python", "Taro (aggregator)", "5+ yrs Django/Flask; 3 days office. Some PayPal copies say in-office"),
    ("Point72", "Machine Learning Engineer, GenAI", "https://www.weekday.works/jobs/ai-jobs-in-bangalore-5", "Weekday (aggregator)", "Find Point72 listing on page"),
    ("BitTwoByte Technology", "AI + Backend Engineer (Agentic AI)", "https://jobfound.org/job/bittwobyte-technology-pvt-ltd-is-hiring-for-artificial-intelligence-engineer-bengaluru-karnataka-india-india-23-october-2026", "jobfound (aggregator)", "LangChain/LangGraph; also needs Node.js"),
    ("WSP", "Senior AI Engineer", "https://quark9.com/jobs/senior-ai-engineer-wsp-in-india-77703ad4-f3cd-44b5-8119-90b3bbc9b074", "quark9 (aggregator)", "Hybrid Bengaluru"),
]


def main():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    existing = {(r["Company"], r["Job_Title"]) for r in rows}
    next_id = max(int(r["Application_ID"]) for r in rows) + 1
    added = 0
    for company, title, url, channel, notes in HYBRID_ROLES:
        if (company, title) in existing:
            continue
        rows.append({
            "Application_ID": str(next_id),
            "Company": company,
            "Job_Title": title,
            "Location": "Bangalore, India (Hybrid)",
            "Target_CTC": "12 - 15 LPA",
            "Job_URL": url,
            "Date_Applied": "",
            "Channel": channel,
            "Sender_Email": "",
            "Status": "To Apply",
            "Reverted_Back": "No",
            "Response_Date": "",
            "Notes": notes,
        })
        next_id += 1
        added += 1

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Added {added} hybrid Bangalore roles (Status: To Apply). Total rows: {len(rows)}")


if __name__ == "__main__":
    main()
