"""
services/document_vision.py

WHY this exists:
  Veterans often have the information we need locked inside physical documents —
  a DD-214 in a folder, a VA letter in a drawer, a discharge paper they've had for decades.
  Instead of asking them to type it out from memory, we let them photograph or scan it
  and send the image to Claude, which reads it like a human would.

  This is multimodal vision — NOT traditional OCR.
  Traditional OCR does pixel-level character scanning. It fails on skewed photos,
  handwriting, stamps, and low-contrast text.
  Claude vision understands the document semantically: it knows what a DD-214 looks like,
  where the "Character of Discharge" box is, and what to do with a partially visible field.

  WHY every extracted field goes back to the veteran for confirmation:
  We never assume extracted data is correct. A blurry photo, a redaction, a typo on the
  original document — any of these could cause a wrong value. The veteran confirms each
  field before it populates their form. VetAssist does not auto-fill without consent.

FLOW:
  1. Receive image bytes + MIME type + list of fields we want
  2. Build a Claude prompt that describes exactly which fields to extract
  3. Send image + prompt to Claude via the messages API (vision input)
  4. Parse the JSON response into a structured dict
  5. Return extracted fields + confidence notes for each
  6. Caller (main.py) returns to frontend; veteran confirms before any field populates
"""

import base64
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# --- Field definitions for documents we know about ---
# WHY a lookup table: each document has a known layout and known field positions.
# Telling Claude exactly what to look for improves accuracy vs. open-ended extraction.

DOCUMENT_FIELD_DEFINITIONS = {
    "DD-214": {
        "document_description": (
            "A DD-214 (Certificate of Release or Discharge from Active Duty) is the official "
            "military discharge document issued to U.S. service members at separation. "
            "It contains boxes numbered 1-30 in a standard layout. Box 1 is name, "
            "Box 12 is service dates, Box 24 is character of discharge, Box 11 is primary MOS."
        ),
        "fields": {
            "name":           "Box 1 — full name of the service member (Last, First, Middle)",
            "branch":         "Box 9 — branch of service (e.g. Army, Navy, Marine Corps, Air Force, Coast Guard)",
            "service_start":  "Box 12a — date entered active duty this period (YYYYMMDD or MM/DD/YYYY format)",
            "service_end":    "Box 12b — separation date this period (YYYYMMDD or MM/DD/YYYY format)",
            "discharge_type": "Box 24 — character of service / type of discharge (e.g. Honorable, General, OTH)",
            "rank":           "Box 4 — grade/rate/rank at time of separation",
            "mos":            "Box 11 — primary specialty (MOS/AFSC/Rating code and title)",
            "deployment_info":"Box 18 — remarks section, which often contains deployment locations and dates",
            "decorations":    "Box 13 — decorations, medals, badges, commendations, citations, campaign ribbons",
        }
    },
    "21-4142": {
        "document_description": (
            "VA Form 21-4142 is the Authorization to Disclose Information to the Department "
            "of Veterans Affairs. It authorizes the VA to obtain private medical records. "
            "It contains the veteran's personal identification information."
        ),
        "fields": {
            "name":    "Veteran's full name field",
            "ssn":     "Social Security Number field (may be partially redacted — extract what is visible)",
            "dob":     "Veteran's date of birth",
            "address": "Current mailing address (street, city, state, ZIP)",
            "phone":   "Daytime phone number",
            "email":   "Email address if present",
        }
    },
    "GENERIC": {
        "document_description": (
            "A VA-related document, military record, or correspondence. "
            "Extract any fields that appear to be personal identification, "
            "service history, medical information, or form field values."
        ),
        "fields": {
            "name":           "Full name of the veteran",
            "ssn":            "Social Security Number (if visible)",
            "dob":            "Date of birth",
            "branch":         "Branch of military service",
            "service_start":  "Service start / entry date",
            "service_end":    "Service end / separation date",
            "discharge_type": "Character of discharge or type of separation",
            "address":        "Mailing or home address",
        }
    }
}


def _build_extraction_prompt(document_type: str, requested_fields: list[str]) -> str:
    """
    Build the Claude prompt for field extraction from a document image.

    WHY we constrain to requested_fields:
      We only ask Claude to extract what the current form actually needs.
      This keeps the response small, focused, and easy to validate.
      It also avoids extracting SSNs or sensitive fields unless the form genuinely requires them.
    """
    doc_def = DOCUMENT_FIELD_DEFINITIONS.get(document_type, DOCUMENT_FIELD_DEFINITIONS["GENERIC"])

    # Filter field definitions to only the ones we actually need
    relevant_fields = {
        field_key: field_desc
        for field_key, field_desc in doc_def["fields"].items()
        if field_key in requested_fields
    }

    # If none of our known fields match, fall back to all fields for this doc type
    if not relevant_fields:
        relevant_fields = doc_def["fields"]

    field_lines = "\n".join(
        f'  "{key}": {desc}' for key, desc in relevant_fields.items()
    )

    return f"""You are reviewing an image of a {document_type} document to help a veteran fill out a VA benefits form.

Document context: {doc_def["document_description"]}

Your task: Extract the following specific fields from the document image. Return ONLY a JSON object — no explanation, no markdown, no code fences. Just the raw JSON.

Fields to extract:
{field_lines}

Rules:
- If a field is clearly visible and readable, include its value as a string.
- If a field is partially visible, include what you can read and add a note in parentheses, e.g. "2003-06 (partial — day not visible)".
- If a field is not present in this document, set its value to null.
- If a field is redacted or intentionally obscured, set its value to "REDACTED".
- Never guess or invent values. Only extract what is actually visible.
- For dates, use YYYY-MM-DD format if possible.
- For names, use "Last, First Middle" format if that matches the document.

Return format (example):
{{
  "name": "Sanchez, Maria Elena",
  "branch": "Army",
  "service_start": "2003-06-15",
  "discharge_type": "Honorable",
  "rank": null
}}

Now extract the fields from the document image provided."""


def extract_fields_from_image(
    image_bytes: bytes,
    mime_type: str,
    document_type: str,
    requested_fields: list[str],
) -> dict:
    """
    Send a document image to Claude and extract structured fields.

    Args:
        image_bytes:      Raw bytes of the uploaded image
        mime_type:        MIME type — "image/jpeg", "image/png", "image/webp", "image/gif"
        document_type:    One of "DD-214", "21-4142", or "GENERIC"
        requested_fields: List of field keys the current form needs (e.g. ["name", "branch"])

    Returns:
        {
          "success": bool,
          "document_type": str,
          "extracted_fields": { field_key: value_or_null },
          "fields_found": int,
          "fields_requested": int,
          "note": str,          # human-readable summary shown to veteran
          "error": str | None   # set if extraction failed
        }

    WHY we return a structured result with success/error flags:
      The caller (main.py) needs to handle partial success gracefully.
      If Claude extracts 3 of 5 fields, that's still useful — we shouldn't fail the
      whole request. The frontend shows what was found and lets the veteran fill the rest.
    """

    # Check for API key — vision requires the Anthropic API
    # WHY: there's no rules-based fallback for image extraction. Without the key,
    # we tell the veteran clearly rather than silently failing.
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "success": False,
            "document_type": document_type,
            "extracted_fields": {},
            "fields_found": 0,
            "fields_requested": len(requested_fields),
            "note": (
                "Document reading requires an AI API key that isn't configured in this environment. "
                "Please enter the missing fields manually, or ask your VSO for help."
            ),
            "error": "ANTHROPIC_API_KEY not set",
        }

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        model = os.environ.get("CLAUDE_MODEL", "claude-opus-4-5")

        # WHY base64: the Anthropic vision API requires images encoded as base64 strings,
        # not raw bytes or URLs. This is standard for multimodal API calls.
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        prompt = _build_extraction_prompt(document_type, requested_fields)

        response = client.messages.create(
            model=model,
            max_tokens=1024,  # WHY 1024: field extraction returns a small JSON object, not prose
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        raw_text = response.content[0].text.strip()

        # WHY strip code fences: Claude sometimes wraps JSON in ```json ... ```
        # even when told not to. Strip defensively.
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        extracted = json.loads(raw_text)

        # Count how many fields actually came back with non-null values
        fields_found = sum(1 for v in extracted.values() if v is not None and v != "REDACTED")

        # Build a human-readable note for the veteran
        if fields_found == 0:
            note = "We couldn't read any fields from this image. Please check the photo quality and try again, or enter the fields manually."
        elif fields_found < len(requested_fields):
            note = (
                f"We found {fields_found} of {len(requested_fields)} fields in your document. "
                "Please review each value and fill in anything that's missing or unclear."
            )
        else:
            note = (
                f"We found all {fields_found} fields in your document. "
                "Please review each value carefully before confirming — a blurry photo or "
                "redacted field could cause an incorrect value."
            )

        return {
            "success": True,
            "document_type": document_type,
            "extracted_fields": extracted,
            "fields_found": fields_found,
            "fields_requested": len(requested_fields),
            "note": note,
            "error": None,
        }

    except json.JSONDecodeError as e:
        # WHY handle separately: if Claude returns valid text but not valid JSON,
        # we want a clear error rather than a 500. Log the raw text for debugging.
        logger.error("Claude returned non-JSON from vision extraction: %s", raw_text if 'raw_text' in dir() else "unknown")
        return {
            "success": False,
            "document_type": document_type,
            "extracted_fields": {},
            "fields_found": 0,
            "fields_requested": len(requested_fields),
            "note": "We had trouble reading the document. Please try a clearer photo or enter fields manually.",
            "error": f"JSON parse error: {e}",
        }

    except Exception as e:
        logger.error("Vision extraction failed: %s", str(e))
        return {
            "success": False,
            "document_type": document_type,
            "extracted_fields": {},
            "fields_found": 0,
            "fields_requested": len(requested_fields),
            "note": "Something went wrong reading the document. Please enter the fields manually.",
            "error": str(e),
        }


def suggest_source_documents(missing_field_keys: list[str]) -> list[dict]:
    """
    Given a list of missing field keys, return which source documents
    might contain those fields — so we can suggest the right document to the veteran.

    WHY: Instead of just saying "upload a document," we tell the veteran specifically
    which document to look for and which fields it covers.

    Example return:
    [
      {
        "document_type": "DD-214",
        "document_title": "Certificate of Release or Discharge from Active Duty",
        "covers_fields": ["name", "branch", "service_start", "service_end", "discharge_type"],
        "suggestion": "Your DD-214 may contain 4 of your missing fields. Do you have it nearby?"
      }
    ]
    """
    # Build a reverse map: field_key -> list of document_types that contain it
    field_to_docs: dict[str, list[str]] = {}
    for doc_type, doc_def in DOCUMENT_FIELD_DEFINITIONS.items():
        if doc_type == "GENERIC":
            continue  # Don't suggest "GENERIC" to veterans — it's a fallback, not a real doc
        for field_key in doc_def["fields"]:
            field_to_docs.setdefault(field_key, []).append(doc_type)

    # For each source document, count how many missing fields it covers
    doc_coverage: dict[str, list[str]] = {}
    for field_key in missing_field_keys:
        for doc_type in field_to_docs.get(field_key, []):
            doc_coverage.setdefault(doc_type, []).append(field_key)

    # Build suggestion objects for documents that cover at least one missing field
    suggestions = []
    doc_titles = {
        "DD-214":  "Certificate of Release or Discharge from Active Duty",
        "21-4142": "Authorization to Disclose Information to the VA",
    }

    for doc_type, covered_fields in doc_coverage.items():
        count = len(covered_fields)
        plural = "field" if count == 1 else "fields"
        suggestions.append({
            "document_type": doc_type,
            "document_title": doc_titles.get(doc_type, doc_type),
            "covers_fields": covered_fields,
            "suggestion": (
                f"Your {doc_type} may contain {count} of your missing {plural} "
                f"({', '.join(covered_fields)}). "
                f"Do you have it nearby? You can take a photo or upload a scan."
            ),
        })

    # Sort by coverage — most helpful document first
    suggestions.sort(key=lambda s: len(s["covers_fields"]), reverse=True)
    return suggestions
