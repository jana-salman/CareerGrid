"""Schema-constrained task drafts and their server-side assembly.

The model writes only what needs judgement: the situation, requirements,
project files, README, evidence, and private rubric. The server builds all
mechanical structure (IDs, attachments, inbox layout, the five Frontend steps,
Firebase-safe keys, test scripts) before the full validators and quality gate
run.

Repairs are limited to mechanical formatting and to deleting a provably false
detail (a log line number past the end of a file). The server never invents
evidence, assessment criteria, or file descriptions, and never drops an
assessment check: a draft with such a gap is rejected with a "defect: ..."
entry that is returned to the model as feedback.

Gemini accepts but does not enforce minLength (only minItems/maxItems bound
the output), so text length is checked by the quality gate instead.
"""

import json
import re
from copy import deepcopy
from typing import Any

from services.ai.scenario_quality import CODE_EXTENSIONS, EDGE_CASE_TERMS, PRESERVE_TERMS, is_test_file, unused_modules

STR = {"type": "string"}
STR_LIST = {"type": "array", "items": STR}


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(properties)}


def _list(item: dict[str, Any], minimum: int, maximum: int) -> dict[str, Any]:
    """Array with explicit size bounds, so counts are enforced at generation."""

    return {"type": "array", "items": item, "minItems": minimum, "maxItems": maximum}


def _text(minimum: int) -> dict[str, Any]:
    return {"type": "string", "minLength": minimum}


# The README's substance comes from the model; the server writes the sections
# that follow from facts it already has (structure, verification, handover).
README_DRAFT = _object(
    {
        "overview": _text(250),
        "file_responsibilities": _list(_object({"path": STR, "responsibility": _text(30)}), 3, 12),
        "expected_behaviour": _text(300),
        "example": _text(80),
        "sample_data_and_resources": _text(200),
        "verification_notes": _text(150),
        "test_command": STR,
    }
)


FILE_ITEM = _object({"path": STR, "content": STR})
RESOURCE_ITEM = _object({"name": STR, "content": STR})
PERSON_EMAIL = _object({"sender_name": STR, "sender_title": STR, "subject": STR, "body": STR})

COMMON_DRAFT = {
    "title": STR,
    "company_name": STR,
    "domain": STR,
    "advisor": _object({"name": STR, "title": STR}),
    "email_subject": STR,
    "email_summary": STR,
    "email_body": _text(400),
    "requirements": _list(STR, 3, 5),
    "acceptance_criteria": _list(STR, 3, 6),
    "deliverables": _list(STR, 2, 4),
    "skill_targets": _list(STR, 3, 8),
    "project": _object({"display_name": STR, "slug": STR, "files": _list(FILE_ITEM, 5, 11)}),
    "readme": README_DRAFT,
    "resources": _list(_object({"name": STR, "content": _text(200)}), 2, 3),
}

ASSESSMENT_CRITERIA = _list(
    _object(
        {
            "id": STR,
            "criterion": STR,
            "evidence": STR,
            "files": _list(STR, 1, 4),
            "requirement_numbers": _list({"type": "integer"}, 1, 5),
        }
    ),
    3,
    8,
)
REQUIREMENT_KINDS = ["behaviour", "edge_case", "preserve"]
# One requirement and the private criterion that assesses it, together, so no
# requirement can be left unassessed (the most common live rejection).
PAIRED_REQUIREMENT = _object(
    {
        "requirement": STR,
        "kind": {"type": "string", "enum": REQUIREMENT_KINDS},
        "criterion": STR,
        "evidence": STR,
        "files": _list(STR, 1, 4),
    }
)

BACKEND_DRAFT_SCHEMA = _object(
    {
        **COMMON_DRAFT,
        "requirements": _list(PAIRED_REQUIREMENT, 3, 5),
        "background_email": PERSON_EMAIL,
        "private": _object(
            {
                "root_cause": STR,
                "expected_changes": _list(_object({"path": STR, "expectation": STR}), 2, 5),
                "acceptable_alternatives": STR_LIST,
                "verification_expectations": _list(STR, 2, 8),
                "hints": _list(STR, 3, 3),
                "starter_gap_checks": _list(_object({"id": STR, "file": STR, "must_include_any": _list(STR, 1, 4)}), 2, 5),
                "important_evidence": STR_LIST,
            }
        ),
    }
)

FRONTEND_DRAFT_SCHEMA = _object(
    {
        **COMMON_DRAFT,
        "issue_id": STR,
        "critical_email": PERSON_EMAIL,
        "other_emails": _list(
            _object({**PERSON_EMAIL["properties"], "priority": {"type": "string", "enum": ["high", "medium", "low"]}}),
            4,
            4,
        ),
        "private": _object(
            {
                "root_cause": STR,
                "root_cause_keywords": _list(STR, 2, 5),
                "expected_changes": _list(_object({"file": STR, "change": STR}), 1, 5),
                "acceptable_alternatives": STR_LIST,
                "verification_expectations": _list(STR, 2, 8),
                "patch_checks": _list(
                    _object(
                        {
                            "id": STR,
                            "category": {"type": "string", "enum": ["correctness", "robustness", "accessibility", "regression"]},
                            "description": STR,
                            "feedback": STR,
                            "file": STR,
                            "must_include_any": STR_LIST,
                            "must_not_include": STR_LIST,
                        }
                    ),
                    4,
                    8,
                ),
            }
        ),
    }
)

FRONTEND_TASK_STEPS = [
    ("mail", "Triage the incoming report", "Read the inbox, prioritise the critical issue, and reply to your lead with a first plan.", ["open_emails", "set_priority", "reply"]),
    ("browser", "Investigate the problem", "Reproduce the behaviour across viewports, inspect the evidence, and record your diagnosis.", ["test_viewports", "inspect_evidence", "submit_diagnosis"]),
    ("vscode", "Implement the change", "Edit and save the relevant files in VS Code and explain your change.", ["open_files", "edit_code", "save_diff"]),
    ("testing", "Verify behaviour and regressions", "Check the requirements, edge cases, accessibility, and existing behaviour; record what you checked.", ["run_commands", "test_browser", "release_decision"]),
    ("github", "Deliver for review (pull request or main)", "Review your diff, deliver it through a pull request or a push to main, and send the final team update.", ["review_diff", "create_pr", "final_update"]),
]


def slugify(value: Any, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return slug[:60].strip("-") or fallback


def _key(value: Any, fallback: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").lower()).strip("_")[:40] or fallback


def _texts(value: Any) -> list[str]:
    return [str(item).strip() for item in value if str(item).strip()] if isinstance(value, list) else []


def _email_address(name: str, company: str) -> str:
    return f"{slugify(name, 'lead').replace('-', '.')}@{slugify(company, 'company')}.example"


def _files(draft: dict[str, Any]) -> list[dict[str, str]]:
    seen = set()
    files = []
    for item in draft.get("project", {}).get("files", []) or []:
        path = str(item.get("path") or "").strip().lstrip("./").replace("\\", "/")
        if path and path not in seen:
            seen.add(path)
            files.append({"path": path, "content": str(item.get("content") or "")})
    return files


def _resources(draft: dict[str, Any]) -> list[dict[str, str]]:
    resources, ids = [], set()
    for item in draft.get("resources", []) or []:
        name = str(item.get("name") or "").strip().replace("/", "-")
        if not name:
            continue
        resource_id = slugify(name, "resource")
        while resource_id in ids:
            resource_id += "-2"
        ids.add(resource_id)
        resources.append({"id": resource_id, "name": name, "type": "text", "content": str(item.get("content") or "")})
    return resources


def _strip_invalid_line_numbers(resources: list[dict[str, str]], files: list[dict[str, str]]) -> None:
    """Logs that cite file:line beyond the generated file keep the file name only."""

    lengths = {item["path"]: max(1, len(item["content"].splitlines())) for item in files}
    basenames = {item["path"].rsplit("/", 1)[-1]: item["path"] for item in files}

    def fix(match: re.Match) -> str:
        name, line = match.group(1), int(match.group(2))
        path = name if name in lengths else basenames.get(name.rsplit("/", 1)[-1])
        return match.group(0) if path and line <= lengths[path] else name

    for resource in resources:
        resource["content"] = re.sub(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]+):([1-9][0-9]*)(?::[0-9]+)?", fix, resource["content"])


def _common_public(draft: dict[str, Any], attempt_id: str, files, resources) -> dict[str, Any]:
    company = str(draft.get("company_name") or "Northwind Labs").strip()
    advisor_name = str(draft.get("advisor", {}).get("name") or "Alex Morgan").strip()
    slug = slugify(draft.get("project", {}).get("slug") or draft.get("project", {}).get("display_name"), "workplace-project")
    return {
        "scenario_id": f"{slug}-{slugify(attempt_id, 'attempt')}",
        "title": str(draft.get("title") or "").strip(),
        "company_name": company,
        "advisor": {
            "name": advisor_name,
            "title": str(draft.get("advisor", {}).get("title") or "Engineering Lead").strip(),
            "email": _email_address(advisor_name, company),
        },
        "project": {
            "display_name": str(draft.get("project", {}).get("display_name") or slug).strip(),
            "name": slug,
            "archive_name": f"{slug}.zip",
            "default_branch": "main",
            "files": files,
        },
        "resources": resources,
        "skill_targets": _texts(draft.get("skill_targets")),
    }


def requirement_texts(value: Any) -> list[str]:
    """Requirement sentences, whether given as strings or as paired objects."""

    if not isinstance(value, list):
        return []
    texts = [
        str(item.get("requirement") if isinstance(item, dict) else item or "").strip()
        for item in value
    ]
    return [text for text in texts if text]


def _paired_criteria(draft: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]] | None:
    """Criteria and kinds from paired requirements; None for the older shape."""

    paired = [item for item in draft.get("requirements") or [] if isinstance(item, dict)]
    if not paired:
        return None
    criteria, kinds = [], []
    for number, item in enumerate(item for item in paired if str(item.get("requirement") or "").strip()):
        criteria.append({
            "id": f"requirement_{number + 1}",
            "criterion": item.get("criterion"),
            "evidence": item.get("evidence"),
            "files": item.get("files"),
            "requirement_numbers": [number + 1],
        })
        kinds.append(str(item.get("kind") or "behaviour"))
    # Only public requirements are assessed: no criterion for unstated behaviour.
    return criteria, kinds


# Delivery may be a pull request or a push to main; the handover is the reply email.
PR_DESCRIPTION = re.compile(r"\b(?:pull request|PR)(?:'s)? (description|body|summary)\b", re.IGNORECASE)


def _neutral_delivery(texts: list[str], repairs: list[str]) -> list[str]:
    fixed = [PR_DESCRIPTION.sub("handover reply", text) for text in texts]
    if fixed != texts:
        repairs.append("pr_description_to_handover_reply")
    return fixed


GENERIC_ROLE_TITLE = re.compile(
    r"^\s*(?:junior|senior|lead|mid-level)?\s*(?:backend|back-end|frontend|front-end|software|web|full[- ]?stack)?\s*"
    r"(?:developer|engineer)\s*(?:task|assignment)?\s*$",
    re.IGNORECASE,
)


def _task(draft: dict[str, Any], task_id: str, attachments: list[str]) -> dict[str, Any]:
    return {
        "id": task_id,
        "subject": str(draft.get("email_subject") or draft.get("title") or "").strip(),
        "summary": str(draft.get("email_summary") or "").strip(),
        "body": str(draft.get("email_body") or "").strip(),
        "priority": "high",
        "deadline_minutes": 240,
        "attachments": attachments,
        "requirements": requirement_texts(draft.get("requirements")),
        "deliverables": _texts(draft.get("deliverables")),
        "acceptance_criteria": _texts(draft.get("acceptance_criteria")),
    }


def compose_readme(draft: dict[str, Any], files: list[dict[str, str]], task: dict[str, Any], resources: list[dict[str, str]]) -> str:
    """Write README.md from the model's content plus server-known facts.

    Overview, behaviour, the example, and the data description come from the
    model. Project structure lists every file, Verification states the real
    workspace limits, and Deliverables repeats the task email exactly.
    """

    readme = draft.get("readme") if isinstance(draft.get("readme"), dict) else {}
    title = str(draft.get("project", {}).get("display_name") or draft.get("title") or "Project").strip()
    responsibilities = {
        str(item.get("path") or "").strip().lstrip("./"): str(item.get("responsibility") or "").strip()
        for item in readme.get("file_responsibilities") or []
        if isinstance(item, dict)
    }
    structure = "\n".join(
        f"- `{item['path']}` - {responsibilities.get(item['path']) or _known_responsibility(item['path'])}"
        for item in files
        if item["path"] != "README.md"
    )
    example = str(readme.get("example") or "").strip()
    if example and "```" not in example:
        example = f"```text\n{example}\n```"
    command = str(readme.get("test_command") or "").strip().strip("`") or "pytest"
    resource_names = ", ".join(f"`{item['name']}`" for item in resources)
    deliverables = "\n".join(f"- {item}" for item in task.get("deliverables") or [])
    return f"""# {title}

## Overview

{str(readme.get('overview') or '').strip()}

## Project structure

{structure}

## Expected behaviour

{str(readme.get('expected_behaviour') or '').strip()}

{example}

## Sample data and resources

{str(readme.get('sample_data_and_resources') or '').strip()}

The task email attaches these evidence files: {resource_names or 'none'}.

## Verification

{str(readme.get('verification_notes') or '').strip()}

CareerGrid's terminal cannot run code or tests, so inside the workspace you verify by tracing the code
paths and checking expected results against the examples and sample data. Write or update tests for
every behaviour you change. In CI or a local environment the test suite runs with:

```bash
{command}
```

In your handover, separate what you reasoned through from tests you wrote; do not report tests as executed.

## Deliverables and handover

{deliverables}

Commit and push your work (through a pull request or directly on main), then reply to the task email
with what you found, what you changed, how you verified it, and any remaining risks.
"""


def _normalize_brief(public: dict[str, Any], repairs: list[str]) -> None:
    """Formatting-level fixes that use only the model's own words."""

    task = public["task"]
    for key in ("requirements", "acceptance_criteria", "deliverables"):
        task[key] = _neutral_delivery(task[key], repairs)
    task["body"] = _neutral_delivery([task["body"]], repairs)[0]
    if GENERIC_ROLE_TITLE.match(public["title"] or "") and task["subject"] and not GENERIC_ROLE_TITLE.match(task["subject"]):
        public["title"] = task["subject"]
        repairs.append("title_from_email_subject")


def _drop_unused_modules(draft: dict[str, Any], files: list[dict[str, str]], repairs: list[str]) -> None:
    """Remove source modules that nothing imports and that import nothing.

    Deleting such a file changes no behaviour. A module still named by the
    email, evidence, requirements, or private rubric is kept, and the quality
    gate rejects the draft instead, because removing it would leave a dangling
    reference.
    """

    unused = unused_modules({item["path"]: item["content"] for item in files})
    if not unused:
        return
    context = {key: value for key, value in draft.items() if key not in {"project", "readme"}}
    references = json.dumps(context, ensure_ascii=False)
    for path in unused:
        if path in references or path.rsplit("/", 1)[-1] in references:
            continue
        files[:] = [item for item in files if item["path"] != path]
        repairs.append(f"removed_unused_module:{path}")


def _known_responsibility(path: str) -> str:
    """Descriptions the server can state as fact; anything else must come from the draft."""

    return "Package metadata and the test script." if path == "package.json" else "(not described)"


def _with_readme(draft: dict[str, Any], files: list[dict[str, str]], task: dict[str, Any], resources, repairs: list[str]) -> None:
    if not isinstance(draft.get("readme"), dict):
        return
    described = {
        str(item.get("path") or "").strip().lstrip("./")
        for item in draft["readme"].get("file_responsibilities") or []
        if isinstance(item, dict) and str(item.get("responsibility") or "").strip()
    }
    for item in files:
        if item["path"] not in described and item["path"] not in {"README.md", "package.json"}:
            repairs.append(f"defect: README file_responsibilities must describe {item['path']}.")
    readme = compose_readme(draft, files, task, resources)
    existing = next((item for item in files if item["path"] == "README.md"), None)
    if existing:
        existing["content"] = readme
    else:
        files.insert(0, {"path": "README.md", "content": readme})
    repairs.append("composed_readme")


def assemble_backend(draft: dict[str, Any], *, attempt_id: str, difficulty: str) -> tuple[dict[str, Any], list[str]]:
    """Build a full Backend scenario from a draft. Returns (scenario, repairs)."""

    repairs: list[str] = []
    files = _files(draft)
    _drop_unused_modules(draft, files, repairs)
    resources = _resources(draft)
    _strip_invalid_line_numbers(resources, files)
    public = _common_public(draft, attempt_id, files, resources)
    public["task"] = _task(draft, f"assignment-{public['project']['name']}", [item["id"] for item in resources])
    _normalize_brief(public, repairs)
    _with_readme(draft, files, public["task"], resources, repairs)
    email = draft.get("background_email") or {}
    public["background_emails"] = [{
        "id": "background-1",
        "sender_name": str(email.get("sender_name") or "Team member"),
        "sender_title": str(email.get("sender_title") or "Colleague"),
        "sender_email": _email_address(str(email.get("sender_name") or "team"), public["company_name"]),
        "subject": str(email.get("subject") or "Context"),
        "body": str(email.get("body") or ""),
    }] if email.get("body") else []

    paths = {item["path"]: item["content"] for item in files}
    requirement_count = len(public["task"]["requirements"])
    private_draft = draft.get("private") or {}
    paired = _paired_criteria(draft)
    raw_criteria = paired[0] if paired else private_draft.get("assessment_criteria") or []
    requirement_kinds = paired[1] if paired else []
    criteria = []
    for index, item in enumerate(raw_criteria, start=1):
        listed = _texts(item.get("files"))
        # A criterion may name a test file the participant is expected to add.
        existing = [path for path in listed if path in paths or is_test_file(path)]
        if len(existing) < len(listed):
            repairs.append(
                f"defect: assessment criterion '{item.get('id')}' names files that are not in the project: "
                f"{[path for path in listed if path not in existing][:3]}."
            )
        refs = [ref for ref in item.get("requirement_numbers") or [] if isinstance(ref, int) and 1 <= ref <= requirement_count]
        criteria.append({
            "id": _key(item.get("id"), f"criterion_{index}"),
            "criterion": str(item.get("criterion") or "").strip(),
            "evidence": str(item.get("evidence") or "").strip(),
            "files": existing,
            "requirement_refs": refs,
        })
    # Every gap check is kept as written. One that names a missing file or that
    # the starter already passes is rejected by the quality gate (naming the
    # file and strings): it may mean the starter already meets a requirement,
    # which dropping the check would hide.
    gap_checks = [
        {
            "id": _key(item.get("id"), f"gap_{index}"),
            "any_of": [{"file": str(item.get("file") or "").strip(), "must_include_any": _texts(item.get("must_include_any"))}],
        }
        for index, item in enumerate(private_draft.get("starter_gap_checks") or [], start=1)
    ]
    hints = _texts(private_draft.get("hints"))
    scenario = {
        "public_scenario": public,
        "private_context": {
            "root_cause": str(private_draft.get("root_cause") or "").strip(),
            "expected_changes": [
                {"path": str(item.get("path") or "").strip(), "expectation": str(item.get("expectation") or "").strip()}
                for item in private_draft.get("expected_changes") or []
                # A new regression test file is a legitimate planned change.
                if str(item.get("path") or "").strip() in paths or is_test_file(str(item.get("path") or "").strip())
            ],
            "acceptable_alternatives": _texts(private_draft.get("acceptable_alternatives")),
            "verification_expectations": _texts(private_draft.get("verification_expectations")),
            "progressive_guidance": [
                {"level": level, "guidance": hints[min(level - 1, len(hints) - 1)]}
                for level in (1, 2, 3)
            ] if hints else [],
            "assessment_criteria": criteria,
            "requirement_kinds": requirement_kinds,
            "starter_gap_checks": gap_checks,
            "evaluation_notes": {"difficulty": difficulty, "important_evidence": _texts(private_draft.get("important_evidence"))},
        },
    }
    return scenario, repairs


def _ensure_test_script(files: list[dict[str, str]], repairs: list[str]) -> None:
    package = next((item for item in files if item["path"] == "package.json"), None)
    if package is None:
        files.append({"path": "package.json", "content": json.dumps({"name": "frontend-project", "private": True, "scripts": {"test": "node --test"}}, indent=2) + "\n"})
        repairs.append("added_package_json")
        return
    try:
        data = json.loads(package["content"])
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        return
    scripts = data.get("scripts") if isinstance(data.get("scripts"), dict) else {}
    if scripts.get("test") != "node --test" and any(is_test_file(item["path"]) for item in files):
        data["scripts"] = {**scripts, "test": "node --test"}
        package["content"] = json.dumps(data, indent=2) + "\n"
        repairs.append("normalized_test_script")


def assemble_frontend(draft: dict[str, Any], *, attempt_id: str, company_name: str) -> tuple[dict[str, Any], list[str]]:
    """Build a full Frontend scenario (five fixed steps) from a draft."""

    repairs: list[str] = []
    files = _files(draft)
    _drop_unused_modules(draft, files, repairs)
    _ensure_test_script(files, repairs)
    resources = _resources(draft)
    _strip_invalid_line_numbers(resources, files)
    public = _common_public(draft, attempt_id, files, resources)
    issue_id = re.sub(r"[^A-Z0-9-]", "", str(draft.get("issue_id") or "").upper())[:20] or "FE-1001"
    public["company_name"] = company_name
    critical = draft.get("critical_email") or {}
    critical_email = {
        "id": slugify(critical.get("subject"), "critical-report"),
        "sender_name": str(critical.get("sender_name") or public["advisor"]["name"]),
        "sender_title": str(critical.get("sender_title") or public["advisor"]["title"]),
        "sender_email": _email_address(str(critical.get("sender_name") or "lead"), company_name),
        "subject": str(critical.get("subject") or public["title"]),
        "body": str(critical.get("body") or draft.get("email_body") or ""),
        "priority": "critical",
        "linked_ticket_id": issue_id,
    }
    others = []
    for index, item in enumerate((draft.get("other_emails") or [])[:4], start=1):
        others.append({
            "id": f"{slugify(item.get('subject'), 'message')}-{index}",
            "sender_name": str(item.get("sender_name") or "Colleague"),
            "sender_title": str(item.get("sender_title") or "Team member"),
            "sender_email": _email_address(str(item.get("sender_name") or "team"), company_name),
            "subject": str(item.get("subject") or "Update"),
            "body": str(item.get("body") or ""),
            "priority": item.get("priority") if item.get("priority") in {"high", "medium", "low"} else "low",
            "linked_ticket_id": None,
        })
    public.update(
        scenario_kind="frontend_workplace",
        issue_id=issue_id,
        fictional_company_notice="All employees, code, incidents, and messages in this simulation are fictional.",
        background_emails=others,
        inbox_emails=[critical_email, *others],
        frontend_tasks=[
            {"step": step, "application": app, "title": title, "instructions": text, "required_actions": actions}
            for step, (app, title, text, actions) in enumerate(FRONTEND_TASK_STEPS, start=1)
        ],
        allowed_terminal_commands=["help", "clear", "git diff"],
        viewport_presets={"desktop": 1440, "tablet": 768, "mobile": 375},
    )
    public["task"] = _task(draft, issue_id, ["README.md", *[item["id"] for item in resources]])
    _normalize_brief(public, repairs)
    _with_readme(draft, files, public["task"], resources, repairs)

    paths = {item["path"]: item["content"] for item in files}
    private_draft = draft.get("private") or {}
    checks, seen = [], set()
    for index, item in enumerate((private_draft.get("patch_checks") or [])[:8], start=1):
        check_id = _key(item.get("id"), f"check_{index}")
        while check_id in seen:
            check_id = f"{check_id}_{index}"
        file_path = str(item.get("file") or "").strip()
        condition = {"file": file_path, "must_include_any": _texts(item.get("must_include_any")), "must_not_include": _texts(item.get("must_not_include"))}
        if file_path not in paths:
            repairs.append(f"defect: patch check '{check_id}' targets {file_path or 'no file'}, which is not in the project.")
        seen.add(check_id)
        checks.append({
            "id": check_id,
            "category": item.get("category") if item.get("category") in {"correctness", "robustness", "accessibility", "regression"} else "correctness",
            "description": str(item.get("description") or check_id),
            "feedback": str(item.get("feedback") or item.get("description") or check_id),
            "any_of": [condition],
        })
    expected_patch = {}
    for index, item in enumerate(private_draft.get("expected_changes") or [], start=1):
        expected_patch[_key(item.get("file"), f"change_{index}")] = str(item.get("change") or "")
    scenario = {
        "public_scenario": public,
        "private_context": {
            "root_cause": str(private_draft.get("root_cause") or "").strip(),
            "root_cause_keywords": [word.lower() for word in _texts(private_draft.get("root_cause_keywords"))][:5],
            "expected_patch": expected_patch,
            "acceptable_alternatives": _texts(private_draft.get("acceptable_alternatives")),
            "verification_expectations": _texts(private_draft.get("verification_expectations")),
            "scoring_notes": {"difficulty": "junior", "domain": str(draft.get("domain") or "")[:80] or "frontend"},
            "patch_checks": checks,
        },
    }
    return deepcopy(scenario), repairs


# --- Staged pipeline: specification first, then the project ---------------
#
# Step 1 ("spec") is short: the job-specific task, the planned files with their
# responsibilities, the evidence plan, and the intended changes. It is checked
# cheaply before the expensive step 2 ("build"), which writes the files,
# evidence content, emails, and private rubric for that exact plan. The two
# are merged into the same draft shape the single-call pipeline produces, so
# the same assembly, validators, and quality gate decide acceptance.

PLANNED_FILE = _object(
    {
        "path": STR,
        "role": {"type": "string", "enum": ["source", "test", "data", "page", "style", "config"]},
        "responsibility": STR,
        "existing_behaviour": STR,
    }
)

SPEC_COMMON = {
    "title": STR,
    "company_name": STR,
    "domain": STR,
    "advisor": _object({"name": STR, "title": STR}),
    "product_overview": STR,
    "situation": STR,
    "requirements": _list(STR, 3, 5),
    "acceptance_criteria": _list(STR, 3, 6),
    "deliverables": _list(STR, 2, 4),
    "skill_targets": _list(STR, 3, 8),
    "project": _object({"display_name": STR, "slug": STR}),
    "files": _list(PLANNED_FILE, 5, 10),
    "evidence": _list(_object({"name": STR, "shows": STR}), 2, 3),
    "root_cause": STR,
    "expected_changes": _list(_object({"path": STR, "change": STR}), 2, 5),
    "test_command": STR,
}

BACKEND_SPEC_SCHEMA = _object(SPEC_COMMON)
FRONTEND_SPEC_SCHEMA = _object({**SPEC_COMMON, "issue_id": STR})

BUILD_README = _object(
    {
        "overview": STR,
        "expected_behaviour": STR,
        "example": STR,
        "sample_data_and_resources": STR,
        "verification_notes": STR,
    }
)
BUILD_COMMON = {
    "files": _list(FILE_ITEM, 5, 10),
    "readme": BUILD_README,
    "resources": _list(RESOURCE_ITEM, 2, 3),
    "email_subject": STR,
    "email_summary": STR,
    "email_body": STR,
}
_BACKEND_PRIVATE = BACKEND_DRAFT_SCHEMA["properties"]["private"]["properties"]
_FRONTEND_PRIVATE = FRONTEND_DRAFT_SCHEMA["properties"]["private"]["properties"]

BACKEND_BUILD_SCHEMA = _object(
    {
        **BUILD_COMMON,
        "background_email": PERSON_EMAIL,
        "private": _object(
            {
                key: _BACKEND_PRIVATE[key]
                for key in (
                    "acceptable_alternatives", "verification_expectations", "hints",
                    "starter_gap_checks", "important_evidence",
                )
            }
            | {"assessment_criteria": ASSESSMENT_CRITERIA}
        ),
    }
)
FRONTEND_BUILD_SCHEMA = _object(
    {
        **BUILD_COMMON,
        "critical_email": PERSON_EMAIL,
        "other_emails": FRONTEND_DRAFT_SCHEMA["properties"]["other_emails"],
        "private": _object(
            {
                key: _FRONTEND_PRIVATE[key]
                for key in ("root_cause_keywords", "acceptable_alternatives", "verification_expectations", "patch_checks")
            }
        ),
    }
)


def _extension(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""


def _clean_path(value: Any) -> str:
    path = str(value or "").strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/")


def _planned(spec: dict[str, Any]) -> list[dict[str, str]]:
    planned, seen = [], set()
    for item in spec.get("files") or []:
        if not isinstance(item, dict):
            continue
        path = _clean_path(item.get("path"))
        if path and path != "README.md" and path not in seen:  # the server writes README.md
            seen.add(path)
            planned.append({
                "path": path,
                "role": str(item.get("role") or ""),
                "responsibility": str(item.get("responsibility") or "").strip(),
                "existing_behaviour": str(item.get("existing_behaviour") or "").strip(),
            })
    return planned


def spec_problems(spec: Any, *, kind: str) -> list[str]:
    """Cheap checks on a task specification before the project is written.

    These mirror quality-gate rules that a plan can already break, so a weak
    plan is corrected in a short call instead of a long one.
    """

    if not isinstance(spec, dict):
        return ["The specification must be a JSON object."]
    problems = []
    planned = _planned(spec)
    paths = {item["path"] for item in planned}
    sources = [
        item for item in planned
        if _extension(item["path"]) in CODE_EXTENSIONS and not is_test_file(item["path"])
    ]
    tests = [item for item in planned if is_test_file(item["path"])]
    if len(sources) < 3:
        problems.append("Plan at least three source modules with distinct, connected responsibilities.")
    if not tests:
        problems.append("Plan at least one existing test file for current behaviour.")
    if kind == "backend" and not any(_extension(item["path"]) in {".json", ".csv"} for item in planned):
        problems.append("Plan a sample data or fixture file (JSON or CSV).")
    if kind == "frontend":
        for required in ("index.html", "styles.css", "package.json"):
            if required not in paths:
                problems.append(f"Plan the required file {required}.")
    for item in planned:
        if len(item["responsibility"].split()) < 5:
            problems.append(f"Describe the responsibility of {item['path']} in a full sentence.")
    for item in sources:
        if len(item["existing_behaviour"].split()) < 6:
            problems.append(f"Describe the existing, working behaviour of {item['path']} that must be preserved.")

    changes = [item for item in spec.get("expected_changes") or [] if isinstance(item, dict)]
    changed = {_clean_path(item.get("path")) for item in changes} - {""}
    if len(changed) < 2:
        problems.append("expected_changes must need coordinated changes in at least two files.")
    if not any(is_test_file(path) for path in changed):
        problems.append("expected_changes must include adding or updating a test file.")
    for path in sorted(changed):
        if path not in paths and not is_test_file(path):
            problems.append(f"expected_changes names {path}, which is not in the planned files.")

    requirements = [str(item) for item in spec.get("requirements") or []]
    joined = " ".join(requirements + [str(item) for item in spec.get("acceptance_criteria") or []])
    if not EDGE_CASE_TERMS.search(joined):
        problems.append("Requirements or acceptance criteria must include explicit edge cases (empty, invalid, duplicate, limits).")
    if not PRESERVE_TERMS.search(joined):
        problems.append("Include a requirement that states existing behaviour to preserve.")

    evidence = [str(item.get("name") or "").strip() for item in spec.get("evidence") or [] if isinstance(item, dict)]
    if len([name for name in evidence if name]) < 2 or len(set(evidence)) < len(evidence):
        problems.append("Plan two or three evidence files with distinct names.")
    for field_name in ("title", "product_overview", "situation", "root_cause"):
        if len(str(spec.get(field_name) or "").split()) < 3:
            problems.append(f"The specification needs a substantive {field_name}.")
    return problems


def merge_spec_and_build(spec: dict[str, Any], build: Any, *, kind: str) -> tuple[dict[str, Any], list[str]]:
    """Combine an accepted specification with its build into one draft.

    Returns ``(draft, defects)``. Defects are places where the build did not
    follow its plan; they cause a rejection and are never filled in by the server.
    """

    if not isinstance(build, dict):
        return {}, ["defect: The build must be a JSON object."]
    defects = []
    planned = _planned(spec)
    written = [item for item in build.get("files") or [] if isinstance(item, dict)]
    written_paths = {_clean_path(item.get("path")) for item in written}
    missing = [item["path"] for item in planned if item["path"] not in written_paths]
    if missing:
        defects.append(f"defect: Write every planned file; missing: {', '.join(missing[:5])}.")
    resources = [item for item in build.get("resources") or [] if isinstance(item, dict)]
    resource_names = {str(item.get("name") or "").strip() for item in resources}
    absent = [
        str(item.get("name") or "").strip()
        for item in spec.get("evidence") or []
        if isinstance(item, dict) and str(item.get("name") or "").strip() not in resource_names
    ]
    if absent:
        defects.append(f"defect: Write every planned evidence file; missing: {', '.join(absent[:3])}.")

    readme = dict(build["readme"]) if isinstance(build.get("readme"), dict) else {}
    readme["file_responsibilities"] = [
        {"path": item["path"], "responsibility": item["responsibility"]} for item in planned
    ]
    readme["test_command"] = str(spec.get("test_command") or "").strip()
    private = dict(build["private"]) if isinstance(build.get("private"), dict) else {}
    _criteria_from_assessments(private)
    private["root_cause"] = str(spec.get("root_cause") or "").strip()
    changes = [item for item in spec.get("expected_changes") or [] if isinstance(item, dict)]
    if kind == "backend":
        private["expected_changes"] = [
            {"path": _clean_path(item.get("path")), "expectation": str(item.get("change") or "")} for item in changes
        ]
    else:
        private["expected_changes"] = [
            {"file": _clean_path(item.get("path")), "change": str(item.get("change") or "")} for item in changes
        ]
    draft = {
        key: spec.get(key)
        for key in (
            "title", "company_name", "domain", "advisor", "requirements",
            "acceptance_criteria", "deliverables", "skill_targets", "issue_id",
        )
        if key in spec
    }
    draft.update(
        email_subject=build.get("email_subject"),
        email_summary=build.get("email_summary"),
        email_body=build.get("email_body"),
        project={
            **(spec["project"] if isinstance(spec.get("project"), dict) else {}),
            "files": [item for item in written if _clean_path(item.get("path")) != "README.md"],
        },
        readme=readme,
        resources=resources,
        private=private,
    )
    for key in ("background_email", "critical_email", "other_emails"):
        if key in build:
            draft[key] = build[key]
    return draft, defects


def build_schema_for(spec: dict[str, Any], kind: str) -> dict[str, Any]:
    """The build schema for one accepted spec.

    Backend builds give exactly one assessment per requirement, in order, so
    every requirement is assessed by a criterion the model writes (the most
    common live rejection was a requirement with no criterion). There are no
    extra criteria: only public requirements are assessed.
    """

    if kind != "backend":
        return FRONTEND_BUILD_SCHEMA
    count = len([item for item in spec.get("requirements") or [] if str(item).strip()])
    schema = deepcopy(BACKEND_BUILD_SCHEMA)
    private = schema["properties"]["private"]
    private["properties"].pop("assessment_criteria")
    private["properties"]["requirement_assessments"] = _list(
        _object({"criterion": STR, "evidence": STR, "files": _list(STR, 1, 4)}), count, count
    )
    private["required"] = list(private["properties"])
    return schema


def _criteria_from_assessments(private: dict[str, Any]) -> None:
    """Map per-requirement assessments onto numbered assessment criteria."""

    if "requirement_assessments" not in private:
        return
    criteria = []
    for number, item in enumerate(private.pop("requirement_assessments") or [], start=1):
        if isinstance(item, dict):
            criteria.append({**item, "id": f"requirement_{number}", "requirement_numbers": [number]})
    private.pop("additional_criteria", None)  # only public requirements are assessed
    private["assessment_criteria"] = criteria


def spec_for_prompt(spec: dict[str, Any]) -> str:
    """The accepted specification as JSON for the build prompt."""

    keys = [*SPEC_COMMON, "issue_id"]
    return json.dumps({key: spec[key] for key in keys if key in spec}, ensure_ascii=False, indent=1)
