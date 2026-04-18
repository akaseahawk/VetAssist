"""
services/eligibility.py

Rules-based benefit eligibility engine.

MVP approach: simple Python logic against the veteran profile dict and
the benefits_rules.json catalog. No ML, no external API calls.

TODO (post-MVP):
    - Pull live eligibility data from VA Benefits API
    - Support more nuanced rule combinations (income thresholds, priority groups)
    - Add a confidence score or tiered "likely / possible / unlikely" output
"""

from datetime import date, datetime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_date(val: str) -> date:
    """Parse ISO date string to a date object."""
    return datetime.strptime(val, "%Y-%m-%d").date()


def _service_days(veteran: dict) -> int:
    """Calculate total days of service from profile dates."""
    start = _parse_date(veteran["service_start"])
    end = _parse_date(veteran["service_end"])
    return (end - start).days


def _is_post_911(veteran: dict) -> bool:
    """Return True if service started after September 10, 2001."""
    return _parse_date(veteran["service_start"]) > date(2001, 9, 10)


# ---------------------------------------------------------------------------
# Main eligibility function
# ---------------------------------------------------------------------------

def check_eligibility(veteran: dict, benefits_catalog: list) -> list:
    """
    Given a veteran profile dict and the full benefits catalog list,
    return a list of eligible benefit dicts with an added 'eligible' key
    and a 'reason' explaining why.

    This is a simplified rules engine — it errs on the side of inclusion
    (flag likely benefits) rather than hard exclusion.

    Args:
        veteran: dict loaded from data/veterans.json
        benefits_catalog: list of benefit dicts from data/benefits_rules.json

    Returns:
        List of dicts: {benefit_id, title, description, eligible, reason, info_url}
    """

    results = []

    honorable = veteran.get("discharge_type") == "Honorable"
    combat = veteran.get("combat_deployment", False)
    sc_disability = veteran.get("service_connected_disability", False)
    rating = veteran.get("disability_rating_pct", 0)
    conditions = [c.lower() for c in veteran.get("disability_conditions", [])]
    enrolled_hc = veteran.get("enrolled_va_healthcare", False)
    receiving_comp = veteran.get("receiving_disability_comp", False)
    days = _service_days(veteran)
    post_911 = _is_post_911(veteran)

    for benefit in benefits_catalog:
        bid = benefit["id"]
        eligible = False
        reason = ""

        # --- Healthcare Enrollment ---
        if bid == "healthcare_enrollment":
            if enrolled_hc:
                reason = "Already enrolled in VA health care."
            elif honorable and (combat or rating >= 10 or days >= 24):
                eligible = True
                reason = "Honorable discharge with qualifying service or disability rating."
            else:
                reason = "May not meet minimum service or discharge requirements."

        # --- Disability Compensation ---
        elif bid == "disability_compensation":
            if receiving_comp:
                reason = "Already receiving disability compensation."
            elif honorable and sc_disability:
                eligible = True
                reason = "Service-connected disability on file; not yet receiving compensation."
            elif honorable and len(conditions) > 0:
                eligible = True
                reason = "Disability conditions listed; eligibility likely if service-connection can be established."
            else:
                reason = "No service-connected disability on file."

        # --- PTSD / Mental Health ---
        elif bid == "ptsd_benefits":
            if "ptsd" in conditions or combat:
                eligible = True
                reason = "Combat deployment or PTSD condition listed in profile."
            else:
                reason = "No PTSD condition or combat deployment found in profile."

        # --- GI Bill ---
        elif bid == "education_gi_bill":
            if honorable and post_911:
                eligible = True
                reason = "Post-9/11 service with honorable discharge qualifies for GI Bill consideration."
            elif honorable:
                reason = "Service predates Post-9/11 GI Bill eligibility window; may still qualify under Montgomery GI Bill."
            else:
                reason = "Discharge type or service dates do not meet GI Bill requirements."

        # --- Home Loan ---
        elif bid == "home_loan_guarantee":
            if honorable and days >= 90:
                eligible = True
                reason = "Honorable discharge with sufficient service length."
            elif honorable:
                reason = "Minimum service length requirement may not be met."
            else:
                reason = "Discharge type does not meet VA home loan requirements."

        else:
            reason = "Eligibility check not implemented for this benefit."

        results.append({
            "benefit_id": bid,
            "title": benefit["title"],
            "description": benefit["description"],
            "eligible": eligible,
            "reason": reason,
            "info_url": benefit.get("info_url", ""),
        })

    return results
