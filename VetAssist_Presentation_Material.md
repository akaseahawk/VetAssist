# VetAssist Presentation Material

Draft deck: `VetAssist_Wilcore_Innovation_Challenge_Draft.pptx`

This file holds paste-ready narrative material for the Wilcore template, speaker notes, or submission write-up. Demo steps and demo-video coverage are intentionally omitted for now.

## Problem / Opportunity

Veterans often struggle before the VA claim clock even starts. The VA defines a backlogged claim as one pending more than 125 days, and the README cites a January 2025 average processing time of 141.5 days, with early 2026 improvements reducing that to roughly 80 days. VetAssist does not claim to shorten VA adjudication. It addresses the upstream gap: many veterans do not know which benefits are worth exploring, which forms match those benefits, what evidence or source documents they need, or how to avoid submitting an incomplete package. Today, a veteran may move between VA.gov pages, broad federal benefit search tools, paper-first forms, flat PDFs, and VSO appointments while re-entering the same identity and service data. The affected users are veterans and their families, VSOs who help prepare claims, and VA intake teams that receive avoidable incomplete or poorly prepared submissions.

## Solution

VetAssist is a VA benefits and forms preparation assistant. It helps a veteran understand which benefits may be worth exploring, prepare the right form information, and connect with a VSO or VA next step without presenting itself as a decision-maker.

The workflow has three plain-language stages: understand, prepare, and connect. In the understand stage, the veteran can load a synthetic demo profile, enter their own information, or scan a military or VA document when an API key is available. VetAssist uses Claude when configured, with a deterministic rules fallback when the API key is absent, to surface benefits worth exploring. Each result is framed as a possibility, includes a reason tied to the veteran's profile, and points to VA.gov for confirmation.

In the prepare stage, VetAssist maps benefits to the relevant VA forms from the local catalog, prefills fields already known from the profile, flags missing fields, and shows which source documents may contain the missing information. For example, a DD-214 can provide service dates, branch, discharge type, rank, MOS, deployment details, and decorations. Claude vision can read a document photo and return structured values, but the veteran must review and confirm every extracted value before it populates the form table.

In the connect stage, VetAssist generates a preparation package: a cover page with VSO/VA handoff language and branch-specific contacts, plus a field summary sheet showing confirmed and still-missing values. The current MVP intentionally generates a reliable summary package rather than claiming to fill official XFA VA PDFs. The VA and VSO remain the authorities; VetAssist improves readiness before that conversation.

## Expected Impact

- Reduce time-to-preparation from hours or days of searching and manual entry to a target of under 30 minutes for a guided package.
- Reduce repeated data entry by prefilling known identity, contact, service, and condition fields across multiple forms.
- Improve VSO appointment quality by giving the veteran a clear package of confirmed values, missing fields, and source-document hints.
- Conservative quantification from README: if 10% of roughly 1 million annual VA disability claims saved 2 hours each, VetAssist could return about 200,000 veteran-hours per year.
- Originality: no single tool in the project research combines benefit discovery, form matching, field prefill, document vision, conversational follow-up, and VSO/VA handoff in one session.

## Implementation Needs

- MVP already represented in the repo: FastAPI, vanilla frontend, JSON data, Claude-first benefit discovery, rules fallback, form prefill, document vision, source-document suggestions, chat, and PDF package generation.
- Near-term effort: README estimates the hackathon MVP at about 5-6 developer-days. A post-challenge sprint could add hosted deployment, persistence, expanded document types, and more polish in weeks 2-4.
- Pilot effort: README/CLAUDE.md frame a VA pilot as roughly 6-9 months with 3-4 engineers, plus accessibility, security, deployment, and agency coordination work.
- Cost: exact dollars were not present in the project files. A credible estimate needs Wilcore labor rates, cloud/runtime assumptions, security authorization scope, and whether the pilot uses direct Anthropic, AWS Bedrock, GovCloud, or VA-managed infrastructure.
- Dependencies: VA Forms API access, updated form metadata, production database, identity/login.gov or VA identity integration, approved model runtime, audit logging, retention policy, Section 508 review, and FedRAMP/FISMA authorization planning.

## Federal Applicability

The primary federal fit is the Department of Veterans Affairs, especially benefits intake, VSO preparation, claims package readiness, and "Benefits at First Ask" style service flows. The same architecture could later generalize to other federal benefit programs with known rules, forms, and source documents.

For a federal deployment, VetAssist would need Section 508 accessibility alignment, production PII handling, retention limits, encryption, audit trails, approved identity, and a model runtime in an authorized federal environment. The roadmap in CLAUDE.md suggests moving from direct Anthropic API calls to AWS Bedrock Claude and from local runtime to AWS GovCloud or another FedRAMP-authorized environment. A VA pilot would likely need a FISMA Low or Moderate ATO path depending on data sensitivity and system boundary.

Wilcore's SDVOSB background is strategically relevant because the concept directly serves veterans and could become a credible business-development asset for VA modernization or veteran-facing service contracts. A safe contract-structure answer is that VetAssist could begin as a bounded discovery/prototype task order, VSO preparation pilot, or modernization support effort; the exact vehicle should be validated by Wilcore business development before the final submission.

## Risks And Mitigations

- Benefit guidance could be misunderstood as an eligibility ruling. Mitigation: every slide and UI flow should say "worth exploring," not "eligible," and direct veterans to a VSO or the VA.
- VA form metadata may drift. Mitigation: keep the catalog versioned, include VA.gov links, and move to VA Forms API integration after the MVP.
- Claude or document vision may be unavailable. Mitigation: rules fallback for benefit discovery and clear manual entry when no API key is configured.
- Official VA PDFs use XFA fields. Mitigation: current MVP generates a preparation summary instead of pretending to fill official forms.
- PII and sensitive documents would be high risk in production. Mitigation: MVP uses synthetic data only; production needs identity, encryption, retention, audit logging, access control, and ATO planning.

## Q&A Prep

**What is VetAssist?** VetAssist helps veterans identify benefits worth exploring, prepare the right form information, and bring a clearer package to a VSO or the VA.

**Why now?** VA processing has improved, but veterans still face a confusing preparation gap before filing; modern AI can now explain forms, read document photos, and ask plain-language follow-up questions in one guided flow.

**Why Wilcore?** Wilcore's SDVOSB identity and federal delivery focus make a veteran-service preparation tool strategically aligned with both mission and business development.

**Is this making eligibility decisions?** No. VetAssist only surfaces benefits worth exploring and prepares paperwork; the VA and VSO make determinations.

**How is this different from VA.gov?** VA.gov has authoritative information, but VetAssist personalizes the path by combining discovery, form matching, prefill, document vision, and conversational gap filling.

**What data does it store?** The MVP uses synthetic JSON profiles and does not store real veteran data. Production storage requirements are not implemented yet.

**How would this be secured for federal use?** Move to an approved cloud boundary, use Bedrock or another approved model runtime, add identity, encryption, audit logs, retention controls, Section 508 review, and a FISMA/FedRAMP authorization path.

**What would the first pilot look like?** A bounded VA or VSO preparation pilot with synthetic or consented users, limited benefit categories, a current form catalog, no adjudication decisions, and measured time-to-prepared-package.

**What are the biggest risks?** Misstating eligibility, stale form metadata, PII handling, model availability, and overpromising official form-fill support.

**What would it cost to implement?** The repo does not include a dollar estimate. The effort frame is 3-4 engineers over 6-9 months for a pilot, plus cloud, model, security, accessibility, and authorization costs.

**What is the timeline from MVP to pilot?** A realistic path is weeks 2-4 for hosted persistence and document expansion, months 2-3 for VA Forms API/Bedrock/accessibility work, months 4-6 for identity/GovCloud/ATO preparation, and a 6-9 month pilot window.

## Retrieved And Interpreted From Project Files

- MVP purpose, narrative, data points, diagrams, roadmap, impact framing, and source links from `README.md`.
- Architecture, service interactions, real-vs-placeholder status, and post-MVP priorities from `CLAUDE.md`.
- Submission requirements and judging criteria from `INNOVATION_CHALLENGE_TODO.md`.
- VA design-system positioning, accessibility implications, and prototype-notice guidance from `VA_DESIGN_PRESENTATION_POINTS.md` and `VA_DESIGN_UI_AUDIT.md`.
- Working backend routes and constraints from `main.py`.
- Claude-first benefit discovery with rules fallback from `services/benefit_discovery.py`.
- Form matching, prefill, missing-field summaries, and source-document hints from `services/form_matcher.py`.
- Document photo extraction and supported document types from `services/document_vision.py`.
- PDF package behavior and XFA limitation rationale from `services/pdf_generator.py`.
- Synthetic veteran profiles from `data/veterans.json`.
- Five benefit definitions and VA.gov links from `data/benefits_rules.json`.
- Five VA form definitions, field counts, digitization flags, and source-document metadata from `data/forms_catalog.json`.
- Branch-specific VSO contacts and benefit notes from `data/branch_contacts.json`.
- Synthetic document mockup purpose and disclaimers from `forms_to_verify/README.md`.

## Additional Information Needed

- Final team member names, departments, speaking roles, and each person's contribution/learning note.
- Confirmed live presentation time slot during April 28-May 1, 2026.
- Final submission location, sharing permissions, and incognito/private-link verification.
- Exact cost estimate using Wilcore rates and chosen pilot assumptions.
- Final decision on whether team contribution notes stay in the deck or are submitted separately; draft recommendation is to keep them in the deck once known.
- Confirmation that challenge-period/IP/data-rights requirements are satisfied.
- Dependency license review if the judges or organizers ask for it.
- Current verified external statistics for VA backlog, processing time, annual claim volume, and any acquisition-path claims before final submission.
- Production deployment assumptions: agency sponsor, system boundary, data retention, identity provider, model runtime, and security authorization target.
