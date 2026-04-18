# CLAUDE.md — VetAssist Architecture Guide

This file is for Claude Code and any developer continuing work on this project.
Read this before making changes.

---

## Project purpose

VetAssist is a one-week hackathon MVP built for the Wilcore Innovation Challenge.
It helps veterans identify likely VA benefits, understand what forms they need,
see which fields can be prefilled from their profile, and ask a conversational
assistant for missing information.

---

## Intended architecture

```
main.py                 FastAPI app — all routes live here
services/
  eligibility.py        Rules-based benefit matching (no ML, no API calls)
  form_matcher.py       Maps benefits → forms, prefills fields from profile
  claude_chat.py        Calls Anthropic Claude API (falls back to placeholder)
data/
  veterans.json         3 synthetic veteran profiles (no real PII)
  benefits_rules.json   5 benefit definitions with eligibility rules
  forms_catalog.json    5 VA form definitions with field metadata
templates/
  index.html            Single-page frontend (vanilla JS, no framework)
```

**The data layer is JSON files.** There is no database. Do not add one.
This is correct for the MVP — it makes the project easy to run, easy to demo,
and easy to explain to non-technical judges.

---

## What is real vs. what is a placeholder

| Component | Status |
|---|---|
| Veteran profile loading | REAL — reads from data/veterans.json |
| Eligibility engine | REAL — Python rules in services/eligibility.py |
| Form field prefill | REAL — maps profile fields to form fields |
| Conversational assistant | REAL if ANTHROPIC_API_KEY is set; PLACEHOLDER otherwise |
| Document upload / OCR | PLACEHOLDER — endpoint exists, returns 501 |
| PDF generation / output | PLACEHOLDER — endpoint exists, returns 501 |
| VA API integration | PLACEHOLDER — uses local JSON instead |
| Authentication | NOT IMPLEMENTED — not needed for MVP |
| Database | NOT IMPLEMENTED — not needed for MVP |

---

## Key constraints — do not violate these

- **No database.** JSON files are the data layer.
- **No authentication.** Not needed for a local demo.
- **No cloud deployment.** This runs locally with `uvicorn`.
- **No complex frontend framework.** One HTML file with vanilla JS.
- **No overengineering.** If a feature is not needed for the main happy-path demo, skip it.
- **Minimal dependencies.** Only what is in requirements.txt.

---

## Running the app

```bash
pip install -r requirements.txt
cp .env.example .env
# optionally add your ANTHROPIC_API_KEY to .env
uvicorn main:app --reload
# open http://localhost:8000
```

The app runs without an API key — Claude responses will be placeholder strings.

---

## Happy-path demo flow

1. User opens http://localhost:8000
2. Selects a veteran from the dropdown (e.g. Maria Sanchez)
3. Clicks "Load Profile" — sees profile summary
4. Sees eligible benefits highlighted in green
5. Sees suggested VA forms with prefilled fields and missing fields identified
6. Types a question in the chat box — receives a response from Claude (or placeholder)
7. Can navigate to VA.gov info links for any form

This is the one flow to keep working. Do not break it.

---

## What to build next (post-MVP)

These are clearly labeled as TODO in the code. Add them in order of priority:

1. **Document upload + OCR** — Accept DD214 or flat PDF, extract text, merge into prefill context
   - Tools: pytesseract (local), AWS Textract (cloud/federal)
   - Endpoint: POST /api/upload

2. **Printable output** — Generate a PDF package with prefilled fields, cover note, instructions
   - Tools: reportlab or weasyprint
   - Endpoint: POST /api/generate-output

3. **Multi-turn conversation history** — Persist chat turns server-side per session

4. **Real VA Forms API** — Replace forms_catalog.json with live data from api.va.gov

5. **AWS Bedrock integration** — Swap Anthropic direct API for Bedrock Claude endpoint
   - Required for FedRAMP / federal deployment
   - Claude model remains the same — only the SDK call changes

6. **Authentication** — Add for any real deployment (VA PIV or login.gov integration)

7. **Database** — Replace JSON files with PostgreSQL or DynamoDB once data grows

---

## Notes for federal deployment path

- Use AWS Bedrock (us-east-1 or us-gov-west-1) instead of direct Anthropic API
- Deploy on FedRAMP-authorized infrastructure (AWS GovCloud)
- Ensure Section 508 accessibility compliance in the frontend
- Store no real veteran PII in the MVP — profile data is synthetic
- Future: integrate with VA Identity Service or login.gov for authentication
- Consider FISMA Low/Moderate ATO path for a VA pilot
