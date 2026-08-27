"""Version 1 private workplace evaluation rubrics."""


WORKPLACE_RUBRIC_VERSION = "workplace_v1"


def build_frontend_demo_private_rubric() -> dict:
    """Return the server-only rubric for the deterministic Frontend demo."""

    return {
        "root_cause": (
            "product.js queries #checkout-btn while the semantic button uses "
            "#buy-now-btn, leaving checkoutButton null."
        ),
        "expected_patch": {
            "product_js": (
                "Select #buy-now-btn after DOM readiness, guard missing elements, "
                "and retain native button keyboard behavior."
            )
        },
        "acceptable_alternatives": [
            "getElementById('buy-now-btn')",
            "deferred script with a null guard",
            "DOMContentLoaded initialization with a null guard",
        ],
        "verification_expectations": [
            "desktop click",
            "375px mobile",
            "Enter and Space",
            "visible focus",
            "no console errors",
            "repeated clicks",
            "build and lint",
        ],
        "scoring_notes": {
            "difficulty": "junior",
            "scope": "focused frontend regression",
        },
    }
