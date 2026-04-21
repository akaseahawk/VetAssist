"""
services/benefit_discovery.py

Benefit discovery layer — surfaces VA benefits a veteran may want to explore.

HOW THIS WORKS:
    Two modes depending on whether an Anthropic API key is configured:

    LIVE MODE (API key set):
        Claude reads the veteran's profile and uses its own knowledge of VA
        benefits to suggest what may be worth exploring. Claude reasons from
        the profile the same way a knowledgeable VSO would — looking at branch,
        service dates, discharge type, conditions, deployments, and known
        circumstances to suggest relevant benefit categories.

        WHY Claude instead of hardcoded rules:
        VA benefit eligibility is nuanced. Rules change. Edge cases exist.
        A veteran's situation rarely fits neatly into simple if/else logic.
        Claude can reason across combinations of factors the way a human advisor
        would — and frame results as possibilities, not determinations.

    FALLBACK MODE (no API key):
        The hardcoded rules engine in eligibility.py runs instead.
        Same "worth exploring" framing — just less nuanced.
        This keeps the app fully runnable without an API key for setup,
        demos without connectivity, and collaborators during development.

CRITICAL FRAMING RULES:
    - These are NOT eligibility determinations.
    - The VA and the veteran's VSO make the final determination.
    - We surface possibilities so the veteran knows what to ask about.
    - Every result includes a VA.gov link for the veteran to research themselves.
    - The veteran decides whether to proceed — we help them prepare if they do.

FUTURE / AGENTIC PATH (post-MVP, do not build now):
    An agent with VA.gov search access could query live policy documents,
    check for newly enacted legislation (like the PACT Act), and handle
    edge cases that require reading current regulations. This would be a
    separate research agent that runs only when Claude flags uncertainty.
"""

import os
import json
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Load the benefits catalog — used by both modes
# ---------------------------------------------------------------------------

def _load_benefits_catalog() -> list:
    """Load benefits definitions from data/benefits_rules.json."""
    data_dir = Path(__file__).parent.parent / "data"
    path = data_dir / "benefits_rules.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f).get("benefits", [])


# ---------------------------------------------------------------------------
# LIVE MODE: Claude-driven benefit discovery
# ---------------------------------------------------------------------------

def _discover_with_claude(veteran: dict, benefits_catalog: list, api_key: str, model: str) -> list:
    """
    Ask Claude to review the veteran's profile and suggest which benefits
    from the catalog may be worth exploring.

    Claude receives:
      - The veteran's full profile
      - The catalog of available benefits (titles, descriptions, VA.gov links)
      - Explicit instructions to only surface genuinely relevant possibilities
      - Explicit instructions on framing (worth exploring, not a determination)

    Returns a list of benefit dicts with Claude's reasoning added.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # Build a clean summary of the veteran's profile for Claude
    profile_summary = f"""
Veteran Profile:
- Name: {veteran.get('name')}
- Branch: {veteran.get('branch')}
- Service: {veteran.get('service_start')} to {veteran.get('service_end')}
- Discharge: {veteran.get('discharge_type')}
- Combat deployment: {veteran.get('combat_deployment')} — locations: {', '.join(veteran.get('deployment_locations', []) or [])}
- Service-connected disability: {veteran.get('service_connected_disability')} — rating: {veteran.get('disability_rating_pct', 0)}%
- Conditions: {', '.join(veteran.get('disability_conditions', []) or [])}
- Enrolled in VA health care: {veteran.get('enrolled_va_healthcare')}
- Currently receiving disability compensation: {veteran.get('receiving_disability_comp')}
- Annual income: ${veteran.get('income_annual', 0):,}
- Dependents: {veteran.get('dependents', 0)}
"""

    # Build the catalog summary for Claude to reference
    catalog_summary = "\n".join([
        f"- ID: {b['id']} | Title: {b['title']} | Description: {b['description']} | Info: {b.get('info_url', '')}"
        for b in benefits_catalog
    ])

    prompt = f"""You are a knowledgeable VA benefits advisor helping a veteran understand
what benefits may be worth exploring based on their service history and profile.

{profile_summary}

Available benefit categories to consider:
{catalog_summary}

Your task:
1. Review this veteran's profile carefully.
2. For each benefit category listed, decide if it is genuinely worth this veteran exploring
   based on their specific situation. Do NOT surface benefits that clearly do not apply.
3. For each benefit you surface, provide:
   - A plain-language explanation of why it may apply to THIS veteran specifically
   - A clear statement that this is not a determination — they should talk to their VSO or the VA
   - The benefit ID exactly as listed above

Return your response as a JSON array. Each item must have these exact fields:
{{
  "benefit_id": "the exact ID from the catalog",
  "worth_exploring": true or false,
  "plain_language_reason": "2-3 sentences explaining why this specific veteran may want to look into this benefit, written directly to them",
  "important_note": "This is not an eligibility determination. Talk to your VSO or the VA to confirm whether this applies to your situation."
}}

Only include benefits where worth_exploring is true.
Be conservative — only surface what genuinely seems relevant.
Do not guess or assume facts not in the profile.

Important constraints:
- Your VA knowledge has a training cutoff. If a benefit rule or eligibility threshold
  may have changed recently (e.g. PACT Act expansions post-2022, new rating schedules),
  note this uncertainty in the plain_language_reason so the veteran knows to verify.
- Do not present your assessment as current or authoritative — frame it as a starting
  point for a VSO or VA conversation, not a conclusion.
- If you are not confident a benefit applies, set worth_exploring to false.
  A shorter accurate list is better than a longer speculative one.

Return only the JSON array, no other text."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()

        # Strip markdown code fences if Claude wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        claude_results = json.loads(raw)

        # Merge Claude's reasoning back with the full catalog data
        # so callers get titles, descriptions, and URLs alongside Claude's notes
        catalog_by_id = {b["id"]: b for b in benefits_catalog}
        output = []
        for item in claude_results:
            if not item.get("worth_exploring"):
                continue
            bid = item.get("benefit_id")
            catalog_entry = catalog_by_id.get(bid, {})
            output.append({
                "benefit_id":          bid,
                "title":               catalog_entry.get("title", bid),
                "description":         catalog_entry.get("description", ""),
                "worth_exploring":     True,
                "reason":              item.get("plain_language_reason", ""),
                "important_note":      item.get("important_note", "Talk to your VSO or the VA to confirm."),
                "info_url":            catalog_entry.get("info_url", ""),
                "source":              "claude",
            })

        return output

    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # If Claude returns malformed JSON, fall back to rules engine
        # and log the error clearly so a developer can debug
        print(f"[benefit_discovery] Claude response parse error: {e} — falling back to rules engine")
        return None  # Signals to caller to use fallback

    except Exception as e:
        print(f"[benefit_discovery] Claude API error: {e} — falling back to rules engine")
        return None


# ---------------------------------------------------------------------------
# FALLBACK MODE: hardcoded rules engine
# ---------------------------------------------------------------------------

def _discover_with_rules(veteran: dict, benefits_catalog: list) -> list:
    """
    Run the hardcoded rules engine from eligibility.py as a fallback.
    Used when no API key is configured.

    Applies the same 'worth exploring' framing as the Claude mode —
    the rules are a starting point, not a determination.
    """
    from services.eligibility import check_eligibility

    results = check_eligibility(veteran, benefits_catalog)

    # Reframe the output language — rules say "eligible", we say "worth exploring"
    output = []
    for r in results:
        if not r.get("eligible"):
            continue
        output.append({
            "benefit_id":      r["benefit_id"],
            "title":           r["title"],
            "description":     r["description"],
            "worth_exploring": True,
            "reason":          r["reason"],
            "important_note":  (
                "This is based on general profile information, not a formal eligibility determination. "
                "Talk to your VSO or the VA to confirm whether this applies to your situation."
            ),
            "info_url":        r.get("info_url", ""),
            "source":          "rules_fallback",
        })

    return output


# ---------------------------------------------------------------------------
# Main entry point — called by main.py
# ---------------------------------------------------------------------------

def discover_benefits(veteran: dict) -> dict:
    """
    Discover benefits worth exploring for a veteran.

    Tries Claude first if an API key is available.
    Falls back to the rules engine if not, or if Claude fails.

    Args:
        veteran: Full veteran profile dict from data/veterans.json

    Returns:
        {
            "benefits":    list of benefit dicts (worth_exploring=True only)
            "mode":        "claude" | "rules_fallback"
            "disclaimer":  str — shown to veteran in the UI
        }
    """
    # WHY strip + strip quotes: some hosting platforms (Railway, Render) wrap
    # env var values in double quotes when set via their UI. Stripping both
    # whitespace and surrounding quotes ensures the key is always clean.
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    model   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6").strip().strip('"').strip("'")

    catalog = _load_benefits_catalog()

    # Try Claude if we have a key
    if api_key:
        claude_results = _discover_with_claude(veteran, catalog, api_key, model)
        if claude_results is not None:
            return {
                "benefits": claude_results,
                "mode": "claude",
                "disclaimer": (
                    "These benefits were identified based on your profile by an AI assistant "
                    "with knowledge of VA programs. They are possibilities worth exploring — "
                    "not a determination of eligibility. Please talk to your VSO or the VA "
                    "to confirm what applies to your specific situation before taking action."
                ),
            }
        # Claude failed — fall through to rules

    # Fallback: hardcoded rules engine
    rules_results = _discover_with_rules(veteran, catalog)
    return {
        "benefits": rules_results,
        "mode": "rules_fallback",
        "disclaimer": (
            "These benefits were identified using general eligibility guidelines "
            "based on your profile. They are possibilities worth exploring — "
            "not a determination of eligibility. For accurate guidance, please "
            "talk to your VSO or contact the VA directly before taking action. "
            "(AI-assisted discovery is not available in this environment — these results are based on general eligibility guidelines.)"
        ),
    }
