"""Version 4 scenario-generation prompts: a staged pipeline.

Step 1 asks only for a job-specific task specification (short, fast, checked
cheaply). Step 2 receives that accepted specification and writes the starter
project, evidence, emails, and private rubric. Response shapes are enforced by
the JSON schemas in services.ai.scenario_drafts; the server writes README.md
structure, IDs, inbox layout, and other mechanical formatting.
"""

from typing import Any

from ai_prompt.prompts.scenario_v3 import WORKSPACE, _feedback_block, _job_block

SCENARIO_PROMPT_VERSION = "scenario_v4_staged"

SPEC_RULES = """WHAT A GOOD SPECIFICATION CONTAINS:
- A believable EXISTING product that fits the job context, and a concrete situation (what users or
  stakeholders observed, business impact) that makes the work necessary now.
- 3-5 related requirements stating OBSERVABLE behaviour (inputs, outputs, error responses, UI states),
  with explicit edge cases (empty, invalid, duplicate, limits, missing...) and at least one
  requirement to preserve existing behaviour. Requirements may mention modules or endpoints as a real
  ticket would, but must not disclose the fix (no code, patches, or "change X to Y"). Never require a
  pull request or PR description: delivery is a pull request or a push to main.
- The title names the work (for example "Reject overlapping clinic bookings"), not the role.
- The planned files: 3-6 connected source modules (each with a responsibility and the existing,
  working behaviour it already has), 1-2 existing test files for current behaviour, and sample data.
  Do not plan README.md; CareerGrid writes it.
- 2-3 evidence files (logs, a ticket, an API/UI contract, sample requests, stakeholder notes) and
  what each one shows.
- root_cause and expected_changes are private: the real cause and the 2-4 files a correct solution
  changes, including a test file. The work is roughly 30-60 minutes for a junior (investigate,
  trace, implement, test, hand over)."""

BUILD_RULES = """WRITE THE PROJECT FOR EXACTLY THIS SPECIFICATION:
- Write every planned file with the same path (no README.md). Source modules are real, working code
  (typically 20-120 lines each; at least 8 functions/methods across them) that import each other
  as planned. The starter must NOT already meet the requirements: the planned root cause is present
  in the code, and nothing else is broken.
- Existing tests (3-6 cases) import the project code, pass against this starter code, and cover current
  behaviour, not the requested change.
- Write every planned evidence file (same name), each at least six lines, consistent with the code
  (real paths, field names, and messages) and showing the problem without stating the fix.
- No comments or text that reveal the cause or fix: no "bug", "fix this", "TODO: fix", "starter", and no
  comments stating what the code should do next to the defect (for example "# Should check ...",
  "# The total should reflect ...", "# Current behaviour returns 500"). Comments describe what code does.
- Every source module is imported by another module or by the tests, and there are at least 8
  functions/methods across the source modules.
- readme fields (CareerGrid assembles README.md): overview (3+ sentences: what the service does and for
  whom), expected_behaviour (the intended contract in 3+ sentences), example (a concrete input and
  output), sample_data_and_resources (the data files and what each evidence file contains),
  verification_notes (how to verify by reading code paths and checking examples). Write each as
  full paragraphs of at least 40 words; describe intended behaviour, never the defect.
- email_body: a realistic message from the advisor explaining the situation and business impact and
  naming README.md and every evidence file."""


def build_spec_prompt(
    *,
    kind: str,
    role: str,
    difficulty: str,
    competencies: list[str],
    company_name: str | None,
    job_context: dict[str, Any] | None,
    feedback: list[str] | None = None,
) -> str:
    if kind == "frontend":
        stack = (
            "Stack: only HTML, CSS, and classic JavaScript files loaded by index.html with defer (no framework or "
            "bundler). Plan index.html, styles.css, package.json, 3-5 .js files (for example data, pure helpers, "
            "rendering, page wiring), and tests/<name>.test.js using node:test that requires the helper module. "
            f"At most 10 files. The participant works at {company_name!r}. issue_id looks like \"FE-1234\". "
            "test_command is \"npm test\"."
        )
    else:
        stack = (
            "Stack: Python (Flask or plain modules), pytest tests under tests/, and JSON or CSV sample data. "
            "test_command is \"pytest\"."
        )
    return f"""Plan a realistic workplace assignment for a {difficulty} {role}. Return only the task
specification (no code yet). Target competencies: {', '.join(competencies)}.
{stack}

{_job_block(job_context)}

Either a feature request or the investigation of a reported problem is fine; choose what fits the
job context best.

{WORKSPACE}

{SPEC_RULES}

company_name and advisor are fictional. project.slug is lowercase-hyphenated. evidence[].name are file
names such as "payments-error.log".{_feedback_block(feedback)}"""


def build_project_prompt(*, kind: str, spec_json: str, feedback: list[str] | None = None) -> str:
    if kind == "frontend":
        extra = """FRONTEND NOTES: the pure helper ends with
`if (typeof module !== 'undefined') { module.exports = { ... }; }` so the node:test file can require it.
package.json has "scripts": {"test": "node --test"}. critical_email is the urgent report about this
issue; other_emails are exactly four unrelated, realistic workplace messages (priority high/medium/low).
private.patch_checks: 4-8 exact-substring checks against the participant's FINAL files, each on one
existing file with short, robust patterns any correct solution would contain. At least two (including
one correctness check) must FAIL on the starter files you wrote; others may confirm preserved behaviour.
private.root_cause_keywords are 2-5 lowercase words a correct diagnosis would mention."""
    else:
        extra = """BACKEND NOTES: background_email is a short, related message from a colleague.
private.requirement_assessments: exactly one per requirement, in the same order (item 1 assesses
requirement 1), each naming the project files where the evidence will be (existing files or new test
files). Do not assess anything the requirements do not state. private.starter_gap_checks: 2-5 checks, each on a SOURCE file
(not a test file) listed in expected_changes, with strings a correct solution must add there (for
example an error code from the contract, a field the fix must read, or a new status code). Before
answering, check every string against the starter file you wrote: it must NOT appear there anywhere,
including in comments, imports, or constants. private.hints are three progressively more specific
mentor hints."""
    return f"""Write the starter project and assignment materials for this accepted task specification.

<task_specification>
{spec_json}
</task_specification>

{WORKSPACE}

{BUILD_RULES}

{extra}{_feedback_block(feedback)}"""
