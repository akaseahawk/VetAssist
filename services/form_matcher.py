"""
services/form_matcher.py

Maps eligible benefits to VA forms and resolves which fields can be prefilled
from the veteran's profile vs. which still need input.

HOW IT WORKS:
    1. get_forms_for_benefits() finds which forms in the catalog correspond
       to a veteran's eligible benefit IDs.
    2. prefill_fields() walks each form's required fields, looks up values
       in the veteran profile, and marks each field as 'prefilled' or 'missing'.
    3. build_field_summary() counts known vs. missing fields and returns
       a list of missing ones for the chat layer to ask about.
    4. get_missing_fields_for_veteran() is a convenience wrapper used by the
       upload route and document suggestions endpoint.

WHY pure Python, no database:
    Form matching and prefill are deterministic lookups — no ML, no API calls.
    All form definitions and field mappings live in data/forms_catalog.json.
    This keeps the service fast, stateless, and easy to test.

WHY source_documents pass through here:
    Each field definition in the catalog may include a source_documents list
    (e.g. ["DD-214"]) identifying which physical document contains that field.
    form_matcher passes this through so the frontend can show a photo upload
    button on missing fields without needing to know the catalog structure itself.
"""


def get_forms_for_benefits(eligible_benefit_ids: list, forms_catalog: list) -> list:
    """
    Given a list of eligible benefit IDs, return all matching forms
    from the catalog.

    Args:
        eligible_benefit_ids: list of benefit ID strings (e.g. ["healthcare_enrollment"])
        forms_catalog: list of form dicts from data/forms_catalog.json

    Returns:
        List of matching form dicts.
    """
    matched = []
    seen_form_ids = set()

    for form in forms_catalog:
        form_benefit_ids = form.get("benefit_ids", [])
        if any(bid in eligible_benefit_ids for bid in form_benefit_ids):
            if form["id"] not in seen_form_ids:
                matched.append(form)
                seen_form_ids.add(form["id"])

    return matched


def prefill_fields(form: dict, veteran: dict) -> dict:
    """
    For a single form, compare required fields against the veteran profile
    and return a dict with known values pre-populated and missing fields
    flagged for follow-up.

    Args:
        form: a single form dict from forms_catalog.json
        veteran: the veteran profile dict

    Returns:
        {
          "form_id": str,
          "form_title": str,
          "digitized": bool,
          "info_url": str,
          "fields": [
            {
              "key": str,
              "label": str,
              "value": str or None,
              "status": "prefilled" | "missing" | "ask"
            }
          ]
        }
    """
    fields_out = []

    for field in form.get("required_fields", []):
        key = field["key"]
        label = field["label"]
        source = field.get("source", "ask")
        profile_field = field.get("profile_field")
        value = None
        status = "missing"

        if source == "profile" and profile_field:
            # Support nested keys like "address.city"
            parts = profile_field.split(".")
            val = veteran
            try:
                for part in parts:
                    val = val[part]
                if val is not None and val != "" and val != []:
                    # WHY special-case booleans: profile stores True/False but
                    # select fields use "Yes"/"No" as display options. We convert
                    # here so the <select> pre-selects the right option.
                    if isinstance(val, bool):
                        value = "Yes" if val else "No"
                    # WHY normalize gender codes: the profile may store abbreviated
                    # codes ("M", "F") but VA forms use full words. Map to the
                    # standard option labels so the select pre-selects correctly.
                    elif key == "gender" and isinstance(val, str):
                        gender_map = {"M": "Male", "F": "Female", "m": "Male", "f": "Female"}
                        value = gender_map.get(val, val)  # pass through if already full word
                    # Serialize lists as comma-separated strings
                    elif isinstance(val, list):
                        value = ", ".join(str(v) for v in val)
                    else:
                        value = str(val)
                    status = "prefilled"
                else:
                    status = "missing"
            except (KeyError, TypeError):
                status = "missing"
        elif source == "ask":
            status = "ask"

        fields_out.append({
            "key":              key,
            "label":            label,
            "value":            value,
            "status":           status,
            # WHY include field_type: the frontend uses this to render the
            # correct input control (date picker, select, textarea, text).
            # Keeping it in the catalog means UI decisions stay data-driven.
            "field_type":       field.get("field_type", "text"),
            # WHY include options: select fields need their allowed values.
            # Passing from the catalog keeps the frontend from hardcoding them.
            "options":          field.get("options", []),
            # WHY include required: lets the frontend validate before confirming.
            "required":         field.get("required", False),
            # WHY include source_documents: the frontend uses this to show
            # a '📷 From DD-214' upload button on missing fields.
            # Passing it through from the catalog keeps the frontend stateless.
            "source_documents": field.get("source_documents", []),
        })

    return {
        "form_id":    form["id"],
        "form_title": form["title"],
        "digitized":  form.get("digitized", True),
        "info_url":   form.get("info_url", ""),
        # WHY include benefit_ids: the frontend groups forms under their
        # matching benefit section, so it needs to know which benefit(s)
        # each form belongs to. Passing it through from the catalog keeps
        # the grouping logic data-driven and out of the template.
        "benefit_ids": form.get("benefit_ids", []),
        "fields":     fields_out,
    }


def build_field_summary(prefilled_form: dict) -> dict:
    """
    Given a prefilled form dict, return counts of prefilled vs. missing fields
    and a list of fields still needing input.

    Args:
        prefilled_form: output from prefill_fields()

    Returns:
        {
          "total": int,
          "prefilled_count": int,
          "missing_count": int,
          "missing_fields": list of {key, label}
        }
    """
    fields = prefilled_form.get("fields", [])
    prefilled = [f for f in fields if f["status"] == "prefilled"]
    missing = [f for f in fields if f["status"] in ("missing", "ask")]

    return {
        "total": len(fields),
        "prefilled_count": len(prefilled),
        "missing_count": len(missing),
        "missing_fields": [{"key": f["key"], "label": f["label"]} for f in missing],
    }


def get_missing_fields_for_veteran(
    veteran: dict,
    forms_data: dict,
    form_id: str | None = None,
) -> list[str]:
    """
    Return a list of field keys that are still missing for a veteran
    across all forms (or a specific form if form_id is given).

    WHY this helper exists:
      The upload route and suggestions endpoint both need to know which fields
      are missing so they can tell Claude exactly what to extract, and so they
      can suggest the right source document to the veteran.
      Centralizing this logic here keeps main.py clean.

    Args:
        veteran:   veteran profile dict
        forms_data: full forms catalog dict (with "forms" key)
        form_id:   optional — if given, only look at that specific form

    Returns:
        List of field key strings that have status "missing" or "ask",
        deduplicated across forms (same field may appear on multiple forms).
    """
    catalog = forms_data.get("forms", [])

    # Filter to specific form if requested
    if form_id:
        catalog = [f for f in catalog if f["id"] == form_id]

    missing_keys: set[str] = set()

    for form in catalog:
        prefilled = prefill_fields(form, veteran)
        for field in prefilled["fields"]:
            if field["status"] in ("missing", "ask"):
                missing_keys.add(field["key"])

    return sorted(missing_keys)
