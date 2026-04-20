# VetAssist

**VA Benefits & Forms AI Assistant | Wilcore Innovation Challenge | April 20–27, 2026**

> Veterans deserve better than a stack of confusing forms and a Google search.
> VetAssist identifies likely benefits, explains required forms, prefills what it can,
> and asks plain-language follow-up questions for the rest.

```bash
git clone https://github.com/akaseahawk/VetAssist
cd VetAssist
pip install -r requirements.txt
cp .env.example .env          # optionally add ANTHROPIC_API_KEY
uvicorn main:app --reload
# open http://localhost:8000
```

The app runs without an API key. Claude responses fall back gracefully so the
demo works locally even in an offline environment.

---

## Act 1 — The Problem

### Why Veterans Are Left Behind

> *"The average VA disability claim takes 102.4 days to process — and that clock
> doesn't even start until the veteran figures out which forms to file."*
> — VA Benefits Administration, FY2023 Annual Benefits Report

Veterans earned their benefits through service and sacrifice. Getting those benefits
should not require a law degree, a research project, or a stack of paper forms
with overlapping fields filled out by hand.

**What veterans face today:**

- No single entry point to understand what they qualify for
- 3–5 forms per claim, many still flat PDFs or scanned images — not digital
- The same name, SSN, service dates, and address re-entered on every form
- Form instructions written for administrators, not veterans
- Incomplete submissions → rejections → months of delay → benefits never received

**Diagram 1 — The painful journey today:**

```mermaid
flowchart TD
    A([Veteran suspects\nbenefits exist]) --> B[Google:\nVA disability forms]
    B --> C[VA.gov search\nresults — confusing]
    C --> D[47-page PDF form\nmanual fill-out]
    D --> E[Re-enter same info\non 3–5 forms]
    E --> F{Submission}
    F -->|Incomplete| G([❌ Rejected\n102+ day delay])
    F -->|Wrong form| G
    F -->|Correct| H([✅ Claim begins\n102+ day wait])

    style A fill:#f5f5f5,stroke:#999
    style G fill:#ffe0e0,stroke:#cc0000
    style H fill:#e0f0e0,stroke:#006600
```

*Pain points: No guidance · Paper-first · Repeated data entry · Plain-language gap*

---

## Act 2 — The Solution

### What VetAssist Does

Three things, in order:

**Understand** — Read the veteran's profile and surface the benefits worth exploring
in plain language, with reasons specific to that veteran's situation.

**Prepare** — Show the required forms, prefill every field already known,
and ask for missing information conversationally — one question at a time.

**Connect** — Point the veteran to their VSO, the VA, and the specific VA.gov pages
they need. VetAssist prepares them. The VA and VSO make the final call.

**Diagram 2 — What VetAssist does:**

```mermaid
flowchart TD
    subgraph UNDERSTAND["🔍 UNDERSTAND"]
        U1[Load veteran profile]
        U2[Claude reviews service history\nbranch · discharge · conditions]
        U3[Surface benefits worth exploring\nnot a ruling — plain language]
        U1 --> U2 --> U3
    end

    subgraph PREPARE["📋 PREPARE"]
        P1[Show required forms]
        P2[Prefill every known field\nfrom veteran profile]
        P3[Flag missing fields\nask one at a time via chat]
        P4[Veteran edits any\nprefilled field before continuing]
        P1 --> P2 --> P3 --> P4
    end

    subgraph CONNECT["🔗 CONNECT"]
        C1[VA.gov link on\nevery benefit card]
        C2[VSO contacts\nby branch]
        C3[Warm handoff\ninstructions per benefit]
        C4[VetAssist prepares.\nVSO + VA decide.]
        C1 --> C2 --> C3 --> C4
    end

    UNDERSTAND --> PREPARE --> CONNECT
```

### Before vs. After

**Diagram 3 — Experience comparison:**

```mermaid
flowchart LR
    subgraph BEFORE["❌ Before VetAssist"]
        direction TB
        B1[Veteran guesses\nwhat they qualify for]
        B2[Searches VA.gov manually\nfinds 47-page PDFs]
        B3[Re-enters same info\non 3–5 separate forms]
        B4[Prints · Handwrites\nScans · Mails]
        B5([102+ days\nConfusion])
        B1 --> B2 --> B3 --> B4 --> B5
    end

    subgraph AFTER["✅ With VetAssist"]
        direction TB
        A1[Profile loads automatically\nbenefits identified in seconds]
        A2[Matching forms displayed\nfields prefilled from profile]
        A3[Chat asks only what's missing\none question at a time]
        A4[Printable / email-ready package\nnext steps + VSO contacts]
        A5([30 minutes\nGuided · Clear])
        A1 --> A2 --> A3 --> A4 --> A5
    end

    style B5 fill:#ffe0e0,stroke:#cc0000
    style A5 fill:#e0f0e0,stroke:#006600
```

### Why Now

- The VA processes over 1 million disability claims per year ([VA FY2023 Benefits Report](https://www.benefits.va.gov/REPORTS/abr/))
- Post-9/11 veterans are aging into benefit eligibility windows now
- VA.gov digital modernization is ongoing but form complexity remains
- Claude and other frontier LLMs now reliably explain forms in plain language
- Wilcore's SDVOSB identity and existing VA relationships create a direct path to pilot this

### Impact

> **CEO lens:** Wilcore is an SDVOSB built to serve veterans. This project does exactly that —
> and it comes with a credible path to a federal proposal. A working prototype today is a BD
> asset tomorrow. The before/after story is memorable: veterans go from a 102-day confusion
> to a guided 30-minute process. That's the kind of impact that wins challenges and opens
> doors with VA program offices.

- Reduce time-to-submission from hours or days to under 30 minutes
- Reduce incomplete submissions through prefill and guided follow-ups
- Scalable to any federal benefit program with known forms and eligibility rules
- Maps directly to active VA modernization priorities
- Could support a Wilcore BD opportunity as a Task Order under an existing VA IDIQ or 8(a) sole-source

Quantified (conservative): If 10% of ~1M annual VA disability claims used a tool like this
and saved 2 hours each, that's ~200,000 veteran-hours recovered per year.

---

## Act 3 — How It Works

> **CTO lens (primary):** Every layer is replaceable without touching the others.
> JSON → DB, Anthropic → Bedrock, local → GovCloud. The MVP is the simplest
> credible version of the full architecture — not a throwaway.

### Diagram 4 — System Architecture

```mermaid
flowchart TD
    Browser["🌐 Veteran's Browser\ntemplates/index.html\nvanilla JS · no build step"]

    API["⚙️ FastAPI Application\nmain.py\nGET / · GET /api/veterans\nGET /api/eligibility · GET /api/forms\nPOST /api/chat · POST /api/upload stub"]

    BD["benefit_discovery.py\nClaude-first discovery\nrules fallback"]
    FM["form_matcher.py\nMaps benefits → forms\nPrefills fields · Flags missing"]
    CC["claude_chat.py\nConversational assistant\nBranch-aware greeting"]

    DATA["data/\nveternas.json\nbenefits_rules.json\nforms_catalog.json\nbranch_contacts.json"]

    CLAUDE["☁️ Anthropic Claude API\nor placeholder mode\nwithout API key"]

    Browser -->|HTTP| API
    API --> BD
    API --> FM
    API --> CC
    BD --> DATA
    FM --> DATA
    CC --> DATA
    BD -->|Claude-first| CLAUDE
    CC --> CLAUDE
    API -->|JSON response| Browser
```

### Diagram 5 — Data Flow: MVP → Next Sprint → Federal

```mermaid
flowchart TD
    subgraph MVP["🟢 MVP — Today"]
        M1[Veteran data → data/veterans.json\nsynthetic JSON profiles]
        M2[Benefit rules → data/benefits_rules.json]
        M3[Form catalog → data/forms_catalog.json]
        M4[AI model → Anthropic API direct\nor placeholder mode]
        M5[Infra → Local laptop · uvicorn · no cloud]
    end

    subgraph NEXT["🟡 Next Sprint — Post-Hackathon"]
        N1[Veteran data → DD-214 upload + OCR\nAWS Textract]
        N2[Benefit rules → rules engine\n+ Claude nuance layer]
        N3[Form catalog → VA Forms API\napi.va.gov]
        N4[AI model → Anthropic API\n+ conversation persistence]
        N5[Output → Printable PDF package\nreportlab]
        N6[Infra → Hosted cloud · no auth yet]
    end

    subgraph FED["🔵 Federal Deployment — VA Pilot"]
        F1[Veteran data → VA Identity Service\nlogin.gov]
        F2[Benefit rules → VA Benefits API\nlive data]
        F3[Form catalog → VA Forms API\nlive + versioned]
        F4[AI model → AWS Bedrock Claude\nFedRAMP-authorized]
        F5[Infra → AWS GovCloud\nFISMA Low/Moderate ATO]
        F6[Auth → VA PIV card\nor login.gov identity]
    end

    MVP -->|Sprint 2–4\nweeks 2–4| NEXT
    NEXT -->|Months 2–6\nfederal contract| FED
```

### Diagram 6 — Eligibility Approach: Claude-Driven with Rules Fallback

```mermaid
flowchart TD
    START([Veteran profile loaded]) --> CHECK{ANTHROPIC_API_KEY\nset in environment?}

    CHECK -->|Yes| CLAUDE["☁️ Claude reads full veteran profile\nUses innate VA knowledge\nReasons from: branch · discharge\ncombat history · conditions · deployments"]
    CHECK -->|No| RULES["📋 Hardcoded rules engine\nservices/eligibility.py\nRULE_REGISTRY pattern\nPure Python · fast · auditable"]

    CLAUDE -->|Fails or malformed JSON| RULES
    CLAUDE -->|Success| MERGE
    RULES --> MERGE

    MERGE["Merge with catalog metadata\nTitles · descriptions · VA.gov links"] --> FRAME

    FRAME["🛡️ Always framed as:\n'worth exploring' — NOT 'eligible'\n\n• Plain-language reason\n• Specific to this veteran\n• VA.gov Learn more link\n• Talk to your VSO note"]

    FRAME --> END([Results returned to frontend])

    NOTE["⚠️ VetAssist is NOT the decision maker.\nThe VA and the veteran's VSO are."]
    FRAME --- NOTE

    style CLAUDE fill:#e8f0fe,stroke:#4285f4
    style RULES fill:#fef9e7,stroke:#f0ad4e
    style FRAME fill:#e8f8e8,stroke:#34a853
    style NOTE fill:#fff3cd,stroke:#ffc107
```

### Diagram 7 — Service Interaction Map

```mermaid
flowchart TD
    REQ([HTTP Request]) --> MAIN

    subgraph MAIN["main.py — all routes"]
        R1["GET /api/eligibility/{id}"]
        R2["GET /api/forms/{id}"]
        R3["POST /api/chat"]
        R4["POST /api/upload stub"]
        R5["GET /api/veterans · GET /health"]
    end

    R1 --> BD
    R2 --> BD
    R3 --> BD

    subgraph BD["services/benefit_discovery.py"]
        BD1["discover_benefits(veteran)"]
        BD2["_discover_with_claude()\nAnthropics messages.create()\nparse JSON · merge catalog"]
        BD3["_discover_with_rules() fallback\neligibility.check_eligibility()\nRULE_REGISTRY lookup"]
        BD1 --> BD2
        BD2 -->|"failure / no key"| BD3
    end

    R2 --> FM
    R3 --> FM

    subgraph FM["services/form_matcher.py"]
        FM1["get_forms_for_benefits()"]
        FM2["prefill_fields()"]
        FM3["build_field_summary()"]
        FM1 --> FM2 --> FM3
    end

    R3 --> CC

    subgraph CC["services/claude_chat.py"]
        CC1["chat(message, veteran,\nbenefits, missing, verified,\nhistory, active_form)"]
        CC2["Build system prompt\nprofile + benefits + missing fields"]
        CC3["Load branch_contacts.json\nfor VSO info + branch greeting"]
        CC4["anthropic.messages.create()\nor placeholder string"]
        CC1 --> CC2 --> CC3 --> CC4
    end

    BD --> DATA
    FM --> DATA
    CC --> DATA

    subgraph DATA["data/ — JSON files"]
        D1[veterans.json]
        D2[benefits_rules.json]
        D3[forms_catalog.json]
        D4[branch_contacts.json]
    end

    BD2 --> ANTHROPIC["☁️ Anthropic Claude API"]
    CC4 --> ANTHROPIC

    MAIN -->|JSON response| FE(["🌐 templates/index.html\nvanilla JS frontend"])
```

### Eligibility Engine Detail

**No hardcoded rules by default — Claude drives this.**

When `ANTHROPIC_API_KEY` is set, Claude reads the veteran's profile and uses its
own knowledge of VA benefits to surface what's worth exploring. It reasons from
branch, service dates, discharge type, conditions, and deployments — the same
factors a knowledgeable VSO would consider.

The hardcoded rules engine in `services/eligibility.py` runs only as a fallback
when no API key is configured. This keeps the app fully runnable for demos, development,
and offline environments without compromising the default experience.

**Critical framing (non-negotiable):**
- Always: *"worth exploring"* — never *"eligible"* or *"you qualify"*
- Always: disclaimer banner before any benefit cards
- Always: *"Talk to your VSO or the VA to confirm"* on every benefit
- Always: VA.gov link on every benefit card
- VetAssist is a preparation tool — the VA makes the determination

### What Is Real vs. Mocked

| Component | Status | Notes |
|-----------|--------|-------|
| Veteran profile loading | **Real** | Reads from `data/veterans.json` |
| Benefit discovery | **Real** | Claude-first; rules fallback |
| Form field prefill | **Real** | Maps profile fields to form field metadata |
| VA form titles and VA.gov links | **Real** | 5 actual VA forms with public URLs |
| Conversational assistant | **Real** (with API key) | Graceful placeholder without |
| Document upload / OCR | **Stub** | Endpoint exists; returns descriptive message |
| Printable PDF output | **Stub** | Endpoint exists; returns descriptive message |
| VA API integration | **Stub** | Uses local JSON instead |
| Veteran PII | **Synthetic** | No real data used |

---

## Act 4 — Implementation Path Forward

> **COO lens:** This is a bounded, realistic one-week build with a clear demo path.
> The scope is intentionally constrained — no database, no cloud, no auth.
> Every dependency is justified. If this moves past the challenge, the roadmap
> is phased and each sprint has a defined deliverable.

### Diagram 8 — Two-Track Implementation Roadmap

```mermaid
flowchart TD
    MVP["✅ Week 1 — Hackathon MVP\nSynthetic profiles · Rules engine · Prefill\nClaude chat · Forms catalog · Demo frontend\nDisclaimer framing · VA.gov links"]

    MVP --> TRACK_A & TRACK_B

    subgraph TRACK_A["Track A — Product Depth"]
        direction TB
        A2["Sprint 2 — weeks 2–4\nDD-214 upload + OCR extraction\nPrintable / email-ready output\nConversation persistence"]
        A3["Sprint 3 — months 2–3\nLive VA Forms API integration\nMulti-benefit workflow\nVSO warm handoff integration"]
        A4["Sprint 4 — months 4–6\nVA Benefits API live eligibility\nMulti-agency expansion SSA · HUD\nVA login.gov identity"]
        A2 --> A3 --> A4
    end

    subgraph TRACK_B["Track B — Infrastructure"]
        direction TB
        B2["Sprint 2 — weeks 2–4\nHosted deployment\nDatabase PostgreSQL or DynamoDB\nBasic auth layer"]
        B3["Sprint 3 — months 2–3\nAWS Bedrock Claude endpoint swap\nFedRAMP-authorized infrastructure\nSection 508 accessibility baseline"]
        B4["Sprint 4 — months 4–6\nAWS GovCloud deployment\nFISMA Low/Moderate ATO process\nVA PIV / login.gov integration"]
        B2 --> B3 --> B4
    end

    A4 & B4 --> PILOT(["🎯 VA Pilot\n6–9 months · 3–4 engineers"])

    style MVP fill:#e0f0e0,stroke:#34a853
    style PILOT fill:#e8f0fe,stroke:#4285f4
```

### Feasibility — Why This Works in One Week

| Task | Effort |
|------|--------|
| Backend + eligibility engine | 1–2 days |
| Forms catalog + prefill logic | 1 day |
| Frontend (HTML/JS) | 1 day |
| Claude chat integration | 0.5 days |
| Docs + diagrams + README | 0.5 days |
| Demo recording + submission | 0.5 days |
| **Total** | **~5–6 developer-days** |

**Why it stays simple:**
- No database — JSON files for everything
- No authentication — synthetic data only
- No cloud deployment — runs on any laptop with Python
- One HTML page — no framework, no build step
- Placeholder integrations — OCR and PDF output are stubs; core flow works without them

### Dependencies

- Python 3.10+
- FastAPI + uvicorn (lightweight, production-grade)
- Anthropic Python SDK (optional — app runs without it)
- No paid services required to run the MVP

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Benefit suggestions are not legally precise | Always framed as "worth exploring." Disclaimer before every card. VSO recommended. |
| Form field metadata may drift from VA.gov | Catalog is versioned JSON; easy to update. Direct VA.gov links included. |
| Claude API unavailable or slow | Graceful rules fallback. Demo does not depend on live API. |
| OCR / PDF output not ready for demo | Clearly labeled stub. Core demo works without them. |
| Judges ask about PII / data security | Synthetic data only. No real veteran data stored anywhere. |
| "Why not just use VA.gov?" | VA.gov has no eligibility discovery, no prefill, no conversational guidance. VetAssist bridges those gaps. |

### Federal Applicability

> **CTO lens (primary):** The architecture is intentionally modular and swap-ready.
> The model layer is abstracted in `services/claude_chat.py` — one environment variable
> switches from Anthropic direct to AWS Bedrock. The data layer is JSON today and
> PostgreSQL or DynamoDB tomorrow with no service-layer changes. The eligibility engine
> is pure Python rules — no ML dependency, fully auditable, easy to extend.
> The federal deployment path runs through Bedrock on AWS GovCloud (FedRAMP-authorized)
> with a FISMA Low/Moderate ATO.

- **Primary agency:** Department of Veterans Affairs (VA)
  - Aligns with VA Digital Modernization Strategy and Benefits Modernization priorities
  - Directly addresses the "Benefits at First Ask" theme from the Wilcore challenge
- **Compliance path:**
  - Section 508: accessible HTML, keyboard-navigable, screen-reader compatible with minor additions
  - FedRAMP: swap Anthropic API for AWS Bedrock (Claude) on FedRAMP-authorized infrastructure
  - FISMA Low/Moderate: appropriate for a VA benefits guidance tool with synthetic or de-identified data
- **Contract structure:** Could be delivered as a Task Order under an existing VA IDIQ or via an 8(a) sole-source to Wilcore as an SDVOSB
- **Broader applicability:** Same architecture applies to any federal benefit program with known forms (SSA, HUD, USDA rural benefits)

### Why This Scores Well Against the Wilcore Rubric

| Criterion | Weight | How VetAssist Addresses It |
|-----------|--------|---------------------------|
| **Impact** | 30% | Reduces veteran friction in a high-stakes process; clear federal proposal path |
| **Originality** | 25% | Combines benefit discovery, form mapping, prefill, and conversational guidance — no single VA tool does all four |
| **Feasibility** | 20% | Runs locally today; realistic one-week scope; clear post-MVP roadmap |
| **Clarity** | 15% | One-screen demo, plain-language output, diagrams, before/after story |
| **Collaboration** | 10% | Three defined teammate roles with clear ownership and bounded time commitment |

Directly aligns with the Wilcore challenge themes: *"Benefits at First Ask"*
and *"Closing the Digital Divide"* — and with Wilcore's SDVOSB identity.

---

## Demo Narrative

> This is the story to tell in the video and presentation.

**Before:** Maria is an Army veteran. She knows she may have PTSD from her deployments
in Iraq and Afghanistan. She tries to file a claim but doesn't know where to start.
She Googles "VA disability forms," finds a 47-page PDF, and gives up.

**With VetAssist:**
1. Maria opens VetAssist and selects her profile
2. In seconds, she sees benefits worth exploring: disability compensation, PTSD benefits, VA health care
3. She sees matching forms — one flagged as "not fully digitized"
4. Most fields are already filled in from her profile (name, service dates, branch, conditions)
5. The chat assistant asks her one question at a time for the rest
6. She answers conversationally. The assistant confirms and moves to the next.
7. She sees a summary ready to bring to her VSO or the VA

**The before/after:** hours of confusion → under 30 minutes, guided.

---

## Repository Structure

```
VetAssist/
├── main.py                    # FastAPI app — all routes
├── requirements.txt           # Minimal dependencies
├── .env.example               # Environment variable template
├── .gitignore
├── README.md                  # This file
├── COLLABORATOR_BRIEF.md      # Plain-language teammate recruitment guide
├── CLAUDE.md                  # Architecture guide for Claude Code and developers
├── data/
│   ├── veterans.json          # 3 synthetic veteran profiles
│   ├── benefits_rules.json    # 5 benefit definitions (rules fallback)
│   ├── forms_catalog.json     # 5 VA form definitions with field metadata
│   └── branch_contacts.json  # VSO contacts + branch-specific benefit notes
├── services/
│   ├── benefit_discovery.py   # Claude-first discovery; rules fallback
│   ├── eligibility.py         # Hardcoded rules engine (fallback mode)
│   ├── form_matcher.py        # Form selection and field prefill
│   └── claude_chat.py         # Conversational assistant (Claude API)
├── forms_to_verify/
│   ├── README.md              # Explains folder purpose
│   ├── DD_214_mockup_example.png
│   ├── VA_21-4142_authorization_to_disclose_mockup.png
│   └── VA_21-0781_PTSD_stressor_statement_mockup.png
└── templates/
    └── index.html             # Single-page frontend (vanilla JS, no framework)
```

---

*VetAssist — Wilcore Innovation Challenge 2026*
*Synthetic data only. Not a real VA system. No real veteran PII used.*
*VetAssist helps veterans prepare. The VA and their VSO make the final determination.*
