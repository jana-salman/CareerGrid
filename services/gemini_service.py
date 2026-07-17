import os

from dotenv import load_dotenv
from google import genai


# Load variables from the .env file.
load_dotenv()


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


def test_gemini_connection() -> str:
    """
    Send a small request to confirm that Gemini is connected.
    """
    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite"
    )

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