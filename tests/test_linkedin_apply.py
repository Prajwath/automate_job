"""Offline regression tests. All browser pages and tracker files are synthetic."""
import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import linkedin_apply as bot


class RulesAndTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.csv = Path(self.temp.name) / "jobs.csv"
        self.patches = patch.multiple(bot, CSV_FILE=self.csv, LOG_FILE=Path(self.temp.name) / "test.log")
        self.patches.start()
        self.addCleanup(self.patches.stop)
        self.app = {"email": "candidate@example.test", "expected ctc": "12 - 15 LPA"}
        self.job = {"Company": "Example", "Job_Title": "Python Developer",
                    "Job_URL": "https://www.linkedin.com/jobs/view/123/", "Location": "Bengaluru (hybrid)"}

    def test_canonical_url_handles_slug_query_and_trailing_slash(self):
        self.assertEqual(bot.canonical_url("https://in.linkedin.com/jobs/view/python-dev-at-example-123/?trackingId=x"), self.job["Job_URL"].rstrip("/"))
        self.assertNotEqual(bot.canonical_url("https://example.test/jobs/view/123"), bot.canonical_url(self.job["Job_URL"]))

    def test_update_existing_to_apply_instead_of_appending_duplicate(self):
        row = bot.record_job(self.job, self.app, "To Apply", "Queued")
        self.assertNotIn(bot.canonical_url(self.job["Job_URL"]), bot.get_existing_applied_urls())
        updated = bot.record_job(self.job, self.app, "Applied", "Confirmed")
        _, rows = bot.read_tracker()
        self.assertEqual(len(rows), 1)
        self.assertEqual(updated["Application_ID"], row["Application_ID"])
        self.assertEqual(updated["Sender_Email"], self.app["email"])
        self.assertTrue(updated["Date_Applied"])
        self.assertIn(bot.canonical_url(self.job["Job_URL"]), bot.get_existing_applied_urls())

    def test_blocked_and_uncertain_jobs_are_not_retried(self):
        for status in ("Needs You", "Submission uncertain", "Skipped"):
            bot.record_job(self.job, self.app, status, "Needs review")
            self.assertIn(bot.canonical_url(self.job["Job_URL"]), bot.get_existing_applied_urls())

    def test_header_only_csv_retains_columns(self):
        with open(self.csv, "w", newline="") as f:
            csv.writer(f).writerow(bot.COLUMNS + ["Extra"])
        bot.record_job(self.job, self.app, "Applied", "Confirmed")
        fields, rows = bot.read_tracker()
        self.assertIn("Extra", fields)
        self.assertEqual(rows[0]["Status"], "Applied")

    def test_numbers_and_skill_experience_are_never_guessed(self):
        app = {"expected ctc": "12 - 15 LPA", "current ctc": "8 LPA",
               "notice period": "Immediate / 30 Days", "total experience": "2.5 years"}
        self.assertIsNone(bot.answer_for("Expected CTC in LPA", app, {}, "number"))
        self.assertIsNone(bot.answer_for("Notice period in days", app, {}, "number"))
        self.assertIsNone(bot.answer_for("How many years of experience do you have with Rust?", app, {}))
        self.assertEqual(bot.answer_for("Years of experience", app, {}, "number"), "2.5")
        self.assertEqual(bot.answer_for("Current CTC (LPA)", app, {}, "number"), "8")
        self.assertIsNone(bot.answer_for("Current salary in INR", app, {}, "number"))

    def test_completed_whole_years_are_never_rounded_up(self):
        app = {'total experience': '2.5 years'}
        self.assertEqual(bot.answer_for('How many years of work experience do you have? (Only Whole Numbers Allowed)', app, {}, 'number'), '2')

    def test_confirmed_notice_period_controls_urgent_start_answer(self):
        app = {'notice period':'30 Days'}
        self.assertEqual(bot.answer_for('We must fill this position urgently. Can you start immediately?',app,{},'radio'),'No')
        self.assertEqual(bot.answer_for('Notice period in days',app,{},'number'),'30')

    def test_authorization_is_not_assumed_for_foreign_country(self):
        app = {"work authorization": "Yes"}
        self.assertIsNone(bot.answer_for("Are you authorized to work in USA?", app, {}))
        self.assertEqual(bot.answer_for("Are you authorized to work in India?", app, {}), "Yes")

    def test_exact_answers_and_never_fill_precedence(self):
        answers = {bot.normalize("What is your expected CTC in LPA?"): "14"}
        self.assertEqual(bot.answer_for("What is your expected CTC in LPA? *", {}, answers), "14")
        self.assertIsNone(bot.answer_for("What is your expected CTC in LPA?", {"never auto-fill": "ctc"}, answers))

    def test_empty_profile_setting_uses_default_not_project_root(self):
        with patch.object(bot, "setting", return_value=""):
            self.assertNotEqual(bot.default_profile(), bot.ROOT_DIR)


class OfflineBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch(headless=True)
        except Exception:
            cls.pw.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.context.route("**/*", lambda route: route.abort())
        self.page = self.context.new_page()
        self.page.set_default_timeout(1000)
        self.temp = tempfile.TemporaryDirectory()
        self.resume = Path(self.temp.name) / "resume.pdf"
        self.resume.write_bytes(b"%PDF-1.4 offline test")
        self.app = {"email": "candidate@example.test", "resume path": str(self.resume)}
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.context.close)

    def form(self, fields="", action="document.querySelector('.jobs-easy-apply-modal').innerHTML = '<p>Application sent</p>'"):
        self.page.set_content(f"""
        <button onclick="document.querySelector('.jobs-easy-apply-modal').hidden=false">Easy Apply</button>
        <div class="jobs-easy-apply-modal" hidden>
          {fields}
          <button onclick="window.submitted=(window.submitted||0)+1; {action}">Submit application</button>
        </div>
        """)

    def test_confirmation_required_and_before_submit_runs_first(self):
        self.form('<label>Email<input name="email" type="email" required></label><input type="file" name="resume">')
        calls = []
        result = bot.apply_job(self.page, self.app, before_submit=lambda: calls.append(self.page.evaluate("window.submitted || 0")), confirmation_timeout=0.3)
        self.assertEqual(result.status, "Applied")
        self.assertEqual(calls, [0])
        self.assertEqual(self.page.evaluate("window.submitted"), 1)

    def test_missing_confirmation_is_uncertain_and_never_retries(self):
        self.form(action="")
        result = bot.apply_job(self.page, self.app, confirmation_timeout=0.1)
        self.assertEqual(result.status, "Submission uncertain")
        self.assertEqual(self.page.evaluate("window.submitted"), 1)

    def test_unknown_required_question_blocks_submission(self):
        self.form('<label>Years with Rust<input type="number" required></label>')
        result = bot.apply_job(self.page, self.app)
        self.assertEqual(result.status, "Needs You")
        self.assertIn("Rust", result.reason)
        self.assertIsNone(self.page.evaluate("window.submitted"))
        self.assertTrue(self.page.locator(".jobs-easy-apply-modal").is_visible())

    def test_required_consent_is_not_silently_accepted(self):
        self.form('<label>Accept terms<input type="checkbox" required></label>')
        self.assertEqual(bot.apply_job(self.page, self.app).status, "Needs You")
        self.assertFalse(self.page.get_by_role("checkbox").is_checked())

    def test_standalone_asterisk_required_field_blocks(self):
        self.form('<label>Required custom question *<input type="text"></label>')
        self.assertEqual(bot.apply_job(self.page, self.app).status, "Needs You")
        self.assertIsNone(self.page.evaluate("window.submitted"))

    def test_dropdown_never_matches_no_to_not_applicable(self):
        self.form('<label>Visa sponsorship<select required><option value="">Select</option><option>Not applicable</option><option>No</option></select></label>', action="")
        self.app["visa sponsorship"] = "No"
        bot.apply_job(self.page, self.app, confirmation_timeout=0.1)
        self.assertEqual(self.page.locator("select").input_value(), "No")

    def test_radio_sponsorship_and_resume_upload(self):
        self.form('''<fieldset><legend>Visa sponsorship</legend>
        <label>Yes<input type="radio" name="sponsor" required></label>
        <label>No<input type="radio" name="sponsor" required></label></fieldset>
        <input type="file" name="resume"><input type="file" name="cover-letter">''', action="")
        self.app["visa sponsorship"] = "No"
        result = bot.apply_job(self.page, self.app, confirmation_timeout=0.1)
        self.assertEqual(result.status, "Submission uncertain")
        self.assertTrue(self.page.get_by_role("radio", name="No", exact=True).is_checked())
        self.assertEqual(self.page.locator('[name=resume]').evaluate("e => e.files[0].name"), "resume.pdf")
        self.assertEqual(self.page.locator('[name=cover-letter]').evaluate("e => e.files.length"), 0)

    def test_custom_radio_options_use_visible_choice_text(self):
        self.form('''<div><p>Are you an Engineering graduate*</p><fieldset role="radiogroup">
        <div role="radio" aria-label="Are you an Engineering graduate" onclick="this.querySelector('input').checked=true"><div><input id="yes" type="radio" name="engineering"><label for="yes"></label></div><p>Yes</p></div>
        <div role="radio" aria-label="Are you an Engineering graduate" onclick="this.querySelector('input').checked=true"><div><input id="no" type="radio" name="engineering"><label for="no"></label></div><p>No</p></div>
        </fieldset></div>''', action="")
        self.app['engineering graduate']='No'
        result=bot.apply_job(self.page,self.app,confirmation_timeout=0.1)
        self.assertEqual(result.status,'Submission uncertain')
        self.assertTrue(self.page.locator('#no').is_checked())
        self.assertFalse(self.page.locator('#yes').is_checked())

    def test_fill_is_scoped_to_application_modal(self):
        self.form('<label>Email<input type="email" required></label>', action="")
        self.page.locator("body").evaluate("e => e.insertAdjacentHTML('afterbegin', '<label>Email<input id=outside required></label>')")
        bot.apply_job(self.page, self.app, confirmation_timeout=0.1)
        self.assertEqual(self.page.locator("#outside").input_value(), "")
        self.assertEqual(self.page.locator('.jobs-easy-apply-modal input').input_value(), self.app["email"])

    def test_multiple_steps(self):
        self.page.set_content('''<button onclick="document.querySelector('.jobs-easy-apply-modal').hidden=false">Easy Apply</button>
        <div class="jobs-easy-apply-modal" hidden><label>Email<input type="email" required></label>
        <button onclick="this.parentElement.innerHTML = `<p>Review</p><button onclick=&quot;this.parentElement.innerHTML='Application sent'&quot;>Submit application</button>`">Next</button></div>''')
        result = bot.apply_job(self.page, self.app, confirmation_timeout=0.3)
        self.assertEqual(result.status, "Applied")

    def test_external_apply_button_is_not_clicked(self):
        self.page.set_content('<button onclick="window.clicked=true">Apply</button>')
        self.assertEqual(bot.apply_job(self.page, self.app).status, "Skipped")
        self.assertIsNone(self.page.evaluate("window.clicked"))

    def test_application_limit_stops_run(self):
        self.form()
        self.page.locator("body").evaluate("e => e.insertAdjacentHTML('afterbegin', '<p>You have reached the daily application limit</p>')")
        result = bot.apply_job(self.page, self.app)
        self.assertTrue(result.stop)
        self.assertEqual(result.status, "Needs You")
        self.assertIsNone(self.page.evaluate("window.submitted"))

    def modern_job(self):
        return '''<section><div><a href="https://www.linkedin.com/company/example/">Example</a>
        <div><p>Python Developer</p></div><p>Bengaluru · 1 day ago · Over 100 applicants</p></div>
        <span>Hybrid</span><span>Full-time</span><button>Easy Apply</button></section>'''

    def test_native_dialog_excludes_background_carousel_next_button(self):
        self.page.set_content('''<section><input aria-label="Search"><button aria-label="Next" onclick="window.backgroundClicked=true">→</button></section>
        <button onclick="document.querySelector('dialog').showModal()">Easy Apply</button>
        <dialog><h2>Apply to Example</h2><label>Email<input type="email" required></label>
        <button onclick="this.closest('dialog').innerHTML='Application sent'">Submit application</button></dialog>''')
        result=bot.apply_job(self.page,self.app,confirmation_timeout=0.3)
        self.assertEqual(result.status,'Applied')
        self.assertIsNone(self.page.evaluate('window.backgroundClicked'))

    def test_loading_native_dialog_never_selects_background_navigation(self):
        self.page.set_content('''<section><input aria-label="Search"><button aria-label="Next" onclick="window.backgroundClicked=true">→</button></section>
        <button id="open">Easy Apply</button><dialog>Loading</dialog>''')
        self.page.evaluate("""() => {
            document.querySelector('#open').onclick=()=>{
                const dialog=document.querySelector('dialog');dialog.showModal();
                setTimeout(()=>{
                    dialog.innerHTML='<h2>Apply to Example</h2><label>Email<input type="email" required></label><button id="send">Submit application</button>';
                    dialog.querySelector('#send').onclick=()=>dialog.innerHTML='Application sent';
                },400);
            };
        }""")
        result=bot.apply_job(self.page,self.app,confirmation_timeout=0.3)
        self.assertEqual(result.status,'Applied')
        self.assertIsNone(self.page.evaluate('window.backgroundClicked'))

    def test_empty_dialog_does_not_hide_portaled_application_controls(self):
        self.page.set_content('''<button onclick="document.querySelector('section').hidden=false">Easy Apply</button>
        <div role="dialog"><button aria-label="Close"></button></div>
        <section hidden><h2>Apply to Example</h2><label>Email<input type="email" required></label>
        <footer><button onclick="this.closest('section').innerHTML='Application sent'">Submit application</button></footer></section>''')
        result = bot.apply_job(self.page, self.app, confirmation_timeout=0.3)
        self.assertEqual(result.status, 'Applied')

    def test_resume_upload_reacquires_portaled_form_after_dom_refresh(self):
        self.page.set_content('''<button onclick="document.querySelector('section').hidden=false">Easy Apply</button>
        <section hidden><h2>Apply to Example</h2><label>Email<input type="email" required></label>
        <input type="file" name="resume" onchange="this.closest('section').removeAttribute('data-li-modal')">
        <footer><button onclick="this.closest('section').innerHTML='Application sent'">Submit application</button></footer></section>''')
        result=bot.apply_job(self.page,self.app,confirmation_timeout=0.3)
        self.assertEqual(result.status,'Applied')

    def test_modern_title_is_paragraph_and_actual_location_is_parsed(self):
        self.page.set_content(self.modern_job())
        job = bot.extract_job(self.page)
        self.assertEqual(job["Company"], "Example")
        self.assertEqual(job["Job_Title"], "Python Developer")
        self.assertEqual(job["Location"], "Bengaluru")
        self.assertEqual(job["workplace"], "Hybrid")
        self.assertFalse(bot.location_matches("Mumbai Metropolitan Region", "Bengaluru, Karnataka, India"))
        self.assertTrue(bot.location_matches("Bangalore Urban", "Bengaluru, Karnataka, India"))

    def test_modern_cards_filter_city_and_workplace_before_visiting(self):
        html = '''<div role="button" componentkey="job-card-component-ref-111">Python Developer Bengaluru (On-site)</div>
        <div role="button" componentkey="job-card-component-ref-222">Python Developer Mumbai (Hybrid)</div>
        <div role="button" componentkey="job-card-component-ref-333">Python Developer Bangalore (Hybrid)</div>'''
        self.context.unroute("**/*")
        self.context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
        ids = bot.harvest_job_ids(self.page, "http://offline.test/search", location="Bengaluru", workplace="hybrid")
        self.assertEqual(ids, ["333"])

    def test_dry_run_never_calls_application_or_tracker_writer(self):
        self.context.unroute("**/*")
        self.context.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=self.modern_job()))
        fake_pw = MagicMock()
        fake_pw.chromium.launch_persistent_context.return_value = self.context
        manager = MagicMock()
        manager.__enter__.return_value = fake_pw
        args = SimpleNamespace(profile_dir=Path(self.temp.name) / "profile", scheduled=False,
            login=False, headed=False, keywords=["Python Developer"], location="Bengaluru",
            posted_days=7, geo_id="105214831", workplace="hybrid", max=1, dry_run=True)
        with patch("playwright.sync_api.sync_playwright", return_value=manager), \
             patch.object(bot, "get_existing_applied_urls", return_value=set()), \
             patch.object(bot, "harvest_job_ids", return_value=["123"]), \
             patch.object(bot, "log"), \
             patch.object(bot, "apply_job") as apply, patch.object(bot, "record_job") as write:
            self.assertEqual(bot.run_linkedin_bot(args, self.app, {}), 0)
            apply.assert_not_called()
            write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
