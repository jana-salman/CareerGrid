from typing import Any


def validate_ux_usability_audit_response(
    response: dict[str, Any]
) -> tuple[bool, str]:

    if not isinstance(response, dict):
        return False, "Invalid UX audit response."

    issues = response.get("flagged_issues", [])

    if len(issues) < 3:
        return False, "Flag at least 3 UX issues."

    for issue in issues:
        if not issue.get("category"):
            return False, "Every issue needs a category."

        if not issue.get("severity"):
            return False, "Every issue needs a severity."

        if len(issue.get("proposed_fix", "").strip()) < 20:
            return False, "Every issue needs a meaningful proposed fix."

    if response.get("usability_test_runs", 0) < 1:
        return False, "Run the usability test."

    if not response.get("release_decision"):
        return False, "Choose a release decision."

    if len(response.get("release_summary", "").strip()) < 40:
        return False, "Explain your release recommendation."

    return True, ""