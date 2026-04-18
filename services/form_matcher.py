"""
services/form_matcher.py

Maps eligible benefits to required VA forms and identifies which fields
are known from the veteran profile vs. still missing (need to be asked).

MVP approach: pure Python, reads from forms_catalog.json.
No external API calls.

TODO (post-MVP):
    - Integrate VA Forms API to pull live form metadata
    - Support actual PDF prefill using pypdf or fillpdf
    - Support flat/scanned form upload (OCR pipeline)
    - Add logic to deduplicate shared fields across multiple forms
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
                    # Serialize lists as comma-separated strings
                    if isinstance(val, list):
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
            "key": key,
            "label": label,
            "value": value,
            "status": status,
        })

    return {
        "form_id": form["id"],
        "form_title": form["title"],
        "digitized": form.get("digitized", True),
        "info_url": form.get("info_url", ""),
        "fields": fields_out,
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
