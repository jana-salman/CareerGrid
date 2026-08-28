"""Version 1 workplace-evaluation prompt."""

import json
from typing import Any


WORKPLACE_EVALUATION_PROMPT_VERSION = "workplace_evaluation_v1"


def build_workplace_evaluation_prompt(evidence: dict[str, Any]) -> str:
    """Build the private, evidence-based workplace evaluation prompt."""

    return f"""Evaluate this CareerGrid workplace submission using only the evidence.
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
