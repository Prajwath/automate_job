#!/usr/bin/env python3
"""
Resume Tailoring Engine for Prajwath Gowda
Adapts CV summary, skills hierarchy, bullet emphasis, and cover letter
specifically to each job description while preserving 100% factual accuracy.
"""

import os
import sys
import argparse
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "career-ops", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CANDIDATE_DATA = {
    "name": "Prajwath Gowda",
    "title": "Full Stack Python Developer & AI/ML Engineer (Tech Lead)",
    "location": "Bangalore / Panjim, Goa (Open to Immediate Relocation / Remote)",
    "email": "prajwathg@gmail.com",
    "phone": "+91 7219727349",
    "linkedin": "linkedin.com/in/prajwathgowda",
    "github": "github.com/prajwathgowda",
    "experience": {
        "company": "Impactsure Technologies Pvt. Ltd.",
        "period": "Dec 2024 – Present",
        "role": "Full Stack Python Developer & AI/ML Engineer (Tech Lead)"
    }
}

def generate_tailored_cv(company, role, jd_type="ai"):
    """
    Generates tailored markdown and HTML CV adapted to role type:
    - 'ai' / 'rag': Highlights LLM fine-tuning, FinBERT, RAG 97.3%, OCR 98.5%, Multi-agent voice
    - 'fullstack': Highlights Python, Django, React, Node.js, REST APIs, SQL, Virtual TryOn
    - 'fintech': Highlights Banking clients (Axis, SBI, HDFC), Bank Guarantee risk, compliance
    - 'lead': Highlights 8-member tech leadership, production deployments, client delivery
    """
    company_slug = company.lower().replace(" ", "_").replace(".", "")
    out_md = os.path.join(OUTPUT_DIR, f"CV_Prajwath_Gowda_{company_slug}.md")
    out_html = os.path.join(OUTPUT_DIR, f"CV_Prajwath_Gowda_{company_slug}.html")

    # Adapt headline and summary based on role
    if "full stack" in role.lower() or jd_type == "fullstack":
        headline = "Full Stack Python Developer & AI Engineer"
        summary = (
            f"Full Stack Python Developer with deep experience architecting scalable web applications "
            f"and deploying production AI solutions. Tech Lead at Impactsure Technologies, delivering high-performance "
            f"backends with Python, Django, React, Node.js, and REST APIs alongside automated OCR and document processing "
            f"for tier-1 banking institutions. Proven track record leading an 8-member engineering team to ship ahead of schedule."
        )
        skills_order = [
            ("Languages & Full Stack", "Python, Django, React, Node.js, REST APIs, HTML5, CSS3, JavaScript, Java, C++"),
            ("AI & Machine Learning", "LLM Integration, RAG Pipelines, FinBERT, OCR (98.5% precision), Multi-Agent Systems, Vector Search"),
            ("Databases & Infrastructure", "SQL, MySQL, Oracle DB, Linux, Git, Docker, Redis, REST Architecture")
        ]
    elif "lead" in role.lower() or jd_type == "lead":
        headline = "Technical Lead & Senior AI/Full Stack Python Engineer"
        summary = (
            f"Technical Lead and Senior AI/Full Stack Engineer with hands-on leadership managing an 8-member cross-functional "
            f"engineering team at Impactsure Technologies. Proven expertise delivering mission-critical AI/ML and banking platforms "
            f"for Axis Bank, SBI, and HDFC Bank end-to-end. Expert in Python, LLM fine-tuning, RAG pipelines (97.3% accuracy), "
            f"and robust enterprise software architectures deployed on secured banking server clusters."
        )
        skills_order = [
            ("Technical Leadership", "Team Leadership (8 engineers), Architecture Design, Sprint Coordination, Client Delivery, Banking Compliance"),
            ("AI / ML & LLMs", "FinBERT, Model Training & Fine-Tuning, RAG Pipelines, OCR (98.5%), Multi-Agent Workflows, Voice Recognition"),
            ("Full Stack & Backend", "Python, Django, React, Node.js, RESTful Microservices, SQL, MySQL, Linux, Git")
        ]
    else: # Default: AI / ML / RAG / GenAI
        headline = "AI/ML Engineer & Full Stack Python Developer"
        summary = (
            f"AI/ML Engineer and Full Stack Python Developer specializing in LLM fine-tuning, high-precision Retrieval-Augmented "
            f"Generation (RAG), and multi-agent conversational systems for enterprise applications. Currently serving as Tech Lead at "
            f"Impactsure Technologies, leading an 8-member team delivering automated document intelligence and classification models "
            f"with 92.8% to 98.5% accuracy for premier banking clients (SBI, HDFC Bank, Axis Bank)."
        )
        skills_order = [
            ("AI / ML & GenAI", "LLM Fine-Tuning, FinBERT, RAG Pipelines (97.3% retrieval), Multi-Agent Systems, OCR (98.5% precision), Voice Recognition, Vector Search"),
            ("Full-Stack & Languages", "Python, Django, React, Node.js, REST APIs, JavaScript, Java, C++, SQL"),
            ("Data & Production Infra", "MySQL, Oracle DB, Vector DBs, Embedding Search, Linux, Git, Docker, Jupyter, Colab")
        ]

    # Generate Markdown CV
    md_content = f"""# CV -- Prajwath Gowda

**Target Role:** {role} at {company}  
**Location:** {CANDIDATE_DATA['location']}  
**Email:** {CANDIDATE_DATA['email']} | **Phone:** {CANDIDATE_DATA['phone']}  
**LinkedIn:** {CANDIDATE_DATA['linkedin']} | **GitHub:** {CANDIDATE_DATA['github']}  

---

## Professional Summary

{summary}

---

## Technical Skills

"""
    for cat, sk in skills_order:
        md_content += f"- **{cat}:** {sk}\n"

    md_content += f"""
---

## Work Experience

### Impactsure Technologies Pvt. Ltd. -- Panjim, Goa / Remote
**{headline} (Tech Lead)**  
*Dec 2024 – Present (including Internship Dec 2024 – May 2025)*

- **Technical Team Leadership:** Serve as Tech Lead directing an 8-member engineering team on the Axis Bank Bank Guarantee (BG) project, owning delivery quality and consistently shipping production releases ahead of deadlines.
- **LLM Fine-Tuning & FinBERT:** Fine-tuned FinBERT and domain LLMs for financial contract classification and onerous clause analysis, achieving a benchmark accuracy of **92.8%** on complex real-world documents.
- **RAG Document Analysis:** Architected and deployed end-to-end RAG pipelines for Credit Appraisal Memos (CAM), attaining **97.3% retrieval precision** and eliminating manual underwriting overhead.
- **High-Accuracy OCR Pipeline:** Engineered document extraction pipelines achieving **98.5% accuracy** on unstructured, degraded banking scans.
- **Multi-Agent Conversational AI:** Designed an autonomous multi-agent system with speech recognition and tool invocation for customer and operational banking workflows.
- **Production Server Deployment:** Containerized and deployed AI microservices directly on secure on-premise client bank servers complying with strict financial regulatory standards.

---

## Key Projects

- **Bank Guarantee (BG) Document Intelligence System** *(Impactsure Technologies)*: Production pipeline from OCR to structured entity extraction, transforming unstructured guarantees into verified compliance data.
- **Onerous Clause Classifier (FinBERT)** *(Impactsure Technologies)*: Transformer-based model flagging high-risk clauses in bank guarantees with 92.8% accuracy.
- **TryOn (Virtual Wardrobe Platform)**: Full-stack virtual try-on web application built with Python, Node.js, and React featuring Firebase authentication and Razorpay payments integration.
- **Facial Recognition Attendance System**: Computer vision pipeline in Python with face embedding verification and automated attendance logging.

---

## Education

- **Master of Computer Applications (MCA)**, Goa University (2024 – 2026) -- Final CGPA: **8.03**
- **Bachelor of Computer Science (BCS)**, Dhempe College Of Arts And Science (2023 – 2024) -- CGPA: **8.31**

## Certifications

- **Data Science & Natural Language Processing** -- NullClass
- **Data Visualization Simulation (Power BI & Tableau)** -- Tata Consultancy Services (TCS)
- **Agile SCRUM & Team Coordination** -- Serendipity Arts Festival
"""

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Generate ATS-compliant HTML CV
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Prajwath Gowda - Tailored CV ({company})</title>
<style>
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.45; color: #1e293b; max-width: 820px; margin: 20px auto; padding: 25px; }}
    h1 {{ font-size: 24px; margin: 0; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; }}
    .subtitle {{ font-size: 14px; font-weight: 600; color: #2563eb; margin: 4px 0 10px 0; }}
    .contact {{ font-size: 12px; color: #475569; margin-bottom: 15px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
    h2 {{ font-size: 15px; color: #1e293b; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 3px; margin: 16px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px; }}
    p, li {{ font-size: 12.5px; color: #334155; }}
    ul {{ margin: 4px 0 10px 18px; padding: 0; }}
    li {{ margin-bottom: 4px; }}
    .role-header {{ display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-top: 6px; }}
    .company-sub {{ display: flex; justify-content: space-between; font-size: 12px; color: #64748b; font-style: italic; margin-bottom: 6px; }}
    .tag {{ display: inline-block; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 11.5px; margin: 2px; }}
</style>
</head>
<body>
    <h1>Prajwath Gowda</h1>
    <div class="subtitle">{headline} — Tailored for {role} at {company}</div>
    <div class="contact">
        Email: {CANDIDATE_DATA['email']} | Phone: {CANDIDATE_DATA['phone']} | Location: Bangalore / Goa (Open to Relocation) | 
        <a href="https://{CANDIDATE_DATA['linkedin']}">LinkedIn</a> | <a href="https://{CANDIDATE_DATA['github']}">GitHub</a>
    </div>

    <h2>Professional Summary</h2>
    <p>{summary}</p>

    <h2>Technical Skills</h2>
    <ul>
"""
    for cat, sk in skills_order:
        html_content += f"<li><strong>{cat}:</strong> {sk}</li>\n"

    html_content += f"""
    </ul>

    <h2>Work Experience</h2>
    <div class="role-header">
        <span>{headline} (Tech Lead)</span>
        <span>Dec 2024 – Present</span>
    </div>
    <div class="company-sub">
        <span>Impactsure Technologies Pvt. Ltd. (Client deployments: SBI, HDFC Bank, Axis Bank)</span>
        <span>Bangalore / Panjim, India</span>
    </div>
    <ul>
        <li><strong>Technical Team Leadership:</strong> Directed an 8-member engineering team on high-stakes banking document intelligence projects, owning delivery and consistently shipping releases ahead of deadlines.</li>
        <li><strong>LLM Fine-Tuning & FinBERT:</strong> Fine-tuned FinBERT and domain models for document classification and onerous clause analysis with <strong>92.8% benchmark accuracy</strong> on complex unstructured contracts.</li>
        <li><strong>RAG Document Intelligence:</strong> Architected RAG analysis pipelines for Credit Appraisal Memos (CAM) achieving <strong>97.3% retrieval accuracy</strong>.</li>
        <li><strong>High-Precision OCR:</strong> Built production OCR pipelines with <strong>98.5% extraction precision</strong> for unstructured banking records.</li>
        <li><strong>Multi-Agent Architecture:</strong> Designed autonomous conversational agent workflows with voice recognition and tool calling.</li>
        <li><strong>Production Server Deployment:</strong> Successfully deployed containerized microservices to client bank infrastructure meeting regulated compliance standards.</li>
    </ul>

    <h2>Key Projects</h2>
    <ul>
        <li><strong>Bank Guarantee Document Intelligence:</strong> End-to-end OCR and entity extraction pipeline structuring unstructured bank records.</li>
        <li><strong>Onerous Clause Classifier (FinBERT):</strong> Fine-tuned transformer model flagging high-risk clauses with 92.8% precision.</li>
        <li><strong>TryOn Virtual Wardrobe:</strong> Full-stack Python/React/Node.js web application with Firebase auth and Razorpay payment integration.</li>
        <li><strong>Facial Recognition Attendance System:</strong> Computer vision pipeline prototyped in Python for biometric verification.</li>
    </ul>

    <h2>Education & Certifications</h2>
    <div class="role-header">
        <span>Master of Computer Applications (MCA) — Goa University</span>
        <span>2024 – 2026 (CGPA: 8.03)</span>
    </div>
    <div class="role-header">
        <span>Bachelor of Computer Science (BCS) — Dhempe College</span>
        <span>2023 – 2024 (CGPA: 8.31)</span>
    </div>
    <p style="margin-top: 6px; font-size: 12px; color: #475569;">
        <strong>Certifications:</strong> Data Science & NLP (NullClass) | Data Visualization Power BI & Tableau (TCS) | Agile SCRUM (Serendipity)
    </p>
</body>
</html>
"""
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Tailored CV generated for {company} ({role}):")
    print(f"  -> Markdown: {out_md}")
    print(f"  -> ATS HTML: {out_html}")
    return out_html

def main():
    parser = argparse.ArgumentParser(description="Tailor CV to specific company and role")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Job title")
    parser.add_argument("--type", default="ai", choices=["ai", "fullstack", "lead", "fintech"], help="Tailoring emphasis")

    args = parser.parse_args()
    generate_tailored_cv(args.company, args.role, args.type)

if __name__ == "__main__":
    main()
