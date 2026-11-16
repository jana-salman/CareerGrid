"""Version 3 workplace-evaluation prompt.

Adds: two accepted submission routes (pull request or direct to main), Git
workflow assessed separately from technical quality, an explicit distinction
between executed tests and written verification claims, and a personalized
roadmap that must cite the submitted evidence.
"""

import json
from typing import Any


WORKPLACE_EVALUATION_PROMPT_VERSION = "workplace_evaluation_v3"


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

Return JSON only with: overall_score (0-100, weighting technical dimensions far above
git_workflow), summary,
dimensions (technical_accuracy, problem_solving, verification_testing,
git_workflow, communication, independence; each with score, max_score, feedback),
strengths, areas_for_improvement, recommended_next_steps, advisor_feedback,
git_workflow_feedback (2-4 sentences),
personalized_roadmap (2-4 items, each {{"skill": string, "evidence": string quoting or
naming the specific file, change, commit message, or message from the submission that
shows the gap, "gap": string explaining what is missing and why it matters in this
role, "next_steps": [2-3 concrete, specific learning actions]}}), and
review_message (a concise email announcing the attached review).
Evidence: {json.dumps(evidence, ensure_ascii=False)}"""
