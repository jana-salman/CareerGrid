"""Version 1 scenario-generation prompts."""

from typing import Any


SCENARIO_PROMPT_VERSION = "scenario_v1"


def build_backend_scenario_prompt(
    *,
    blueprint: dict[str, Any],
    company_id: str,
    attempt_id: str,
) -> str:
    """Build the Backend workplace scenario-generation prompt."""

    return f"""Create ONE strict JSON object for a CareerGrid educational workplace simulation.
Role: {blueprint['role']}; company identifier: {company_id}; attempt identifier: {attempt_id}.
Target competencies: {', '.join(blueprint['competencies'])}.

Return only this shape: {{"public_scenario": {{"scenario_id": string, "title": string,
"advisor": {{"name": string, "title": string, "email": string}},
"task": {{"id": string, "subject": string, "summary": string, "body": string,
"priority": "high", "deadline_minutes": 240, "attachments": [string]}},
"background_emails": [{{"id": string, "sender_name": string, "sender_title": string,
"sender_email": string, "subject": string, "body": string}}],
"project": {{"display_name": string, "name": string, "archive_name": string ending .zip, "default_branch": "main",
"files": [{{"path": string, "content": string}}]}},
"resources": [{{"id": string, "name": string, "type": "text", "content": string}}],
"skill_targets": [string]}}, "private_context": {{"root_cause": string,
"expected_changes": [{{"path": string, "expectation": string}}],
"acceptable_alternatives": [string], "verification_expectations": [string],
"progressive_guidance": [{{"level": 1, "guidance": string}}, {{"level": 2, "guidance": string}}, {{"level": 3, "guidance": string}}],
"evaluation_notes": {{"difficulty": "junior", "important_evidence": [string]}}}}}}.

The scenario must have one focused root cause and be solvable solely by reading its files/resources.
Do not require internet, databases, real APIs, package installation, execution, credentials, or secrets.
Use a realistic small repository (maximum 12 text files) and a focused fix. Avoid ambiguity, tricks,
multiple unrelated failures, binaries, base64, path traversal, and dangerous shell content. The task email
must not reveal the solution. Logs should be useful evidence without spelling it out. Attachments, if listed,
must exactly match a project path, resource id, or resource name. Never include private context in public_scenario.

For project naming, display_name is the concise human-friendly label, for example "User Profile Service".
project.name is the technical folder and repository slug and MUST use only lowercase letters, digits, and single
hyphens: no spaces, underscores, punctuation, uppercase letters, or leading/trailing hyphens. For example,
"User Profile Service" must use project.name "user-profile-service". Set archive_name to project.name + ".zip".

Do not put answer-revealing annotations in public source code or resources. In particular, never write comments
or text such as "BUG HERE", "FIX THIS", "this line causes the crash/error", "change this line", "root cause is",
"solution is", or "incorrect value/field". Normal realistic developer comments are allowed. Logs may name a file
and line number as evidence, but source comments must not identify the faulty line, root cause, or required fix.
If a README advertises a local test command, include the actual minimal project files/configuration needed for that
command to be meaningful; otherwise do not advertise a test command. If a public log or stack trace includes a
source filename and line number, calculate that location from the FINAL generated file content. The referenced file
must exist and the line must be in range. If you cannot guarantee this, omit the precise line number and use a
filename/function-level trace instead."""


def build_frontend_scenario_prompt(*, company_name: str, attempt_id: str) -> str:
    """Build the Frontend workplace scenario-generation prompt."""

    return f"""Create a fictional Junior Frontend Developer CareerGrid scenario for display company {company_name!r}.
Use issue FE-4021 and one coherent Buy Now checkout-panel regression. Produce exactly five tasks: Mail prioritization,
Browser investigation, VS Code patch, Browser/Terminal verification, and GitHub/final communication. Use only HTML,
CSS, JavaScript, JSON, and Markdown. Do not reveal root_cause or expected_patch in public_scenario. Return JSON matching
the established Frontend workplace scenario structure. Attempt identifier: {attempt_id}."""
