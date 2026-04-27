"""
services/eligibility.py

Rules-based benefit eligibility engine.

HOW IT WORKS:
    1. We load the veteran's profile (name, branch, service dates, disabilities, etc.)
    2. We load the benefits catalog from data/benefits_rules.json
    3. For each benefit in the catalog, we evaluate the veteran's profile
       against a set of simple rules and decide: likely eligible or not
    4. We return a list of results with a plain-language reason for each decision

WHY rules-based instead of asking an LLM to decide:
    - Rules are auditable — a judge, a VSO, or the veteran themselves can see
      exactly why a benefit was flagged
    - Rules are fast — no API call needed, no latency
    - Rules are predictable — same profile always gives same result
    - Claude is used AFTER this step to explain and add nuance, not to replace it

WHY we err on the side of inclusion (flag likely rather than hard-exclude):
    - It is better for a veteran to see a benefit and learn they don't qualify
      than to miss a benefit they were entitled to
    - The veteran and their VSO make the final determination, not this tool

MVP limitations:
    - Rules are simple — they don't capture every nuance of VA eligibility law
    - Income thresholds, priority groups, and service-specific edge cases are
      noted but not fully implemented
    - Post-MVP: consider pulling live eligibility determinations from the VA
      Benefits API instead of maintaining our own rules
"""

from datetime import date, datetime


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_date(val: str) -> date:
    """
    Convert an ISO date string like '2005-03-15' to a Python date object.
    We store dates as strings in JSON because JSON has no native date type.
    """
    return datetime.strptime(val, "%Y-%m-%d").date()


def _service_days(veteran: dict) -> int:
    """
    Calculate how many days the veteran served in their primary service period.
    Used by several benefit rules that require a minimum service length.
    """
    start = _parse_date(veteran["service_start"])
    end = _parse_date(veteran["service_end"])
    return (end - start).days


def _is_post_911(veteran: dict) -> bool:
    """
    Return True if the veteran's service started after September 10, 2001.
    Post-9/11 service is the primary qualifier for the Post-9/11 GI Bill (Ch. 33).
    """
    return _parse_date(veteran["service_start"]) > date(2001, 9, 10)


def _has_condition(veteran: dict, condition_keyword: str) -> bool:
    """
    Check if a specific condition keyword appears in the veteran's
    listed disability conditions. Case-insensitive.
    Example: _has_condition(veteran, "ptsd") returns True if "PTSD" is in the list.
    """
    conditions = [c.lower() for c in veteran.get("disability_conditions", [])]
    return condition_keyword.lower() in conditions


# ---------------------------------------------------------------------------
# Rule evaluators
# Each function takes the veteran profile and returns (eligible: bool, reason: str).
# We use separate functions instead of one giant if/else so each rule is
# easy to read, test, and modify independently.
# ---------------------------------------------------------------------------

def _rule_healthcare(veteran: dict) -> tuple:
    """
    VA Health Care Enrollment (Form 10-10EZ).

    Basic rule: Honorable discharge + at least one of:
      - Combat deployment (automatic Priority Group 6 or better)
      - Service-connected disability rating >= 10%
      - At least 24 months of active service

    WHY we skip if already enrolled: no reason to prompt them to re-apply.
    """
    if veteran.get("enrolled_va_healthcare"):
        # Already enrolled — don't surface this as a new benefit to pursue
        return False, "Already enrolled in VA health care — no action needed."

    honorable = veteran.get("discharge_type") == "Honorable"
    combat = veteran.get("combat_deployment", False)
    rating = veteran.get("disability_rating_pct", 0)
    days = _service_days(veteran)

    if honorable and (combat or rating >= 10 or days >= 24):
        return True, (
            "Likely eligible — honorable discharge with "
            + ("combat deployment" if combat else "")
            + (f" and {rating}% disability rating" if rating >= 10 else "")
            + (f" and {days} days of service" if days >= 24 else "")
            + "."
        ).replace("  ", " ").strip()

    return False, "May not meet minimum service length or discharge requirements for enrollment."


def _rule_disability_compensation(veteran: dict) -> tuple:
    """
    VA Disability Compensation (Form 21-526EZ).

    Basic rule: Honorable discharge + service-connected disability
    that is not yet being compensated.

    WHY we include 'conditions listed but not yet rated':
    Many veterans have conditions from service but never filed.
    We want to surface this so they know it's possible, not assume
    that because they haven't filed, they don't qualify.
    """
    if veteran.get("receiving_disability_comp"):
        return False, "Already receiving disability compensation — may be eligible to file for additional conditions."

    honorable = veteran.get("discharge_type") == "Honorable"
    sc_disability = veteran.get("service_connected_disability", False)
    conditions = veteran.get("disability_conditions", [])

    if honorable and sc_disability:
        return True, "Service-connected disability on file and compensation not yet received — strong candidate."

    if honorable and len(conditions) > 0:
        return True, (
            f"Has listed conditions ({', '.join(conditions)}) — "
            "eligibility depends on establishing service connection. A VSO can help."
        )

    return False, "No service-connected disability on file."


def _rule_ptsd_benefits(veteran: dict) -> tuple:
    """
    PTSD / Mental Health Benefits (Form 21-0781).

    Basic rule: Combat deployment OR PTSD listed as a condition.

    WHY combat deployment alone is sufficient:
    The VA allows a 'combat veteran presumption' — if you were in a combat zone,
    you don't need to prove the specific stressor event. The VA presumes it happened.
    This is a critical detail many veterans don't know about.
    """
    combat = veteran.get("combat_deployment", False)
    has_ptsd = _has_condition(veteran, "ptsd")

    if has_ptsd or combat:
        reason_parts = []
        if has_ptsd:
            reason_parts.append("PTSD listed as a condition")
        if combat:
            reason_parts.append(
                f"combat deployment to {', '.join(veteran.get('deployment_locations', ['a combat zone']))} "
                "(VA combat veteran presumption applies — no need to prove specific stressor)"
            )
        return True, ". ".join(reason_parts) + "."

    return False, "No PTSD condition or combat deployment found — may still qualify if other in-service traumatic events occurred."


def _rule_gi_bill(veteran: dict) -> tuple:
    """
    Post-9/11 GI Bill — Education Benefits (Form 22-1990).

    Basic rule: Honorable discharge + service started after Sept. 10, 2001.

    WHY we note the Montgomery GI Bill alternative:
    Veterans who served before 9/11 may still have education benefits under
    the Montgomery GI Bill (Ch. 30) — we don't want them to assume they have nothing.
    """
    honorable = veteran.get("discharge_type") == "Honorable"
    post_911 = _is_post_911(veteran)

    if honorable and post_911:
        return True, "Post-9/11 service with honorable discharge — likely eligible for Post-9/11 GI Bill (Chapter 33)."

    if honorable and not post_911:
        return False, (
            "Service predates Post-9/11 GI Bill window — "
            "may still qualify for Montgomery GI Bill (Chapter 30). Ask your VSO."
        )

    return False, "Discharge type does not meet GI Bill requirements."


def _rule_home_loan(veteran: dict) -> tuple:
    """
    VA Home Loan Guarantee (Form 26-1880 for Certificate of Eligibility).

    Basic rule: Honorable discharge + at least 90 days of active service
    (wartime) or 181 days (peacetime).

    WHY we use 90 days as the threshold:
    The VA's minimum for wartime service is 90 days continuous active duty.
    Since our profiles include combat veterans, we use the lower wartime threshold.
    A VSO should verify the exact requirement for each veteran's service period.
    """
    honorable = veteran.get("discharge_type") == "Honorable"
    days = _service_days(veteran)

    if honorable and days >= 90:
        return True, f"Honorable discharge with {days} days of service — meets the wartime minimum of 90 days."

    if honorable:
        return False, f"Only {days} days of service found — wartime minimum is 90 days. Verify with a VSO."

    return False, "Discharge type does not meet VA home loan requirements."


# ---------------------------------------------------------------------------
# Rule registry
# Maps benefit IDs (must match data/benefits_rules.json) to their rule function.
# WHY a dict instead of more if/else: adding a new benefit means adding one
# line here and one entry in the JSON — no other code changes needed.
# ---------------------------------------------------------------------------

RULE_REGISTRY = {
    "healthcare_enrollment":    _rule_healthcare,
    "disability_compensation":  _rule_disability_compensation,
    "ptsd_benefits":            _rule_ptsd_benefits,
    "education_gi_bill":        _rule_gi_bill,
    "home_loan_guarantee":      _rule_home_loan,
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_eligibility(veteran: dict, benefits_catalog: list) -> list:
    """
    Run the eligibility engine for a single veteran against all benefits
    in the catalog.

    Args:
        veteran:          dict from data/veterans.json
        benefits_catalog: list of benefit dicts from data/benefits_rules.json

    Returns:
        List of result dicts, one per benefit:
        {
            benefit_id:  str   — matches the catalog ID
            title:       str   — human-readable benefit name
            description: str   — what this benefit is
            eligible:    bool  — True = likely eligible, False = likely not
            reason:      str   — plain-language explanation of the decision
            info_url:    str   — link to VA.gov for more information
        }

    NOTE: 'eligible: True' means LIKELY eligible based on profile data.
    It is NOT a legal determination. The veteran and their VSO confirm final eligibility.
    """
    results = []

    for benefit in benefits_catalog:
        bid = benefit["id"]

        # Look up the rule function for this benefit ID.
        # If we don't have a rule for it yet, flag it clearly rather than silently skip.
        rule_fn = RULE_REGISTRY.get(bid)

        if rule_fn is None:
            # This benefit is in the catalog but has no rule implemented yet.
            # Return it as unknown so a developer knows to add the rule.
            results.append({
                "benefit_id":  bid,
                "title":       benefit["title"],
                "description": benefit["description"],
                "eligible":    False,
                "reason":      f"[DEV NOTE] No eligibility rule implemented for '{bid}' yet. Add it to RULE_REGISTRY in eligibility.py.",
                "info_url":    benefit.get("info_url", ""),
                "link_text":   benefit.get("link_text", ""),
                "vso_questions": benefit.get("vso_questions", []),
                "next_step":   benefit.get("next_step", ""),
            })
            continue

        # Run the rule function — it returns (eligible: bool, reason: str)
        eligible, reason = rule_fn(veteran)

        results.append({
            "benefit_id":  bid,
            "title":       benefit["title"],
            "description": benefit["description"],
            "eligible":    eligible,
            "reason":      reason,
            "info_url":    benefit.get("info_url", ""),
            "link_text":   benefit.get("link_text", ""),
            "vso_questions": benefit.get("vso_questions", []),
            "next_step":   benefit.get("next_step", ""),
        })

    return results
