# forms_to_verify/

This folder contains mockup images of VA forms and military documents that veterans
commonly receive as physical paper, flat PDFs, or scanned images — and that VetAssist
is designed to help process.

---

## Why this folder exists

One of the core problems VetAssist solves is that **not all VA forms are truly digital.**
Some forms:
- Are delivered by mail as flat printed documents
- Exist only as static PDFs with no fill-in capability online
- Are physically handed to veterans at VA offices, military bases, or VSO offices
- Are forms a veteran may photograph with their phone and need help reading and filling out

VetAssist's document photo-to-prefill feature — built and working in the current MVP —
lets veterans photograph these documents and send the image to Claude, which reads it
using multimodal vision (not OCR). Claude understands the document semantically:
it knows what a DD-214 looks like and where each field lives, even in a tilted phone photo.
Extracted fields are shown to the veteran for review and confirmation before anything
populates their form.

---

## What's in this folder

| File | Form | Status |
|------|------|--------|
| `DD_214_mockup_example.png` | DD Form 214 — Certificate of Release or Discharge from Active Duty | **MOCKUP** — Synthetic data, realistic structure based on publicly available field names from [National Archives](https://www.archives.gov/personnel-records-center/dd-214) |
| `VA_21-4142_authorization_to_disclose_mockup.png` | VA Form 21-4142 — Authorization to Disclose Information to the VA | **MOCKUP** — Field layout matches the [official public form](https://www.vba.va.gov/pubs/forms/vba-21-4142-are.pdf); all fields sourced from public VA documentation |
| `VA_21-0781_PTSD_stressor_statement_mockup.png` | VA Form 21-0781 — Statement in Support of Claimed Mental Health Disorder(s) | **MOCKUP** — Structure based on [VA.gov public documentation](https://www.va.gov/forms/21-0781/); uses synthetic veteran data |

---

## Important disclaimers

- **None of these are official government forms.** They are programmatically generated mockups
  for demo and development purposes only.
- **All veteran data shown is synthetic.** No real PII is used anywhere. "MARIA E. SANCHEZ"
  is a fictional test profile.
- **These should be replaced with real examples before any production use.**
  Real paper forms can be obtained by:
  - Requesting your DD-214 from the [National Archives eVetRecs system](https://www.archives.gov/veterans/military-service-records)
  - Downloading VA forms directly from [VA.gov/vaforms](https://www.va.gov/vaforms/)
  - Visiting a local VA Regional Office or VSO

---

## How these are used in the demo

During the VetAssist demo:

1. The presenter shows the veteran profile for Maria Sanchez
2. VetAssist identifies she needs VA Form 21-0781 (PTSD Stressor Statement) —
   which is **not a truly digitized form online** (no structured data entry flow)
3. The demo shows the mockup image of the form as if Maria photographed it from a VA office
4. The veteran clicks the “📷 From DD-214” button on a missing field row and uploads a photo
5. Claude reads the document image and extracts the relevant fields
6. The veteran reviews each extracted value in the confirmation modal and edits anything wrong
7. Confirmed fields populate the form table automatically
8. The chat assistant asks for any remaining fields in plain language

This demonstrates one of VetAssist's most differentiated capabilities: **reading paper
documents the veteran already has and using that information to prefill new forms** —
something no existing VA tool does. The veteran never has to re-type information from a
document they're already holding.

---

## Verification tasks before submission

If you want to verify or improve these mockups before the hackathon demo:

- [ ] Compare `DD_214_mockup_example.png` fields against an actual DD-214 image online (e.g., [Military.com guide](https://www.military.com/benefits/records-and-forms/dd214.html))
- [ ] Confirm VA Form 21-4142 field order matches current [August 2024 version](https://www.vba.va.gov/pubs/forms/vba-21-4142-are.pdf)
- [ ] Confirm VA Form 21-0781 structure matches current version at [VA.gov](https://www.va.gov/forms/21-0781/)
- [ ] If a real DD-214 photo is available (redacted), replace the mockup for a more authentic demo
