# VA Design System Presentation Points

## Positioning

VetAssist is a science-fair proof of concept, not an official VA.gov product. The UI should borrow the trust, clarity, and accessibility habits of the Veterans Affairs Design System (VADS) without implying that this demo is an official government website.

## What VADS Adds

VADS stands for Veterans Affairs Design System. It gives VA teams shared components, styling conventions, content guidance, and accessibility patterns for Veteran-facing digital services.

For this proof of concept, the most useful VADS components are:

- Button
- Alert
- Loading indicator
- Segmented progress bar
- Text input
- Select
- Date input
- Textarea
- File input
- Modal
- Minimal footer

These map closely to the current VetAssist flow, so adopting them later would be a practical migration rather than a design rewrite.

## Implementation Path

The clean implementation path is to introduce a small frontend build step, such as Vite, and import the VADS component library from npm:

```bash
npm install @department-of-veterans-affairs/component-library
```

That would let the app use `va-*` web components while keeping FastAPI as the backend. The current machine does not have `node` or `npm` available, so this repo cannot install the package locally yet. For this demo pass, the low-risk work is to improve the existing vanilla HTML with VADS-aligned labels and modal behavior.

## Banner, Header, And Footer

Because this is a science-fair proof of concept, the safest banner choice is a prototype notice rather than the Official Gov Banner. The Official Gov Banner is appropriate for real U.S. government websites, but using it here could make the demo look more official than it is.

The most appropriate header and footer patterns are the VA Design System minimal header and minimal footer. This app is a focused task flow: the Veteran is trying to prepare benefits paperwork, not browse a large content site. A minimal header and footer support that by providing a VA-aligned frame without adding navigation choices that could pull users away from the task.

Presentation wording:

> For the proof of concept, we would use a clear prototype notice instead of the Official Gov Banner so we do not imply this is an official VA site. If this became a VA.gov-bound product, the Official Gov Banner would be required. For the app frame, the VADS minimal header and minimal footer are the best fit because VetAssist is a focused form-preparation flow, and the minimal pattern keeps users oriented without distracting them from completing the task.

## Semantics Overhaul Risk

A full semantic refactor would be useful later, but it is not the right first move before a demo. The current page is a single HTML file whose behavior depends on:

- Stable element IDs used by JavaScript.
- Inline event handlers such as `onclick`, `oninput`, and `onchange`.
- Dynamic HTML generated with `innerHTML`.
- CSS class names used by both styling and state logic.
- Form values collected by selectors like `.field-input[data-field-key]`.

Changing the overall structure to real forms, fieldsets, legends, VADS components, and custom event listeners is doable, but it would touch many code paths at once. That creates demo risk because the existing happy path already works.

Low-risk improvements:

- Add `for` attributes to labels that already have stable input IDs.
- Convert dynamic field labels from plain divs to real labels.
- Upgrade the custom modal with native dialog semantics while preserving the same open, close, and confirm functions.

Higher-risk changes to defer:

- Replacing the whole page with Vite-managed modules.
- Replacing every native input with a VADS web component in one pass.
- Reworking step navigation, tabs, and form sections simultaneously.
- Changing submit and validation behavior before the demo.

## Demo Message

VetAssist is not claiming to determine eligibility. The strongest design story is that it helps Veterans prepare: it identifies benefits worth exploring, maps them to forms, prefills what is known, asks the Veteran to verify every value, and prepares a package they can bring to a VSO or VA appointment.
