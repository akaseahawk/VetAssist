"""
services/pdf_generator.py

Generates a two-part downloadable PDF package for a veteran:

  Page 1+  — COVER PAGE
             Personalized to branch of service. Includes:
               • Appreciation note for their service
               • Clear disclaimer that VetAssist is not a decision-maker
               • What to do next (step-by-step)
               • Primary and secondary VSO contact for their branch
               • VA benefits phone line
               • How to find their nearest VA Regional Office
               • Branch-specific benefit notes (e.g. CRSC for Army)

  Page 2+  — PREFILL SUMMARY SHEET (one section per form)
             For each VA form the veteran worked through:
               • Form number, full title, and VA.gov link
               • Table of all confirmed field values (green rows)
               • Table of all still-missing fields (amber rows)
               • Field-level source document hints where available

WHY a summary sheet instead of a filled PDF:
    VA forms use Adobe XFA interactive format. Standard Python PDF libraries
    cannot write into XFA fields — the result would be a flat overlay that
    looks wrong and may not be accepted. A clean summary sheet that the
    veteran or their VSO uses while filling the real form on VA.gov is more
    honest and more reliable.

WHY reportlab specifically:
    Reportlab is the most mature Python PDF generation library, ships with
    no native dependencies beyond Pillow, and is already installed in this
    environment. It gives us full layout control without a headless browser.

USAGE:
    from services.pdf_generator import build_veteran_package
    pdf_bytes = build_veteran_package(veteran, forms, branch_contacts)
    # Returns raw PDF bytes — caller writes to a temp file or streams directly.
"""

import io
import json
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Brand colors — kept consistent with the frontend's VA blue + green palette
# ---------------------------------------------------------------------------
VA_BLUE   = colors.HexColor("#1a3a6b")
VA_GREEN  = colors.HexColor("#2e7d32")
VA_AMBER  = colors.HexColor("#b45309")
VA_LIGHT  = colors.HexColor("#f1f8f1")
AMBER_BG  = colors.HexColor("#fffbeb")
HEADER_BG = colors.HexColor("#e8edf7")
RULE_COLOR = colors.HexColor("#c5cfe0")

# ---------------------------------------------------------------------------
# Paragraph styles
# WHY define them here: keeps all type decisions in one place and makes it
# easy for a designer to adjust without hunting through the render functions.
# ---------------------------------------------------------------------------
BASE       = getSampleStyleSheet()

H1 = ParagraphStyle(
    "H1", fontName="Helvetica-Bold", fontSize=18,
    textColor=VA_BLUE, spaceAfter=4, alignment=TA_LEFT,
)
H2 = ParagraphStyle(
    "H2", fontName="Helvetica-Bold", fontSize=13,
    textColor=VA_BLUE, spaceAfter=4, spaceBefore=14, alignment=TA_LEFT,
)
H3 = ParagraphStyle(
    "H3", fontName="Helvetica-Bold", fontSize=10,
    textColor=VA_GREEN, spaceAfter=3, spaceBefore=10,
)
BODY = ParagraphStyle(
    "BODY", fontName="Helvetica", fontSize=9,
    textColor=colors.HexColor("#222222"), leading=14, spaceAfter=4,
)
BODY_BOLD = ParagraphStyle(
    "BODY_BOLD", fontName="Helvetica-Bold", fontSize=9,
    textColor=colors.HexColor("#222222"), leading=14,
)
SMALL = ParagraphStyle(
    "SMALL", fontName="Helvetica", fontSize=8,
    textColor=colors.HexColor("#555555"), leading=12, spaceAfter=3,
)
DISCLAIMER = ParagraphStyle(
    "DISCLAIMER", fontName="Helvetica-Oblique", fontSize=8,
    textColor=colors.HexColor("#5d4037"), leading=12,
    borderColor=colors.HexColor("#f9a825"), borderWidth=1,
    borderPadding=6, backColor=colors.HexColor("#fff8e1"),
)
TAGLINE = ParagraphStyle(
    "TAGLINE", fontName="Helvetica-Oblique", fontSize=9,
    textColor=colors.HexColor("#555"), alignment=TA_CENTER, spaceAfter=2,
)
CENTER_BOLD = ParagraphStyle(
    "CENTER_BOLD", fontName="Helvetica-Bold", fontSize=10,
    textColor=VA_BLUE, alignment=TA_CENTER, spaceAfter=2,
)


def _rule():
    """Thin horizontal rule — used as a section divider throughout the doc."""
    return HRFlowable(width="100%", thickness=0.5, color=RULE_COLOR, spaceAfter=6)


def _spacer(h=0.15):
    return Spacer(1, h * inch)


# ---------------------------------------------------------------------------
# Cover page
# ---------------------------------------------------------------------------

def _build_cover(veteran: dict, branch_contacts: dict) -> list:
    """
    Build the cover page flowables.

    WHY a cover page:
        Veterans handing this to a VSO or bringing it to a VA office need
        context at the top — who prepared this, what it is, what it is NOT,
        and exactly what to do next. The field data alone is not enough.

    Args:
        veteran:         the veteran profile dict
        branch_contacts: the full branch_contacts.json loaded as a dict

    Returns:
        list of reportlab Flowable objects
    """
    name   = veteran.get("name", "Veteran")
    branch = veteran.get("branch", "")

    # Pull branch-specific contact block, fall back to default
    contacts = branch_contacts.get(branch, branch_contacts.get("default", {}))

    primary_vso      = contacts.get("primary_vso", "Veterans of Foreign Wars (VFW)")
    primary_vso_url  = contacts.get("primary_vso_url", "https://www.vfw.org")
    secondary_vso    = contacts.get("secondary_vso", "Disabled American Veterans (DAV)")
    secondary_vso_url = contacts.get("secondary_vso_url", "https://www.dav.org")
    va_line          = contacts.get("va_benefits_line", "1-800-827-1000")
    regional_note    = contacts.get("va_regional_note", "Find your nearest VA Regional Office at va.gov/find-locations")
    greeting         = contacts.get("greeting_note", "Thank you for your service and sacrifice.")
    branch_benefits  = contacts.get("branch_specific_benefits", [])

    today = date.today().strftime("%B %d, %Y")

    story = []

    # Header block
    story.append(Paragraph("VetAssist", H1))
    story.append(Paragraph("VA Benefits &amp; Forms Preparation Package", TAGLINE))
    story.append(_rule())
    story.append(_spacer(0.08))
    story.append(Paragraph(f"Prepared for: <b>{name}</b>", BODY_BOLD))
    if branch:
        story.append(Paragraph(f"Branch of Service: <b>{branch}</b>", BODY))
    story.append(Paragraph(f"Date: {today}", SMALL))
    story.append(_spacer(0.18))

    # Appreciation
    story.append(Paragraph(greeting, BODY))
    story.append(_spacer(0.1))

    # Disclaimer — prominent
    story.append(Paragraph(
        "<b>Important — please read before using this document:</b><br/><br/>"
        "VetAssist is a preparation tool. It is <b>not</b> a determination of eligibility, "
        "a legal opinion, or a filing on your behalf. The VA and your VSO make eligibility "
        "decisions — not this tool. Everything in this package is based on the information "
        "you entered and should be reviewed and confirmed with a VSO or VA representative "
        "before you submit anything.<br/><br/>"
        "Nothing from your session was stored. This PDF is the only record.",
        DISCLAIMER,
    ))
    story.append(_spacer(0.2))

    # What to do next
    story.append(Paragraph("What to do next", H2))
    story.append(_rule())
    next_steps = [
        "1.  Review the field summary on the following pages. Correct anything that looks wrong.",
        "2.  Bring this document to your VSO appointment or VA office visit.",
        "3.  Your VSO can help you fill out the actual forms on VA.gov using this as a reference.",
        "4.  For forms that are fully digital (noted on each section), you can also file directly "
            "at VA.gov — log in with your ID.me or Login.gov account.",
        "5.  If any fields are still blank, the source document listed next to each field is "
            "where you'll find that information (e.g. DD-214, medical records).",
    ]
    for step in next_steps:
        story.append(Paragraph(step, BODY))
    story.append(_spacer(0.2))

    # VSO contacts
    story.append(Paragraph("Your VSO contacts", H2))
    story.append(_rule())
    story.append(Paragraph(
        f"Based on your branch of service, these organizations specialize in supporting {branch or 'your'} veterans:",
        BODY,
    ))
    story.append(_spacer(0.08))

    vso_data = [
        ["", "Organization", "Website"],
        ["Primary VSO",   primary_vso,   primary_vso_url],
        ["Secondary VSO", secondary_vso, secondary_vso_url],
        ["VA Benefits Line", va_line,    "va.gov or call the number"],
    ]
    vso_table = Table(vso_data, colWidths=[1.3*inch, 2.5*inch, 2.9*inch])
    vso_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0), VA_BLUE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
        ("GRID",         (0, 0), (-1, -1), 0.4, RULE_COLOR),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(vso_table)
    story.append(_spacer(0.1))
    story.append(Paragraph(regional_note, SMALL))
    story.append(_spacer(0.2))

    # Branch-specific benefits (if any)
    if branch_benefits:
        story.append(Paragraph(f"Other benefits worth asking your VSO about ({branch})", H2))
        story.append(_rule())
        story.append(Paragraph(
            "These are specific to your branch of service. Mention them to your VSO "
            "to see if any apply to your situation.",
            SMALL,
        ))
        story.append(_spacer(0.08))
        for b in branch_benefits:
            story.append(Paragraph(b["name"], H3))
            story.append(Paragraph(b["description"], BODY))
            story.append(Paragraph(f"More info: {b['info_url']}", SMALL))

    return story


# ---------------------------------------------------------------------------
# Prefill summary sheet — one section per form
# ---------------------------------------------------------------------------

def _build_form_section(form: dict) -> list:
    """
    Build the prefill summary flowables for one VA form.

    WHY one section per form (not one page):
        Some veterans have 2-3 forms. Forcing a page break per form wastes
        paper and makes the document feel bureaucratic. Sections flow naturally
        and a VSO can flip through quickly.

    Args:
        form: a prefilled form dict from prefill_fields() — includes form_id,
              form_title, digitized, info_url, fields, and summary.

    Returns:
        list of reportlab Flowable objects
    """
    story = []

    form_id    = form.get("form_id", "")
    form_title = form.get("form_title", "")
    digitized  = form.get("digitized", True)
    info_url   = form.get("info_url", "")
    fields     = form.get("fields", [])
    summary    = form.get("summary", {})

    prefilled_count = summary.get("prefilled_count", 0)
    missing_count   = summary.get("missing_count", 0)
    total           = summary.get("total", len(fields))

    # Form header
    story.append(Paragraph(f"VA Form {form_id}", H2))
    story.append(Paragraph(form_title, BODY_BOLD))
    story.append(_spacer(0.05))

    # Meta row: digital status + VA.gov link
    digital_label = "Available online at VA.gov" if digitized else "PAPER FORM — must be submitted in person or by mail"
    digital_color = "#2e7d32" if digitized else "#c8102e"
    story.append(Paragraph(
        f'<font color="{digital_color}"><b>{"✓ Digital" if digitized else "⚠ Paper only"}</b></font>'
        f' &nbsp;|&nbsp; {info_url}',
        SMALL,
    ))
    story.append(_spacer(0.05))

    # Progress summary bar (text)
    story.append(Paragraph(
        f"Fields completed: <b>{prefilled_count} of {total}</b> &nbsp;|&nbsp; "
        f"Still needed: <b>{missing_count}</b>",
        BODY,
    ))
    story.append(_rule())

    # Split fields into prefilled vs. missing
    prefilled_fields = [f for f in fields if f.get("status") == "prefilled"]
    missing_fields   = [f for f in fields if f.get("status") in ("missing", "ask")]

    # --- Prefilled fields table ---
    if prefilled_fields:
        story.append(Paragraph("✓  Information we have", H3))
        table_data = [["Field", "Value", "Notes"]]
        for f in prefilled_fields:
            source_docs = f.get("source_documents", [])
            note = ", ".join(source_docs) if source_docs else ""
            table_data.append([
                Paragraph(f["label"], SMALL),
                Paragraph(str(f.get("value") or ""), SMALL),
                Paragraph(note, SMALL),
            ])
        t = Table(table_data, colWidths=[2.2*inch, 2.8*inch, 1.7*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), VA_LIGHT),
            ("TEXTCOLOR",     (0, 0), (-1, 0), VA_GREEN),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fdf7")]),
            ("GRID",          (0, 0), (-1, -1), 0.3, RULE_COLOR),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(_spacer(0.12))

    # --- Missing fields table ---
    if missing_fields:
        story.append(Paragraph("○  Still needed — bring or look up these values", H3))
        # Override H3 color for the needed section
        story[-1] = Paragraph(
            "○  Still needed — bring or look up these values",
            ParagraphStyle("H3A", parent=H3, textColor=VA_AMBER),
        )
        table_data = [["Field", "Where to find it"]]
        for f in missing_fields:
            source_docs = f.get("source_documents", [])
            hint = (
                "From: " + ", ".join(source_docs)
                if source_docs
                else "Ask your VSO or check your personal records"
            )
            table_data.append([
                Paragraph(f["label"], SMALL),
                Paragraph(hint, SMALL),
            ])
        t = Table(table_data, colWidths=[2.8*inch, 3.9*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), AMBER_BG),
            ("TEXTCOLOR",     (0, 0), (-1, 0), VA_AMBER),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#fffdf5")]),
            ("GRID",          (0, 0), (-1, -1), 0.3, RULE_COLOR),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    story.append(_spacer(0.25))
    return story


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_veteran_package(
    veteran: dict,
    forms: list,
    branch_contacts: dict,
) -> bytes:
    """
    Generate the full two-part PDF package and return raw bytes.

    WHY return bytes instead of writing a file:
        The caller (the FastAPI route) streams the bytes directly as an HTTP
        response. No temp files means no cleanup needed and no disk I/O race
        conditions if multiple users generate PDFs at the same time.

    Args:
        veteran:         veteran profile dict (name, branch, etc.)
        forms:           list of prefilled form dicts from prefill_fields()
                         — each must include a 'summary' key from build_field_summary()
        branch_contacts: the full branch_contacts.json loaded as a dict

    Returns:
        Raw PDF bytes ready to stream or write.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
        title=f"VetAssist Package — {veteran.get('name', 'Veteran')}",
        author="VetAssist — Wilcore Innovation Challenge",
        subject="VA Benefits Preparation Package",
    )

    story = []

    # Part 1: cover page
    story.extend(_build_cover(veteran, branch_contacts))

    # Part 2: one section per form the veteran worked through
    if forms:
        story.append(_rule())
        story.append(Paragraph("Field Summary by Form", H2))
        story.append(Paragraph(
            "Use this section as a reference when filling out your forms at VA.gov "
            "or with your VSO. Green rows are values we already have. "
            "Amber rows are fields you'll still need to provide.",
            BODY,
        ))
        story.append(_spacer(0.15))

        for form in forms:
            story.extend(_build_form_section(form))

    # Footer note
    story.append(_rule())
    story.append(Paragraph(
        "Generated by VetAssist — Wilcore Innovation Challenge. "
        "This document is a preparation aid only. "
        "VetAssist does not determine eligibility, make filings, or store personal information.",
        SMALL,
    ))

    doc.build(story)
    return buffer.getvalue()
