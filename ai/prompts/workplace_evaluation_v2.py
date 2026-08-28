"""Version 2 workplace-evaluation prompt with explicit participant roles."""

from typing import Any

from ai.prompts.workplace_evaluation_v1 import build_workplace_evaluation_prompt as build_v1_prompt


WORKPLACE_EVALUATION_PROMPT_VERSION = "workplace_evaluation_v2"


def build_workplace_evaluation_prompt(evidence: dict[str, Any]) -> str:
    """Preserve the v1 rubric while disambiguating advisor and student messages."""

    prompt = build_v1_prompt(evidence)
    participant_instruction = (
        "The review_message must be written by the advisor to the student named in "
        "participant_context.student_display_name. Never copy or relabel a student-authored "
        "completion or confirmation message as the advisor's review, and never address the "
        "advisor as though they were the student.\n"
    )
    return prompt.replace("Return JSON only with:", participant_instruction + "Return JSON only with:")
