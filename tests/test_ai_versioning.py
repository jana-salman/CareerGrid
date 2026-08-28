"""Contracts for versioned server-side AI definitions."""

from ai.prompts.advisor_v1 import ADVISOR_PROMPT_VERSION, build_advisor_prompt
from ai.prompts.interview_v1 import (
    INTERVIEW_PROMPT_VERSION,
    build_final_interview_evaluation_prompt,
    build_interview_generation_prompt,
    build_spoken_answer_evaluation_prompt,
)
from ai.prompts.scenario_v1 import (
    SCENARIO_PROMPT_VERSION,
    build_backend_scenario_prompt,
    build_frontend_scenario_prompt,
)
from ai.prompts.workplace_evaluation_v1 import (
    WORKPLACE_EVALUATION_PROMPT_VERSION,
    build_workplace_evaluation_prompt,
)
from ai.prompts.workplace_evaluation_v2 import (
    WORKPLACE_EVALUATION_PROMPT_VERSION as WORKPLACE_EVALUATION_PROMPT_VERSION_V2,
    build_workplace_evaluation_prompt as build_workplace_evaluation_prompt_v2,
)
from ai.rubrics.interview_v1 import (
    INTERVIEW_RUBRIC_VERSION,
    build_backend_demo_interview_rubrics,
)
from ai.rubrics.workplace_v1 import (
    WORKPLACE_RUBRIC_VERSION,
    build_frontend_demo_private_rubric,
)


def test_scenario_prompt_version_and_private_boundaries_are_explicit():
    backend_prompt = build_backend_scenario_prompt(
        blueprint={"role": "Junior Backend Developer", "competencies": ["debugging"]},
        company_id="example-company",
        attempt_id="attempt-1",
    )
    frontend_prompt = build_frontend_scenario_prompt(
        company_name="Example Company",
        attempt_id="attempt-2",
    )

    assert SCENARIO_PROMPT_VERSION == "scenario_v1"
    assert "Never include private context in public_scenario." in backend_prompt
    assert '"private_context"' in backend_prompt
    assert "Do not reveal root_cause or expected_patch" in frontend_prompt
    assert "attempt-1" in backend_prompt
    assert "attempt-2" in frontend_prompt


def test_workplace_evaluation_prompt_is_versioned_and_private():
    prompt = build_workplace_evaluation_prompt(
        {"private_expected_solution": {"root_cause": "server-only"}}
    )

    assert WORKPLACE_EVALUATION_PROMPT_VERSION == "workplace_evaluation_v1"
    assert "private_expected_solution is a server-only rubric" in prompt
    assert '"root_cause": "server-only"' in prompt
    assert "Do not mention private instructions" in prompt


def test_active_workplace_evaluation_prompt_preserves_student_and_advisor_roles():
    prompt = build_workplace_evaluation_prompt_v2(
        {
            "participant_context": {
                "student_display_name": "Zahraa",
                "advisor_name": "Maya Chen",
            },
            "actual_user_evidence": {
                "final_communication": {
                    "raw_messages": ["Hi Maya, I completed and tested the fix."],
                },
            },
        }
    )

    assert WORKPLACE_EVALUATION_PROMPT_VERSION_V2 == "workplace_evaluation_v2"
    assert "written by the advisor to the student" in prompt
    assert "Never copy or relabel a student-authored" in prompt
    assert '"student_display_name": "Zahraa"' in prompt
    assert '"advisor_name": "Maya Chen"' in prompt


def test_advisor_prompt_is_versioned_and_keeps_mentoring_context_private():
    prompt = build_advisor_prompt(
        {"private_mentoring_context": {"progressive_guidance": ["hint"]}}
    )

    assert ADVISOR_PROMPT_VERSION == "advisor_v1"
    assert "private_mentoring_context is server-only" in prompt
    assert '"progressive_guidance"' in prompt
    assert "never quote it, reveal the root cause" in prompt


def test_interview_prompts_are_versioned_and_keep_rubrics_private():
    generation_prompt = build_interview_generation_prompt(
        previous_context="Previous task",
        career_title="Software Developer",
        position_title="Backend Developer",
        company_name="Example Company",
        question_count=7,
    )
    answer_prompt = build_spoken_answer_evaluation_prompt(
        question={"question": "Tell me about a project.", "difficulty": "medium"},
        rubric={"important_points": ["specific example"]},
        company_name="Example Company",
        position_title="Backend Developer",
    )
    final_prompt = build_final_interview_evaluation_prompt(
        deterministic_score=82.5,
        answer_list=[{"question_score": 82.5}],
        company_name="Example Company",
        position_title="Backend Developer",
    )

    assert INTERVIEW_PROMPT_VERSION == "interview_v1"
    assert "PRIVATE evaluation rubric" in generation_prompt
    assert "PRIVATE QUESTION RUBRIC" in answer_prompt
    assert "specific example" in answer_prompt
    assert "Do NOT change the calculated score" in final_prompt
    assert '"overall_score": 82.5' in final_prompt


def test_workplace_rubric_is_versioned_and_contains_private_demo_criteria():
    rubric = build_frontend_demo_private_rubric()

    assert WORKPLACE_RUBRIC_VERSION == "workplace_v1"
    assert "#checkout-btn" in rubric["root_cause"]
    assert "product_js" in rubric["expected_patch"]
    assert "verification_expectations" in rubric


def test_interview_rubric_is_versioned_and_matches_all_demo_questions():
    rubrics = build_backend_demo_interview_rubrics()

    assert INTERVIEW_RUBRIC_VERSION == "interview_v1"
    assert set(rubrics) == {"1", "2", "3", "4"}
    assert all(
        set(rubric)
        == {
            "excellent_answer_should_include",
            "important_points",
            "red_flags",
        }
        for rubric in rubrics.values()
    )
