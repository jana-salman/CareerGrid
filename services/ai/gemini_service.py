"""Create configured Google Gemini clients for CareerGrid AI services."""

import os

from google import genai

from config import get_gemini_model


def get_gemini_client():
    """
    Create and return a Gemini API client.

    Raises:
        RuntimeError: If GEMINI_API_KEY is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file."
        )

    return genai.Client(api_key=api_key)


def check_gemini_connection() -> str:
    """
    Send a manual diagnostic request to confirm Gemini connectivity.

    This is intentionally not an automated test because it consumes an external
    API and requires credentials and network access.
    """
    model = get_gemini_model()

    client = get_gemini_client()

    try:
        response = client.models.generate_content(
            model=model,
            contents=(
                "Reply with exactly this sentence and nothing else: "
                "CareerGrid Gemini connection works."
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text.strip()

    finally:
        client.close()
