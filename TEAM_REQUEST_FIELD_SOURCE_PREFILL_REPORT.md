# Team Request Interpretation Report: Source-Document Prefill

Date: April 24, 2026

## Request Summary

The team is asking VetAssist to do more than show a blank list of missing form fields. After a veteran chooses a form and VetAssist has used the initial profile information to prefill everything it can, the app should:

1. Identify every field that is still not filled.
2. Determine which of those missing fields could likely be answered from another written record the veteran may have nearby.
3. Tell the veteran which record may contain the answer.
4. Offer a way to take or upload a picture of that record.
5. Use document extraction to prefill those missing fields.
6. Require the veteran to review, edit, and confirm extracted values before they become part of the form.

The intended workflow starts immediately after the form is chosen, because that is the first point where VetAssist knows the exact form fields and can compare them against the profile data already available.

## Where This Fits In The Current Workflow

The requested feature belongs in the current "Choose a Form to Work On" step.

Current flow:

1. Veteran loads or enters profile information.
2. VetAssist discovers benefits worth exploring.
3. Veteran chooses a matching VA form.
4. VetAssist prefills fields from the profile.
5. VetAssist separates known fields from fields still needed.
6. Veteran manually fills missing fields, uploads a document photo where available, or proceeds to chat for remaining gaps.

The team request specifically expands step 5. The missing-field review should become smarter and more document-aware.

## My Understanding Of The Desired User Experience

When the veteran selects a form, the form review page should show something like:

- "We filled 18 of 31 fields from your profile."
- "13 fields are still needed."
- "A DD-214 may fill 4 of these fields: service dates, discharge type, rank, MOS."
- "A VA award letter may fill 2 fields: disability rating, rated conditions."
- "A private medical record may help with treatment provider and treatment dates."
- "Some fields still need your direct answer, such as signature date or narrative explanations."

The veteran should be able to choose a suggested document and take a picture or upload an image. VetAssist should extract only the missing fields relevant to the selected form, show the extracted values in a review modal, and populate the form only after confirmation.

## What Already Exists In The Codebase

Several pieces of this request already exist:

- `services/form_matcher.py` already compares each selected form against the veteran profile and marks fields as `prefilled`, `missing`, or `ask`.
- `services/form_matcher.py` already passes `source_documents` from `data/forms_catalog.json` into the frontend response.
- `static/js/app.js` already splits selected-form fields into "Information we already have" and "Still needed from you."
- Missing field rows already show a per-field document upload button when the catalog includes `source_documents`.
- The document upload flow already sends all still-needed field keys to `/api/upload`, so one DD-214 upload can fill multiple missing fields.
- The vision flow already stages extracted values in a modal and requires veteran confirmation before populating the form.
- `main.py` has `/api/upload/suggestions/{veteran_id}`, which can group missing fields by possible source document, although the current frontend does not appear to use this endpoint in the selected-form UI.

In other words, the MVP already partially implements the idea at field-row level.

## Gaps Between Current App And Requested Behavior

The fuller request appears to require these improvements:

1. Broader field tagging

   The form catalog should identify all fields that can reasonably be sourced from a written record, not just a subset. Today, several fields have `source_documents`, but many plausible document-fillable fields do not.

2. Grouped document suggestions

   The UI should not rely only on individual "From DD-214" buttons beside each row. It should also present grouped suggestions such as "Scan your DD-214 to fill these 4 fields." This makes the feature visible and easier to understand.

3. "Take a picture" option in the form step

   Step 1 identity scanning already has a richer camera/photo flow. The selected-form document upload path currently behaves more like a file picker. The requested wording implies a direct "take a picture" option should also be available at this later step.

4. Better source-document catalog

   Current known document extraction definitions focus on DD-214, VA Form 21-4142, military ID, VA letter, and generic records. The request likely wants a more complete mapping of handy written records, such as DD-214, VA award or rating letters, private medical records, VA medical records, insurance cards, bank documents, school enrollment records, mortgage/lender documents, and buddy statements, depending on the form.

5. Prioritization

   The app should suggest the most useful records first, based on how many missing fields each record could fill and how likely the veteran is to have it handy.

6. Own-profile support

   The current upload flow can work for manually entered profiles because it sends visible missing fields directly. If grouped document suggestions use `/api/upload/suggestions/{veteran_id}`, that route would need an equivalent path for own-profile sessions or should compute suggestions fully on the client from the active form data.

## Suggested Product Requirements

The feature should meet these requirements:

- After a form is selected, VetAssist displays all fields that were not filled by the profile.
- For each missing field, VetAssist identifies whether it can be filled from:
  - a likely source document,
  - direct veteran input,
  - chat follow-up,
  - or a combination of these.
- VetAssist groups missing fields by suggested written record.
- Each suggested record shows which fields it may fill.
- The veteran can take a picture or upload an image of the suggested record.
- VetAssist extracts only fields relevant to the selected form and current missing-field list.
- VetAssist never silently applies extracted values.
- The veteran can review, edit, confirm, or cancel extracted values.
- Confirmed extracted values update the form, progress count, and missing-field list.
- Fields that cannot reasonably be filled from a document remain available for manual entry or chat.

## Suggested Acceptance Criteria

1. Given a selected form with profile-prefilled data, the UI shows a count of known and missing fields.
2. Given missing fields with `source_documents`, the UI shows grouped source-document suggestions above or within the missing-fields section.
3. Given multiple fields that can be filled from the same source document, one document scan can populate all matching fields found in the image.
4. Given an extraction result, the user sees an editable review screen before values are applied.
5. Given the user confirms extracted values, the matching rows move from "needed" to "known" and the progress count updates.
6. Given fields with no source-document hint, the UI keeps them as manual or chat follow-up fields.
7. Given no AI API key, the app explains that document reading is unavailable and leaves manual entry available.

## Implementation Direction

The smallest useful code update would be:

1. Expand `data/forms_catalog.json` so every document-fillable field has `source_documents`.
2. Add a selected-form "Suggested records to scan" panel in `static/js/app.js`.
3. Reuse the existing `/api/upload` and vision confirmation modal.
4. Add direct camera capture support to the selected-form document upload flow, borrowing from the Step 1 scan flow.
5. Keep manual entry and chat as fallback paths.

The existing architecture is well-positioned for this. The main work is making the source-document mapping more complete and making the UI present those suggestions as a primary part of the form review step.

## Non-Goals

This request does not appear to ask VetAssist to:

- decide eligibility,
- submit forms to the VA,
- store real veteran documents,
- auto-populate fields without review,
- or guarantee that a suggested document will contain every missing value.

The intended feature is a preparation aid: it helps veterans use records they already have to reduce typing and improve form completeness before bringing the package to a VSO or the VA.
