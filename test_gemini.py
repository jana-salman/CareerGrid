"""Manual Gemini connectivity check; not part of the offline test suite."""

from services.gemini_service import check_gemini_connection


if __name__ == "__main__":
    try:
        result = check_gemini_connection()

        print("SUCCESS:")
        print(result)

    except Exception as error:
        print("GEMINI TEST FAILED:")
        print(type(error).__name__)
        print(error)
