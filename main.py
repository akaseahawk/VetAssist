"""
main.py — VetAssist FastAPI application

HOW THIS APP WORKS (read this first):
    VetAssist follows a simple, linear flow:
      1. Veteran is selected → profile loaded from JSON
      2. Eligibility engine runs rules → returns list of likely benefits
      3. Veteran sees benefits, selects a form to work on
      4. Form fields are prefilled from profile → missing fields identified
      5. Veteran edits/confirms prefilled fields in the UI (no assumptions)
      6. Claude asks for missing fields conversationally — one at a time
      7. Output package generated (post-MVP)

    Claude is used for conversation only — the rules engine handles eligibility.
    Claude can add nuance and explain benefits using its innate knowledge,
    but it does not make eligibility decisions.

WHY FastAPI:
    - Lightweight, fast, and has automatic API docs at /docs
    - Built-in request/response validation via Pydantic
    - Easy to swap in a real database or auth layer later without rewriting routes

WHY JSON files instead of a database:
    - Zero setup — clone and run, no database server needed
    - Easy to read and edit for demo purposes
    - Clear separation: data lives in /data, logic lives in /services
    - Post-MVP: replace load_json() calls with database queries — nothing else changes

RUNNING LOCALLY:
    pip install -r requirements.txt
    cp .env.example .env           # add ANTHROPIC_API_KEY for live chat
    uvicorn main:app --reload
    open http://localhost:8000

API ENDPOINTS:
    GET  /                          → serves the frontend HTML page
    GET  /api/veterans              → list all veteran profiles (id, name, branch)
    GET  /api/veterans/{id}         → full profile for one veteran
    GET  /api/eligibility/{id}      → run benefit eligibility for a veteran
    GET  /api/forms/{id}            → matched forms + prefilled fields for a veteran
    POST /api/chat                  → send a message to the conversational assistant
    POST /api/upload                → (stub) future: accept DD214/PDF and extract fields
    POST /api/generate-output       → (stub) future: produce printable/email output
    GET  /health                    → health check

TODO (post-MVP — do not add these to the MVP):
    - POST /api/upload: accept DD214 or flat PDF, OCR it, merge fields into prefill
    - POST /api/generate-output: produce a printable PDF or email-ready package
    - Authentication via login.gov or VA identity service
    - Replace JSON files with PostgreSQL or DynamoDB
    - Deploy to AWS Bedrock + GovCloud for FedRAMP-eligible federal use
"""

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file if present (sets ANTHROPIC_API_KEY, CLAUDE_MODEL, etc.)
load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VetAssist",
    description="Veteran benefits and forms assistant — Wilcore Innovation Challenge MVP",
    version="0.1.0",
)

# Mount static files (CSS, images) if that folder exists.
# WHY conditional: keeps the app runnable even if /static doesn't exist yet.
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ---------------------------------------------------------------------------
# Data helpers
# WHY load from disk on each request (not cached in memory):
# For an MVP with a handful of JSON files, this is fine — files are small.
# If this became a production app with many users, we'd cache these in memory
# or replace with database queries. For now, simplicity wins.
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str):
    """Read and parse a JSON file from the /data directory."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r") as f:
        return json.load(f)


def get_veteran_by_id(veteran_id: str) -> Optional[dict]:
    """
    Find and return a single veteran profile by ID.
    Returns None if not found — callers handle the 404 response.
    """
    for v in load_json("veterans.json"):
        if v["id"] == veteran_id:
            return v
    return None


def get_benefits_catalog() -> list:
    """Return the list of benefit definitions from benefits_rules.json."""
    return load_json("benefits_rules.json").get("benefits", [])


def get_forms_catalog() -> list:
    """Return the list of form definitions from forms_catalog.json."""
    return load_json("forms_catalog.json").get("forms", [])


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """
    Serve the single-page HTML frontend.
    WHY not use a template engine: one static HTML file is simpler to read,
    edit, and demo. No Jinja2, no build step needed.
    """
    template = Path(__file__).parent / "templates" / "index.html"
    if not template.exists():
        return HTMLResponse("<h1>VetAssist</h1><p>Frontend not found.</p>")
    return HTMLResponse(content=template.read_text())


# ---------------------------------------------------------------------------
# Veteran routes
# ---------------------------------------------------------------------------

@app.get("/api/veterans")
async def list_veterans():
    """
    Return a summary list of all veteran profiles.
    We only return id, name, and branch here — not the full profile —
    to keep the dropdown response small and fast.
    """
    veterans = load_json("veterans.json")
    return [{"id": v["id"], "name": v["name"], "branch": v["branch"]} for v in veterans]


@app.get("/api/veterans/{veteran_id}")
async def get_veteran(veteran_id: str):
    """Return the full profile for a single veteran."""
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")
    return veteran


# ---------------------------------------------------------------------------
# Eligibility route
# ---------------------------------------------------------------------------

@app.get("/api/eligibility/{veteran_id}")
async def get_eligibility(veteran_id: str):
    """
    Discover benefits worth exploring for a veteran.

    HOW IT WORKS:
      - If ANTHROPIC_API_KEY is set: Claude reads the veteran profile and uses
        its own VA knowledge to surface relevant benefits — reasoning the way
        a knowledgeable VSO would, not from hardcoded rules.
      - If no API key: falls back to the rules engine in eligibility.py.
      - Either way, results are framed as 'worth exploring' — never a determination.

    WHY this is a separate route from /api/forms:
      The veteran sees benefits FIRST and decides which ones to pursue.
      They then select a form. Two-step flow matches the intended UX.

    IMPORTANT: This system does not determine eligibility.
      The VA and the veteran's VSO make that determination.
      We help veterans understand what to ask about and prepare paperwork.
    """
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")

    from services.benefit_discovery import discover_benefits
    result = discover_benefits(veteran)

    return {
        "veteran_id":   veteran_id,
        "veteran_name": veteran["name"],
        "branch":       veteran.get("branch", ""),
        "benefits":     result["benefits"],
        "mode":         result["mode"],
        "disclaimer":   result["disclaimer"],
    }


# ---------------------------------------------------------------------------
# Forms route
# ---------------------------------------------------------------------------

@app.get("/api/forms/{veteran_id}")
async def get_forms(veteran_id: str):
    """
    Return the VA forms the veteran likely needs, with fields prefilled
    from their profile and missing fields identified.

    Flow:
      1. Run eligibility to get eligible benefit IDs
      2. Match those IDs to forms in the catalog
      3. For each form, prefill fields from the profile
      4. Return prefilled fields + a summary of what's known vs. missing

    WHY we run eligibility again here (instead of caching):
    This keeps each endpoint self-contained and stateless — easier to
    debug and test. The eligibility check is fast (pure Python, no I/O).
    Post-MVP: if this becomes slow, pass eligible_ids as a query parameter.
    """
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")


    # Step 1: Discover which benefits are worth exploring for this veteran
    # Uses Claude if API key is set, rules engine as fallback
    from services.benefit_discovery import discover_benefits
    from services.form_matcher import get_forms_for_benefits, prefill_fields, build_field_summary
    discovery = discover_benefits(veteran)
    eligible_ids = [b["benefit_id"] for b in discovery["benefits"]]

    # Step 2: Find forms that correspond to those eligible benefits
    matched_forms = get_forms_for_benefits(eligible_ids, get_forms_catalog())

    # Step 3: For each form, prefill what we know and flag what's missing
    output = []
    for form in matched_forms:
        prefilled = prefill_fields(form, veteran)
        summary   = build_field_summary(prefilled)
        output.append({**prefilled, "summary": summary})

    return {
        "veteran_id":          veteran_id,
        "veteran_name":        veteran["name"],
        "eligible_benefit_ids": eligible_ids,
        "forms":               output,
    }


# ---------------------------------------------------------------------------
# Chat route
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    veteran_id:           str
    message:              str
    # Prior conversation turns sent from the frontend.
    # WHY the frontend sends history: the backend is stateless — no session.
    # The frontend accumulates turns and sends them back each time.
    # This is simple and works fine for a local MVP.
    conversation_history: list = []
    # The form the veteran is currently working on (e.g. "21-526EZ").
    # Helps Claude focus its questions on the right form's missing fields.
    active_form_id:       Optional[str] = None
    # Fields the veteran has already confirmed as correct in the UI.
    # Claude uses this to avoid re-asking for things already verified.
    verified_fields:      dict = {}


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Send the veteran's message to Claude and return the response.

    WHY we compute context here (not cache it):
    Each chat turn needs current missing fields — the veteran may have
    just confirmed some fields in the UI, changing what's still needed.
    The eligibility check is fast, so recomputing is fine for the MVP.

    What Claude receives:
      - Full veteran profile (branch, service, conditions, etc.)
      - Eligible benefit list with reasons (from rules engine)
      - Branch-specific VSO contacts and benefit notes
      - Fields still missing for the active form
      - Fields already verified by the veteran (don't re-ask)
      - Last 20 turns of conversation history
    """
    veteran = get_veteran_by_id(request.veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{request.veteran_id}' not found.")

    from services.benefit_discovery import discover_benefits
    from services.form_matcher import get_forms_for_benefits, prefill_fields, build_field_summary
    from services.claude_chat import chat as claude_chat

    # Discover benefits to give Claude full context for the conversation
    discovery = discover_benefits(veteran)
    eligibility_results = discovery["benefits"]  # Claude chat uses these for context
    eligible_ids = [b["benefit_id"] for b in eligibility_results]

    # Find missing fields for the active form (or all eligible forms if none selected)
    forms_catalog = get_forms_catalog()

    if request.active_form_id:
        # Veteran is working on a specific form — only show that form's missing fields
        active_forms = [f for f in forms_catalog if f["id"] == request.active_form_id]
    else:
        # No form selected yet — show all forms' missing fields (benefits phase)
        active_forms = get_forms_for_benefits(eligible_ids, forms_catalog)

    # Collect all missing fields across relevant forms, deduplicated by field key.
    # WHY deduplicate: multiple forms may need the same field (e.g. SSN appears
    # on almost every form). We only want to ask the veteran once.
    seen_keys  = set(request.verified_fields.keys())  # don't re-ask verified fields
    missing    = []
    for form in active_forms:
        prefilled = prefill_fields(form, veteran)
        summary   = build_field_summary(prefilled)
        for field in summary["missing_fields"]:
            if field["key"] not in seen_keys:
                missing.append(field)
                seen_keys.add(field["key"])

    # Call Claude with full context
    result = claude_chat(
        user_message=request.message,
        veteran=veteran,
        eligible_benefits=eligibility_results,
        missing_fields=missing,
        verified_fields=request.verified_fields,
        conversation_history=request.conversation_history,
        active_form=request.active_form_id,
    )

    return {
        "veteran_id":    request.veteran_id,
        "reply":         result["response"],
        "model":         result["model"],
        "missing_count": len(missing),  # lets the UI show progress
        "error":         result.get("error"),
    }


# ---------------------------------------------------------------------------
# Upload stub
# Post-MVP: OCR a DD214 or flat PDF and merge fields into prefill context
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "DD-214",
    veteran_id: Optional[str] = None,
    requested_fields: Optional[str] = None,  # comma-separated list of field keys
):
    """
    Accept a photo or scan of a veteran's document and extract fields using Claude vision.

    WHY multimodal vision and not OCR:
      Traditional OCR scans pixels for characters. It fails on skewed phone photos,
      stamps, handwriting, and low-contrast backgrounds — all common in veteran documents.
      Claude vision understands the document semantically: it knows what a DD-214
      looks like and where the discharge type field is, even in a tilted photo.

    WHY the veteran confirms every field before it populates:
      We never auto-fill without consent. A blurry photo or partially redacted field
      can produce a wrong value. The veteran reviews each extracted value with an Edit
      button, then clicks Confirm. Only confirmed values flow into their form.

    Args:
      file:             Image file (JPEG, PNG, WebP, or GIF)
      document_type:    "DD-214", "21-4142", or "GENERIC"
      veteran_id:       Optional — used to look up which fields are still missing
      requested_fields: Comma-separated field keys to extract (e.g. "name,branch,service_start")
                        If omitted, defaults to the known fields for the document type.

    Returns:
      {
        "success": bool,
        "document_type": str,
        "extracted_fields": { field_key: value_or_null },
        "fields_found": int,
        "fields_requested": int,
        "note": str,       # shown to veteran above the confirmation table
        "error": str|null
      }
    """

    # Validate file type — we only support image formats Claude vision accepts
    # WHY: Claude vision does not accept PDFs or text files via the image API.
    # PDF support would require a PDF-to-image conversion step (post-MVP).
    ALLOWED_MIME_TYPES = {
        "image/jpeg":  True,
        "image/png":   True,
        "image/webp":  True,
        "image/gif":   True,
    }
    mime_type = file.content_type or "image/jpeg"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"File type '{mime_type}' is not supported. "
                "Please upload a JPEG, PNG, WebP, or GIF image. "
                "If you have a PDF, take a screenshot or photo of the relevant page."
            ),
        )

    # Read the image bytes from the upload
    image_bytes = await file.read()

    # Parse requested_fields from comma-separated string to list
    # WHY: query params are easier for the frontend to construct than a JSON body
    # alongside a file upload (multipart forms mix poorly with JSON bodies).
    field_list: list[str] = []
    if requested_fields:
        field_list = [f.strip() for f in requested_fields.split(",") if f.strip()]

    # If veteran_id is provided and no fields were specified,
    # look up which fields are still missing for that veteran and request those.
    # WHY: this lets the frontend say "extract what we're missing" without
    # having to know the field list itself.
    if veteran_id and not field_list:
        veteran = get_veteran_by_id(veteran_id)
        if veteran:
            from services.form_matcher import get_missing_fields_for_veteran
            try:
                field_list = get_missing_fields_for_veteran(veteran, {"forms": get_forms_catalog()})
            except Exception:
                pass  # If lookup fails, fall back to document-type defaults

    # Call the vision extraction service
    from services.document_vision import extract_fields_from_image
    result = extract_fields_from_image(
        image_bytes=image_bytes,
        mime_type=mime_type,
        document_type=document_type,
        requested_fields=field_list,
    )

    return result


@app.get("/api/upload/suggestions/{veteran_id}")
async def get_document_suggestions(veteran_id: str, form_id: Optional[str] = None):
    """
    For a given veteran and optional form, return which source documents
    might contain their missing fields — so the UI can suggest the right document.

    WHY a separate suggestions endpoint:
      The frontend needs to know what to suggest BEFORE the veteran has uploaded
      anything. This lets us show "Your DD-214 might have 4 of your missing fields"
      right next to the missing field rows in the table.
    """
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found")

    # Find missing fields — ask fields that haven't been answered yet
    # We look across all forms or just the specified one
    from services.form_matcher import get_missing_fields_for_veteran
    try:
        missing_fields = get_missing_fields_for_veteran(veteran, {"forms": get_forms_catalog()}, form_id=form_id)
    except Exception:
        missing_fields = []

    from services.document_vision import suggest_source_documents
    suggestions = suggest_source_documents(missing_fields)

    return {
        "veteran_id": veteran_id,
        "form_id": form_id,
        "missing_fields": missing_fields,
        "document_suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Output generation stub
# Post-MVP: produce a printable PDF or email-ready package
# ---------------------------------------------------------------------------

@app.post("/api/generate-output")
async def generate_output():
    """
    STUB — not implemented in the MVP.

    What this will do (future sprint):
      1. Take the veteran's profile + verified form fields
      2. Generate a prefilled PDF using pypdf or reportlab
      3. Include a cover sheet with: submission instructions, who to contact,
         what to bring, and next steps — all customized to their branch and benefit
      4. Return as a downloadable file or email it directly

    WHY this is valuable:
    The veteran gets a complete package they can print, bring to a VSO, or
    email to their VA regional office — with no repeated data entry.
    """
    return {
        "status":  "not_implemented",
        "message": (
            "Printable/email output generation is planned for a future sprint. "
            "In the MVP, form field data is displayed in the browser and can be reviewed there."
        ),
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Simple health check. Used to verify the server is running."""
    return {"status": "ok", "app": "VetAssist", "version": "0.1.0-mvp"}
