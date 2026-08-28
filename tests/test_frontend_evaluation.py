from services.ai.evaluation_service import evaluate_frontend_workplace_progress


def test_frontend_evaluation_has_ten_dimensions_and_bounded_score():
    responses = {
        "step_1": {
            "written_response": "I will reproduce this critical issue.",
            "selected_priority": "Critical",
        },
        "step_2": {
            "viewports_tested": ["Desktop", "Mobile"],
            "evidence_opened": ["Console"],
            "selected_root_cause": "selector mismatch",
            "investigation_summary": "The Buy Now selector is wrong.",
            "proposed_next_action": "Patch it",
        },
        "step_3": {
            "changed_files": {"product.js": "fixed"},
            "patch_checks": {
                "correct_selector": True,
                "safe_initialization": True,
                "null_guard": True,
                "click_handler": True,
                "semantic_button": True,
            },
        },
    }
    responses["step_4"] = {
        "commands_run": ["npm test"],
        "viewport_checks": ["Desktop", "Mobile"],
        "accessibility_checks": ["keyboard"],
        "verified_results": {
            "desktop_mouse": True,
            "mobile_layout": True,
            "keyboard_activation": True,
            "focus_visibility": True,
            "console_clean": True,
            "repeated_clicks": True,
            "regression": True,
        },
    }
    responses["step_5"] = {
        "reviewed_files": ["product.js"],
        "source_step_3_files": ["product.js"],
        "commit_message": "Fix Buy Now selector",
        "pr_title": "Fix checkout interaction",
        "pr_description": (
            "Correct the selector and retain native keyboard behavior."
        ),
        "testing_checklist": ["npm test"],
        "release_recommendation": "Ready",
        "final_team_message": (
            "The focused fix is verified on desktop and mobile and is ready "
            "for review."
        ),
    }
    result = evaluate_frontend_workplace_progress(responses)
    assert 0 <= result["overall_score"] <= 100
    assert len(result["dimensions"]) == 10
    assert result["frontend_readiness"]
