# Wilcore Innovation Challenge Todo List

Source: `Wilcore_Innovation_Challenge_FINAL.pdf`

Scope: Requirements from the challenge overview, participation rules, submission steps, judging criteria, presentation expectations, federal context, and rules/IP sections. Theme Ideas and Questions sections are intentionally excluded.

## Deadline And Logistics

- [x] Confirm final team roster.
    Akash, Matt Otto, Tyson Newell, Selia Straus
- [x] Confirm each team member is a Wilcore employee and will remain active through Friday, May 1, 2026.
- [x] Confirm the team has no more than 6 people.
- [x] Confirm each team member is only participating on this one team.
- [ ] Select a live presentation time slot for the April 28-May 1, 2026 presentation window.
- [ ] Prepare final materials before Monday, April 27, 2026 at 11:59 PM ET.
- [ ] Send submission email to `innovate@wilcore.io` before the deadline.
- [ ] Include links to the write-up/slides and recorded demo in the submission email.
- [ ] Grant the `innovate@wilcore.io` Google group access to all submitted materials.
- [ ] Verify every submitted link opens correctly in an incognito/private browser session.
- [ ] Do a final lock check before submission; no changes are allowed after the deadline.

## Required Submission Package

- [x] Create the official slide deck using the Wilcore presentation template.
- [ ] Include the team member names and departments.
- [x] Include the idea title: `VetAssist`.
- [x] Write the problem/opportunity section in 100-200 words.
- [x] Explain what is broken or missing today.
- [x] Explain who is affected by the problem.
- [x] Write the solution section in 200-400 words.
- [x] Explain what VetAssist is.
- [x] Explain how VetAssist works.
- [x] Explain why VetAssist is better than the current process.
- [x] Add expected impact, including what improves and by roughly how much.
- [ ] Add implementation needs with rough effort, cost, and dependencies.
- [x] Add federal applicability.
- [ ] Add what each team member did and learned.
- [x] Decide whether the team contribution notes belong in the deck or should be submitted separately.
- [x] Add optional supporting materials if useful: diagrams, mockups, data, architecture notes, or demo screenshots.
- [ ] Record a video demo that shows a functional MVP, not only static slides.
- [ ] Confirm the recorded demo link is included in the submission email.

## Functional MVP Demo

- [ ] Start with a clean local run of the app from the README instructions.
- [ ] Show the app loading successfully in the browser.
- [ ] Show a demo veteran profile flow.
- [ ] Show the manual profile entry flow.
- [ ] Show document scan/photo upload and extraction if an API key is available.
- [ ] Show graceful fallback behavior when the API key is unavailable.
- [ ] Show benefits surfaced as "worth exploring," not eligibility determinations.
- [ ] Show VA.gov links or next-step references on benefit cards.
- [ ] Show form matching for selected benefits.
- [ ] Show prefilled fields from the veteran profile.
- [ ] Show missing field identification.
- [ ] Show source document suggestions for missing fields.
- [ ] Show veteran review/edit/confirmation before using extracted or prefilled data.
- [ ] Show conversational follow-up for remaining gaps.
- [ ] Show generated output package or clearly label the output as the MVP summary package.
- [ ] Show VSO/VA handoff language: VetAssist prepares; VA/VSO decides.
- [ ] Avoid using any real veteran data in the demo.
- [ ] Use synthetic profiles and synthetic document images only.

## Slide Deck Content

- [x] Problem Statement: clearly define the problem or opportunity.
- [x] Problem Statement: identify who is affected.
- [x] Problem Statement: describe current cost, risk, or gap.
- [x] Problem Statement: include data where possible.
- [x] Proposed Solution: explain VetAssist in plain language.
- [x] Proposed Solution: explain how the workflow works end to end.
- [x] Proposed Solution: explain what makes it meaningfully better than existing options.
- [x] Impact & Value: quantify the benefit where possible.
- [x] Impact & Value: frame impact in terms of user benefit.
- [x] Feasibility & Roadmap: outline the realistic path to implementation.
- [x] Feasibility & Roadmap: describe what it would take to build or deploy.
- [x] Feasibility & Roadmap: list key risks and mitigations.
- [x] Federal Applicability: explain how VetAssist could benefit a federal agency or program.
- [ ] Team: explain what each team member brought to the project.
- [x] Include the MVP architecture diagram.
- [x] Include the before/after user journey.
- [x] Include the MVP-to-federal roadmap.
- [x] Include any supporting research sources for claims about VA claims, backlog, form complexity, or veteran experience.

## Presentation Standards

- [x] Use the official Wilcore slide template.
- [x] Keep language clear and jargon-free.
- [x] Assume judges may not have deep VA benefits, AI, or software architecture expertise.
- [x] Support claims with data, research, or reasoned logic.
- [x] Remove unsupported assertions from slides and speaker notes.
- [x] Prepare direct answers about cost.
- [x] Prepare direct answers about timeline.
- [x] Prepare direct answers about risks.
- [x] Prepare direct answers about security and privacy.
- [x] Prepare direct answers about federal deployment feasibility.
- [ ] Confirm all team members have a speaking role.
- [ ] Rehearse for a 20-minute presentation.
- [x] Prepare for a 10-minute Q&A.
- [ ] Assume the presentation will be recorded for internal use.

## Judging Criteria Optimization

- [x] Impact, 30%: make the benefit to veterans, VA customers, Wilcore, and federal clients concrete.
- [x] Impact, 30%: quantify time saved, reduced incomplete submissions, or improved preparation quality.
- [x] Originality, 25%: explain how VetAssist differs from VA.gov, VA Form Wizard, benefits.gov, and a standard VSO appointment.
- [x] Originality, 25%: emphasize the combined flow of benefit discovery, form matching, prefill, document vision, and conversational gap filling.
- [ ] Feasibility, 20%: show that the MVP already runs.
- [x] Feasibility, 20%: explain replaceable architecture: JSON to database, direct Anthropic to Bedrock, local runtime to cloud/GovCloud.
- [x] Feasibility, 20%: define post-MVP dependencies such as identity, production data storage, VA form integration, cloud deployment, and security authorization.
- [x] Clarity, 15%: keep the story simple: understand, prepare, connect.
- [ ] Clarity, 15%: make screenshots and demo flow easy to follow.
- [ ] Collaboration, 10%: document each team member's work and learning.

## Federal Applicability

- [x] Name the likely federal agency/program fit, especially the Department of Veterans Affairs.
- [x] Explain the government service gap VetAssist addresses.
- [x] Explain how the idea could support VA benefits intake, VSO preparation, or claims package readiness.
- [x] Address Section 508 accessibility expectations.
- [x] Address FedRAMP/FISMA implications for any production federal deployment.
- [x] Address data privacy for veteran PII and sensitive documents.
- [x] Address whether production deployment would need VA identity/login.gov integration.
- [x] Address how model usage could move from direct API calls to an approved federal environment.
- [x] Address whether the app could fit into a government contract structure.
- [x] Prepare a short explanation of why Wilcore's SDVOSB background makes the idea strategically relevant.

## Rules, IP, And Data Rights

- [ ] Confirm the idea and project work were created during the challenge period.
- [ ] Remove any confidential third-party information from slides, demo data, code comments, screenshots, and recordings.
- [x] Remove or replace any real veteran PII.
- [x] Confirm all demo profiles are synthetic.
- [x] Confirm all demo documents are synthetic or safe to use.
- [ ] Review software dependencies for restrictive, copyleft, or viral license obligations.
- [ ] Document dependency licenses if asked.
- [ ] Avoid including third-party IP with restrictions that would limit Wilcore's rights or government rights.
- [ ] Avoid any materials that conflict with FAR/DFARS data-rights expectations.
- [ ] Avoid export-controlled material or anything that could raise ITAR/EAR concerns.
- [ ] Be comfortable with the challenge license terms granting Wilcore broad rights to use, develop, modify, commercialize, and propose the submitted idea.
- [ ] Be ready to execute follow-up documents if Wilcore asks to confirm rights for a future product, proposal, audit, or contract effort.

## VetAssist Project Polish Before Submission

- [ ] Finish the highest-value UI fixes from `VA_DESIGN_UI_AUDIT.md` that reduce demo risk.
- [ ] Keep the prototype notice clear so the app does not imply it is an official VA.gov product.
- [ ] Make the "not an eligibility determination" disclaimer visible and consistent.
- [ ] Confirm every major claim in `README.md` and slides has a source or reasoned basis.
- [ ] Review the "Credible BD path" note in `README.md` and replace placeholders or uncertain claims before presenting.
- [ ] Make sure the app can run from a fresh clone using `requirements.txt`.
- [ ] Confirm `README.md` has accurate setup, run, and fallback-mode instructions.
- [ ] Run the app locally and test the complete happy path.
- [ ] Test the no-API-key path.
- [ ] Test at least one document scan path with an API key if available.
- [ ] Capture clean screenshots for backup in case the live demo fails.
- [ ] Record a clean demo video after final app polish.
- [ ] Save the final deck, write-up, demo video, and supporting materials in one shareable location.

## Q&A Prep

- [x] Prepare a one-sentence answer to "What is VetAssist?"
- [x] Prepare a one-sentence answer to "Why now?"
- [x] Prepare a one-sentence answer to "Why Wilcore?"
- [x] Prepare an answer to "Is this making eligibility decisions?"
- [x] Prepare an answer to "How is this different from VA.gov?"
- [x] Prepare an answer to "What data does it store?"
- [x] Prepare an answer to "How would this be secured for federal use?"
- [x] Prepare an answer to "What would the first pilot look like?"
- [x] Prepare an answer to "What are the biggest risks?"
- [x] Prepare an answer to "What would it cost to implement?"
- [x] Prepare an answer to "What is the timeline from MVP to pilot?"
