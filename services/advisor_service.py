"""Generate progressive, scenario-aware advisor guidance with Gemini."""

import json
from typing import Any

from google.genai import types

from ai.prompts.advisor_v1 import build_advisor_prompt
from config import get_gemini_model
from services.gemini_service import get_gemini_client
from services.gemini_utils import clean_json_response


class AdvisorReplyError(RuntimeError):
    """Raised when Gemini cannot produce a usable advisor reply."""


ALLOWED_INTENTS = {
    "help_request",
    "clarification",
    "progress_update",
    "final_submission",
    "follow_up",
}


def generate_advisor_reply(
    advisor_context: dict[str, Any],
) -> dict[str, Any]:
    """Generate a structured, conversational advisor response from verified context."""
    model = get_gemini_model()
    prompt = build_advisor_prompt(advisor_context)

    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.45,
                ),
            )
    except Exception as error:
        raise AdvisorReplyError("Gemini request failed.") from error

    if not response.text:
        raise AdvisorReplyError("Gemini returned an empty advisor reply.")

    try:
        parsed = json.loads(clean_json_response(response.text))
    except json.JSONDecodeError as error:
        raise AdvisorReplyError("Gemini returned invalid advisor JSON.") from error

    if not isinstance(parsed, dict):
        raise AdvisorReplyError("Gemini advisor reply must be an object.")

    reply = str(parsed.get("advisor_reply") or "").strip()

    if not reply:
        raise AdvisorReplyError("Gemini advisor reply is missing text.")

    intent = str(parsed.get("intent") or "follow_up").strip()

    if intent not in ALLOWED_INTENTS:
        intent = "follow_up"

    try:
        guidance_level = int(parsed.get("guidance_level", 1) or 1)
    except (TypeError, ValueError):
        guidance_level = 1

    return {
        "intent": intent,
        "advisor_reply": reply,
        "needs_more_information": bool(
            parsed.get("needs_more_information", False)
        ),
        "guidance_level": max(
            1,
            min(3, guidance_level),
        ),
    }
