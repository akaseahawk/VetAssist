"""
main.py — VetAssist FastAPI application

Minimal local MVP. No database, no authentication, no cloud deployment.
Runs entirely on local JSON files and a single HTML page.

Usage:
    pip install -r requirements.txt
    cp .env.example .env           # then add your ANTHROPIC_API_KEY
    uvicorn main:app --reload

Endpoints:
    GET  /                    → serves index.html
    GET  /api/veterans        → list all synthetic veteran profiles
    GET  /api/veterans/{id}   → get one veteran's full profile
    GET  /api/eligibility/{id} → run eligibility check for a veteran
    GET  /api/forms/{id}      → get matched forms with prefilled fields
    POST /api/chat            → send a message to the conversational assistant

TODO (post-MVP):
    - POST /api/upload        → accept DD214 or flat PDF and extract text (OCR)
    - POST /api/generate-output → produce a printable/email-ready package
    - Authentication and session management for production
    - Replace JSON files with a real database (PostgreSQL or DynamoDB)
    - Deploy to AWS Bedrock endpoint for FedRAMP-eligible infrastructure
"""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VetAssist",
    description="Veteran benefits assistant — Wilcore Innovation Challenge MVP",
    version="0.1.0",
)

# Serve static files if the static/ directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ---------------------------------------------------------------------------
# Data loading utilities
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename: str) -> any:
    """Load and return parsed JSON from the data directory."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    with open(filepath, "r") as f:
        return json.load(f)


def get_all_veterans() -> list:
    return load_json("veterans.json")


def get_veteran_by_id(veteran_id: str) -> dict:
    veterans = get_all_veterans()
    for v in veterans:
        if v["id"] == veteran_id:
            return v
    return None


def get_benefits_catalog() -> list:
    data = load_json("benefits_rules.json")
    return data.get("benefits", [])


def get_forms_catalog() -> list:
    data = load_json("forms_catalog.json")
    return data.get("forms", [])


# ---------------------------------------------------------------------------
# Route: Serve frontend
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main single-page frontend."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if not template_path.exists():
        return HTMLResponse("<h1>VetAssist</h1><p>Frontend template not found.</p>", status_code=200)
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())


# ---------------------------------------------------------------------------
# Route: Veterans
# ---------------------------------------------------------------------------

@app.get("/api/veterans")
async def list_veterans():
    """Return all synthetic veteran profiles (names and IDs only for listing)."""
    veterans = get_all_veterans()
    return [{"id": v["id"], "name": v["name"], "branch": v["branch"]} for v in veterans]


@app.get("/api/veterans/{veteran_id}")
async def get_veteran(veteran_id: str):
    """Return the full profile for a specific veteran."""
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")
    return veteran


# ---------------------------------------------------------------------------
# Route: Eligibility
# ---------------------------------------------------------------------------

@app.get("/api/eligibility/{veteran_id}")
async def get_eligibility(veteran_id: str):
    """
    Run the rules-based eligibility engine for a veteran.
    Returns a list of benefits with eligible=True/False and a reason string.
    """
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")

    from services.eligibility import check_eligibility
    catalog = get_benefits_catalog()
    results = check_eligibility(veteran, catalog)

    return {
        "veteran_id": veteran_id,
        "veteran_name": veteran["name"],
        "benefits": results,
    }


# ---------------------------------------------------------------------------
# Route: Forms
# ---------------------------------------------------------------------------

@app.get("/api/forms/{veteran_id}")
async def get_forms(veteran_id: str):
    """
    Return matched VA forms for a veteran's eligible benefits,
    with fields prefilled where possible and missing fields identified.
    """
    veteran = get_veteran_by_id(veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{veteran_id}' not found.")

    from services.eligibility import check_eligibility
    from services.form_matcher import get_forms_for_benefits, prefill_fields, build_field_summary

    # Step 1: Get eligible benefits
    benefits_catalog = get_benefits_catalog()
    eligibility_results = check_eligibility(veteran, benefits_catalog)
    eligible_ids = [b["benefit_id"] for b in eligibility_results if b["eligible"]]

    # Step 2: Match forms to eligible benefits
    forms_catalog = get_forms_catalog()
    matched_forms = get_forms_for_benefits(eligible_ids, forms_catalog)

    # Step 3: Prefill fields from profile
    output = []
    for form in matched_forms:
        prefilled = prefill_fields(form, veteran)
        summary = build_field_summary(prefilled)
        output.append({
            **prefilled,
            "summary": summary,
        })

    return {
        "veteran_id": veteran_id,
        "veteran_name": veteran["name"],
        "eligible_benefit_ids": eligible_ids,
        "forms": output,
    }


# ---------------------------------------------------------------------------
# Route: Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    veteran_id: str
    message: str
    conversation_history: list = []  # List of {role, content} dicts


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Send a user message to the conversational assistant.
    Returns Claude's reply (or a placeholder if API key is not configured).
    """
    veteran = get_veteran_by_id(request.veteran_id)
    if not veteran:
        raise HTTPException(status_code=404, detail=f"Veteran '{request.veteran_id}' not found.")

    # Get missing fields to give Claude context
    from services.eligibility import check_eligibility
    from services.form_matcher import get_forms_for_benefits, prefill_fields, build_field_summary

    benefits_catalog = get_benefits_catalog()
    eligibility_results = check_eligibility(veteran, benefits_catalog)
    eligible_ids = [b["benefit_id"] for b in eligibility_results if b["eligible"]]

    forms_catalog = get_forms_catalog()
    matched_forms = get_forms_for_benefits(eligible_ids, forms_catalog)

    all_missing = []
    for form in matched_forms:
        prefilled = prefill_fields(form, veteran)
        summary = build_field_summary(prefilled)
        all_missing.extend(summary["missing_fields"])

    # Deduplicate missing fields by key
    seen_keys = set()
    deduped_missing = []
    for field in all_missing:
        if field["key"] not in seen_keys:
            deduped_missing.append(field)
            seen_keys.add(field["key"])

    from services.claude_chat import chat as claude_chat
    result = claude_chat(
        user_message=request.message,
        veteran=veteran,
        missing_fields=deduped_missing,
        conversation_history=request.conversation_history,
    )

    return {
        "veteran_id": request.veteran_id,
        "reply": result["response"],
        "model": result["model"],
        "error": result.get("error"),
    }


# ---------------------------------------------------------------------------
# TODO: Upload endpoint (placeholder — OCR not implemented in MVP)
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_document():
    """
    TODO (post-MVP): Accept a DD214, flat PDF, or scanned image.
    Extract text using pytesseract or AWS Textract.
    Merge extracted fields into the veteran's form prefill context.
    """
    return {
        "status": "not_implemented",
        "message": "Document upload and OCR are planned for a future sprint. "
                   "In the MVP, veteran data is loaded from a synthetic JSON profile.",
    }


# ---------------------------------------------------------------------------
# TODO: Output generation endpoint (placeholder)
# ---------------------------------------------------------------------------

@app.post("/api/generate-output")
async def generate_output():
    """
    TODO (post-MVP): Generate a printable PDF or email-ready package
    with all prefilled form fields, a cover note, and submission instructions.
    Could use reportlab, weasyprint, or fillpdf for PDF generation.
    """
    return {
        "status": "not_implemented",
        "message": "Printable/email output generation is planned for a future sprint. "
                   "In the MVP, form field data is displayed in the browser UI.",
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "app": "VetAssist", "version": "0.1.0-mvp"}
