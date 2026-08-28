"""Shared helpers for parsing JSON out of Gemini text responses."""

import json
from typing import Any


def clean_json_response(response_text: str) -> str:
    """Remove optional Markdown code blocks from Gemini's response."""

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def extract_json(text: str) -> dict[str, Any]:
    """Convert Gemini output into a JSON object even when the model
    wraps it in markdown code fences.
    """

    if not text:
        raise ValueError("Gemini returned an empty response.")

    cleaned = clean_json_response(text)

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini response did not contain valid JSON.")

    return json.loads(cleaned[start:end + 1])
