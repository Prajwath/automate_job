#!/usr/bin/env python3
"""
AI form filler used by auto_apply.py (Claude or Gemini).

Collects every unanswered question on an application form (text boxes, text
areas, dropdowns, radio buttons, checkboxes and searchable "combobox"
dropdowns), sends them to Claude together with your resume PDF and
applicant.txt, and fills in the answers Claude returns.

Provider, from .env or the environment:
  Gemini: pip install google-genai, GEMINI_API_KEY="..."   (model: gemini-2.5-flash)
  Claude: pip install anthropic,    ANTHROPIC_API_KEY="..." (model: claude-opus-5-5)
Set AI_PROVIDER="gemini" or "claude" to choose when both keys are present.
"""

import os
import re
import json
import base64

MODEL = "claude-opus-5-5"
GEMINI_MODEL = "gemini-2.5-flash"
ENV_KEYS = ("AI_PROVIDER", "GEMINI_API_KEY", "ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You fill in job application forms for one candidate.

You get the candidate's resume (PDF), their applicant details, the job, and a list of form fields. Return an answer for every field id you were given.

Rules:
- Use only facts from the resume and applicant details. Never invent employers, degrees, certifications, dates, skills or numbers.
- For dropdown, radio, checkbox and combobox fields, "answer" must be copied exactly from that field's options. For checkbox groups where several options apply, join them with " || ".
- Yes/no eligibility questions (work authorization, sponsorship, relocation, hybrid/office days, notice period) must match the applicant details truthfully.
- Questions asking for a number (years, CTC, days) get a plain number unless the field clearly wants text.
- Free-text questions (why this company, cover letter, describe a project): first person, specific to this company and role, grounded in the resume, under 120 words, no clichés, no markdown.
- Demographic questions (gender, race, ethnicity, disability, veteran status): use the applicant details if they answer it, otherwise pick the "decline to answer" style option, or set skip if there is none.
- Required consent checkboxes (privacy policy, data processing, "I confirm the information is accurate") should be checked: answer with the option text.
- If you can't answer a field truthfully from the information given, set skip to true and leave answer empty. Never guess at facts.
"""

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "answer": {"type": "string"},
                    "skip": {"type": "boolean"},
                },
                "required": ["id", "answer", "skip"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["answers"],
    "additionalProperties": False,
}

# Tags every visible, still-empty field with data-aa-id and returns its label, type and options.
COLLECT_JS = r"""() => {
  const clean = s => (s || '').replace(/\s+/g, ' ').replace(/[*✱]/g, '').trim();
  const visible = e => !!(e.offsetParent || e.getClientRects().length);
  const labelFor = el => {
    if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return clean(l.innerText); }
    const by = el.getAttribute('aria-labelledby');
    if (by) { const t = by.split(' ').map(i => document.getElementById(i)).filter(Boolean).map(n => n.innerText).join(' '); if (t.trim()) return clean(t); }
    if (el.getAttribute('aria-label')) return clean(el.getAttribute('aria-label'));
    const wrap = el.closest('label'); if (wrap) return clean(wrap.innerText);
    let node = el.parentElement;
    for (let i = 0; i < 5 && node; i++, node = node.parentElement) {
      const l = node.querySelector('label, legend, .application-label, .text, [class*=label]');
      if (l && !l.contains(el)) return clean(l.innerText);
    }
    return clean(el.getAttribute('placeholder') || el.name || '');
  };
  const required = el => el.required || el.getAttribute('aria-required') === 'true' || /\*|✱/.test((el.closest('div,fieldset,label') || el).innerText.slice(0, 200));
  let n = 0; const out = []; const seenGroups = new Set();
  const tag = el => { const id = 'f' + (n++); el.setAttribute('data-aa-id', id); return id; };

  for (const el of document.querySelectorAll('input, textarea, select, [role=combobox]')) {
    if (!visible(el) || el.disabled || el.closest('[data-aa-skip]')) continue;
    const type = (el.getAttribute('type') || el.tagName).toLowerCase();
    if (['hidden', 'submit', 'button', 'file', 'search', 'image', 'reset'].includes(type) && el.getAttribute('role') !== 'combobox') continue;

    if (type === 'radio' || type === 'checkbox') {
      const key = el.name || labelFor(el);
      if (seenGroups.has(key)) continue;
      seenGroups.add(key);
      const members = el.name ? [...document.querySelectorAll(`input[name="${CSS.escape(el.name)}"]`)] : [el];
      if (members.some(m => m.checked)) continue;
      const box = el.closest('fieldset, [role=radiogroup], [role=group]');
      let groupLabel = '';
      if (box) {
        const legend = box.querySelector('legend, [class*=label], .text');
        groupLabel = legend ? legend.innerText : '';
      } else if (members.length > 1) {
        let common = members[0].parentElement;
        while (common && !members.every(m => common.contains(m))) common = common.parentElement;
        const head = common && [...common.children].find(c => !c.querySelector('input') && c.innerText.trim());
        groupLabel = head ? head.innerText : '';
      } else {
        groupLabel = labelFor(el);
      }
      const options = members.map(m => clean((m.labels && m.labels[0] && m.labels[0].innerText) || m.closest('label')?.innerText || m.value));
      const id = tag(el);
      members.forEach((m, i) => m.setAttribute('data-aa-opt', id + ':' + i));
      out.push({ id, kind: type === 'radio' ? 'radio' : (members.length > 1 ? 'checkbox_group' : 'checkbox'),
                 label: clean(groupLabel || labelFor(el)).slice(0, 300), options, required: required(el) });
      continue;
    }
    if (el.getAttribute('role') === 'combobox' || el.closest('[class*=select__control]')) {
      const shown = el.closest('[class*=select__control], [class*=container]');
      if (shown && shown.querySelector('[class*=single-value], [class*=multi-value]')) continue;
      out.push({ id: tag(el), kind: 'combobox', label: labelFor(el).slice(0, 300), options: [], required: required(el) });
      continue;
    }
    if (el.tagName === 'SELECT') {
      if (el.value) continue;
      const options = [...el.options].map(o => o.text.trim()).filter(t => t && !/^(select|choose|--)/i.test(t));
      out.push({ id: tag(el), kind: 'select', label: labelFor(el).slice(0, 300), options, required: required(el) });
      continue;
    }
    if (el.value) continue;
    out.push({ id: tag(el), kind: el.tagName === 'TEXTAREA' ? 'textarea' : 'text', label: labelFor(el).slice(0, 300), options: [], required: required(el) });
  }
  return out;
}"""


def load_dotenv_keys(root_dir):
    """Let the API keys live in .env next to the other secrets."""
    env_file = os.path.join(root_dir, ".env")
    if not os.path.exists(env_file):
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.strip().partition("=")
            value = value.strip().strip('"').strip("'")
            if key in ENV_KEYS and value and not os.environ.get(key):
                os.environ[key] = value


def make_agent(applicant, applicant_text, resume_path, root_dir):
    """Pick Gemini or Claude from AI_PROVIDER / whichever API key is set."""
    load_dotenv_keys(root_dir)
    provider = os.environ.get("AI_PROVIDER", "").lower()
    if not provider:
        provider = "gemini" if os.environ.get("GEMINI_API_KEY") else "claude"
    if provider == "gemini":
        return GeminiAgent(applicant, applicant_text, resume_path)
    return FormAgent(applicant, applicant_text, resume_path, root_dir)


def job_prompt(row, fields):
    job = f"Company: {row['Company']}\nRole: {row['Job_Title']}\nLocation: {row.get('Location', '')}\nNotes: {row.get('Notes', '')}"
    return f"Job:\n{job}\n\nForm fields:\n{json.dumps(fields, ensure_ascii=False, indent=1)}"


def parse_answers(text):
    answers = json.loads(text).get("answers", [])
    return {a["id"]: a["answer"] for a in answers if not a.get("skip") and a.get("answer", "").strip()}


def collect_fields(page, never=()):
    fields = page.evaluate(COLLECT_JS)
    kept = []
    for f in fields:
        if any(n in f["label"].lower() for n in never):
            continue
        if f["kind"] == "combobox":
            f["options"] = combobox_options(page, f["id"])
        kept.append(f)
    return kept


def combobox_options(page, field_id):
    """Open a searchable dropdown just long enough to read its options."""
    el = page.locator(f'[data-aa-id="{field_id}"]')
    try:
        el.click(timeout=3000)
        page.wait_for_timeout(400)
        opts = page.locator("[role=option], [class*=select__option]").all_inner_texts()
        page.keyboard.press("Escape")
        return [o.strip() for o in opts if o.strip()][:80]
    except Exception:
        return []


class FormAgent:
    """Claude provider."""
    name = f"Claude ({MODEL})"

    def __init__(self, applicant, applicant_text, resume_path, root_dir):
        import anthropic  # only needed when the agent is used

        self.client = anthropic.Anthropic()
        self.applicant = applicant
        with open(resume_path, "rb") as f:
            resume_b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        # Same bytes for every job, so this prefix is cached across applications.
        self.profile_blocks = [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": resume_b64},
             "title": "Candidate resume"},
            {"type": "text", "text": "Applicant details:\n" + applicant_text, "cache_control": {"type": "ephemeral"}},
        ]

    def answer(self, row, fields):
        """Ask Claude for answers. Returns {field_id: answer} for fields it could answer."""
        if not fields:
            return {}
        response = self.client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": ANSWER_SCHEMA}},
            messages=[{
                "role": "user",
                "content": self.profile_blocks + [
                    {"type": "text", "text": job_prompt(row, fields)},
                ],
            }],
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("Claude declined to answer this form")
        text = next((b.text for b in response.content if b.type == "text"), "")
        return parse_answers(text)


class GeminiAgent:
    """Gemini provider."""
    name = f"Gemini ({GEMINI_MODEL})"

    def __init__(self, applicant, applicant_text, resume_path):
        from google import genai  # only needed when the agent is used
        from google.genai import types

        self.types = types
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        with open(resume_path, "rb") as f:
            self.resume = types.Part.from_bytes(data=f.read(), mime_type="application/pdf")
        self.applicant_text = applicant_text

    def answer(self, row, fields):
        if not fields:
            return {}
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[self.resume, "Applicant details:\n" + self.applicant_text, job_prompt(row, fields)],
            config=self.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_json_schema=ANSWER_SCHEMA,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned no answer for this form")
        return parse_answers(response.text)


def _match(options, answer):
    a = answer.strip().lower()
    for opt in options:
        if opt.strip().lower() == a:
            return opt
    for opt in options:
        if a and (a in opt.lower() or opt.lower() in a):
            return opt
    return None


def fill_answers(page, fields, answers, log=print):
    """Put Claude's answers into the form. Returns labels it couldn't fill."""
    failed = []
    for f in fields:
        ans = answers.get(f["id"])
        if not ans:
            continue
        el = page.locator(f'[data-aa-id="{f["id"]}"]')
        try:
            kind = f["kind"]
            if kind in ("text", "textarea"):
                el.fill(ans)
            elif kind == "select":
                opt = _match(f["options"], ans)
                if not opt:
                    raise ValueError(f"'{ans}' is not an option")
                el.select_option(label=opt)
            elif kind in ("radio", "checkbox", "checkbox_group"):
                wanted = [w.strip() for w in ans.split("||")] if kind == "checkbox_group" else [ans]
                for w in wanted:
                    opt = _match(f["options"], w)
                    if opt is None and kind == "checkbox" and w.lower() in ("yes", "true", "checked"):
                        opt = f["options"][0] if f["options"] else None
                    if opt is None:
                        continue
                    i = f["options"].index(opt)
                    page.locator(f'[data-aa-opt="{f["id"]}:{i}"]').check(force=True)
            elif kind == "combobox":
                el.click()
                el.press_sequentially(ans[:40], delay=20)
                page.wait_for_timeout(500)
                opts = page.locator("[role=option], [class*=select__option]")
                texts = opts.all_inner_texts()
                opt = _match(texts, ans)
                if opt is not None:
                    opts.nth(texts.index(opt)).click()
                else:
                    page.keyboard.press("Enter")
        except Exception as e:
            failed.append(f["label"])
            log(f"   could not fill '{f['label'][:60]}': {e}")
    return failed
