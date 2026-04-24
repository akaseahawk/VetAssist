// ---------------------------------------------------------------------------
// App state
// All state lives here — no hidden globals scattered through the code.
// ---------------------------------------------------------------------------
const state = {
  veteranId:           null,   // currently selected veteran ID
  veteran:             null,   // full veteran profile dict
  eligibilityResults:  [],     // output of /api/eligibility
  forms:               [],     // output of /api/forms
  activeFormId:        null,   // the form tab the veteran has selected
  activeForm:          null,   // the full form dict for the active form
  verifiedFields:      {},     // fields the veteran has confirmed or edited
  conversationHistory: [],     // chat turns [{role, content}]
  scanPhotoFile:       null,   // photo captured from webcam/mobile camera
  scanCameraStream:    null,   // active MediaStream while the scan camera is open
};

// ---------------------------------------------------------------------------
// Source-document metadata for the selected-form suggestions panel.
// The catalog tells us which field can come from which document; this lookup
// gives the UI human-readable names and scan hints for those document IDs.
// ---------------------------------------------------------------------------
const SOURCE_DOCUMENT_META = {
  "DD-214": {
    title: "DD-214 discharge papers",
    description: "Often has service dates, branch, discharge type, rank, MOS, deployments, and awards.",
    priority: 1,
  },
  "21-4142": {
    title: "VA Form 21-4142 or authorization form",
    description: "May contain SSN, date of birth, address, phone, and email.",
    priority: 2,
  },
  "VA_LETTER": {
    title: "VA award letter or rating decision",
    description: "May contain VA file number, rating, service-connected status, conditions, and mailing address.",
    priority: 3,
  },
  "MILITARY_ID": {
    title: "Military ID or CAC",
    description: "Useful for name, branch, rank, and date of birth.",
    priority: 4,
  },
  "SERVICE_RECORD": {
    title: "Service record, orders, or award citation",
    description: "May support deployments, unit assignment, combat exposure, awards, or event details.",
    priority: 5,
  },
  "MEDICAL_RECORD": {
    title: "VA or federal medical record",
    description: "May contain diagnoses, treatment dates, facilities, providers, and condition history.",
    priority: 6,
  },
  "PRIVATE_MEDICAL_RECORD": {
    title: "Private medical record",
    description: "May contain private provider names, treatment dates, diagnoses, and treatment history.",
    priority: 7,
  },
  "BUDDY_STATEMENT": {
    title: "Buddy statement or lay statement",
    description: "Can help with event descriptions, dates, locations, witnesses, and service connection details.",
    priority: 8,
  },
  "INSURANCE_CARD": {
    title: "Health insurance card",
    description: "May contain insurance provider, policy number, plan type, and contact number.",
    priority: 9,
  },
  "MEDICARE_CARD": {
    title: "Medicare card",
    description: "Can confirm Medicare enrollment and member information.",
    priority: 10,
  },
  "MEDICAID_CARD": {
    title: "Medicaid card",
    description: "Can confirm Medicaid enrollment and member information.",
    priority: 11,
  },
  "BANK_RECORD": {
    title: "Bank statement or direct deposit record",
    description: "May contain bank name, routing number, account number, address, or balances.",
    priority: 12,
  },
  "TAX_RETURN": {
    title: "Tax return",
    description: "May contain annual income, spouse income, and dependent count.",
    priority: 13,
  },
  "W2": {
    title: "W-2 wage statement",
    description: "May contain annual wages for the prior tax year.",
    priority: 14,
  },
  "PAY_STUB": {
    title: "Pay stub",
    description: "May contain current employment status and year-to-date income.",
    priority: 15,
  },
  "EMPLOYMENT_RECORD": {
    title: "Employment record",
    description: "May show current employment or work limitations.",
    priority: 16,
  },
  "RETIREMENT_PAY_STATEMENT": {
    title: "Military retirement pay statement",
    description: "Can confirm whether military retirement pay is being received.",
    priority: 17,
  },
  "SCHOOL_RECORD": {
    title: "School enrollment or acceptance record",
    description: "May contain school, program, enrollment status, and training start date.",
    priority: 18,
  },
  "LOAN_DOCUMENT": {
    title: "Mortgage or lender document",
    description: "May contain loan purpose, lender, prior loan, property address, and entitlement details.",
    priority: 19,
  },
  "PROPERTY_RECORD": {
    title: "Property record",
    description: "May contain the property address or state for a home loan form.",
    priority: 20,
  },
};

// ---------------------------------------------------------------------------
// Step 1: Load veteran list on page load
// ---------------------------------------------------------------------------
async function init() {
  try {
    const res = await fetch("/api/veterans");
    const veterans = await res.json();
    const sel = document.getElementById("veteran-select");
    veterans.forEach(v => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = `${v.name}  (${v.branch})`;
      sel.appendChild(opt);
    });
  } catch (e) {
    console.error("Failed to load veterans list:", e);
  }
}

// ---------------------------------------------------------------------------
// Step 1: Load a veteran profile + run eligibility + load forms
// ---------------------------------------------------------------------------
async function loadVeteran() {
  const sel = document.getElementById("veteran-select");
  if (!sel.value) return;

  // Reset state for a fresh load
  state.veteranId           = sel.value;
  state.conversationHistory = [];
  state.verifiedFields      = {};
  state.activeFormId        = null;
  state.activeForm          = null;

  setStep(1);
  show("card-benefits");
  hide("card-forms");
  hide("card-chat");
  document.getElementById("profile-loading").style.display = "block";

  // Load profile and eligibility in parallel — both are needed before showing Step 2
  const [profileRes, eligRes] = await Promise.all([
    fetch(`/api/veterans/${state.veteranId}`),
    fetch(`/api/eligibility/${state.veteranId}`),
  ]);

  state.veteran            = await profileRes.json();
  const eligData           = await eligRes.json();
  state.eligibilityResults = eligData.benefits || [];

  // Show profile summary
  renderProfile(state.veteran);

  // Show benefits — pass disclaimer text and mode badge from the API response
  // WHY three args: renderBenefits() needs the disclaimer string and mode label
  // from the backend, not just the benefit list, so it can show the right framing
  // Hide loading indicators now that data has arrived
  document.getElementById("profile-loading").style.display = "none";
  document.getElementById("benefit-spinner").style.display = "none";
  renderBenefits(eligData.benefits || [], eligData.disclaimer || "", eligData.mode || "rules_fallback");
  // WHY setStep(2) here, not earlier: the stepper reflects what the veteran
  // can actually act on. Benefits are visible now, so step 2 is active.
  setStep(2);

  // Load forms (prefill data) in the background.
  // WHY show card-forms early: we reveal the card immediately so the veteran
  // can see the spinner while the fetch is in flight — avoids a visual jump.
  show("card-forms");
  document.getElementById("forms-loading").style.display = "block";

  const formsRes = await fetch(`/api/forms/${state.veteranId}`);
  const formsData = await formsRes.json();
  state.forms = formsData.forms || [];

  // Hide spinner now that tabs are about to render
  document.getElementById("forms-loading").style.display = "none";
  renderFormTabs(state.forms);
  // WHY setStep(3): forms are now visible — veteran can pick one. Step 3 is active.
  setStep(3);
}

// ---------------------------------------------------------------------------
// Render: profile summary card
// ---------------------------------------------------------------------------
function renderProfile(v) {
  // Branch-aware greeting — simple client-side version
  // (Claude does the full personalization in chat)
  const greetings = {
    "Army":        "Thank you for your service and sacrifice in the Army — and to your family for theirs.",
    "Marine Corps":"Semper Fidelis — thank you for your service and dedication in the Marine Corps.",
    "Air Force":   "Thank you for your service in the Air Force and for what you and your family gave.",
    "Navy":        "Thank you for your service in the United States Navy.",
    "Coast Guard": "Semper Paratus — thank you for your service in the Coast Guard.",
  };
  const greeting = greetings[v.branch] || "Thank you for your service and sacrifice.";
  document.getElementById("profile-greeting").textContent = greeting;

  const grid = document.getElementById("profile-grid");
  grid.innerHTML = [
    ["Name",       v.name],
    ["Branch",     v.branch],
    ["Service",    `${v.service_start} to ${v.service_end}`],
    ["Discharge",  v.discharge_type],
    ["Combat",     v.combat_deployment ? "Yes — " + (v.deployment_locations || []).join(", ") : "No"],
    ["Disability", v.disability_rating_pct > 0 ? `${v.disability_rating_pct}% — ${(v.disability_conditions||[]).join(", ")}` : "None on file"],
    ["VA Health Care", v.enrolled_va_healthcare ? "Enrolled" : "Not enrolled"],
  ].map(([label, value]) => `
    <div class="profile-item">
      <div class="label">${label}</div>
      <div class="value">${escHtml(String(value))}</div>
    </div>
  `).join("");

  show("profile-summary");
}

// ---------------------------------------------------------------------------
// Render: benefits worth exploring
// Each card shows: title, plain-language reason, VA.gov link, important note
// ---------------------------------------------------------------------------
function renderBenefits(benefits, disclaimer, mode) {
  // Show disclaimer banner
  const disc = document.getElementById("benefit-disclaimer");
  if (disc) disc.style.display = "block";

  // Show mode badge so a developer or judge can see which mode is running
  const badge = document.getElementById("mode-badge");
  if (badge) {
    badge.textContent = mode === "claude"
      ? "(AI-powered suggestions)"
      : "(Offline mode — general guidelines)";
  }

  const grid = document.getElementById("benefit-grid");

  if (!benefits || benefits.length === 0) {
    grid.innerHTML = `<p class="benefit-empty">
      No specific benefits were identified based on your profile.
      This does not mean you have no benefits — please speak with a VSO.
    </p>`;
    return;
  }

  // Each benefit gets a card (not just a badge) so the veteran can read the reason
  // and click through to VA.gov before deciding whether to fill out a form
  grid.innerHTML = benefits.map(b => `
    <div class="benefit-card">
      <div class="benefit-card-inner">
        <div>
          <div class="benefit-title">
            ✓ ${escHtml(b.title)}
          </div>
          <div class="benefit-reason">
            ${escHtml(b.reason)}
          </div>
          <div class="benefit-note">
            ${escHtml(b.important_note)}
          </div>
        </div>
        ${b.info_url ? `
          <a href="${escHtml(b.info_url)}" target="_blank" rel="noopener"
             class="benefit-link">
            Learn more ↗
          </a>` : ""}
      </div>
    </div>
  `).join("");
}

// ---------------------------------------------------------------------------
// Render: form selector grouped by benefit
//
// WHY group by benefit instead of a flat tab list:
//   Step 2 showed the veteran a list of benefits worth exploring.
//   Grouping the forms under those same benefit names creates parallelism —
//   the veteran can immediately connect "I want to explore Disability
//   Compensation" to "here are the forms for that benefit".
//
// WHY show both form number AND full title:
//   Form numbers like "21-526EZ" mean nothing to most veterans.
//   The title tells them what the form actually is before they click.
//
// HOW grouping works:
//   1. Walk the eligible benefits list (state.eligibilityResults) in order
//      so the form groups appear in the same sequence as the benefits above.
//   2. For each benefit, find all forms whose benefit_ids include that benefit.
//   3. Render a header (benefit name) + tabs (forms) for each group.
//   4. Skip a benefit if no forms matched it (e.g. informational-only benefits).
// ---------------------------------------------------------------------------
function renderFormTabs(forms) {
  const container = document.getElementById("form-groups");

  // Build a lookup: benefit_id → list of forms that belong to it
  // WHY build the lookup instead of nesting loops: O(n) not O(n²),
  // and it's easier to read for a junior developer.
  const byBenefit = {};
  forms.forEach(f => {
    (f.benefit_ids || []).forEach(bid => {
      if (!byBenefit[bid]) byBenefit[bid] = [];
      byBenefit[bid].push(f);
    });
  });

  // Walk benefits in the order the eligibility engine returned them
  // so the form groups mirror the benefits list above
  const benefitOrder = (state.eligibilityResults || []).map(b => ({
    id:    b.benefit_id,
    title: b.title,
  }));

  // WHY no deduplication: if a form belongs to two benefits (e.g. 21-526EZ
  // covers both Disability Compensation and PTSD Benefits), we show it under
  // BOTH benefit groups. The veteran needs to know it applies to both —
  // either so they fill it out once and use it for both, or so they
  // understand the full scope of what that one form covers.
  let html = "";
  benefitOrder.forEach(benefit => {
    const matchedForms = byBenefit[benefit.id] || [];
    if (matchedForms.length === 0) return; // no forms for this benefit

    html += `
      <div class="benefit-form-group">
        <div class="benefit-form-group-header">${escHtml(benefit.title)}</div>
        <div class="form-tabs">
          ${matchedForms.map(f => {
            // WHY check benefit_ids.length > 1: if a form covers multiple
            // benefits, show a subtle note so the veteran knows one form
            // serves both — they don't have to fill it out twice.
            const multiNote = (f.benefit_ids || []).length > 1
              ? `<span class="multi-benefit-note">covers multiple benefits</span>`
              : '';
            return `
              <div
                class="form-tab"
                id="tab-${f.form_id}-${benefit.id}"
                onclick="selectForm('${f.form_id}')"
                title="${escHtml(f.form_title)}"
              >
                <div class="form-tab-id">VA ${escHtml(f.form_id)}</div>
                <div class="form-tab-title">
                  ${escHtml(f.form_title)}
                </div>
                ${multiNote}
                ${!f.digitized ? '<span class="not-digital">PAPER FORM</span>' : ''}
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;
  });

  // Fallback: if eligibilityResults wasn't populated yet, show ungrouped tabs
  // WHY: defensive — the grouped view depends on state.eligibilityResults
  // being set before renderFormTabs() is called. The call order in
  // loadProfileAndBenefits() guarantees this, but a safe fallback prevents
  // a blank forms section if something changes later.
  if (!html) {
    html = `<div class="form-tabs">${
      forms.map(f => `
        <div class="form-tab" id="tab-${f.form_id}" onclick="selectForm('${f.form_id}')">
          <div class="form-tab-id">VA ${escHtml(f.form_id)}</div>
          <div class="form-tab-title">${escHtml(f.form_title)}</div>
          ${!f.digitized ? '<span class="not-digital">PAPER FORM</span>' : ''}
        </div>
      `).join("")
    }</div>`;
  }

  container.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Step 3: Veteran selects a form to work on
// ---------------------------------------------------------------------------
function selectForm(formId) {
  state.activeFormId = formId;
  state.activeForm   = state.forms.find(f => f.form_id === formId);

  // Update tab styling — mark ALL tabs for this form active (a form can
  // appear under multiple benefit groups, so there may be more than one tab).
  // WHY querySelectorAll + startsWith: tab IDs are now "tab-{formId}-{benefitId}"
  // so we can't do a single getElementById lookup anymore.
  document.querySelectorAll(".form-tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".form-tab").forEach(t => {
    if (t.id.startsWith(`tab-${formId}`)) t.classList.add("active");
  });

  if (!state.activeForm) return;
  renderFormDetail(state.activeForm);
  show("form-detail");
  setStep(3);
}

// ---------------------------------------------------------------------------
// Render: unified field review for the selected form
//
// WHY two sections instead of one table:
//   Veterans need a clear mental model. "What we already know" vs. "what we
//   still need" are different jobs. Mixing them in one table causes confusion.
//
// HOW it works:
//   - Every field is an <input> — pre-populated (green) or blank (amber)
//   - Veteran can edit any pre-populated value before confirming
//   - Veteran fills in missing fields directly — or uses the photo upload
//   - One "Confirm All" button at the bottom collects everything at once
// ---------------------------------------------------------------------------
function renderFormDetail(form) {
  const f = form;

  // Form header with VA.gov link and paper-form warning if applicable
  document.getElementById("form-header").innerHTML = `
    <strong>VA Form ${escHtml(f.form_id)}</strong> — ${escHtml(f.form_title)}
    ${!f.digitized ? '<span class="not-digital-badge">Paper / Non-Digitized Form</span>' : ''}
    &nbsp;<a class="va-link" href="${escHtml(f.info_url)}" target="_blank" rel="noopener">[VA.gov info ↗]</a>
  `;

  // Progress bar
  const pct = f.summary.total > 0
    ? Math.round((f.summary.prefilled_count / f.summary.total) * 100)
    : 0;
  document.getElementById("progress-label").textContent =
    `${f.summary.prefilled_count} of ${f.summary.total} fields known — ${f.summary.missing_count} still needed from you`;
  document.getElementById("progress-bar").style.width = pct + "%";

  // Split fields into two groups
  const knownFields   = [];
  const neededFields  = [];

  f.fields.forEach(field => {
    // A field is "known" if we have a value from the profile OR it was already verified
    const verifiedVal = state.verifiedFields[field.key];
    const isKnown = verifiedVal !== undefined || field.status === "prefilled";
    const displayVal = verifiedVal !== undefined ? verifiedVal : (field.value || "");

    if (isKnown) {
      knownFields.push({ ...field, displayVal });
    } else {
      neededFields.push({ ...field, displayVal: "" });
    }
  });

  renderDocumentSuggestions(neededFields);

  // Render Section A — Known fields
  const knownHeader = document.getElementById("section-known-header");
  const knownDiv    = document.getElementById("fields-known");
  if (knownFields.length > 0) {
    knownHeader.style.display = "flex";
    knownDiv.innerHTML = knownFields.map(field => buildFieldRow(field, "is-known")).join("");
  } else {
    knownHeader.style.display = "none";
    knownDiv.innerHTML = "";
  }

  // Render Section B — Needed fields
  const neededHeader = document.getElementById("section-needed-header");
  const neededDiv    = document.getElementById("fields-needed");
  if (neededFields.length > 0) {
    neededHeader.style.display = "flex";
    neededDiv.innerHTML = neededFields.map(field => buildFieldRow(field, "is-needed")).join("");
  } else {
    neededHeader.style.display = "none";
    neededDiv.innerHTML = "";
  }

  // Reset error state
  document.getElementById("confirm-error").style.display = "none";
}

// ---------------------------------------------------------------------------
// Render grouped source-document suggestions for the fields still needed.
//
// WHY grouped suggestions:
//   A veteran should not have to notice several small "From DD-214" buttons
//   scattered through the field list. This panel says which record is worth
//   finding first and exactly which missing fields it may fill.
// ---------------------------------------------------------------------------
function renderDocumentSuggestions(neededFields) {
  const container = document.getElementById("document-suggestions");
  if (!container) return;

  const suggestions = buildDocumentSuggestionGroups(neededFields);
  if (suggestions.length === 0) {
    container.innerHTML = "";
    return;
  }

  const totalDocFillable = new Set(
    suggestions.flatMap(s => s.fields.map(field => field.key))
  ).size;
  const totalNeeded = neededFields.length;
  const manualCount = Math.max(totalNeeded - totalDocFillable, 0);

  container.innerHTML = `
    <section class="doc-suggestions-panel" aria-label="Suggested records to scan">
      <div class="doc-suggestions-header">
        <div>
          <div class="doc-suggestions-title">Suggested records to scan</div>
          <p class="doc-suggestions-copy">
            ${totalDocFillable} of ${totalNeeded} still-needed field${totalNeeded === 1 ? "" : "s"}
            may be fillable from records you might already have nearby.
            ${manualCount > 0 ? `${manualCount} field${manualCount === 1 ? "" : "s"} will still need your answer.` : ""}
          </p>
        </div>
      </div>
      <div class="doc-suggestion-list">
        ${suggestions.map(s => buildDocumentSuggestionCard(s)).join("")}
      </div>
    </section>
  `;
}

function buildDocumentSuggestionGroups(neededFields) {
  const groups = new Map();

  neededFields.forEach(field => {
    (field.source_documents || []).forEach(docType => {
      if (!groups.has(docType)) {
        groups.set(docType, {
          documentType: docType,
          meta: SOURCE_DOCUMENT_META[docType] || {
            title: docType,
            description: "May contain one or more values needed for this form.",
            priority: 99,
          },
          fields: [],
        });
      }
      groups.get(docType).fields.push(field);
    });
  });

  return Array.from(groups.values())
    .sort((a, b) => {
      const coverageDiff = b.fields.length - a.fields.length;
      if (coverageDiff !== 0) return coverageDiff;
      return (a.meta.priority || 99) - (b.meta.priority || 99);
    });
}

function buildDocumentSuggestionCard(suggestion) {
  const fieldKeys = suggestion.fields.map(field => field.key).join(",");
  const fieldLabels = suggestion.fields
    .slice(0, 4)
    .map(field => `<span class="doc-field-chip">${escHtml(field.label)}</span>`)
    .join("");
  const hiddenCount = suggestion.fields.length - 4;
  const statusId = `doc-suggest-status-${safeDomId(suggestion.documentType)}`;

  return `
    <article class="doc-suggestion-card">
      <div class="doc-suggestion-main">
        <div class="doc-suggestion-title">${escHtml(suggestion.meta.title)}</div>
        <p class="doc-suggestion-desc">${escHtml(suggestion.meta.description)}</p>
        <div class="doc-field-chip-row">
          ${fieldLabels}
          ${hiddenCount > 0 ? `<span class="doc-field-chip more">+${hiddenCount} more</span>` : ""}
        </div>
        <div class="doc-suggestion-status" id="${statusId}" aria-live="polite"></div>
      </div>
      <div class="doc-suggestion-actions">
        <button
          type="button"
          class="btn btn-primary doc-scan-btn"
          data-doc-type="${escHtml(suggestion.documentType)}"
          data-field-keys="${escHtml(fieldKeys)}"
          onclick="triggerSuggestedDocUpload(this, 'camera', event)">
          Take Photo
        </button>
        <button
          type="button"
          class="btn btn-outline doc-scan-btn"
          data-doc-type="${escHtml(suggestion.documentType)}"
          data-field-keys="${escHtml(fieldKeys)}"
          onclick="triggerSuggestedDocUpload(this, 'file', event)">
          Choose Image
        </button>
      </div>
    </article>
  `;
}

// ---------------------------------------------------------------------------
// Build a single field row as an editable input
//
// WHY always an input (not just display text):
//   The veteran needs to be able to correct any value — prefilled or not.
//   Displaying a value as plain text implies it’s locked. Nothing is locked.
//
// Args:
//   field      — field object from the API
//   inputClass — "is-known" (green) or "is-needed" (amber)
//
// WHY each field_type gets its own control:
//   - date fields use type="date" so the browser provides a date picker.
//     Veterans shouldn't need to remember date formats.
//   - select fields render a <select> from the options list in the catalog.
//     This prevents invalid values and reduces typing.
//   - textarea fields give space for narrative answers (e.g. stressor descriptions).
//   - text is the fallback for everything else.
//
// WHY always editable (never display-only):
//   The veteran needs to be able to correct any prefilled value.
//   Displaying a value as plain text implies it's locked. Nothing is locked.
// ---------------------------------------------------------------------------
function buildFieldRow(field, inputClass) {
  const fieldType   = field.field_type || "text";
  const options     = field.options || [];
  const isRequired  = field.required || (inputClass === "is-needed");
  const placeholder = inputClass === "is-needed" ? "Type your answer here…" : "";

  const requiredMark = isRequired
    ? `<span class="required-mark" title="Required">*</span>`
    : "";

  // Build the input control based on field_type
  let inputHtml;
  if (fieldType === "select" && options.length > 0) {
    // WHY <select>: constrained options prevent invalid values and reduce typing burden
    const opts = options.map(o =>
      `<option value="${escHtml(o)}" ${field.displayVal === o ? 'selected' : ''}>${escHtml(o)}</option>`
    ).join("");
    inputHtml = `
      <select
        id="input-${field.key}"
        class="field-input ${inputClass}"
        data-field-key="${field.key}"
        data-required="${isRequired}"
        onchange="this.classList.remove('is-error')">
        <option value="">— select —</option>
        ${opts}
      </select>`;
  } else if (fieldType === "date") {
    // WHY type="date": gives the browser's native date picker.
    // The text fallback (type="text") is used only if the browser doesn't support it.
    inputHtml = `
      <input
        type="date"
        id="input-${field.key}"
        class="field-input ${inputClass}"
        value="${escHtml(field.displayVal)}"
        data-field-key="${field.key}"
        data-required="${isRequired}"
        oninput="this.classList.remove('is-error')"
      />`;
  } else if (fieldType === "textarea") {
    // WHY <textarea>: narrative fields like stressor descriptions need more space.
    // A single-line input creates a frustrating UX for multi-sentence answers.
    inputHtml = `
      <textarea
        id="input-${field.key}"
        class="field-input ${inputClass} textarea-resize"
        placeholder="${placeholder}"
        data-field-key="${field.key}"
        data-required="${isRequired}"
        oninput="this.classList.remove('is-error')"
        rows="3"
      >${escHtml(field.displayVal)}</textarea>`;
  } else {
    // Default: plain text input
    inputHtml = `
      <input
        type="text"
        id="input-${field.key}"
        class="field-input ${inputClass}"
        value="${escHtml(field.displayVal)}"
        placeholder="${placeholder}"
        data-field-key="${field.key}"
        data-required="${isRequired}"
        oninput="this.classList.remove('is-error')"
      />`;
  }

  return `
    <div class="field-row" id="row-${field.key}">
      <div>
        <label class="field-label" for="input-${field.key}">
          ${escHtml(field.label)}${requiredMark}
        </label>
      </div>
      ${inputHtml}
    </div>`;
}

// ---------------------------------------------------------------------------
// Confirm All: collect every input at once, validate, then proceed to chat
//
// WHY collect all at once:
//   The veteran has reviewed everything on screen. We shouldn’t drip-feed
//   them questions for things they’ve already filled in right in front of them.
//   Chat is only for anything that genuinely couldn’t be filled here.
// ---------------------------------------------------------------------------
function confirmFields() {
  const errorEl = document.getElementById("confirm-error");
  errorEl.style.display = "none";

  // Collect all field inputs on screen
  const allInputs = document.querySelectorAll(".field-input[data-field-key]");
  let hasError = false;

  allInputs.forEach(input => {
    const key   = input.dataset.fieldKey;
    const val   = input.value.trim();
    const isReq = input.dataset.required === "true";

    if (isReq && val === "") {
      // Flag empty required fields in red — don’t proceed
      input.classList.add("is-error");
      hasError = true;
    } else {
      // Store everything the veteran has provided or confirmed
      // WHY store even known fields: veteran may have edited them
      if (val !== "") {
        state.verifiedFields[key] = val;
      }
      input.classList.remove("is-error");
    }
  });

  if (hasError) {
    errorEl.style.display = "block";
    // Scroll to the first error
    const firstError = document.querySelector(".field-input.is-error");
    if (firstError) firstError.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  // All good — reveal the download button on the form card so the veteran
  // can download immediately without waiting until the end of chat
  const dlForms = document.getElementById("download-btn-forms");
  if (dlForms) dlForms.style.display = "block";

  // Move to chat
  show("card-chat");
  setStep(4);

  // Count what’s still missing after their input
  // WHY recount: some "needed" fields may have been left blank intentionally
  // (veteran skipped optional fields) — chat can follow up on those.
  const stillMissing = state.activeForm
    ? state.activeForm.fields.filter(
        f => !state.verifiedFields[f.key] && f.status !== "prefilled"
      ).length
    : 0;

  const filledCount = Object.keys(state.verifiedFields).length;
  const formTitle   = state.activeForm ? `VA Form ${state.activeForm.form_id}` : "your form";
  const firstName   = state.veteran ? state.veteran.name.split(" ")[0] : "";
  const branch      = state.veteran?.branch ? ` for your service in the ${state.veteran.branch}` : "";

  // Greeting reflects what just happened — how much was filled, what’s left
  let greeting;
  if (stillMissing === 0) {
    greeting = `Thank you${branch}${firstName ? `, ${firstName}` : ""}. ` +
      `All ${filledCount} fields for ${formTitle} are confirmed. ` +
      `You’re ready to bring this to your VSO or the VA. ` +
      `Ask me anything about next steps or what to expect.`;
  } else {
    greeting = `Thank you${branch}${firstName ? `, ${firstName}` : ""}. ` +
      `I’ve saved the information you confirmed for ${formTitle}. ` +
      `There ${stillMissing === 1 ? "is" : "are"} still ${stillMissing} field${stillMissing > 1 ? "s" : ""} ` +
      `that need${stillMissing === 1 ? "s" : ""} your input. ` +
      `I’ll ask you about ${stillMissing === 1 ? "it" : "them"} here — one at a time. Ready when you are.`;
  }

  addMessage("assist", greeting);
  document.getElementById("card-chat").scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------------------------------------------------------------------------
// Chat: send a message
// WHY we disable the input and show 'Thinking...' during the request:
//   Real AI responses take 1–10 seconds. Without a loading indicator, the
//   veteran has no feedback that anything is happening — it looks broken.
//   We show a real spinner only while the request is actually in flight.
// ---------------------------------------------------------------------------
async function sendChat() {
  const input   = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send-btn");
  const thinking = document.getElementById("chat-thinking");
  const message = input.value.trim();
  if (!message || !state.veteranId) return;

  input.value = "";
  addMessage("user", message);
  state.conversationHistory.push({ role: "user", content: message });

  // Show loading state while waiting for API response
  input.disabled   = true;
  sendBtn.disabled = true;
  sendBtn.textContent = "Sending...";
  thinking.style.display = "block";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        veteran_id:           state.veteranId,
        message:              message,
        conversation_history: state.conversationHistory.slice(-20),
        active_form_id:       state.activeFormId,
        verified_fields:      state.verifiedFields,
      }),
    });

    const data = await res.json();
    const reply = data.reply || "I'm sorry — something went wrong. Please try again.";

    addMessage("assist", reply);
    state.conversationHistory.push({ role: "assistant", content: reply });
    setStep(5);

    const modeNote = document.getElementById("chat-mode-note");
    if (data.model === "placeholder") {
      modeNote.textContent = "Conversational assistant unavailable — AI connection not configured in this environment.";
    } else if (data.model && data.model !== "error") {
      modeNote.textContent = `Powered by ${data.model}`;
    }

  } catch (e) {
    addMessage("assist", "Something went wrong — please check your connection and try again.");
  } finally {
    // Always restore input regardless of success or error
    input.disabled      = false;
    sendBtn.disabled    = false;
    sendBtn.textContent = "Send";
    thinking.style.display = "none";
    input.focus();
  }
}

// ---------------------------------------------------------------------------
// Utility: add a message bubble to the chat
// ---------------------------------------------------------------------------
function addMessage(role, text) {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `msg msg-${role}`;
  div.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

// ---------------------------------------------------------------------------
// Utility: update the step indicator bar
// ---------------------------------------------------------------------------
function setStep(n) {
  for (let i = 1; i <= 5; i++) {
    const el = document.getElementById(`step-${i}`);
    if (!el) continue;
    el.classList.remove("active", "done");
    if (i === n)  el.classList.add("active");
    if (i < n)    el.classList.add("done");
  }
}

// ---------------------------------------------------------------------------
// Utility: show/hide elements
// ---------------------------------------------------------------------------
function show(id) { document.getElementById(id)?.classList.remove("hidden"); }
function hide(id) { document.getElementById(id)?.classList.add("hidden"); }

// ---------------------------------------------------------------------------
// Utility: escape HTML to prevent XSS when inserting user or API data into DOM
// WHY: any data coming from the API (veteran names, field values, etc.) could
// contain characters like < > & that would break the HTML if unescaped.
// ---------------------------------------------------------------------------
function escHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function safeDomId(str) {
  return String(str || "").replace(/[^a-zA-Z0-9_-]/g, "_");
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Profile mode toggle — demo / own / scan
// ---------------------------------------------------------------------------
// WHY mode is a parameter and not inferred from button click alone:
//   scanDocument() calls setProfileMode('own', true) after a successful
//   scan to transition to the own-info form with values pre-populated.
//   keepOwnValues=true skips clearing those inputs on the transition.
// ---------------------------------------------------------------------------
function setProfileMode(mode, keepOwnValues = false) {
  const isDemo = mode === "demo";
  const isOwn  = mode === "own";
  const isScan = mode === "scan";

  document.getElementById("profile-demo-section").style.display = isDemo ? "block" : "none";
  document.getElementById("profile-own-section").style.display  = isOwn  ? "block" : "none";
  document.getElementById("profile-scan-section").style.display = isScan ? "block" : "none";

  document.getElementById("btn-mode-demo").classList.toggle("active", isDemo);
  document.getElementById("btn-mode-own").classList.toggle("active",  isOwn);
  document.getElementById("btn-mode-scan").classList.toggle("active", isScan);
  if (!isScan) closeScanCamera();

  // When switching to own-info form without keepOwnValues, clear any prior values
  // so a fresh entry doesn't carry over stale data from a previous scan.
  if (isOwn && !keepOwnValues) {
    // Only clear if no scan data is already populated — check by seeing if
    // the first name field is empty (set by scanDocument when keepOwnValues=true)
    // This is intentionally lightweight: a full reset is not needed here
    // because the form starts blank on every page load anyway.
  }

  if (isScan) updateScanDocHint();
}

// ---------------------------------------------------------------------------
// Scan document — Step 1 identity photo extraction
// ---------------------------------------------------------------------------

// WHY describe hints here in JS instead of fetching /api/scan-identity/document-types:
//   The hint is a one-liner string per doc type. Embedding it avoids an extra
//   network request on every page load. If IDENTITY_SCAN_DOCUMENTS changes in
//   Python, update this object to match.
const SCAN_DOC_HINTS = {
  "DD-214":      "Contains your name, branch, service dates, discharge type, and MOS — the most complete option.",
  "MILITARY_ID": "Contains your name, branch, and rank. Doesn't have service dates or discharge info.",
  "VA_LETTER":   "Contains your name, disability rating, and sometimes service dates.",
  "GENERIC":     "Any other military or VA record — we'll extract whatever we can find.",
};

function updateScanDocHint() {
  // Update the hint text under the doc type selector when the user changes it
  const sel  = document.getElementById("scan-doc-type");
  const hint = document.getElementById("scan-doc-hint");
  if (sel && hint) hint.textContent = SCAN_DOC_HINTS[sel.value] || "";
}

// Wire up the doc type selector change event once the DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  const sel = document.getElementById("scan-doc-type");
  if (sel) sel.addEventListener("change", updateScanDocHint);
});

function previewScanImage(input) {
  // Show a small preview of the selected image so the veteran can verify
  // they photographed the right document before submitting.
  state.scanPhotoFile = null;
  closeScanCamera();
  if (input.files && input.files[0]) setScanPreview(input.files[0]);
}

function previewScanCameraImage(input) {
  // Native mobile camera capture returns a file, just like a regular picker.
  closeScanCamera();
  if (input.files && input.files[0]) {
    state.scanPhotoFile = input.files[0];
    document.getElementById("scan-file-input").value = "";
    setScanPreview(state.scanPhotoFile);
  }
}

function setScanPreview(file) {
  const preview    = document.getElementById("scan-preview");
  const previewImg = document.getElementById("scan-preview-img");
  const reader     = new FileReader();

  reader.onload = e => {
    previewImg.src        = e.target.result;
    preview.style.display = "block";
  };
  reader.readAsDataURL(file);
}

function prefersNativeCameraCapture() {
  return window.matchMedia?.("(pointer: coarse)").matches ||
    /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

async function openScanCamera() {
  const errDiv = document.getElementById("scan-error");
  const panel  = document.getElementById("scan-camera-panel");
  const video  = document.getElementById("scan-camera-video");
  const nativeCameraInput = document.getElementById("scan-camera-input");

  errDiv.style.display = "none";

  if (prefersNativeCameraCapture() && nativeCameraInput) {
    closeScanCamera();
    nativeCameraInput.click();
    return;
  }

  const isLocalhost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
  if (!window.isSecureContext && !isLocalhost) {
    errDiv.textContent = "Direct webcam capture requires HTTPS or localhost. Open the app over HTTPS, or choose an image file instead.";
    errDiv.style.display = "block";
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    errDiv.textContent = "This browser does not support direct camera capture. Please choose an image file instead.";
    errDiv.style.display = "block";
    return;
  }

  closeScanCamera();

  try {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
    } catch (firstErr) {
      // Desktop webcams often do not have a rear/environment camera.
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    }

    state.scanCameraStream = stream;
    video.srcObject        = stream;
    panel.style.display    = "block";
    await video.play();
  } catch (err) {
    errDiv.textContent = "Could not open the camera. Please allow camera access or choose an image file instead.";
    errDiv.style.display = "block";
  }
}

function captureScanPhoto() {
  const video     = document.getElementById("scan-camera-video");
  const canvas    = document.getElementById("scan-camera-canvas");
  const fileInput = document.getElementById("scan-file-input");
  const errDiv    = document.getElementById("scan-error");

  if (!state.scanCameraStream || !video.videoWidth || !video.videoHeight) {
    errDiv.textContent = "The camera is not ready yet. Please try again in a moment.";
    errDiv.style.display = "block";
    return;
  }

  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(blob => {
    if (!blob) {
      errDiv.textContent = "Could not capture the photo. Please try again or choose an image file.";
      errDiv.style.display = "block";
      return;
    }

    state.scanPhotoFile = new File([blob], `scan-photo-${Date.now()}.jpg`, { type: "image/jpeg" });
    fileInput.value = "";
    setScanPreview(state.scanPhotoFile);
    closeScanCamera();
    errDiv.style.display = "none";
  }, "image/jpeg", 0.92);
}

function closeScanCamera() {
  const panel = document.getElementById("scan-camera-panel");
  const video = document.getElementById("scan-camera-video");

  if (state.scanCameraStream) {
    state.scanCameraStream.getTracks().forEach(track => track.stop());
    state.scanCameraStream = null;
  }

  if (video) video.srcObject = null;
  if (panel) panel.style.display = "none";
}

async function scanDocument() {
  // ---------------------------------------------------------------------------
  // WHY this function exists:
  //   Veterans who choose "Scan a document" shouldn't have to type their name,
  //   branch, and service dates manually if they have a DD-214 or military ID
  //   nearby. This function sends the photo to Claude via /api/scan-identity,
  //   maps the extracted fields to the own-info form inputs, then transitions
  //   to the own-info form for the veteran to review and confirm.
  //
  // WHY we map to the own-info form rather than going straight to eligibility:
  //   We never auto-fill without the veteran seeing the values first.
  //   The scan populates the form; the veteran confirms; loadOwnProfile() runs.
  // ---------------------------------------------------------------------------

  const fileInput  = document.getElementById("scan-file-input");
  const docType    = document.getElementById("scan-doc-type").value;
  const loading    = document.getElementById("scan-loading");
  const resultNote = document.getElementById("scan-result-note");
  const errDiv     = document.getElementById("scan-error");
  const toFormDiv  = document.getElementById("scan-to-form-prompt");
  const btnSubmit  = document.getElementById("btn-scan-submit");

  // Clear any prior result
  resultNote.style.display = "none";
  errDiv.style.display     = "none";
  toFormDiv.style.display  = "none";

  const selectedFile = state.scanPhotoFile || (fileInput.files && fileInput.files[0]);

  if (!selectedFile) {
    errDiv.textContent    = "Please select or take a photo first.";
    errDiv.style.display  = "block";
    return;
  }

  // Show loading state
  loading.style.display    = "block";
  btnSubmit.disabled       = true;
  btnSubmit.textContent    = "Reading document…";

  try {
    const formData = new FormData();
    formData.append("file",          selectedFile);
    formData.append("document_type", docType);

    const res = await fetch("/api/scan-identity", {
      method: "POST",
      body:   formData,   // WHY no Content-Type header: fetch sets multipart boundary automatically
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.note || data.error || "Could not read the document.");
    }

    // Map extracted fields to the own-info form inputs
    // WHY a mapping object: field keys from the API don't always match the HTML
    // input IDs exactly. Keeping the mapping here makes it easy to adjust.
    const fields = data.extracted_fields || {};
    const fieldMap = {
      // extracted key          → own-info input ID
      name:             null,   // handled separately — split into first/last
      branch:           "own-branch",
      service_start:    "own-service-start",
      service_end:      "own-service-end",
      discharge_type:   "own-discharge",
      dob:              "own-dob",
      disability_rating: null,  // handled separately — strip the % sign
      conditions:       "own-conditions",
      rank:             null,   // no direct input in the own-info form
    };

    // Name: split "Last, First" or "First Last" into two inputs
    if (fields.name) {
      const nameParts = fields.name;
      if (nameParts.includes(",")) {
        // "Last, First Middle" format
        const [last, rest] = nameParts.split(",").map(s => s.trim());
        const firstParts   = (rest || "").split(" ");
        setValue("own-name-first", firstParts[0] || "");
        setValue("own-name-last",  last);
      } else {
        // "First Last" format
        const parts = nameParts.trim().split(" ");
        setValue("own-name-first", parts[0] || "");
        setValue("own-name-last",  parts.slice(1).join(" ") || "");
      }
    }

    // Disability rating: strip the % symbol before setting
    if (fields.disability_rating) {
      const rating = String(fields.disability_rating).replace("%", "").trim();
      setValue("own-rating", rating);
    }

    // All other mapped fields
    Object.entries(fieldMap).forEach(([key, inputId]) => {
      if (!inputId || !fields[key]) return; // skip nulls and unmapped fields
      setValue(inputId, fields[key]);
    });

    // Show result note to the veteran
    resultNote.textContent    = data.note;
    resultNote.style.display  = "block";
    toFormDiv.style.display   = "block";

  } catch (err) {
    errDiv.textContent   = err.message || "Something went wrong. Please try again or enter fields manually.";
    errDiv.style.display = "block";
  } finally {
    // Always restore UI whether scan succeeded or failed
    loading.style.display  = "none";
    btnSubmit.disabled     = false;
    btnSubmit.textContent  = "📷 Extract Fields from Photo";
  }
}

function setValue(id, value) {
  // Helper: set an input or select value if the element exists and value is non-null.
  // WHY guard with if (el): avoids silent errors if an ID changes.
  const el = document.getElementById(id);
  if (!el || value === null || value === undefined || value === "REDACTED") return;
  el.value = value;
}

// ---------------------------------------------------------------------------
// Load a veteran's own manually entered profile
// WHY we build a profile object client-side:
//   Real veterans enter their own information. We construct a profile object
//   that matches the same shape as the synthetic profiles so the rest of the
//   app works identically regardless of where the data came from.
// WHY we call /api/eligibility with POST:
//   The veteran profile isn't in veterans.json, so we can't use the GET
//   /api/eligibility/{id} endpoint. We pass the profile directly in the body.
// ---------------------------------------------------------------------------
async function loadOwnProfile() {
  const firstName = document.getElementById("own-name-first").value.trim();
  const lastName  = document.getElementById("own-name-last").value.trim();
  const branch    = document.getElementById("own-branch").value;
  const errorEl   = document.getElementById("own-error");

  // Validate required fields before proceeding
  if (!firstName || !lastName) {
    errorEl.textContent = "Please enter your first and last name.";
    errorEl.style.display = "block";
    return;
  }
  if (!branch) {
    errorEl.textContent = "Please select your branch of service.";
    errorEl.style.display = "block";
    return;
  }
  errorEl.style.display = "none";

  // Build a profile object from the form fields
  // WHY we normalize booleans from string selects:
  //   HTML selects return strings. The backend and eligibility engine
  //   expect booleans for fields like combat_deployment.
  const tooBool = id => {
    const v = document.getElementById(id).value;
    if (v === "true")  return true;
    if (v === "false") return false;
    return null;
  };

  const profile = {
    id:                          "own",
    name:                        `${firstName} ${lastName}`,
    branch,
    discharge_type:              document.getElementById("own-discharge").value || null,
    service_start:               document.getElementById("own-service-start").value || null,
    service_end:                 document.getElementById("own-service-end").value || null,
    combat_deployment:           tooBool("own-combat"),
    deployment_locations:        document.getElementById("own-deployments").value
                                   .split(",").map(s => s.trim()).filter(Boolean),
    service_connected_disability: tooBool("own-scd"),
    disability_rating_pct:       parseInt(document.getElementById("own-rating").value) || 0,
    disability_conditions:       document.getElementById("own-conditions").value
                                   .split(",").map(s => s.trim()).filter(Boolean),
    dob:                         document.getElementById("own-dob").value || null,
    enrolled_va_healthcare:      tooBool("own-va-hc"),
    receiving_disability_comp:   tooBool("own-comp"),
    income_annual:               parseInt(document.getElementById("own-income").value) || null,
    dependents:                  parseInt(document.getElementById("own-dependents").value) || 0,
    address: {
      street: document.getElementById("own-addr-street").value || "",
      city:   document.getElementById("own-addr-city").value   || "",
      state:  document.getElementById("own-addr-state").value  || "",
      zip:    document.getElementById("own-addr-zip").value    || "",
    },
    phone:  document.getElementById("own-phone").value  || null,
    email:  document.getElementById("own-email").value  || null,
    dd214_on_file: null,
    notes: "Real veteran — self-entered profile",
  };

  // Store the profile and a synthetic ID
  state.veteran            = profile;
  state.veteranId          = "own";
  state.conversationHistory = [];
  state.verifiedFields     = {};
  state.activeFormId       = null;
  state.activeForm         = null;

  // Show loading state
  document.getElementById("profile-loading").style.display = "block";
  setStep(1);
  show("card-benefits");
  hide("card-forms");
  hide("card-chat");

  try {
    // Run eligibility directly with the veteran profile in the request body
    // WHY POST not GET: there's no veteran ID in the database to look up.
    const eligRes = await fetch("/api/eligibility/own", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ veteran: profile }),
    });
    const eligData = await eligRes.json();

    // Load forms with the same inline profile
    const formsRes = await fetch("/api/forms/own", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ veteran: profile }),
    });
    const formsData = await formsRes.json();

    state.eligibilityResults = eligData.benefits || [];
    state.forms = formsData.forms || [];

    document.getElementById("profile-loading").style.display = "none";
    document.getElementById("benefit-spinner").style.display = "none";

    renderProfile(state.veteran);
    renderBenefits(eligData.benefits || [], eligData.disclaimer || "", eligData.mode || "rules_fallback");
    // WHY setStep(2) after benefits render: step 2 "Review Benefits" is now active.
    setStep(2);
    // Show card-forms + spinner first so the veteran sees activity immediately
    show("card-forms");
    document.getElementById("forms-loading").style.display = "block";
    // Hide spinner now that tabs are about to render
    document.getElementById("forms-loading").style.display = "none";
    renderFormTabs(state.forms);
    // WHY setStep(3): forms section is visible, veteran can now choose one.
    setStep(3);

  } catch (e) {
    document.getElementById("profile-loading").style.display = "none";
    document.getElementById("own-error").textContent = "Something went wrong loading your profile. Please try again.";
    document.getElementById("own-error").style.display = "block";
  }
}

// ---------------------------------------------------------------------------
// Download preparation package
// ---------------------------------------------------------------------------
// WHY this function collects all forms from state:
//   The backend is stateless — it has no memory of what the veteran confirmed.
//   We send the full current state (veteran profile + all forms with their
//   confirmed field values) so the PDF reflects everything from this session.
//
// WHY we include all forms, not just the active one:
//   The veteran may have worked through multiple forms. The PDF package
//   should cover all of them, not just whichever tab was last selected.
//
// WHY we use a temporary <a> click to trigger the download:
//   The response is a PDF file stream. Creating an object URL from the
//   blob and clicking a hidden anchor is the standard browser pattern
//   for triggering a file download from a fetch() response.
// ---------------------------------------------------------------------------
async function downloadPackage() {
  if (!state.veteran || !state.forms || state.forms.length === 0) {
    alert("Please load a profile and review your forms before downloading.");
    return;
  }

  // Build the forms payload with current verified field values merged in.
  // WHY merge verifiedFields into the forms payload:
  //   state.verifiedFields holds the veteran's edits from the current session.
  //   The backend needs these latest values — not the original prefilled ones —
  //   so the PDF reflects what the veteran actually confirmed.
  const formsPayload = state.forms.map(form => {
    const updatedFields = form.fields.map(f => ({
      ...f,
      // Use the verified value if the veteran edited or confirmed it;
      // otherwise fall back to the original prefilled value.
      value: (state.verifiedFields[f.key] !== undefined)
        ? state.verifiedFields[f.key]
        : f.value,
      status: (state.verifiedFields[f.key] !== undefined && state.verifiedFields[f.key] !== "")
        ? "prefilled"
        : f.status,
    }));

    // Recompute the summary so field counts are accurate in the PDF
    const prefilled = updatedFields.filter(f => f.status === "prefilled").length;
    const missing   = updatedFields.filter(f => f.status !== "prefilled").length;
    return {
      ...form,
      fields: updatedFields,
      summary: {
        total:           updatedFields.length,
        prefilled_count: prefilled,
        missing_count:   missing,
        missing_fields:  updatedFields
          .filter(f => f.status !== "prefilled")
          .map(f => ({ key: f.key, label: f.label })),
      },
    };
  });

  // Show a loading indicator on whichever button was clicked
  const btns = document.querySelectorAll("[onclick='downloadPackage()']");
  btns.forEach(b => { b.disabled = true; b.textContent = "Generating PDF..."; });

  try {
    const res = await fetch("/api/generate-output", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        veteran:    state.veteran,
        forms:      formsPayload,
        veteran_id: state.veteranId || "veteran",
      }),
    });

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`);
    }

    // Convert the PDF response stream to a blob and trigger a browser download
    const blob     = await res.blob();
    const url      = URL.createObjectURL(blob);
    const anchor   = document.createElement("a");
    anchor.href     = url;
    anchor.download = `vetassist_package.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);

  } catch (err) {
    alert("Could not generate the PDF. Please try again or contact support.");
    console.error("downloadPackage error:", err);
  } finally {
    // Always restore button state whether download succeeded or failed
    btns.forEach(b => { b.disabled = false; b.textContent = "⬇ Download My Preparation Package (PDF)"; });
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
init();


// ---------------------------------------------------------------------------
// Document vision upload flow
// ---------------------------------------------------------------------------
// Track which field triggered the upload and which document type we're reading
state.pendingUploadField  = null;  // field key that triggered the upload
state.pendingDocumentType = null;  // "DD-214", "21-4142", etc.
state.pendingUploadFieldKeys = null; // field keys targeted by a grouped suggestion
state.visionExtracted     = {};    // staging area — confirmed fields move to verifiedFields
state.visionModalTrigger  = null;  // button/input that opened the modal, for focus return
state.keepVisionExtractedOnClose = false;

const visionModal = document.getElementById("vision-modal");
if (visionModal) {
  visionModal.addEventListener("close", () => {
    if (!state.keepVisionExtractedOnClose) state.visionExtracted = {};
    state.keepVisionExtractedOnClose = false;
    restoreVisionModalFocus();
  });
}

function triggerSuggestedDocUpload(button, inputType, event) {
  const docType = button.dataset.docType;
  const fieldKeys = (button.dataset.fieldKeys || "")
    .split(",")
    .map(key => key.trim())
    .filter(Boolean);

  state.pendingUploadField = fieldKeys[0] || null;
  state.pendingDocumentType = docType;
  state.pendingUploadFieldKeys = fieldKeys;
  state.visionModalTrigger = event?.currentTarget || button;
  setDocumentSuggestionStatus(docType, "Waiting for document image...");

  const inputId = inputType === "camera" ? "doc-camera-input" : "doc-upload-input";
  document.getElementById(inputId)?.click();
}

async function handleDocUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Reset the input so the same file can be re-uploaded if needed
  event.target.value = "";

  // Show loading state in the triggering field’s input
  const fieldKey     = state.pendingUploadField;
  const documentType = state.pendingDocumentType;
  const trigInput    = document.getElementById(`input-${fieldKey}`);
  const targetedKeys = state.pendingUploadFieldKeys;
  if (trigInput) {
    trigInput.placeholder = "Reading document…";
    trigInput.disabled = true;
  }
  setDocumentSuggestionStatus(documentType, "Reading document... this takes a few seconds.", false, true);

  // Collect all still-needed field keys from the screen (amber inputs)
  // WHY all missing fields, not just the one clicked:
  // If the veteran has their DD-214 open, one upload can fill multiple fields at once.
  // We send everything that’s still blank — Claude extracts what it can find.
  const allMissingKeys = targetedKeys && targetedKeys.length > 0
    ? targetedKeys
    : Array.from(
        document.querySelectorAll(".field-input.is-needed[data-field-key]")
      ).map(el => el.dataset.fieldKey).filter(Boolean);

  // Build form data for multipart upload
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  formData.append("requested_fields", allMissingKeys.join(","));

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData,
      // WHY no Content-Type header: browser sets it automatically with the boundary
      // for multipart/form-data. Setting it manually breaks the boundary.
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const result = await res.json();

    // Re-enable the input regardless of outcome
    if (trigInput) {
      trigInput.placeholder = "Type your answer here…";
      trigInput.disabled = false;
    }

    if (!result.success) {
      // Show error inline under the field
      if (trigInput) {
        trigInput.placeholder = `⚠ ${result.note}`;
        trigInput.classList.add("is-error");
      }
      setDocumentSuggestionStatus(documentType, result.note || "Document reading was unavailable.", true);
      return;
    }

    setDocumentSuggestionStatus(documentType, "Values found. Review them before they populate the form.");
    // Show the confirmation modal with extracted fields
    openVisionModal(result);

  } catch (err) {
    // Show error inline in the triggering field input
    // WHY trigInput: field rows are editable <input> elements, not table cells.
    // We update the input that triggered the upload so the veteran sees the error inline.
    if (trigInput) {
      trigInput.placeholder = `⚠ ${err.message}`;
      trigInput.classList.add("is-error");
      trigInput.disabled = false;
    }
    setDocumentSuggestionStatus(documentType, err.message || "Upload failed.", true);
  } finally {
    state.pendingUploadFieldKeys = null;
  }
}

function setDocumentSuggestionStatus(documentType, message, isError = false, isLoading = false) {
  if (!documentType) return;
  const status = document.getElementById(`doc-suggest-status-${safeDomId(documentType)}`);
  if (!status) return;
  status.classList.toggle("is-error", isError);
  status.innerHTML = message
    ? `${isLoading ? '<span class="spinner"></span>' : ""}${escHtml(message)}`
    : "";
}

function openVisionModal(result) {
  // Build a confirmation form for each extracted field with a non-null value
  // WHY editable inputs and not just display values:
  // The veteran must be able to correct any field before confirming.
  const extracted = result.extracted_fields || {};
  const fieldsDiv = document.getElementById("vision-modal-fields");

  // Stash extracted values so confirmVisionFields() can access them
  state.visionExtracted = {};

  const rows = Object.entries(extracted)
    .filter(([, val]) => val !== null && val !== undefined)
    .map(([key, val], index) => {
      // Find the human-readable label for this field key
      const fieldDef = state.activeForm?.fields?.find(f => f.key === key);
      const label = fieldDef?.label || key;
      const inputId = `vision-field-${index}-${String(key).replace(/[^a-zA-Z0-9_-]/g, "_")}`;
      state.visionExtracted[key] = val;

      return `
        <div class="vision-field-group">
          <label class="vision-field-label" for="${inputId}">
            ${escHtml(label)}
          </label>
          <input
            type="text"
            id="${inputId}"
            value="${escHtml(String(val))}"
            class="vision-field-input"
            data-vision-key="${escHtml(key)}"
            oninput="state.visionExtracted[this.dataset.visionKey] = this.value"
          />
        </div>`;
    });

  if (rows.length === 0) {
    fieldsDiv.innerHTML = `<p class="modal-empty-state">No fields could be extracted from this image.</p>`;
  } else {
    fieldsDiv.innerHTML = rows.join("");
  }

  document.getElementById("vision-modal-note").textContent = result.note || "";
  const modal = document.getElementById("vision-modal");
  if (modal.showModal) {
    modal.showModal();
  } else {
    modal.setAttribute("open", "");
  }

  const firstFocusable = modal.querySelector("#vision-modal-fields input, #vision-modal-confirm, button");
  if (firstFocusable) setTimeout(() => firstFocusable.focus(), 0);
}

function closeVisionModal(clearExtracted = true) {
  const modal = document.getElementById("vision-modal");
  state.keepVisionExtractedOnClose = !clearExtracted;
  if (modal?.open && modal.close) {
    modal.close();
  } else {
    modal?.removeAttribute("open");
    if (clearExtracted) state.visionExtracted = {};
    restoreVisionModalFocus();
  }
}

function restoreVisionModalFocus() {
  if (state.visionModalTrigger && typeof state.visionModalTrigger.focus === "function") {
    state.visionModalTrigger.focus();
  }
  state.visionModalTrigger = null;
}

function confirmVisionFields() {
  const confirmedFields = { ...state.visionExtracted };

  // Move all confirmed extracted values into state.verifiedFields
  // WHY verifiedFields and not direct form state:
  // verifiedFields is the single source of truth for confirmed data.
  // The field table, chat context, and form output all read from it.
  closeVisionModal(false);
  state.visionExtracted = {};

  Object.entries(confirmedFields).forEach(([key, val]) => {
    if (val !== null && val !== undefined && String(val).trim() !== "") {
      state.verifiedFields[key] = String(val).trim();
    }
  });

  // After vision confirm, two things happen:
  // 1. Update any visible input fields on screen with the extracted values
  //    (so the veteran sees the filled-in values right away without a full re-render)
  // 2. Flip those rows from amber (is-needed) to green (is-known)
  Object.entries(state.verifiedFields).forEach(([key, val]) => {
    const input = document.getElementById(`input-${key}`);
    if (input) {
      input.value = val;
      input.classList.remove("is-needed", "is-error");
      input.classList.add("is-known");
    }
  });

  // Also update the active form's field list so the section grouping stays correct
  // on the next full re-render (e.g. if the veteran switches form tabs)
  if (state.activeForm) {
    state.activeForm.fields = state.activeForm.fields.map(field => {
      if (state.verifiedFields[field.key] !== undefined) {
        return { ...field, value: state.verifiedFields[field.key], status: "prefilled" };
      }
      return field;
    });
    const prefilled = state.activeForm.fields.filter(f => f.status === "prefilled").length;
    const total     = state.activeForm.fields.length;
    state.activeForm.summary = {
      ...state.activeForm.summary,
      prefilled_count: prefilled,
      missing_count:   total - prefilled,
    };
    renderFormDetail(state.activeForm);
  }
}
