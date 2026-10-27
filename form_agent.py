#!/usr/bin/env python3
"""
Claude-powered form filler used by auto_apply.py.

Collects every unanswered question on an application form (text boxes, text
areas, dropdowns, radio buttons, checkboxes and searchable "combobox"
dropdowns), sends them to Claude together with your resume PDF and
applicant.txt, and fills in the answers Claude returns.

Needs `pip install anthropic` and an API key in ANTHROPIC_API_KEY (or in .env,
or an `ant auth login` profile).
"""

import os
import re
import json
import base64

MODEL = "claude-opus-5-5"

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


def load_dotenv_key(root_dir):
    """Let ANTHROPIC_API_KEY live in .env next to the other secrets."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env_file = os.path.join(root_dir, ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


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
    def __init__(self, applicant, applicant_text, resume_path, root_dir):
        import anthropic  # only needed when the agent is used

        load_dotenv_key(root_dir)
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
        job = f"Company: {row['Company']}\nRole: {row['Job_Title']}\nLocation: {row.get('Location', '')}\nNotes: {row.get('Notes', '')}"
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
                    {"type": "text", "text": f"Job:\n{job}\n\nForm fields:\n{json.dumps(fields, ensure_ascii=False, indent=1)}"},
                ],
            }],
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("Claude declined to answer this form")
        text = next((b.text for b in response.content if b.type == "text"), "")
        answers = json.loads(text).get("answers", [])
        return {a["id"]: a["answer"] for a in answers if not a["skip"] and a["answer"].strip()}


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
