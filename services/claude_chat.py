"""
services/claude_chat.py

Conversational assistant layer — the human-facing voice of VetAssist.

ROLE OF CLAUDE IN THIS SYSTEM:
    The eligibility engine (eligibility.py) runs rules to produce a list of
    likely-eligible benefits. Claude's job is to:
      1. Explain those results in plain, warm, branch-appropriate language
      2. Ask the veteran for missing form fields — one at a time, conversationally
      3. Verify prefilled information — never assume something is correct
      4. Route the veteran to their specific VSO and VA contacts

    Claude uses its INNATE KNOWLEDGE to explain benefits, clarify form language,
    and handle edge cases the rules engine can't anticipate. This is the key
    distinction: rules give us the list, Claude gives it meaning.

WHY NOT an agent that searches the web for eligibility rules?
    For the MVP: not needed. The rules are known, the benefits are defined.
    Web search adds latency, unpredictability, and complexity — all bad for a demo.

    POST-MVP / AGENTIC FUTURE STATE (good for the presentation):
    - An agent with VA.gov search access could handle edge cases the rules miss
      (e.g., rare exposure-based benefits, newly enacted legislation like the PACT Act)
    - A retrieval-augmented approach could pull live VA policy documents
    - This would be a separate "research agent" that runs only when the rules
      engine returns uncertain results — not on every interaction

TONE REQUIREMENTS (critical — do not remove):
    - Always acknowledge the veteran's service and their family's sacrifice
    - Use branch-appropriate language (see branch_contacts.json)
    - Never assume a field value — always verify with the veteran
    - Never give legal or medical advice — direct to VSO for complex situations
    - Ask only ONE question at a time — do not overwhelm the veteran
    - Use plain language — no VA jargon without explanation

PLACEHOLDER MODE:
    If ANTHROPIC_API_KEY is not set, the function returns a clear placeholder
    string so the app remains runnable locally without a live API key.
    This is intentional for development and demo setup.

TODO (post-MVP):
    - Stream responses for real-time UX (currently waits for full response)
    - Swap Anthropic API for AWS Bedrock for federal/FedRAMP deployment
    - Add crisis language detection (VA crisis line: 988, Press 1)
    - Add guardrails for off-topic or harmful requests
"""

import os
import json
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Load branch contact data once at module level
# WHY: We load this here so we don't re-read the file on every chat call.
# The data is small and static for the lifetime of the app.
# ---------------------------------------------------------------------------

def _load_branch_contacts() -> dict:
    """Load branch_contacts.json from the data directory."""
    data_dir = Path(__file__).parent.parent / "data"
    contacts_path = data_dir / "branch_contacts.json"
    if contacts_path.exists():
        with open(contacts_path, "r") as f:
            return json.load(f)
    return {}

# Module-level cache — loaded once when the service is first imported
_BRANCH_CONTACTS = _load_branch_contacts()


def _get_branch_context(branch: str) -> dict:
    """
    Return the contact and benefit note data for a specific branch.
    Falls back to the 'default' entry if the branch isn't recognized.
    """
    return _BRANCH_CONTACTS.get(branch, _BRANCH_CONTACTS.get("default", {}))


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _build_system_prompt(
    veteran: dict,
    eligible_benefits: list,
    missing_fields: list,
    verified_fields: dict,
    active_form: Optional[str] = None,
) -> str:
    """
    Build the system prompt sent to Claude on every chat turn.

    This prompt is the single most important thing in VetAssist — it defines
    how Claude behaves, what it knows, and what it must and must not do.

    Args:
        veteran:          The veteran's full profile dict
        eligible_benefits: List of benefit result dicts from the eligibility engine
        missing_fields:   Fields still needed for the selected form(s)
        verified_fields:  Fields the veteran has already confirmed as correct
        active_form:      The form ID the veteran is currently working on (if any)

    WHY we pass eligible_benefits into the prompt:
    Claude can use its innate knowledge to add nuance — e.g., explain that a
    combat veteran presumption means they don't need to prove a specific PTSD
    stressor, or that the PACT Act expanded eligibility for burn pit exposure.
    The rules engine flags it; Claude explains it.
    """
    name   = veteran.get("name", "the veteran")
    branch = veteran.get("branch", "the military")
    start  = veteran.get("service_start", "unknown")
    end    = veteran.get("service_end", "unknown")
    discharge = veteran.get("discharge_type", "unknown")
    combat = veteran.get("combat_deployment", False)
    deployments = veteran.get("deployment_locations", [])
    conditions = veteran.get("disability_conditions", [])
    rating = veteran.get("disability_rating_pct", 0)

    # Get branch-specific contacts and benefit notes
    branch_ctx = _get_branch_context(branch)
    primary_vso = branch_ctx.get("primary_vso", "a local VSO")
    primary_vso_url = branch_ctx.get("primary_vso_url", "")
    va_line = branch_ctx.get("va_benefits_line", "1-800-827-1000")
    greeting_note = branch_ctx.get("greeting_note", "Thank you for your service.")
    branch_benefits = branch_ctx.get("branch_specific_benefits", [])

    # Format eligible benefits for Claude's awareness
    eligible_summary = "\n".join([
        f"  - {b['title']}: {b['reason']}"
        for b in eligible_benefits if b.get("eligible")
    ]) or "  None identified yet."

    # Format missing fields so Claude knows what to ask next
    missing_summary = "\n".join([
        f"  - {f['label']} (field key: {f['key']})"
        for f in missing_fields
    ]) or "  None — all fields are prefilled or verified."

    # Format verified fields so Claude doesn't re-ask for them
    verified_summary = "\n".join([
        f"  - {k}: {v}" for k, v in verified_fields.items()
    ]) or "  None confirmed yet."

    # Format branch-specific benefit notes for Claude's awareness
    branch_benefits_summary = "\n".join([
        f"  - {b['name']}: {b['description']}"
        for b in branch_benefits
    ]) or "  None specific to this branch on file."

    prompt = f"""You are VetAssist — a warm, knowledgeable assistant helping {name} navigate their VA benefits and forms.

{greeting_note}

━━━ VETERAN PROFILE SUMMARY ━━━
Name:        {name}
Branch:      {branch}
Service:     {start} to {end}
Discharge:   {discharge}
Combat:      {"Yes — deployed to " + ", ".join(deployments) if combat else "No"}
Conditions:  {", ".join(conditions) if conditions else "None listed"}
Rating:      {rating}% (if any)

━━━ LIKELY ELIGIBLE BENEFITS (from rules engine — use your knowledge to explain and expand) ━━━
{eligible_summary}

━━━ BRANCH-SPECIFIC BENEFITS TO BE AWARE OF ━━━
{branch_benefits_summary}
(Use your knowledge to assess whether any of these apply — do not assume, but ask if relevant.)

━━━ FORM BEING WORKED ON ━━━
{f"Active form: {active_form}" if active_form else "No specific form selected yet — in benefits review phase."}

━━━ FIELDS STILL NEEDED (ask these conversationally — ONE AT A TIME) ━━━
{missing_summary}

━━━ FIELDS ALREADY VERIFIED BY VETERAN (do not re-ask) ━━━
{verified_summary}

━━━ CONTACTS FOR THIS VETERAN ━━━
Primary VSO: {primary_vso} — {primary_vso_url}
VA Benefits Line: {va_line}
VA Crisis Line: 988, Press 1 (mention this if the veteran expresses distress)

━━━ RULES YOU MUST FOLLOW ━━━
1. NEVER assume a field value is correct — always read it back and ask the veteran to confirm.
2. Ask for missing information ONE field at a time. Do not list multiple questions at once.
3. Use plain language. If a form uses jargon, explain it before asking.
4. Never give legal or medical advice. For complex situations, refer to {primary_vso}.
5. Do not ask for the veteran's full SSN — last 4 digits only if needed.
6. If the veteran seems confused, frustrated, or distressed, acknowledge it and slow down.
7. If the veteran asks about a benefit or form you weren't told about, use your knowledge to answer honestly — do not make up information.
8. Always end your response with either: a specific question, a next step, or a clear instruction. Never leave the veteran hanging.
9. Keep responses concise — 2 to 5 sentences unless more detail is clearly needed.
10. You represent Wilcore, a Service-Disabled Veteran-Owned Small Business. Be professional, mission-driven, and human.
"""
    return prompt


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------

def chat(
    user_message: str,
    veteran: dict,
    eligible_benefits: list,
    missing_fields: Optional[list] = None,
    verified_fields: Optional[dict] = None,
    conversation_history: Optional[list] = None,
    active_form: Optional[str] = None,
) -> dict:
    """
    Send the veteran's message to Claude and return a response.

    Args:
        user_message:         What the veteran typed
        veteran:              Full veteran profile dict
        eligible_benefits:    Output from check_eligibility() — Claude uses this
                              plus its own knowledge to explain benefits
        missing_fields:       List of {key, label} dicts for fields still needed
        verified_fields:      Dict of fields the veteran has already confirmed
        conversation_history: Prior turns as [{role, content}] — keeps context
        active_form:          Form ID currently being worked on (e.g. "21-526EZ")

    Returns:
        {
            "response": str,    — Claude's reply to show the veteran
            "model":    str,    — model used, or "placeholder" if no API key
            "error":    str|None — error message if something went wrong
        }
    """

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

    # ------------------------------------------------------------------
    # PLACEHOLDER MODE
    # No API key set — return a descriptive placeholder so the app runs
    # locally without a live key. This is intentional, not broken.
    # ------------------------------------------------------------------
    if not api_key:
        branch = veteran.get("branch", "your branch")
        branch_ctx = _get_branch_context(branch)
        greeting = branch_ctx.get("greeting_note", "Thank you for your service.")
        missing_count = len(missing_fields or [])
        next_field = missing_fields[0]["label"] if missing_fields else None

        placeholder = (
            f"[PLACEHOLDER — add ANTHROPIC_API_KEY to .env for live responses]\n\n"
            f"{greeting}\n\n"
            f"You asked: '{user_message}'\n\n"
            f"In the live version, I would: explain your eligible benefits using VA knowledge, "
            f"{'ask you about your ' + next_field + ' to complete your form' if next_field else 'confirm all your fields are complete'}, "
            f"and connect you with {branch_ctx.get('primary_vso', 'a VSO')} for next steps."
        )
        return {"response": placeholder, "model": "placeholder", "error": None}

    # ------------------------------------------------------------------
    # LIVE MODE — call Claude via Anthropic SDK
    # ------------------------------------------------------------------
    try:
        # Lazy import so the app starts without 'anthropic' installed
        # (placeholder mode above will catch that case first anyway)
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Build the system prompt with full veteran context
        system_prompt = _build_system_prompt(
            veteran=veteran,
            eligible_benefits=eligible_benefits,
            missing_fields=missing_fields or [],
            verified_fields=verified_fields or {},
            active_form=active_form,
        )

        # Build the message list — include prior turns for multi-turn context
        # WHY we limit to last 20 turns: Claude has a context window limit,
        # and older turns are less relevant than recent ones. 20 is generous
        # for a form-filling conversation.
        messages = list(conversation_history or [])[-20:]
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=model,
            max_tokens=600,  # Enough for a thorough but concise response
            system=system_prompt,
            messages=messages,
        )

        reply = (
            response.content[0].text
            if response.content
            else "I'm sorry — I wasn't able to generate a response. Please try again."
        )

        return {"response": reply, "model": model, "error": None}

    except ImportError:
        return {
            "response": "The 'anthropic' package is not installed. Run: pip install anthropic",
            "model": "error",
            "error": "ImportError: anthropic package missing",
        }
    except Exception as exc:
        # Surface the error clearly so developers can debug
        # In production, you'd log this and return a generic message to the user
        return {
            "response": f"Something went wrong reaching the assistant. Please try again. (Error: {str(exc)[:150]})",
            "model": "error",
            "error": str(exc),
        }
