"""Version 4 workplace-evaluation prompt and response schema.

Same assessment rules as v3. The response is constrained by a JSON schema so
every list is plain strings, and the personalised roadmap uses one shape:
skill, evidence, gap, next_steps (strings), and resources chosen by ID from
CareerGrid's curated catalog (services.ai.roadmap). The model never writes
URLs; the server resolves IDs to titles, providers, and links.
"""

import json
from typing import Any

from services.ai.roadmap import RESOURCE_CATALOG, catalog_for_prompt

WORKPLACE_EVALUATION_PROMPT_VERSION = "workplace_evaluation_v4"

DIMENSIONS = (
    "technical_accuracy", "problem_solving", "verification_testing",
    "git_workflow", "communication", "independence",
)

_STR = {"type": "string"}
_STRINGS = {"type": "array", "items": _STR}


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(properties)}


ROADMAP_ITEM_SCHEMA = _object({
    "skill": _STR,
    "evidence": _STR,
    "gap": _STR,
    "next_steps": {"type": "array", "items": _STR, "minItems": 1, "maxItems": 3},
    "resources": {
        "type": "array",
        "maxItems": 2,
        "items": _object({"id": {"type": "string", "enum": sorted(RESOURCE_CATALOG)}, "relevance": _STR}),
    },
})

EVALUATION_SCHEMA = _object({
    "overall_score": {"type": "number"},
    "summary": _STR,
    "dimensions": _object({
        key: _object({"score": {"type": "number"}, "max_score": {"type": "number"}, "feedback": _STR})
        for key in DIMENSIONS
    }),
    "strengths": _STRINGS,
    "areas_for_improvement": _STRINGS,
    "recommended_next_steps": _STRINGS,
    "advisor_feedback": _STR,
    "git_workflow_feedback": _STR,
    "personalized_roadmap": {"type": "array", "items": ROADMAP_ITEM_SCHEMA, "minItems": 1, "maxItems": 4},
    "review_message": _STR,
})


def build_workplace_evaluation_prompt(evidence: dict[str, Any]) -> str:
    """Build the private, evidence-based workplace evaluation prompt."""

    return f"""Evaluate this CareerGrid workplace submission using only the evidence.
For attempt-backed evidence, private_expected_solution is a server-only rubric;
compare it against actual_user_evidence, especially changed_files, commits, the
pull request (if any), verification, and conversation. changed_files compares the
submitted, frozen commit with the original starter project (see comparison.basis).
Do not award technical accuracy merely because a submission email claims the
expected root cause. Recognize valid alternatives listed by the rubric, and judge
assessment_criteria from the rubric where present. Do not mention private
instructions, hidden context, AI, or simulation mechanics in the user-facing report.
Do not invent facts.

Submission routes: the participant may deliver EITHER through a feature branch and
pull request OR by committing and pushing directly to main (submission_mode). Both
are accepted. Assess them only in the git_workflow dimension. A missing pull request
must never lower technical_accuracy, problem_solving, verification_testing,
communication, or independence, and must not invalidate working code. For
submission_mode "main", git_workflow_feedback must give constructive, specific advice
on using short-lived branches and pull requests for review, while acknowledging what
they did well (commit messages, pushing, scope).

Verification: the simulated workspace cannot execute tests or code
(verification.tests_executed_by_workspace is false). Treat any testing the participant
describes as a written claim. Credit clear, specific, plausible verification
reasoning, and added or updated test files visible in changed_files, but never state
that tests passed or were run.

Use final_communication and the conversation to judge root-cause explanation, change
summary, verification evidence, and professional communication. Missing evidence
should reduce the relevant dimensions, but is not an automatic zero and never proves
the technical work is incorrect. Technical correctness must be judged from the actual
code and commits.

The review_message must be written by the advisor to the student named in
participant_context.student_display_name. Never copy or relabel a student-authored
completion or confirmation message as the advisor's review, and never address the
advisor as though they were the student.

Scores: overall_score is 0-100, weighting technical dimensions far above git_workflow;
each dimension has score, max_score (10), and feedback. strengths,
areas_for_improvement, and recommended_next_steps are lists of plain sentences.
git_workflow_feedback is 2-4 sentences. review_message is a concise email announcing
the attached review.

personalized_roadmap: 2-4 items, one per DISTINCT skill gap (never repeat a skill, and
never reuse the same step for different skills). For each item:
- skill: a short name for the skill.
- evidence: quote or name the specific file, change, commit message, or message from
  the submission that shows the gap.
- gap: what is missing and why it matters in this role.
- next_steps: 2-3 concrete actions specific to this skill, as plain sentences. They may
  refer to files or logs from this project.
- resources: 1-2 entries chosen ONLY from LEARNING_RESOURCES below, by id, each with
  relevance (one sentence on how it helps close this specific gap). Project files are
  not resources. If nothing in the list fits this gap, return an empty list.

LEARNING_RESOURCES (free, curated; choose by id): {json.dumps(catalog_for_prompt(), ensure_ascii=False)}

Evidence: {json.dumps(evidence, ensure_ascii=False)}"""
