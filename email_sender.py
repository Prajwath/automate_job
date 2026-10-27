#!/usr/bin/env python3
"""
Email Dispatch & Draft Utility for Prajwath Gowda (prajwathg@gmail.com)
Creates tailored cold/application emails, attaches resume, and sends via Gmail SMTP.
"""
import os
import sys
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RESUME_PATH = os.path.join(ROOT_DIR, "Prajwath_resume.pdf")
ENV_FILE = os.path.join(ROOT_DIR, ".env")

def get_env_var(key, default=""):
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, default)

def generate_email_content(company, role, recipient_name="Hiring Team"):
    subject = f"Application for {role} -- Prajwath Gowda (Tech Lead & AI/ML Engineer)"
    
    body = f"""Hi {recipient_name},

I hope this email finds you well.

I am writing to express my strong interest in the {role} position at {company}. As a Full Stack Python Developer and AI/ML Engineer currently serving as Tech Lead at Impactsure Technologies, I have built and deployed enterprise AI solutions for premier banking institutions including Axis Bank, SBI, and HDFC Bank.

Key highlights of my background:
- Technical Leadership: Led an 8-member engineering team on high-stakes banking document intelligence projects, consistently delivering ahead of strict deadlines.
- LLM & NLP Pipelines: Fine-tuned FinBERT and open-source models for complex document classification with 92.8% benchmark accuracy and built OCR extraction pipelines achieving 98.5% precision.
- RAG & Multi-Agent Architectures: Architected high-throughput RAG systems with 97.3% retrieval accuracy and conversational multi-agent systems with voice recognition and tool calling.
- Full Stack Engineering: Production experience with Python, Django, React, Node.js, REST APIs, and vector databases deployed to secure client infrastructure.

I have attached my resume for your review. I would welcome the opportunity to discuss how my hands-on AI and engineering experience can contribute to {company}'s roadmap.

Best regards,

Prajwath Gowda
Full Stack Python Developer & AI/ML Engineer
Phone: +91 7219727349 | Panjim, Goa, India
Email: prajwathg@gmail.com
LinkedIn: linkedin.com/in/prajwathgowda
GitHub: github.com/prajwathgowda
"""
    return subject, body

def send_email(to_email, company, role, recipient_name="Hiring Team", dry_run=False):
    sender_email = "prajwathg@gmail.com"
    app_password = get_env_var("GMAIL_APP_PASSWORD")

    subject, body = generate_email_content(company, role, recipient_name)

    if dry_run or not app_password:
        print("\n" + "=" * 60)
        print(" [EMAIL DRAFT GENERATED - DRY RUN]")
        print("=" * 60)
        print(f"From:    {sender_email}")
        print(f"To:      {to_email}")
        print(f"Subject: {subject}")
        print(f"Attachment: {RESUME_PATH}")
        print("-" * 60)
        print(body)
        print("=" * 60)
        if not app_password:
            print("\nNote: GMAIL_APP_PASSWORD is not set in .env. To enable direct sending, add:")
            print('GMAIL_APP_PASSWORD="your-16-char-app-password" into /home/prajwath/Documents/job/.env')
        return False

    msg = MIMEMultipart()
    msg['From'] = f"Prajwath Gowda <{sender_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach resume
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(RESUME_PATH))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(RESUME_PATH)}"'
            msg.attach(part)

    try:
        print(f"Connecting to Gmail SMTP server for {to_email}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"Email successfully sent to {to_email} ({company} - {role})!")
        
        # Log to tracker
        import tracker
        tracker.add_application(company=company, title=role, location="Remote", url=to_email, channel="Direct Email", notes=f"Sent to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Application Email Dispatcher")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Job role / title")
    parser.add_argument("--name", default="Hiring Team", help="Recipient contact name")
    parser.add_argument("--dry-run", action="store_true", help="Print draft only, do not send")

    args = parser.parse_args()
    send_email(args.to, args.company, args.role, args.name, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
