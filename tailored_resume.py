#!/usr/bin/env python3
"""Generate a JD-specific text PDF using only verified resume facts.

No third-party model is called. Skill ordering and achievement selection are
based on the actual description, and unknown technologies are never inserted.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import sys
import unicodedata

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'.pdf-deps'))

SKILLS={
 'Python':r'\bpython\b', 'Django':r'\bdjango\b', 'React':r'\breact(?:\.js)?\b',
 'Node.js':r'\bnode(?:\.js|js)?\b', 'JavaScript':r'\bjavascript\b', 'SQL':r'\bsql\b',
 'MySQL':r'\bmysql\b', 'Oracle DB':r'\boracle\b', 'REST APIs':r'\brest(?:ful)?\b|\bapis?\b',
 'LLM fine-tuning':r'\bllms?\b|large language|fine.tun', 'RAG (Retrieval-Augmented Generation)':r'\brag\b|retrieval.augmented',
 'FinBERT':r'finbert|bert|document classification', 'OCR':r'\bocr\b|optical character|document (?:extraction|processing)',
 'Multi-agent systems':r'multi.agent|agentic|agents', 'Vector / embedding search':r'vector|embedding',
 'Prompt engineering':r'prompt', 'Voice recognition':r'voice|speech|conversational',
 'Git':r'\bgit\b|version control', 'Linux':r'\blinux\b',
 'Java':r'\bjava\b', 'C++':r'c\+\+', 'HTML / CSS':r'\bhtml|\bcss',
 'Jupyter / Google Colab':r'jupyter|colab',
}
BULLETS=[
 ('Build AI/ML-driven products as a Full Stack Python Developer for banking-sector clients including SBI, HDFC Bank, Axis Bank and IndusInd Bank.',r'python|software|backend|bank|enterprise|product'),
 ('Serve as Tech Lead on Axis Bank\'s Bank Guarantee project, leading an 8-member engineering team and owning delivery quality.',r'lead|team|collaborat|stakeholder|bank|delivery'),
 ('Fine-tuned FinBERT and LLM models for Bank Guarantee document classification and onerous-clause analysis; the onerous analysis model achieved 92.8% accuracy.',r'llm|fine.tun|bert|nlp|classification|model|train'),
 ('Built OCR pipelines achieving 98.5% extraction accuracy on complex, unstructured banking documents.',r'ocr|extract|pipeline|unstructured|document|computer vision|data'),
 ('Designed RAG-based document analysis pipelines for CAM (Credit Appraisal Memo) documents, achieving 97.3% retrieval accuracy.',r'rag|retriev|vector|embedding|llm|search|pipeline'),
 ('Architected a multi-agent AI system with integrated voice recognition for automated conversational workflows.',r'agent|voice|speech|conversational|automat|workflow|\bai\b'),
 ('Deployed production AI/ML applications directly on client bank servers within secured, regulated banking infrastructure.',r'deploy|production|security|enterprise|bank|infrastructure|ml'),
]
PROJECTS=[
 ('CAM Document Analysis','RAG-based analysis of Credit Appraisal Memo documents with 97.3% retrieval accuracy.',r'rag|retriev|vector|embedding|llm|document'),
 ('Bank Guarantee Document Intelligence','End-to-end OCR-to-entity-extraction pipeline, structuring scanned banking documents for compliance and risk workflows.',r'ocr|document|pipeline|entity|bank|compliance|data'),
 ('Onerous Analysis Model (FinBERT)','FinBERT-based classifier identifying onerous clauses in Bank Guarantee documents; 92.8% accuracy on complex real-world documents.',r'bert|nlp|classification|fine.tun|llm|model|machine learning'),
 ('TryOn - Virtual Wardrobe','Full-stack virtual try-on platform using Python, Node.js and React, with Firebase and Razorpay integration.',r'full.stack|react|node|web|django|backend|api|javascript'),
 ('Facial Recognition Attendance System','Python-based machine-learning/computer-vision attendance system prototyped in Google Colab and Jupyter.',r'computer vision|machine learning|python|research|data scien'),
]


def ascii_text(value):
    value=value.replace('\u2013','-').replace('\u2014','-').replace('\u2011','-').replace('\u2019',"'")
    return unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode()


def rank(text,pattern):return sum(bool(re.search(term,text,re.I)) for term in pattern.split('|'))


def plan(job,app):
    jd=job['jd'];title=job['Job_Title']
    verified_skills=dict(SKILLS)
    if app.get('aws experience')=='2 years':verified_skills['AWS (2 years)']=r'\baws\b|amazon web services'
    if app.get('docker knowledge','').lower()=='yes':verified_skills['Docker (knowledge)']=r'\bdocker\b'
    if app.get('fastapi experience')=='2+ years':verified_skills['FastAPI']=r'\bfastapi\b'
    matched=[name for name,pattern in verified_skills.items() if re.search(pattern,jd,re.I)]
    ordered=matched+[name for name in verified_skills if name not in matched]
    bullets=sorted(enumerate(BULLETS),key=lambda pair:(-rank(jd,pair[1][1]),pair[0]))
    projects=sorted(enumerate(PROJECTS),key=lambda pair:(-rank(jd,pair[1][2]),pair[0]))[:2]
    if re.search(r'backend|full.stack|python developer|software engineer',title,re.I):
        opening='Full Stack Python Developer and AI/ML Engineer with 2 years of experience delivering banking-sector applications.'
        focus='Skills include Python, Django, REST APIs, SQL and production AI integration.'
    elif re.search(r'vision|ocr',title,re.I):
        opening='Python and AI/ML developer with 2 years of experience building document-intelligence products for banking clients.'
        focus='Work includes OCR extraction, document classification and a Python facial-recognition project.'
    else:
        opening='AI/ML Engineer and Full Stack Python Developer with 2 years of experience delivering banking-sector AI applications.'
        focus='Work spans LLM fine-tuning, FinBERT document classification, RAG, OCR and multi-agent conversational workflows.'
    if re.search(r'machine learning',title,re.I):
        opening='Python and AI/ML developer with 2 years of experience delivering banking-sector machine-learning applications.'
        focus='Hands-on work includes model training and fine-tuning, FinBERT document classification, OCR data extraction, data pipelines and production deployment.'
        bullets=sorted(bullets,key=lambda item: -(rank(jd,item[1][1]) + (6 if 'Fine-tuned FinBERT' in item[1][0] else 0) + (3 if 'OCR pipelines' in item[1][0] else 0)))
        projects=[(i,p) for i,p in enumerate(PROJECTS) if p[0] in ('Onerous Analysis Model (FinBERT)','Facial Recognition Attendance System')]
    if re.search(r'front.?end',title,re.I):
        opening='Full Stack Python Developer and AI/ML Engineer with 2 years of experience delivering banking-sector applications.'
        focus='Documented frontend skills include React, JavaScript and HTML/CSS, with a React/Node.js/Python virtual-wardrobe project and experience integrating production AI capabilities.'
        priority=['React','JavaScript','HTML / CSS','REST APIs','Git','Node.js']
        ordered=priority+[name for name in ordered if name not in priority]
        projects=[(i,p) for i,p in enumerate(PROJECTS) if p[0] in ('TryOn - Virtual Wardrobe','CAM Document Analysis')]
        projects.sort(key=lambda pair:0 if pair[1][0]=='TryOn - Virtual Wardrobe' else 1)
    summary=opening+' '+focus
    relevant=', '.join(matched[:7]) or 'Python and production AI applications'
    note=(f"I am interested in the {title} role at {job['Company']}. I bring 2 years of Python and AI/ML experience at Impactsure Technologies, "
          f"where I build banking-sector applications and lead an 8-member team on Axis Bank's Bank Guarantee project. "
          f"The description's focus on {relevant} aligns with my documented skills and project work. My production work includes OCR extraction at 98.5% accuracy and RAG retrieval at 97.3% accuracy. "
          "I would welcome the opportunity to discuss how that experience can support this role.")
    return {'summary':summary,'skills':ordered,'matched_keywords':matched,
            'bullets':[b[1][0] for b in bullets], 'projects':[(p[1][0],p[1][1]) for p in projects], 'cover_note':note}


def generate(job,app,directory):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,KeepTogether
    from pypdf import PdfReader
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    company=re.sub(r'[^A-Za-z0-9]','',job['Company'])[:12] or 'Role'
    data=plan(job,app)
    version=hashlib.sha256(json.dumps({'plan':data,'contact':{k:app[k] for k in ('full name','email','phone','linkedin','github')}},sort_keys=True).encode()).hexdigest()[:6]
    path=directory/f'Prajwath_{company}_{job["id"]}_{version}.pdf' 
    normal=ParagraphStyle('Body',fontName='Helvetica',fontSize=9.6,leading=12.2,spaceAfter=3,textColor=colors.HexColor('#1f2937'))
    small=ParagraphStyle('Small',parent=normal,fontSize=8.5,leading=11,spaceAfter=2)
    head=ParagraphStyle('Section',parent=normal,fontName='Helvetica-Bold',fontSize=10.2,leading=13,spaceBefore=8,spaceAfter=4,textColor=colors.HexColor('#14283d'))
    title=ParagraphStyle('Name',parent=normal,fontName='Helvetica-Bold',fontSize=18,leading=22,spaceAfter=5)
    def p(value,style=normal):return Paragraph(html.escape(ascii_text(value)),style)
    story=[p(app['full name'].upper(),title),p(f"{app['email']} | {app['phone']} | Panjim, Goa, India",small),
           p(f"LinkedIn: {app['linkedin']}",small),p(f"GitHub: {app['github']}",small),
           p(f"TARGET ROLE: {job['Job_Title']} | {job['Company']}",small),
           p('PROFESSIONAL SUMMARY',head),p(data['summary']),
           p('TECHNICAL SKILLS',head),p(' | '.join(data['skills'])),
           p('PROFESSIONAL EXPERIENCE',head),
           p('Full Stack Python Developer - Data Science & AI/ML'),
           p('Impactsure Technologies Pvt. Ltd. | Dec 2024 - Present',small),
           p('Includes a 6-month internship: Dec 2024 - May 2025.',small)]
    for bullet in data['bullets']:story.append(p('- '+bullet))
    story.append(p('SELECTED PROJECTS',head))
    for name,description in data['projects']:story.append(p(name+' - '+description))
    story.extend([p('EDUCATION',head),p('Master of Computer Applications | Goa University | 2024 - 2026 | CGPA: 8.03',small),
                  p('Bachelor of Computer Science | Dhempe College of Arts and Science | 2023 - 2024 | CGPA: 8.31',small),
                  p('CERTIFICATIONS',head),p('Data Science / Language Processing Project - NullClass; Data Visualization Simulation (Power BI & Tableau) - Tata Consultancy Services.',small)])
    doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=38,leftMargin=38,topMargin=30,bottomMargin=30,
        title=f"Prajwath Gowda - {ascii_text(job['Job_Title'])}",author='Prajwath Gowda')
    doc.build(story)
    pdf=PdfReader(path);text='\n'.join(page.extract_text() or '' for page in pdf.pages)
    required=['PRAJWATH GOWDA','PROFESSIONAL EXPERIENCE','EDUCATION','Impactsure','97.3%','98.5%','Dec 2024','May 2025',app['email']]
    missing=[item for item in required if item not in text]
    if missing or len(pdf.pages)!=1:raise ValueError(f'PDF QA failed: pages={len(pdf.pages)}, missing={missing}')
    # A real text layer and standard section headings are checked, not an invented ATS score.
    text_path=path.with_suffix('.txt');text_path.write_text(text)
    png=path.with_suffix('.png')
    subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','1500','-png',str(path),str(path.with_suffix(''))],check=True,capture_output=True)
    manifest={'job_id':job['id'],'company':job['Company'],'role':job['Job_Title'],'source_resume_sha256':hashlib.sha256(Path(app['resume path']).read_bytes()).hexdigest(),
              'jd_sha256':hashlib.sha256(job['jd'].encode()).hexdigest(),'pdf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'pdf':str(path),'preview':str(png),'pages':1,'text_layer_verified':True,'matched_keywords':data['matched_keywords'],'cover_note':data['cover_note']}
    path.with_suffix('.json').write_text(json.dumps(manifest,indent=2))
    return manifest
