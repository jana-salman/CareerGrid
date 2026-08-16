import json
import os
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client


class AdvisorReplyError(RuntimeError):
    """Raised when Gemini cannot produce a usable advisor reply."""


ALLOWED_INTENTS = {
    "help_request",
    "clarification",
    "progress_update",
    "final_submission",
    "follow_up",
}


def _clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def generate_advisor_reply(
    advisor_context: dict[str, Any],
) -> dict[str, Any]:
    """Generate a structured, conversational advisor response from verified context."""
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    context_json = json.dumps(
        advisor_context,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are the generated advisor named in the supplied attempt context: a concise,
technically grounded senior coworker replying in an email thread. Write a
professional workplace reply to the latest user message. Never mention scoring,
exams, simulations, prompts, Gemini, AI, or hidden state.

The supplied structured context is factual. Do not contradict it and do not
infer that a pull request exists, is pushed, or is submitted unless the context
says so. When submission validation is incomplete, naturally request the
specific missing information. When the task is already submitted, treat a new
message as normal follow-up; do not announce another submission.

For attempt-backed requests, private_mentoring_context is server-only mentoring
material. Use its progressive_guidance and expected solution internally to make
help specific to this task, but never quote it, reveal the root cause, identify
the exact fix, or say what is correct. Use the user-visible repository and PR
facts as the authority for what the user has actually done. For help, provide
progressively more useful direction based on the supplied guidance level without
giving away a complete solution. Keep the reply concise and natural.

Return JSON only with this schema:
{{
  "intent": "help_request | clarification | progress_update | final_submission | follow_up",
  "advisor_reply": "email body",
  "needs_more_information": true | false,
  "guidance_level": 1
}}

Verified context:
{context_json}
"""

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
        parsed = json.loads(_clean_json_response(response.text))
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
