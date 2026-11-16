"""Version 1 private workplace evaluation rubrics."""


WORKPLACE_RUBRIC_VERSION = "workplace_v1"


def build_frontend_demo_private_rubric() -> dict:
    """Return the server-only rubric for the deterministic Frontend demo."""

    return {
        "root_cause": (
            "product.js queries #checkout-btn while the semantic button uses "
            "#buy-now-btn, leaving buyButton null; the TypeError at top level stops "
            "the remaining wiring, so colour changes and Close also stop working. "
            "Separately, no quantity validation exists, renderCheckout appends a new "
            "summary line on every press, and opening or closing the panel never "
            "moves focus."
        ),
        "expected_patch": {
            "product_js": (
                "Select #buy-now-btn, validate quantity against the selected "
                "colour's stock and show #quantity-error, and return focus to "
                "Buy Now on Close."
            ),
            "checkout_js": (
                "Replace the summary content instead of appending, and focus the "
                "panel when it opens."
            ),
            "cart_js": "Optionally add a pure quantity-validation helper with unit tests.",
        },
        "acceptable_alternatives": [
            "getElementById('buy-now-btn')",
            "deferred script with a null guard",
            "DOMContentLoaded initialization with a null guard",
            "quantity validation in product.js or as a helper in cart.js",
            "clearing the summary with replaceChildren(), innerHTML = '', or textContent = ''",
            "focusing the panel itself or its heading",
        ],
        "verification_expectations": [
            "desktop click",
            "375px mobile",
            "Enter and Space",
            "visible focus",
            "no console errors",
            "repeated clicks",
            "invalid quantities: 0, negative, decimal, above stock",
            "out-of-stock colour disables Buy Now",
            "unit tests for new logic, described as written rather than executed",
        ],
        "scoring_notes": {
            "difficulty": "junior",
            "scope": "frontend regression plus related checkout defects",
        },
        "root_cause_keywords": ["selector", "quantity", "duplicate", "focus"],
        # Declarative checks evaluated against the participant's final files.
        "patch_checks": [
            {
                "id": "correct_selector",
                "category": "correctness",
                "description": "Script targets the Buy Now button that exists in the markup.",
                "feedback": "The Buy Now control must be wired to the element that actually exists on the page.",
                "any_of": [{
                    "file": "product.js",
                    "must_include_any": ["#buy-now-btn", "getElementById('buy-now-btn')", 'getElementById("buy-now-btn")'],
                    "must_not_include": ["#checkout-btn"],
                }],
            },
            {
                "id": "quantity_validation",
                "category": "correctness",
                "description": "Invalid quantities show #quantity-error and keep checkout closed.",
                "feedback": "Quantities outside 1..stock need a visible message and must not open checkout.",
                "any_of": [
                    {"file": "product.js", "must_include_any": ["quantity-error", "quantityError"]},
                    {"file": "cart.js", "must_include_any": ["quantity-error", "quantityError"]},
                ],
            },
            {
                "id": "single_summary_line",
                "category": "regression",
                "description": "Repeated presses do not duplicate the summary.",
                "feedback": "Re-rendering the checkout summary should replace its contents, not add to them.",
                "any_of": [
                    {"file": "checkout.js", "must_include_all": ["#checkout-summary"], "must_not_include": ["beforeend"]},
                    {"file": "checkout.js", "must_include_any": ["replaceChildren(", "innerHTML = ''", 'innerHTML = ""', "textContent = ''", 'textContent = ""']},
                ],
            },
            {
                "id": "focus_management",
                "category": "accessibility",
                "description": "Focus moves into the panel when it opens.",
                "feedback": "Move keyboard focus into the checkout panel when it opens and back when it closes.",
                "any_of": [
                    {"file": "checkout.js", "must_include_any": [".focus("]},
                    {"file": "product.js", "must_include_any": [".focus("]},
                ],
            },
            {
                "id": "null_guard",
                "category": "robustness",
                "description": "Script guards against a missing button.",
                "feedback": "Guard against page elements that may be missing before using them.",
                "any_of": [{"file": "product.js", "must_include_all": ["if ("], "must_include_any": ["Button", "button"]}],
            },
            {
                "id": "safe_initialization",
                "category": "robustness",
                "description": "Script runs after the DOM is ready.",
                "feedback": "Initialise page behaviour only once the document is ready.",
                "any_of": [
                    {"file": "product.js", "must_include_all": ["DOMContentLoaded"]},
                    {"file": "index.html", "must_include_all": ["product.js\" defer"]},
                ],
            },
            {
                "id": "semantic_button",
                "category": "accessibility",
                "description": "The control remains a native button.",
                "feedback": "Keep interactive controls as native buttons so keyboard users can activate them.",
                "any_of": [{"file": "index.html", "must_include_all": ['id="buy-now-btn"', 'type="button"']}],
            },
        ],
    }
