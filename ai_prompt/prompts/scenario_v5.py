"""Version 5 scenario-generation prompts: one saved assignment per role.

Each company/position (or live listing/position) gets one assignment that is
saved and reused by every attempt, so there is no per-attempt rotation and no
"make it different from recent tasks" instruction. The prompt states what the
assignment must contain and leaves style to the model; the response shape is
enforced by the JSON schemas in services.ai.scenario_drafts, and mechanical
formatting (README layout, IDs, inbox) is assembled by the server.
"""

from typing import Any

from ai_prompt.prompts.scenario_v3 import WORKSPACE, _feedback_block, _job_block

SCENARIO_PROMPT_VERSION = "scenario_v5_shared"

ASSIGNMENT = """WHAT TO WRITE:
One realistic assignment that this company could give a new junior on this team: either a feature
request or the investigation of a reported problem, whichever fits the job context best. It should
take roughly 30-60 minutes of meaningful work: understanding how behaviour flows through the existing
code, implementing related requirements that interact, handling edge cases, keeping existing
behaviour working, writing regression tests, and writing a short handover.

REQUIREMENTS (drafts that miss these are rejected and returned to you with the reasons):
1. An existing, working starter project that a team has been building for a while: 3-6 connected
   source modules that import each other, typically 20-120 lines each, with real behaviour the work
   touches or must keep (validation, persistence, formatting, routing). Drafts with fewer than 8
   functions/methods in total, or with modules that do not import each other, are rejected. Add a
   sample data file and 1-2 test files whose 3-6 tests import the code and pass on the starter.
   Every file is used; no placeholders or padding.
2. 3-5 related requirements that state the EXPECTED behaviour clearly and observably (inputs,
   outputs, errors, UI states). Mark each one's kind: behaviour, edge_case (at least one), or
   preserve (at least one existing behaviour that must keep working). Say what must happen, not how
   to code it.
3. The starter does NOT already meet the requirements, and nothing public gives the solution away:
   no patches or code for the fix, and no comments pointing at the defect ("bug", "fix this",
   "missing validation here", "current implementation ..."). Comments describe what code does.
4. 2-3 evidence files (logs, a ticket, an API or UI contract, sample requests, stakeholder notes) of
   at least six lines each, consistent with the code (real paths, fields, and messages), and named in
   the email.
5. README content in the "readme" fields (CareerGrid writes README.md from them; do not include
   README.md in project.files): what the service does and for whom, a responsibility for every file,
   the intended behaviour, one concrete input/output example, the data and evidence files, and how
   to verify by reading code paths and examples.
6. Each requirement carries its own private assessment (criterion, where an assessor sees the
   evidence, and the files involved, which may include new test files). Assess only what the
   requirement states.
7. Delivery is a pull request OR a push to main, with the handover in the reply email. Never require
   a pull request, a PR description, or a branch name."""


def build_backend_prompt_v5(
    *,
    role: str,
    difficulty: str,
    competencies: list[str],
    job_context: dict[str, Any] | None,
    feedback: list[str] | None = None,
) -> str:
    return f"""Write a workplace assignment for a {difficulty} {role} as one JSON draft.
Target competencies: {', '.join(competencies)}.
Use Python (Flask or plain modules), pytest tests under tests/, and JSON or CSV sample data.

{_job_block(job_context)}

{WORKSPACE}

{ASSIGNMENT}

FIELD NOTES: company_name and advisor are fictional. email_body is the advisor's message explaining
the situation and its impact and naming the README and evidence files. project.slug is
lowercase-hyphenated. private.hints are three progressively more specific mentor hints.
private.starter_gap_checks: 2-5 checks, each on a SOURCE file the work changes, with strings a correct
solution adds there (for example an error code from the contract or a status code); each string must
be absent from that starter file, including comments. private.expected_changes includes a test
file.{_feedback_block(feedback)}"""


def build_frontend_prompt_v5(
    *,
    company_name: str,
    job_context: dict[str, Any] | None,
    feedback: list[str] | None = None,
) -> str:
    return f"""Write a workplace assignment for a junior Frontend Developer as one JSON draft.
The participant works at {company_name!r} (people and messages stay fictional).
Use only HTML, CSS, JavaScript, JSON, and Markdown, with no framework or bundler: index.html,
styles.css, package.json, and 3-5 classic .js files loaded by index.html with defer. Put pure logic in
a helper ending with `if (typeof module !== 'undefined') {{ module.exports = {{ ... }}; }}` and add
tests/<name>.test.js using node:test that requires it. At most 10 files.

{_job_block(job_context)}

{WORKSPACE}

{ASSIGNMENT}

FRONTEND NOTES: requirements are plain sentences here (state edge cases and preserved behaviour in
the wording); they are assessed by private.patch_checks. issue_id looks like "FE-1234".
critical_email is the urgent report; other_emails are exactly four unrelated, realistic workplace
messages (priority high/medium/low). private.patch_checks: 4-8 exact-substring checks on the
participant's final files with short patterns any correct solution would contain; at least two
(including one correctness check) must fail on the starter. private.root_cause_keywords are 2-5
lowercase words a correct diagnosis would mention.{_feedback_block(feedback)}"""
