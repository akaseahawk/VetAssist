# VetAssist — Collaborator Brief

**Wilcore Innovation Challenge | April 20–27, 2026**

Hey — I'm building something for the challenge and wanted to show you what it is
before asking if you're interested in jumping in. Read this first, then decide.
No pressure either way.

---

## What we're building

**VetAssist** — an AI assistant that helps veterans figure out their VA benefits
and complete the required paperwork.

Here's the short version of why it matters:

> The average VA disability claim takes **102 days** to process —
> and that clock doesn't even start until the veteran figures out which forms to file.
> Most of them are still paper.

VetAssist changes that. You open it, it looks at your profile, tells you which
benefits you likely qualify for, shows you which forms you need, and prefills
everything it already knows. For the rest, it asks you in plain language — one
question at a time — like a conversation, not a questionnaire.

The output is printable or email-ready. No re-entering the same name, SSN, and
service dates on five different forms. Done once. Done right.

---

## The demo flow (what judges will see)

```mermaid
flowchart TD
    S1["Step 1\nSelect Veteran\nProfile"] --> S2["Step 2\nBenefits Worth\nExploring"]
    S2 --> S3["Step 3\nChoose a Form"]
    S3 --> S4["Step 4\nConfirm Your Info"]
    S4 --> S5{"Missing fields?"}

    S5 -->|"Has a source doc\ne.g. DD-214"| S5A["Step 5A\n📷 Photo your document\nClaude vision reads it\n— not OCR —"]
    S5A --> S5B["Review extracted fields\nEditable inputs — correct anything\nClick Confirm to populate"]
    S5B --> S6["Step 6\nChat fills the rest\none question at a time"]
    S5 -->|"No source doc\nask directly"| S6

    S1 -.->|"Veteran dropdown\n+ Load Profile button"| S1
    S2 -.->|"Disclaimer banner first\nBenefit cards: reason + VA.gov link"| S2
    S3 -.->|"Form tabs per benefit\ne.g. VA 21-526EZ"| S3
    S4 -.->|"Known fields (green) + Missing fields (amber)\nAll editable inputs\n'Confirm All & Continue'"| S4
    S6 -.->|"Claude handles any remaining gaps\nin plain conversational language"| S6

    style S1 fill:#f5f5f5,stroke:#999
    style S2 fill:#e8f0fe,stroke:#4285f4
    style S3 fill:#e8f0fe,stroke:#4285f4
    style S4 fill:#fef9e7,stroke:#f0ad4e
    style S5A fill:#fff3cd,stroke:#ffc107
    style S5B fill:#fff3cd,stroke:#ffc107
    style S6 fill:#e0f0e0,stroke:#34a853
```

In the demo, we follow **Maria** — an Army veteran, two combat deployments,
30% disability rating for PTSD. She knows she may have benefits she hasn't filed for.
She opens VetAssist. In under two minutes, she knows exactly what she qualifies for,
which forms she needs, and what to bring.

---

## What's already done

The foundation is built and running locally. Here's where things stand:

**Working today:**
- FastAPI backend (Python, runs locally in one command)
- 3 synthetic veteran profiles — different branches, disabilities, service histories
- Claude-first eligibility — Claude reads each profile using its own VA knowledge
  and surfaces what's worth exploring. Hardcoded rules engine kicks in as a fallback
  when no API key is set. **No hardcoded decisions in the default path.**
- 5 real VA forms with field-level metadata and VA.gov links
- Field prefill logic — knows which fields it can fill vs. what to ask for
- **Document photo-to-prefill** — when a field is missing, the UI shows which document
  likely has it (e.g. DD-214). The veteran can photograph that document; Claude reads it
  using multimodal vision (not OCR — it understands the form semantically), extracts the
  fields, and presents them for the veteran to confirm before anything populates
- Conversational Claude assistant (live with API key, graceful placeholder without)
- Single-page HTML frontend with disclaimer banner, benefit cards, form tables, chat,
  document upload button on missing field rows, and vision confirmation modal

**Already in the repo:**
- Mockup images of DD-214, 21-4142, and 21-0781 in `forms_to_verify/` —
  use these to demo the document photo-to-prefill flow during the video

**Not built yet (intentionally):**
- PDF output / printable package (deferred — doesn't affect the main demo)
- Authentication / database (not needed for a local MVP)

---

## Where I need help — and where you fit

I'm not going to give you a generic role. Here's where the project actually needs skills.

---

### Frontend & Accessibility Role

**Background needed:** Frontend engineering, design systems, accessibility (Section 508 / WCAG).

What the UI does right now: it's functional. Veteran selector, benefit cards with
disclaimers, form table with prefill status, chat box. It works.
It's not something you'd be proud to show at a presentation.

**Here's the UX flow you're working with:**

```mermaid
flowchart TD
    FT(["Veteran lands on\nStep 3 — Field Table"])

    FT --> PF["Known fields (green):\nPrefilled from profile — editable input\nVeteran can correct any value"]
    FT --> MF["Missing fields (amber):\nEmpty editable input\n📷 Upload button if a source doc is known"]

    PF --> EDIT["Veteran reviews and edits\nany value inline"]
    MF --> FILL["Veteran types in answer\nor uploads a document photo"]
    FILL --> VISION["Claude reads photo — vision, not OCR\nExtracts fields — veteran confirms each one"]

    EDIT --> CONF
    VISION --> CONF

    CONF(["Veteran clicks\n'Confirm All & Continue'"])
    CONF --> CHAT["Chat opens\nVetAssist greets veteran\nby name + branch"]
    CHAT --> LOOP["Handles any remaining gaps\nin plain conversational language"]
    LOOP --> ANS["Veteran types answer\nAssistant confirms"]
    ANS --> LOOP

    style VISION fill:#fff3cd,stroke:#ffc107
    style CHAT fill:#e8f0fe,stroke:#4285f4
    style CONF fill:#fef9e7,stroke:#f0ad4e
```

**Where this role makes the project:**

1. **Visual polish on `templates/index.html`**
   The entire UI is one HTML file with vanilla CSS — no framework, no build step.
   Pull it up, make it look like something Wilcore would be proud to demo.
   - Priority 1: Loading states (benefit spinner, form tab loading)
   - Priority 2: Field table hierarchy — prefilled vs. missing should read instantly
   - Priority 3: Paper form warning badge prominence (non-digitized forms need a
     clear visual signal — veterans need to know they may need to print and mail)

2. **The "before/after" designed visual**
   The strongest moment in our presentation will be a side-by-side: what a veteran
   does today (Google, paper forms, confusion) vs. what VetAssist does.
   This is the most important non-code deliverable. Figma, Canva, or designed HTML —
   whatever you're fastest in.

3. **Section 508 accessibility baseline**
   Since Wilcore has federal aspirations for this, judges will think about Section 508.
   Basic aria labels, focus states, and WCAG AA color contrast signal that we've
   thought about this seriously.
   - aria-label on all interactive elements (buttons, inputs, select)
   - Visible focus ring on keyboard navigation
   - Color contrast: VA blue (#1a3a6b) on white passes; double-check green status labels

4. **Demo video resolution check**
   The recorded video demo needs to look good at 1080p. Make sure nothing looks
   blurry or misaligned at screen-capture resolution before we record.

**Time ask:** 4–8 hours across the week, heavily weighted toward Wed–Thu.
**What this role owns:** `templates/index.html` visual polish, before/after designed visual,
accessibility baseline, demo video sign-off.

---

### Engineering Role

**Background needed:** Backend engineering, Python, API design, architecture review.

The backend and core logic are in solid shape. What this role provides is a second
set of eyes on the architecture, help tightening the code, and a partner who can
speak credibly to the CTO when hard questions come up.

**Where this role adds real value:**

1. **Document vision review — already built, 1–2 hours to review + test**

   `POST /api/upload` is fully implemented using Claude multimodal vision — not a stub.
   `GET /api/upload/suggestions/{veteran_id}` is also real — it tells the frontend which
   document type has the veteran's missing fields, so the UI can show the "📷 From DD-214"
   button on the right row.

   The frontend also has the full upload flow: hidden file input, upload button per missing field,
   vision confirm modal with editable fields, and `confirmVisionFields()` that merges into state.

   **The job:** test the full flow end-to-end with a real API key:
   ```bash
   # Load Maria (vet_001), select the 21-0781 form
   # Click "From DD-214" on a missing field row
   # Upload: forms_to_verify/DD_214_mockup_example.png
   # Confirm the extracted fields in the modal
   # Verify the field table updates correctly
   ```
   If anything is off, fix it. Read `services/document_vision.py` for the extraction logic
   and `templates/index.html` for the upload/confirm UI. Architecture is in `CLAUDE.md`.

2. **Stress test eligibility edge cases**
   - Malformed date strings in veteran profiles (e.g. `"service_start": null`)
   - Missing profile fields that rules reference (e.g. no `disability_conditions` key)
   - Veteran profile with 0% disability rating but `service_connected_disability: true`
   - Claude returning non-JSON or partial JSON — does the fallback trigger correctly?

   Run these with `python -c "..."` test calls to `discover_benefits()` directly.
   Don't add a test framework — just confirm the happy path and the fallback are bulletproof.

3. **Architecture defense — read CLAUDE.md first**
   When judges ask "how would this work at scale?" or "what would the federal
   deployment look like?" — this role answers credibly.
   `CLAUDE.md` has the full roadmap: local JSON → VA API → Bedrock on GovCloud.
   Help stress-test that story so follow-up questions land well.

4. **Clean install verification**
   Before recording the demo video, do one full clean install:
   ```bash
   git clone https://github.com/akaseahawk/VetAssist
   cd VetAssist
   pip install -r requirements.txt
   uvicorn main:app --reload
   # open http://localhost:8000, run the full happy path with Maria
   ```
   Find anything broken and we fix it together. This is the most important
   quality gate before recording.

**Time ask:** 4–8 hours across the week.
**What this role owns:** Document vision end-to-end test, edge case testing,
architecture Q&A prep, clean install verification.

---

## What the week looks like

| Day | Goal |
|-----|------|
| Mon Apr 20 | Challenge opens — decide if you're in, run the app locally |
| Tue–Wed | Frontend: UI pass. Engineering: code review + upload flow test |
| Thu | Full demo run-through, catch anything broken |
| Fri | Record video demo, finalize submission materials |
| Mon Apr 27 | Deadline 11:59 PM ET |

---

## Getting it running (takes 3 minutes)

```bash
git clone https://github.com/akaseahawk/VetAssist
cd VetAssist
pip install -r requirements.txt
uvicorn main:app --reload
# open http://localhost:8000
```

No API key needed to run the app. The benefit discovery and chat assistant show
graceful fallback responses without one — that's fine for initial review.

---

## Why Wilcore specifically should care about this

Wilcore is an SDVOSB. We work with the VA. This project:
- Directly serves the veteran population we exist to support
- Maps to the challenge themes "Benefits at First Ask" and "Closing the Digital Divide"
- Has a credible path from this demo to a Wilcore federal proposal
- Could realistically become a real thing if it wins

And honestly — it's a project worth doing. Veterans deserve better than a 102-day wait
and a stack of paper forms they have to figure out alone.

---

## Questions?

Just message me. If you want to jump in, let me know which role fits and we'll
divide and conquer. The deadline is tight but the scope is real and the foundation
is already there.
