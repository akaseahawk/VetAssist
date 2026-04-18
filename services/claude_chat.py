"""
services/claude_chat.py

Conversational assistant layer using the Anthropic Claude API.

MVP approach:
    - Sends a system prompt describing the veteran's context and the missing
      form fields, then accepts a user message and returns a response.
    - Uses the Anthropic Python SDK (anthropic>=0.20.0).
    - Falls back to a placeholder string if the API key is not set,
      so the app remains runnable without a live key during development.

TODO (post-MVP):
    - Stream responses back to the frontend for real-time UX
    - Persist conversation history in session state (or a lightweight in-memory store)
    - Add guardrails: redirect off-topic questions, flag crisis language
    - Implement multi-turn context to avoid repeating already-answered fields
    - Swap in an AWS Bedrock Claude endpoint for federal / FedRAMP deployment
"""

import os
import json
from typing import Optional


def _build_system_prompt(veteran: dict, missing_fields: list) -> str:
    """
    Build a system prompt that gives Claude context about the veteran
    and what information is still needed.
    """
    missing_labels = [f["label"] for f in missing_fields] if missing_fields else []

    system = f"""You are VetAssist, a plain-language AI assistant helping veterans 
understand their VA benefits and complete required forms.

You are currently helping: {veteran.get('name', 'this veteran')}
Branch: {veteran.get('branch', 'Unknown')}
Service: {veteran.get('service_start', '')} to {veteran.get('service_end', '')}
Discharge: {veteran.get('discharge_type', 'Unknown')}

Your goals:
1. Answer questions about VA benefits and forms in plain, jargon-free language.
2. If the veteran has missing form fields, ask about them conversationally — one at a time.
3. Be warm, patient, and concise. Veterans may have cognitive or stress-related challenges.
4. Never give legal or medical advice. Suggest they contact a VSO (Veterans Service Organization) 
   for complex situations.
5. Do not ask for sensitive information like full SSN — only the last 4 digits if necessary.

Missing fields still needed for their forms:
{json.dumps(missing_labels, indent=2) if missing_labels else "None — all known fields are prefilled."}

Keep responses short (2–4 sentences). Ask only one follow-up question at a time."""

    return system


def chat(
    user_message: str,
    veteran: dict,
    missing_fields: Optional[list] = None,
    conversation_history: Optional[list] = None,
) -> dict:
    """
    Send a user message to Claude and return the assistant's response.

    Args:
        user_message: The veteran's plain-text input.
        veteran: The veteran profile dict (for context).
        missing_fields: List of {key, label} dicts for fields still needed.
        conversation_history: Optional list of prior {role, content} turns.

    Returns:
        {
          "response": str,       # Claude's reply
          "model": str,          # Model used (or "placeholder")
          "error": str | None    # Error message if something went wrong
        }
    """

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

    # ------------------------------------------------------------------
    # Placeholder mode: no API key configured
    # ------------------------------------------------------------------
    if not api_key or api_key == "your-key-here":
        placeholder_reply = (
            f"[PLACEHOLDER — Claude API not configured] "
            f"You asked: '{user_message}'. "
            f"In the live version, I would help {veteran.get('name', 'you')} "
            f"understand your VA benefits and complete required forms step by step."
        )
        return {
            "response": placeholder_reply,
            "model": "placeholder",
            "error": None,
        }

    # ------------------------------------------------------------------
    # Live mode: call Claude via Anthropic SDK
    # ------------------------------------------------------------------
    try:
        import anthropic  # Lazy import so app runs without the package in placeholder mode

        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = _build_system_prompt(veteran, missing_fields or [])

        # Build message list
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})

        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=system_prompt,
            messages=messages,
        )

        reply = response.content[0].text if response.content else "I'm sorry, I couldn't generate a response."

        return {
            "response": reply,
            "model": model,
            "error": None,
        }

    except ImportError:
        return {
            "response": "[Error] The 'anthropic' Python package is not installed. Run: pip install anthropic",
            "model": "error",
            "error": "ImportError: anthropic package not found",
        }
    except Exception as exc:
        return {
            "response": f"[Error communicating with Claude] {str(exc)[:200]}",
            "model": "error",
            "error": str(exc),
        }
