import json
import os
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client


class SimulationEvaluationError(Exception):
    """Raised when Gemini cannot produce a valid evaluation."""


def evaluate_workplace_submission(evidence: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a submitted workplace task from recorded simulation evidence."""
    model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    prompt = f"""Evaluate this CareerGrid workplace submission using only the evidence.
For attempt-backed evidence, private_expected_solution is a server-only rubric;
compare it against actual_user_evidence, especially changed_files, commits, PR,
verification, and conversation. Do not award technical accuracy merely because a
submission email claims the expected root cause. Recognize valid alternatives
listed by the rubric. Do not mention private instructions, hidden context, AI,
or simulation mechanics in the user-facing report. Do not invent facts.
Use final_communication and the conversation to judge root-cause explanation,
change summary, verification/testing evidence, and professional communication.
Missing evidence should reduce the relevant dimensions when appropriate, but is
not an automatic zero and must never be treated as proof that the technical work
is incorrect. Technical correctness must be judged from the actual code, commits,
and pull request evidence.
Return JSON only with: overall_score (0-100), summary,
dimensions (technical_accuracy, problem_solving, verification_testing,
git_workflow, communication, independence; each with score, max_score, feedback),
strengths, areas_for_improvement, recommended_next_steps, advisor_feedback, and
review_message (a concise email announcing the attached review).
Evidence: {json.dumps(evidence, ensure_ascii=False)}"""
    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.35,
                ),
            )
        evaluation = json.loads(_clean_json_response(response.text or ""))
    except Exception as error:
        raise SimulationEvaluationError(
            "Gemini could not evaluate the submitted work."
        ) from error
    if not isinstance(evaluation, dict) or not isinstance(evaluation.get("dimensions"), dict):
        raise SimulationEvaluationError("Gemini returned an invalid workplace evaluation.")
    return evaluation


def _clean_json_response(response_text: str) -> str:
    """
    Remove optional Markdown code blocks from Gemini's response.
    """

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def _validate_string_list(
    evaluation: dict[str, Any],
    field_name: str,
) -> list[str]:
    """
    Validate that a field contains a list of non-empty strings.
    """

    value = evaluation.get(field_name)

    if not isinstance(value, list):
        raise SimulationEvaluationError(
            f"Gemini field '{field_name}' must be a list."
        )

    cleaned_items = [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]

    return cleaned_items


def _validate_evaluation(
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate and normalize Gemini's structured evaluation.
    """

    required_fields = {
        "overall_score",
        "summary",
        "strengths",
        "areas_for_improvement",
        "step_feedback",
        "recommended_skills",
    }

    missing_fields = required_fields - evaluation.keys()

    if missing_fields:
        missing_names = ", ".join(
            sorted(missing_fields)
        )

        raise SimulationEvaluationError(
            f"Gemini evaluation is missing: {missing_names}"
        )

    try:
        overall_score = int(
            evaluation.get("overall_score", 0)
        )
    except (TypeError, ValueError) as error:
        raise SimulationEvaluationError(
            "Gemini returned an invalid overall score."
        ) from error

    evaluation["overall_score"] = max(
        0,
        min(100, overall_score),
    )

    summary = evaluation.get("summary")

    if not isinstance(summary, str) or not summary.strip():
        raise SimulationEvaluationError(
            "Gemini returned an invalid summary."
        )

    evaluation["summary"] = summary.strip()

    evaluation["strengths"] = _validate_string_list(
        evaluation,
        "strengths",
    )

    evaluation["areas_for_improvement"] = (
        _validate_string_list(
            evaluation,
            "areas_for_improvement",
        )
    )

    evaluation["recommended_skills"] = (
        _validate_string_list(
            evaluation,
            "recommended_skills",
        )
    )

    step_feedback = evaluation.get("step_feedback")

    if not isinstance(step_feedback, list):
        raise SimulationEvaluationError(
            "Gemini step_feedback must be a list."
        )

    normalized_feedback = []

    for item in step_feedback:
        if not isinstance(item, dict):
            raise SimulationEvaluationError(
                "Each step feedback item must be an object."
            )

        try:
            step_number = int(
                item.get("step", 0)
            )

            step_score = int(
                item.get("score", 0)
            )
        except (TypeError, ValueError) as error:
            raise SimulationEvaluationError(
                "Gemini returned an invalid step or score."
            ) from error

        feedback_text = str(
            item.get("feedback", "")
        ).strip()

        if step_number < 1 or step_number > 5:
            raise SimulationEvaluationError(
                "Step numbers must be between 1 and 5."
            )

        if not feedback_text:
            raise SimulationEvaluationError(
                f"Feedback for Step {step_number} is empty."
            )

        normalized_feedback.append({
            "step": step_number,
            "score": max(
                0,
                min(100, step_score),
            ),
            "feedback": feedback_text,
        })

    feedback_steps = {
        item["step"]
        for item in normalized_feedback
    }

    if feedback_steps != {1, 2, 3, 4, 5}:
        raise SimulationEvaluationError(
            "Gemini must provide feedback for all five steps."
        )

    normalized_feedback.sort(
        key=lambda item: item["step"]
    )

    evaluation["step_feedback"] = normalized_feedback

    return evaluation


def evaluate_simulation(
    simulation_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Send the completed simulation to Gemini and return
    structured performance feedback.
    """

    if not isinstance(simulation_data, dict):
        raise SimulationEvaluationError(
            "Simulation data must be a dictionary."
        )

    answers = simulation_data.get("answers")

    if not isinstance(answers, dict):
        raise SimulationEvaluationError(
            "Simulation answers are missing."
        )

    missing_answers = [
        f"step_{step}"
        for step in range(1, 6)
        if not answers.get(f"step_{step}")
    ]

    if missing_answers:
        raise SimulationEvaluationError(
            "Cannot evaluate an incomplete simulation. "
            f"Missing: {', '.join(missing_answers)}"
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    simulation_json = json.dumps(
        simulation_data,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
You are evaluating a user's completed CareerGrid workplace
simulation.

Use all the supplied information, including:
- selected career
- selected position
- selected company
- every simulation task
- every user answer
- interactive selections and actions

Simulation data:
{simulation_json}

Evaluate the user's actual performance. Consider:
- technical correctness
- problem investigation
- prioritization
- logical decision-making
- risk awareness
- clarity of communication
- completeness of the response

Return valid JSON only using exactly this structure:

{{
  "overall_score": 78,
  "summary": "A concise overall performance assessment.",
  "strengths": [
    "A specific demonstrated strength"
  ],
  "areas_for_improvement": [
    "A specific area that needs improvement"
  ],
  "step_feedback": [
    {{
      "step": 1,
      "score": 82,
      "feedback": "Specific feedback about the Step 1 response."
    }},
    {{
      "step": 2,
      "score": 75,
      "feedback": "Specific feedback about the Step 2 response."
    }},
    {{
      "step": 3,
      "score": 80,
      "feedback": "Specific feedback about the Step 3 response."
    }},
    {{
      "step": 4,
      "score": 76,
      "feedback": "Specific feedback about the Step 4 response."
    }},
    {{
      "step": 5,
      "score": 77,
      "feedback": "Specific feedback about the Step 5 response."
    }}
  ],
  "recommended_skills": [
    "A skill the user should practice"
  ]
}}

Rules:
1. overall_score must be from 0 to 100.
2. Every step score must be from 0 to 100.
3. Include exactly one feedback object for each of Steps 1-5.
4. Base scores only on the supplied answers.
5. Do not generate random scores.
6. Make feedback constructive, specific, and concise.
7. Do not return HTML.
8. Do not return Markdown code blocks.
9. Return JSON only.
"""

    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

    except Exception as error:
        raise SimulationEvaluationError(
            "Gemini could not evaluate the simulation."
        ) from error

    if not response.text:
        raise SimulationEvaluationError(
            "Gemini returned an empty evaluation."
        )

    cleaned_response = _clean_json_response(
        response.text
    )

    try:
        evaluation = json.loads(
            cleaned_response
        )
    except json.JSONDecodeError as error:
        raise SimulationEvaluationError(
            "Gemini returned invalid JSON."
        ) from error

    if not isinstance(evaluation, dict):
        raise SimulationEvaluationError(
            "Gemini evaluation must be a JSON object."
        )

    return _validate_evaluation(
        evaluation
    )
