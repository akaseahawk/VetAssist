# VetAssist VA Design System UI Audit

Date: April 24, 2026

## Scope

Reviewed the project-wide UI surface against the VA.gov Design System and content guidance at <https://design.va.gov>.

The current project has one primary frontend:

- `templates/index.html`: single-page vanilla HTML/CSS/JS application.
- `main.py`: serves the template and backend API routes.
- No frontend package, VADS CSS package, VADS web components, component library, or static asset system is currently present.
- April 24 update: Python dependencies were installed locally and the app now runs with `python3 -m uvicorn main:app --host 127.0.0.1 --port 8010`.

The initial audit was based on static source review and VA Design System documentation review. Later cleanup centralized CSS colors, removed inline `style` attributes from the template, fixed label associations, and upgraded the document-review modal.

## VA Design System Baseline

The relevant VA guidance for this app is:

- Design principles: usable by everyone, mobile first, no dead ends, simple task-focused flows, clarity before polish, and Veteran-first service completion.
- VADS implementation: use the CSS Library and reusable Web Components where practical rather than recreating shared UI from scratch.
- Forms: form controls must be accessible, logically ordered, and should not rely on color alone. VA form guidance emphasizes technical accessibility, cognitive accessibility, keyboard navigation, and screen reader support.
- Components: this app maps directly to existing VADS components and patterns including Official Gov Banner, Header Minimal, Footer Minimal, Alert, Loading Indicator, Segmented Progress Bar, Button, Button Group, Text Input, Select, Date Input, Textarea, File Input, Modal, Tabs or accordions, Card, Prefill, and Check Answers.
- Content: language should be conversational, clear, helpful, consistent, and should avoid generic link text such as standalone "Learn more."

Key VA documentation reviewed:

- <https://design.va.gov/about/principles>
- <https://design.va.gov/about/developers/install>
- <https://design.va.gov/about/developers/using-web-components>
- <https://design.va.gov/foundation/color-palette>
- <https://design.va.gov/foundation/typography>
- <https://design.va.gov/templates/forms/accessibility-guidelines>
- <https://design.va.gov/templates/forms/form-step>
- <https://design.va.gov/components/form/>
- <https://design.va.gov/components/form/label>
- <https://design.va.gov/components/form/progress-bar-segmented>
- <https://design.va.gov/components/alert/>
- <https://design.va.gov/components/loading-indicator>
- <https://design.va.gov/components/modal>
- <https://design.va.gov/components/card/>
- <https://design.va.gov/components/tabs>
- <https://design.va.gov/content-style-guide/content-principles>
- <https://design.va.gov/content-style-guide/button-labels>
- <https://design.va.gov/content-style-guide/links>

## Overall Assessment

VetAssist is directionally aligned with the VA design philosophy, but not yet aligned with the VA Design System implementation.

The experience is Veteran-centered in intent: it reduces repeated data entry, explains that benefit suggestions are not determinations, uses VA.gov links, separates known information from missing information, and asks users to review extracted data before using it. These are strong product decisions.

The main gap is execution: the UI is currently a custom MVP with handcrafted CSS, custom components, inline event handlers, and weak semantic structure. For a VA-facing or federal-quality demo, the next pass should replace custom UI primitives with VADS components or VADS-compatible markup.

## Static Metrics

Current state of `templates/index.html` after cleanup:

- Hex color literals are centralized in `:root` CSS custom properties.
- 0 inline `style` attributes.
- 16 inline `onclick` handlers.
- 14 `<button>` elements.
- 24 `<input>` elements.
- 11 `<select>` elements.
- 2 `<textarea>` elements.
- 27 `<label>` elements.
- 0 labels missing `for`.
- 1 `aria-*` attribute.
- 0 `role` attributes.
- No `<main>`, `<form>`, `<fieldset>`, or `<legend>` elements found.

## What Aligns Well

1. The flow focuses on a primary Veteran task.

The app is organized around selection, benefit review, form choice, field review, gap resolution, and PDF preparation. This supports the VA principle to break complex tasks into small ordered steps and reduce repeated data entry.

Relevant code:

- `templates/index.html:468` step indicator.
- `templates/index.html:736` form selection step.
- `templates/index.html:1200` field review logic.

2. Prefilled information is reviewable and editable.

The app deliberately lets users correct prefilled or extracted values before continuing. This aligns with VADS prefill guidance, especially when data comes from a source other than a VA.gov API.

Relevant code:

- `templates/index.html:759` known fields section.
- `templates/index.html:1274` editable field row builder.
- `templates/index.html:2027` vision confirmation modal.

3. Benefit suggestions are framed as preparation, not determination.

The disclaimer at `templates/index.html:713` correctly tells users that VetAssist does not decide eligibility and points them toward a VSO and VA decision-making process.

4. The app uses plain-language intent in many places.

Examples include "Benefits Worth Exploring," "Still needed from you," and "Bring this to your VSO appointment." This is consistent with VA content principles.

## High-Priority Gaps

### 1. Missing Official Gov Banner, VA Header, Crisis Line, and Footer

Current state:

- The page starts with a custom `header` at `templates/index.html:456`.
- There is no Official Gov Banner.
- There is no VA logo or VA.gov global header/minimal header pattern.
- There is no footer/minimal footer.
- There is no Veterans Crisis Line affordance.

Why this matters:

The VA header guidance states that the Official Gov Banner is required for U.S. government websites, and VA headers/footers are part of the broader VA.gov trust frame. Even for a prototype, the absence makes the page feel like a branded third-party MVP rather than a VA-aligned digital service.

Recommendation:

- For a demo not hosted on VA.gov: avoid implying this is an official VA site, but visually align with VA form templates.
- For a VA.gov-bound app: add VADS Official Gov Banner, Header Minimal, Footer Minimal, and Crisis Line affordance.

### 2. No VADS Package, Components, Tokens, or Utilities

Current state:

- `requirements.txt` has no frontend dependency path.
- `templates/index.html` hand-rolls all visual primitives.
- The UI now centralizes colors in CSS custom properties, but those variables are still local names rather than VADS package tokens/utilities.

Why this matters:

The VA docs recommend CSS Library and Web Component library packages for custom applications. Current styling will drift from VADS in color, typography, spacing, focus states, and component behavior.

Recommendation:

- Add VADS CSS Library or Web Components.
- Replace local `.btn`, `.card`, `.spinner`, `.step-bar`, `.field-input`, `.form-tab`, and `.vision-modal` primitives with VADS components where possible.
- At minimum, create VADS-inspired CSS variables mapped to VA semantic tokens and replace hard-coded hex values.

### 3. Form Labels Are Not Programmatically Associated

Current state:

- Manual profile fields at `templates/index.html:531` through `templates/index.html:590` use `<label>` elements without `for`.
- Dynamic form rows render labels as `<div class="field-label">` at `templates/index.html:1381`.
- Modal extracted fields at `templates/index.html:2161` use `<label>` without `for`.

Why this matters:

VADS label guidance says all form inputs must have an associated label. The current UI is likely hard to navigate with screen readers or voice input software.

Recommendation:

- Use VADS `va-text-input`, `va-select`, `va-date`, `va-textarea`, and `va-file-input`.
- If staying native HTML, every label must have a matching `for` and every input/select/textarea must have a stable `id`.
- Dynamic field labels should be real `<label for="input-${field.key}">` elements, not `<div>`.

### 4. Missing Semantic Page and Form Structure

Current state:

- No `<main>` landmark.
- No `<form>` elements.
- No `<fieldset>` or `<legend>` for grouped questions.
- Cards are used as the primary form section container throughout the flow.

Why this matters:

VA form accessibility guidance emphasizes proper markup, keyboard navigation, screen reader support, clear logical flow, and cognitive accessibility. Cards are not fieldsets; VADS card guidance specifically warns against using cards to mimic form fieldsets.

Recommendation:

- Wrap primary content in `<main id="main-content">`.
- Use actual `<form>` elements for profile entry and form review.
- Use `<fieldset>` and `<legend>` for grouped fields such as service history, disability information, contact information, and document scan.
- Use headings in order: one H1, then H2/H3 per section.

### 5. Custom Step Indicator Should Use VADS Segmented Progress Bar

Current state:

- The stepper at `templates/index.html:468` is a row of `<div>` elements with custom glyph numerals and no `aria-current`, accessible name, or structural semantics.

Why this matters:

VADS has a deployed Segmented Progress Bar component for multi-step form flows. The current version is visual only and will not reliably communicate progress to assistive technology.

Recommendation:

- Replace with `va-segmented-progress-bar`.
- If retaining custom markup, use an ordered list, expose current step with `aria-current="step"`, and avoid decorative glyphs as the only status signal.

### 6. Error Handling Is Visual-Only and Not Announced

Current state:

- Required field validation adds `is-error` at `templates/index.html:1412`.
- Error text is one generic hidden div at `templates/index.html:786`.
- Inputs do not receive `aria-invalid`.
- Error messages are not associated with fields through `aria-describedby`.
- Upload errors are placed in placeholders at `templates/index.html:2135`.

Why this matters:

VA error recovery guidance emphasizes explaining what went wrong and how to fix it. VADS label guidance expects field-level error messages, error styling after interaction, and screen reader-readable error state.

Recommendation:

- Add field-level messages beneath each invalid input.
- Set `aria-invalid="true"` and `aria-describedby`.
- Use a summary alert at the top of the form when submit fails.
- Do not place errors in placeholder text; placeholders are not reliable instructions or error containers.

### 7. Modal Does Not Meet Expected Accessibility Behavior

Current state:

- The vision modal at `templates/index.html:2029` is a custom fixed div.
- No `role="dialog"`, `aria-modal`, accessible title reference, escape-key behavior, focus trap, initial focus, return focus, or inert background behavior.

Why this matters:

The VADS modal component exists specifically for focused single-task dialogs and exposes properties for focus and accessibility behavior.

Recommendation:

- Replace with `va-modal`.
- Keep modal content brief and focused on confirming extracted fields.
- Ensure focus enters the modal, is trapped while open, can close with Escape, and returns to the triggering upload button.

### 8. Buttons and Links Need VADS Semantics and Content Cleanup

Current state:

- Many controls use custom `.btn` classes.
- Some link text is generic, such as "Learn more" at `templates/index.html:1057`.
- Some button labels exceed VA content guidance, such as "Download My Preparation Package (PDF)".
- Navigation-like options are implemented as buttons in the profile mode toggle.

Why this matters:

VA guidance says buttons are for actions and links are for places. Button labels should be sentence case, short, and action-oriented. Link text should describe where the link takes the user, and new-tab links should disclose that behavior.

Recommendation:

- Replace `.btn` with `va-button` or VADS button classes.
- Change "Learn more" to contextual text such as "Learn about disability compensation on VA.gov (opens in a new tab)".
- Shorten repeated download CTA to "Download PDF" with supporting text nearby.
- Use segmented button or radio pattern for profile mode selection.

### 9. Color and Status Depend Too Much on Custom Green/Amber/Red

Current state:

- Known fields are green, missing fields are amber, errors are red.
- The status meaning is sometimes carried by color plus symbols, but not semantic labels or ARIA state.
- Focus color is custom blue rather than the VA focus token.

Why this matters:

VADS color guidance uses semantic tokens with specific system meaning. Form status should not depend on color alone. VA focus styles should be obvious and consistent.

Recommendation:

- Use VA semantic color tokens.
- Add text labels that do not rely on color, such as "Known information" and "Information needed."
- Use VADS alert/status components for state summaries.
- Use the VA focus outline token (`#face00` in current docs) or VADS-provided focus utilities.

### 10. The "Forms as Tabs" Pattern Is Risky at Current Scale

Current state:

- Form selection is rendered as custom tab-like divs at `templates/index.html:1127`.
- They use `onclick`, no keyboard tab behavior, no `role="tablist"`, no active semantics, and no arrow-key support.

Why this matters:

VADS tabs are candidate/use-with-caution and work best with 3 or fewer tabs. This app may produce multiple forms grouped under multiple benefits, which may overflow and become difficult on mobile.

Recommendation:

- If there are usually 3 or fewer forms, use `va-tabs`.
- If there can be more, prefer accordions or a simple list of form cards with action buttons.
- For grouped benefits, consider VADS accordion sections by benefit, each containing form list items.

## Recommended Remediation Roadmap

### Phase 1: Accessibility and Trust Baseline

1. Add semantic layout: skip link, `<main>`, proper H1, form elements, fieldsets, legends.
2. Fix all label associations.
3. Replace visual-only validation with field errors and a top form alert.
4. Replace the custom modal with `va-modal`.
5. Add accessible progress semantics or `va-segmented-progress-bar`.
6. Ensure upload, scan, and chat loading states are announced.

### Phase 2: VADS Visual Alignment

1. Introduce VADS CSS Library or Web Components.
2. Replace custom buttons, alerts, loading indicators, progress, inputs, selects, textareas, file inputs, modal, and cards.
3. Replace hard-coded colors with VADS tokens/utilities.
4. Switch typography to Source Sans Pro and the VADS type scale.
5. Remove most inline styles and move styling into a maintainable stylesheet.

### Phase 3: Flow and Content Polish

1. Add a proper intro or task title that clarifies this is preparation, not VA adjudication.
2. Add "Need help?" content with VSO/VA contact support near form steps.
3. Make links contextual and disclose new tabs.
4. Rework form selection to accordions or VADS tabs depending on final form count.
5. Add a true review/check-answers step before PDF generation.

## Suggested Component Mapping

| Current UI | Recommended VA-aligned replacement |
|---|---|
| Custom header | Official Gov Banner + Header Minimal, or prototype-safe non-official header |
| `.step-bar` | `va-segmented-progress-bar` |
| Disclaimer box | `va-alert` informational/warning |
| Custom spinner | `va-loading-indicator` |
| `.btn` | `va-button`, button group, segmented button where appropriate |
| Manual profile fields | `va-text-input`, `va-select`, `va-date` |
| Upload controls | `va-file-input` |
| Known/missing field rows | VADS form controls inside fieldsets, plus prefill/update patterns |
| Custom modal | `va-modal` |
| Form tabs | `va-tabs` only for small tab sets; otherwise accordions/list |
| Benefit cards | `va-card`, `va-summary-box`, or service list item depending on final information architecture |
| Download CTA | VADS button group and review/check-answers flow |

## Bottom Line

The product concept is compatible with VA design philosophy. The current UI implementation is not yet VADS-compliant.

The most important next move is not visual polish; it is replacing custom, visual-only form behavior with accessible VADS-backed structure. Once labels, landmarks, errors, modal focus, progress, and component tokens are corrected, the app will feel much closer to a credible VA-facing experience.
