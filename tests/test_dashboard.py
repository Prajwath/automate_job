"""Dashboard status and refresh behavior, with all HTTP requests intercepted."""
import csv
import io
import unittest
from pathlib import Path


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)
        cls.html = (Path(__file__).resolve().parents[1] / 'dashboard.html').read_text()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.addCleanup(self.context.close)
        self.statuses = ['Applied', 'Needs You', 'Submission uncertain']
        self.failed = False
        self.sources = []
        self.context.route('**/*', self.route)

    def tracker(self):
        buf = io.StringIO()
        columns = ['Application_ID','Company','Job_Title','Location','Target_CTC','Job_URL','Date_Applied','Channel','Sender_Email','Status','Reverted_Back','Response_Date','Notes']
        writer=csv.DictWriter(buf,fieldnames=columns);writer.writeheader()
        for i,status in enumerate(self.statuses,1):
            writer.writerow({'Application_ID':str(i),'Company':f'Company {i}','Job_Title':'Python Developer','Status':status,'Channel':'LinkedIn Easy Apply'})
        return buf.getvalue()

    def route(self,route):
        if 'job_applications.csv' in route.request.url:
            self.sources.append(route.request.url)
            route.fulfill(status=503 if self.failed else 200,content_type='text/csv',body=self.tracker())
        else:
            route.fulfill(status=200,content_type='text/html',body=self.html)

    def test_unconfirmed_entries_are_excluded_from_applied_and_reply_counts(self):
        self.page.goto('http://localhost:5050/dashboard.html')
        self.page.wait_for_function("document.querySelector('#sub').textContent.startsWith('Live')")
        self.assertEqual(self.page.locator('#total').inner_text(),'1')
        self.assertEqual(self.page.locator('#replied').inner_text(),'0 replies')
        self.assertIn('2 not submitted',self.page.locator('#todo').inner_text())

    def test_local_reply_override_cannot_turn_blocked_form_into_applied(self):
        self.page.goto('http://localhost:5050/dashboard.html')
        self.page.wait_for_function("document.querySelector('#sub').textContent.startsWith('Live')")
        self.page.evaluate("overrides['2']='pos'; render()")
        self.assertEqual(self.page.locator('#total').inner_text(),'1')
        self.assertEqual(self.page.locator('#replied').inner_text(),'0 replies')

    def test_automatic_polling_updates_without_reload_and_failure_is_visible(self):
        self.page.goto('http://localhost:5050/dashboard.html')
        self.page.wait_for_function("document.querySelector('#total').textContent==='1'")
        self.statuses[1]='Applied'
        self.page.wait_for_function("document.querySelector('#total').textContent==='2'",timeout=7000)
        self.failed=True
        self.page.evaluate('load()')
        self.page.wait_for_function("document.querySelector('#sub').textContent.includes('Connection lost')")
        self.assertEqual(self.page.locator('#total').inner_text(),'2')

    def test_hosted_dashboard_fetches_canonical_published_tracker(self):
        self.page.goto('https://dashboard.example.test/')
        self.page.wait_for_function("document.querySelector('#sub').textContent.startsWith('Live')")
        self.assertTrue(self.sources[0].startswith('https://raw.githubusercontent.com/prajwath/automate_job/main/job_applications.csv?'))


if __name__=='__main__':
    unittest.main()
