import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import job_batch as batch
import tailored_resume as resume


class TailoringTests(unittest.TestCase):
    def job(self,jd,title='AI Engineer'):
        return {'id':'123','Company':'Example','Job_Title':title,'jd':jd,'advertised_ctc':'Not disclosed'}

    def test_standalone_and_ranged_experience_requirements_are_respected(self):
        for jd in ('Experience: 8–10 Years\nPython automation','Required Qualifications\n5–9 years of overall software development experience. Python', 'Years of Experience Required for Role: 5–8 years\nPython'):
            self.assertIn('exceeds 2',batch.fit(self.job(jd)))
        self.assertEqual(batch.fit(self.job('With nearly 80 years of global experience, we serve companies.\nQualifications\n2+ years of experience in Python.')),'')

    def test_current_employer_is_excluded_even_through_a_recruiter(self):
        for company,jd in [('Impactsure Technologies Pvt. Ltd.','Python RAG'),('Impact Sure Technologies','Python RAG'),('Recruiter','Hiring for Impactsure Technologies: Python RAG')]:
            job=self.job(jd);job['Company']=company
            self.assertIn('Excluded current employer',batch.fit(job))

    def test_newly_confirmed_skills_preserve_knowledge_qualification(self):
        plan=resume.plan(self.job('Python AWS Docker Kubernetes'),{'aws experience':'2 years','docker knowledge':'Yes'})
        self.assertIn('AWS (2 years)',plan['skills'])
        self.assertIn('Docker (knowledge)',plan['skills'])
        self.assertNotIn('Kubernetes',' '.join(plan['skills']))

    def test_monthly_salary_and_mandatory_institution_are_respected(self):
        job=self.job('Python backend APIs')
        job['advertised_ctc']='50K INR/month - 90K INR/month'
        self.assertIn('below 12 LPA',batch.fit(job))
        job['advertised_ctc']='100K INR/month - 150K INR/month'
        self.assertEqual(batch.fit(job),'')
        self.assertIn('institution',batch.fit(self.job('Python AI','AI Researcher (only IIT & CSE passouts)')))

    def test_rag_and_backend_descriptions_prioritize_different_real_evidence(self):
        rag=resume.plan(self.job('Python RAG vector embedding retrieval LLM pipelines'),{})
        backend=resume.plan(self.job('Python Django React Node.js REST APIs SQL web development','Backend Engineer'),{})
        self.assertIn('RAG-based',rag['bullets'][0])
        self.assertNotEqual(rag['skills'],backend['skills'])
        self.assertNotEqual(rag['projects'][0],backend['projects'][0])

    def test_unknown_jd_technologies_are_not_added_as_candidate_skills(self):
        plan=resume.plan(self.job('Python AWS Azure FastAPI Kubernetes Docker RAG'),{})
        skills=' '.join(plan['skills'])
        for term in ('AWS','Azure','FastAPI','Kubernetes','Docker'):self.assertNotIn(term,skills)

    def test_pay_and_benefits_are_not_fabricated(self):
        result=batch.offering('We build Python products.','Example role','hybrid')
        self.assertEqual(result['advertised_ctc'],'Not disclosed')
        self.assertNotIn('insurance',result['perks'])
        self.assertIn('Hybrid',result['perks'])
        result=batch.offering('Benefits: health insurance and flexible working hours. Salary: 12-18 LPA.','','remote')
        self.assertIn('12-18 LPA',result['advertised_ctc'])
        self.assertIn('Health insurance',result['perks'])

    def test_reviewed_pdf_has_extractable_facts_one_page_and_no_invented_skills(self):
        import sys
        sys.path.insert(0,str(resume.ROOT/'.pdf-deps'))
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/'source.pdf';base.write_bytes(b'Source fixture')
            app={'full name':'Prajwath Gowda','email':'candidate@example.test','phone':'+91 0000000000','linkedin':'https://linkedin.com/in/example','github':'https://github.com/example','resume path':str(base)}
            job=self.job('Python RAG vector embedding retrieval LLM pipelines AWS Kubernetes')
            manifest=resume.generate(job,app,Path(tmp)/'tailored')
            pdf=PdfReader(manifest['pdf']);text=' '.join(p.extract_text() for p in pdf.pages)
            self.assertEqual(len(pdf.pages),1)
            for fact in ('97.3%','98.5%','92.8%','Dec 2024','May 2025'):self.assertIn(fact,text)
            self.assertNotIn('Kubernetes',text)
            self.assertTrue(Path(manifest['preview']).exists())


if __name__=='__main__':unittest.main()
