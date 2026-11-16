"""Gemini generation and validation for workplace simulation scenarios."""

import json
import logging
import os
import posixpath
import re
from collections.abc import Callable, Collection
from copy import deepcopy
from typing import Any

from ai_prompt.prompts.scenario_v5 import SCENARIO_PROMPT_VERSION as SINGLE_PROMPT_VERSION
from ai_prompt.prompts.scenario_v5 import build_backend_prompt_v5
from ai_prompt.prompts.scenario_v4 import SCENARIO_PROMPT_VERSION as STAGED_PROMPT_VERSION
from ai_prompt.prompts.scenario_v4 import build_project_prompt, build_spec_prompt
from services.ai.scenario_quality import is_test_file
from services.ai.generation_runtime import (
    GenerationAttemptError,
    GenerationReport,
    Step,
    generation_max_attempts,
    generation_pipeline,
    run_generation,
    run_pipeline,
)
from services.ai.scenario_drafts import (
    BACKEND_BUILD_SCHEMA,
    BACKEND_DRAFT_SCHEMA,
    BACKEND_SPEC_SCHEMA,
    assemble_backend,
    build_schema_for,
    merge_spec_and_build,
    spec_for_prompt,
    spec_problems,
)


logger = logging.getLogger(__name__)


class ScenarioGenerationError(RuntimeError):
    """Raised when a workplace scenario cannot be generated safely."""


class ScenarioQualityError(ScenarioGenerationError):
    """Raised when a well-formed scenario is too shallow or inconsistent."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems[:5]))
        self.problems = problems




SCENARIO_BLUEPRINTS = {
    ("software-developer", "backend-developer"): {
        "role": "junior/intern Backend Developer",
        "competencies": [
            "reading logs, tickets, and error evidence",
            "tracing request and data flow across modules",
            "handling edge cases and invalid input",
            "implementing related changes coherently across a few files",
            "updating or adding tests and explaining verification",
            "a Git delivery workflow (pull request or direct to main)",
            "communicating findings, changes, and risks clearly",
        ],
        "difficulty": "junior",
    },
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".json", ".md", ".txt", ".log", ".yml",
    ".yaml", ".env.example", ".csv",
}
PRIVATE_FIELD_NAMES = {
    "root_cause", "expected_changes", "acceptable_alternatives",
    "verification_expectations", "progressive_guidance", "evaluation_notes",
    "expected_patch", "scoring_notes", "private_context",
    "assessment_criteria", "starter_gap_checks", "patch_checks", "root_cause_keywords",
}
MAX_FILES = 12
MAX_FILE_CONTENT_LENGTH = 20_000
MAX_SCENARIO_JSON_LENGTH = 120_000
PROJECT_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FORBIDDEN_CONTENT_PATTERNS = (
    re.compile(r"\brm\s+-rf\b", re.IGNORECASE),
    re.compile(r"\bcurl\b[^\n|]*\|\s*(?:sh|bash)\b", re.IGNORECASE),
    re.compile(r"\bpowershell\b[^\n]*\s-enc(?:odedcommand)?\b", re.IGNORECASE),
)
SOLUTION_LEAK_PATTERNS = (
    re.compile(r"\bbug\s+(?:is\s+)?here\b", re.IGNORECASE),
    # "Can you fix it today?" is a normal request; "fix here" points at code.
    re.compile(r"\bfix\s+here\b", re.IGNORECASE),
    re.compile(r"\b(?:this\s+)?line(?:\s+\d+)?(?:\s+below)?\s+(?:causes|is\s+causing)\s+the\s+(?:crash|error)\b", re.IGNORECASE),
    re.compile(r"\bthis\s+is\s+the\s+bug\b", re.IGNORECASE),
    re.compile(r"\bchange\s+this\s+line\b", re.IGNORECASE),
    # "The root cause is X" discloses it; "what the root cause is" and "is unknown" do not.
    re.compile(r"(?<!what )(?<!what the )\broot\s+cause\s+is\s+(?!unknown|unclear|not\b|still\b|being\b|under\b)", re.IGNORECASE),
    re.compile(r"\bthe\s+(?:fix|solution)\s+is\s+to\b", re.IGNORECASE),
    re.compile(r"\b(?:starter|intentional|deliberate|planted|seeded)\s+(?:bug|defect)\b", re.IGNORECASE),
)
# Code comments that point at the planted defect ("// BUG:", "# FIXME", "TODO: fix").
# Applied to source files only: tickets and logs legitimately say "bug" or
# "known issue", and Markdown headings start with "#".
CODE_COMMENT_LEAK_PATTERN = re.compile(
    r"(?:#|//|/\*|<!--)[ \t]*(?:"
    r"bug\b(?!-)|fixme\b|todo:?\s*fix\b|fix\s+(?:this|it|here)\b|"
    # Hints that state the expected behaviour next to the defect, seen in live drafts:
    # "# Should check if 15 <= duration <= 120", "# The total_count should reflect ...",
    # "# Note: Current behavior returns 500, requirement asks for 400".
    r"(?:note:\s*)?(?:the\s+\w+\s+)?should\s+(?:check|validate|verify|handle|reject|return|reflect|include|"
    r"use|be|not|raise|compare|match|filter|skip)\b|"
    r"(?:note:\s*)?current(?:ly)?\s+behaviou?r\b|requirement\s+(?:asks|says|wants|expects)|"
    r"missing\s+(?:check|validation)|off[- ]by[- ]one)",
    re.IGNORECASE,
)


# Hint phrases anywhere inside a code comment ("# CURRENT IMPLEMENTATION: Missing validation ...").
COMMENT_TEXT = {
    ".py": re.compile(r"#[^\n]*"),
    ".js": re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL),
}
COMMENT_TEXT[".ts"] = COMMENT_TEXT[".mjs"] = COMMENT_TEXT[".js"]
COMMENT_HINT = re.compile(
    r"current(?:ly)?\s+(?:implementation|behaviou?r)|"
    r"missing\s+(?:validation|check|idempotency|guard|handling)|"
    r"(?:no|lacks?)\s+(?:validation|idempotency)\b|"
    r"not\s+(?:yet\s+)?(?:validated|implemented|handled|checked)\b|"
    r"\b(?:intentional(?:ly)?|deliberate(?:ly)?)\b",
    re.IGNORECASE,
)


def comment_hint(path: str, content: str) -> re.Match | None:
    pattern = COMMENT_TEXT.get(os.path.splitext(path)[1])
    if pattern is None:
        return None
    for comment in pattern.finditer(content):
        if COMMENT_HINT.search(comment.group(0)):
            return comment
    return None


def _leak_detail(text: str, match: re.Match, where: str) -> str:
    line = text[text.rfind("\n", 0, match.start()) + 1:text.find("\n", match.end()) if "\n" in text[match.end():] else len(text)]
    return f"Public scenario content reveals the solution in {where}: {line.strip()[:120]!r}. Remove hints about the defect."
CODE_EXTENSIONS_FOR_LEAKS = {".py", ".js", ".ts", ".mjs", ".html", ".css"}
SOURCE_LINE_REFERENCE_PATTERN = re.compile(
    r"(?P<filename>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(?P<line>[1-9][0-9]*)(?::[0-9]+)?"
)


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScenarioGenerationError(f"Scenario field '{field_name}' is required.")
    return value.strip()


def _safe_relative_path(value: Any) -> str:
    path = _required_text(value, "file path").replace("\\", "/")
    normalized = posixpath.normpath(path)
    if (
        path.startswith("/")
        or re.match(r"^[A-Za-z]:", path)
        or ".." in path.split("/")
        or normalized in {"", ".", ".."}
        or normalized.startswith("../")
        or "/../" in f"/{normalized}"
    ):
        raise ScenarioGenerationError("Scenario contains an unsafe project path.")
    return normalized


def _contains_private_field(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            key in PRIVATE_FIELD_NAMES or _contains_private_field(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_private_field(child) for child in value)
    return False


def _validate_public_content(text: str, where: str = "the public brief") -> None:
    if any(pattern.search(text) for pattern in FORBIDDEN_CONTENT_PATTERNS):
        raise ScenarioGenerationError("Scenario contains unsafe shell content.")
    for pattern in SOLUTION_LEAK_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ScenarioGenerationError(_leak_detail(text, match, where))


def _validate_test_command_consistency(files: list[dict[str, Any]]) -> None:
    """Require the minimal local test structure advertised by a README."""
    markdown = "\n".join(
        str(file_item.get("content", ""))
        for file_item in files
        if str(file_item.get("path", "")).lower().endswith(".md")
    )
    paths = {str(file_item.get("path", "")) for file_item in files}
    has_python_test = any(
        re.search(r"(?:^|/)test[^/]*\.py$", path, re.IGNORECASE)
        for path in paths
    )
    if re.search(r"\bpython(?:3)?\s+-m\s+unittest\b", markdown, re.IGNORECASE) and not has_python_test:
        raise ScenarioGenerationError("README advertises unittest without a Python test file.")
    if re.search(r"\bpytest\b", markdown, re.IGNORECASE) and not has_python_test:
        raise ScenarioGenerationError("README advertises pytest without a Python test file.")
    if re.search(r"\bnpm\s+test\b", markdown, re.IGNORECASE):
        package_file = next(
            (file_item for file_item in files if file_item.get("path") == "package.json"),
            None,
        )
        try:
            package_data = json.loads(package_file["content"]) if package_file else {}
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ScenarioGenerationError("README advertises npm test without a valid package.json.") from error
        if not isinstance(package_data.get("scripts"), dict) or not package_data["scripts"].get("test"):
            raise ScenarioGenerationError("README advertises npm test without a test script.")


def _validate_resource_line_references(
    resources: list[dict[str, Any]],
    file_contents: dict[str, str],
) -> None:
    """Reject log/source references that cannot point to generated code."""
    basenames: dict[str, list[str]] = {}
    for path in file_contents:
        basenames.setdefault(posixpath.basename(path), []).append(path)

    for resource in resources:
        content = str(resource.get("content", ""))
        for match in SOURCE_LINE_REFERENCE_PATTERN.finditer(content):
            referenced = match.group("filename").lstrip("./")
            candidates = [
                path for path in file_contents
                if path == referenced or path.endswith(f"/{referenced}")
            ]
            if not candidates and re.search(r"site-packages|dist-packages|/usr/|lib/python|node_modules|<frozen", referenced):
                continue  # a library frame, as real tracebacks contain
            if not candidates:
                candidates = basenames.get(posixpath.basename(referenced), [])
            if len(candidates) != 1:
                raise ScenarioGenerationError(
                    f"Evidence refers to {match.group(0)!r}, which is not a single project file."
                )
            line_count = max(1, len(file_contents[candidates[0]].splitlines()))
            if int(match.group("line")) > line_count:
                raise ScenarioGenerationError(
                    "Resource trace refers to a line outside the generated file."
                )


PrivateContextValidator = Callable[[dict[str, Any], set[str]], None]


def _validate_standard_private_context(
    private: dict[str, Any],
    file_paths: set[str],
) -> None:
    """Validate the standard Backend workplace evaluation contract."""

    expected_changes = private.get("expected_changes")
    if not isinstance(expected_changes, list) or not expected_changes:
        raise ScenarioGenerationError("Private context needs expected changes.")
    for change in expected_changes:
        if not isinstance(change, dict):
            raise ScenarioGenerationError("Every expected change must be an object.")
        path = _safe_relative_path(change.get("path"))
        if path not in file_paths and not is_test_file(path):
            raise ScenarioGenerationError(f"Expected change refers to {path}, which is not in the project.")
        _required_text(change.get("expectation"), "expected_changes.expectation")

    guidance = private.get("progressive_guidance")
    if not isinstance(guidance, list) or not guidance:
        raise ScenarioGenerationError("Private context needs progressive guidance.")
    levels = set()
    for item in guidance:
        if not isinstance(item, dict) or item.get("level") not in {1, 2, 3}:
            raise ScenarioGenerationError("Guidance must use levels 1 through 3.")
        _required_text(item.get("guidance"), "progressive_guidance.guidance")
        levels.add(item["level"])
    if levels != {1, 2, 3}:
        raise ScenarioGenerationError(
            "Private context needs guidance for levels 1, 2, and 3."
        )

    if not isinstance(private.get("evaluation_notes"), dict):
        raise ScenarioGenerationError("Private context needs evaluation notes.")


def _string_list(value: Any, field: str, minimum: int, maximum: int) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ScenarioGenerationError(
            f"Task field '{field}' needs {minimum}-{maximum} entries."
        )
    return [_required_text(item, field) for item in value]


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def assert_private_not_public(public: dict[str, Any], private: dict[str, Any]) -> None:
    """Reject scenarios whose public text repeats private solution sentences."""

    public_text = _normalized(json.dumps(public, ensure_ascii=False))
    secrets = [private.get("root_cause", "")]
    secrets += [
        change.get("expectation", "")
        for change in private.get("expected_changes", []) or []
        if isinstance(change, dict)
    ]
    expected_patch = private.get("expected_patch")
    if isinstance(expected_patch, dict):
        secrets += [str(value) for value in expected_patch.values()]
    for secret in secrets:
        candidate = _normalized(secret)
        if len(candidate) >= 30 and candidate in public_text:
            raise ScenarioGenerationError("Public scenario repeats the private solution.")


def validate_task_brief(public: dict[str, Any]) -> None:
    """Require the public brief used by the task panel and the evaluator."""

    task = public["task"]
    _string_list(task.get("requirements"), "task.requirements", 2, 8)
    _string_list(task.get("deliverables"), "task.deliverables", 2, 6)
    _string_list(task.get("acceptance_criteria"), "task.acceptance_criteria", 2, 8)


def validate_assessment_criteria(private: dict[str, Any], public: dict[str, Any]) -> None:
    criteria = private.get("assessment_criteria")
    if not isinstance(criteria, list) or not 3 <= len(criteria) <= 10:
        raise ScenarioGenerationError("Private context needs 3-10 assessment criteria.")
    ids = set()
    for item in criteria:
        if not isinstance(item, dict):
            raise ScenarioGenerationError("Every assessment criterion must be an object.")
        criterion_id = _required_text(item.get("id"), "assessment_criteria.id")
        _required_text(item.get("criterion"), "assessment_criteria.criterion")
        _required_text(item.get("evidence"), "assessment_criteria.evidence")
        if criterion_id in ids:
            raise ScenarioGenerationError("Assessment criteria IDs must be unique.")
        ids.add(criterion_id)
    if len(criteria) < len(public["task"].get("acceptance_criteria", [])) // 2:
        raise ScenarioGenerationError(
            "Assessment criteria do not cover the public acceptance criteria."
        )


def validate_generated_backend_scenario(payload: Any) -> dict[str, dict[str, Any]]:
    """Structural validation, then the brief, rubric, leak, and quality gates."""

    from services.ai.scenario_quality import assignment_quality_problems

    scenario = validate_workplace_scenario(payload)
    public, private = scenario["public_scenario"], scenario["private_context"]
    validate_task_brief(public)
    validate_assessment_criteria(private, public)
    assert_private_not_public(public, private)
    problems = assignment_quality_problems(scenario, kind="backend")
    if problems:
        raise ScenarioQualityError(problems)
    return scenario


def attempt_error(error: Exception, repairs: list[str] | None = None) -> GenerationAttemptError:
    """Turn a rejected draft into a reason code and model feedback."""

    defects = [item[len("defect: "):] for item in repairs or [] if item.startswith("defect: ")]
    if isinstance(error, ScenarioQualityError):
        return GenerationAttemptError("quality", str(error), error.problems + defects, repairs=repairs)
    message = str(error) or type(error).__name__
    reason = "solution_leak" if "reveals the solution" in message else "structure"
    return GenerationAttemptError(reason, message, [message, *defects], repairs=repairs)


def accept_assembled(
    scenario: dict[str, dict[str, Any]],
    repairs: list[str],
    validate: Callable[[dict[str, dict[str, Any]]], dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Validate an assembled scenario; any recorded defect also rejects it."""

    try:
        validated = validate(scenario)
    except ScenarioGenerationError as error:
        raise attempt_error(error, repairs) from error
    defects = [item[len("defect: "):] for item in repairs if item.startswith("defect: ")]
    if defects:
        raise GenerationAttemptError("quality", defects[0], defects, repairs=repairs)
    return validated


def run_task_generation(
    *,
    kind: str,
    report: GenerationReport,
    single_prompt: Callable[[list[str] | None], str],
    single_schema: dict[str, Any],
    spec_prompt: Callable[[list[str] | None], str],
    spec_schema: dict[str, Any],
    build_schema: dict[str, Any],
    assemble: Callable[[dict[str, Any]], tuple[dict[str, dict[str, Any]], list[str]]],
    validate: Callable[[dict[str, dict[str, Any]]], dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]] | None:
    """Run the configured pipeline ("staged" or "single"). None means fallback."""

    def accept_draft(draft: Any, defects: list[str] | None = None) -> dict[str, dict[str, Any]]:
        if not isinstance(draft, dict) or not draft:
            raise GenerationAttemptError("structure", "The draft was not a JSON object.")
        scenario, repairs = assemble(draft)
        return accept_assembled(scenario, [*(defects or []), *repairs], validate)

    pipeline = generation_pipeline()
    report.pipeline = pipeline
    if pipeline == "single":
        report.prompt_version = SINGLE_PROMPT_VERSION
        return run_generation(
            report=report, build_prompt=single_prompt, build_scenario=accept_draft,
            schema=single_schema, temperature=0.9,
        )

    report.prompt_version = STAGED_PROMPT_VERSION

    def accept_spec(_previous: Any, spec: Any) -> dict[str, Any]:
        problems = spec_problems(spec, kind=kind)
        if problems:
            raise GenerationAttemptError("spec_quality", problems[0], problems)
        return spec

    def accept_build(spec: dict[str, Any], build: Any) -> dict[str, dict[str, Any]]:
        draft, defects = merge_spec_and_build(spec, build, kind=kind)
        return accept_draft(draft, defects)

    steps = [
        # A varied, job-specific plan benefits from a higher temperature...
        Step("spec", lambda _previous, feedback: spec_prompt(feedback), spec_schema, accept_spec, 2, 0.9),
        # ...while writing a project that matches the plan needs consistency.
        Step(
            "build",
            lambda spec, feedback: build_project_prompt(kind=kind, spec_json=spec_for_prompt(spec), feedback=feedback),
            lambda spec: build_schema_for(spec, kind) if build_schema is not None else None,
            accept_build, max(1, generation_max_attempts() - 1), 0.5,
        ),
    ]
    return run_pipeline(report=report, steps=steps, temperature=0.9)


def validate_workplace_scenario(
    payload: Any,
    *,
    private_context_validator: PrivateContextValidator | None = None,
    allowed_extensions: Collection[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate shared public data and the selected private-context contract.

    The default private contract is used by generated and predefined Backend
    scenarios. Career-specific services may supply a narrow private validator
    and file allowlist while retaining all shared path, file, resource, and
    leak protections.
    """
    if not isinstance(payload, dict):
        raise ScenarioGenerationError("Scenario must be a JSON object.")
    public = payload.get("public_scenario")
    private = payload.get("private_context")
    if not isinstance(public, dict) or not isinstance(private, dict):
        raise ScenarioGenerationError("Scenario must include public and private sections.")
    if _contains_private_field(public):
        raise ScenarioGenerationError("Public scenario contains private solution fields.")
    _required_text(public.get("scenario_id"), "public_scenario.scenario_id")
    _required_text(public.get("title"), "public_scenario.title")

    advisor = public.get("advisor")
    task = public.get("task")
    project = public.get("project")
    resources = public.get("resources", [])
    if not isinstance(advisor, dict) or not isinstance(task, dict) or not isinstance(project, dict):
        raise ScenarioGenerationError("Scenario is missing advisor, task, or project data.")
    for field in ("name", "title", "email"):
        _required_text(advisor.get(field), f"advisor.{field}")
    for field in ("id", "subject", "summary", "body"):
        _required_text(task.get(field), f"task.{field}")
    # The brief itself must not state the cause or the fix either.
    for field in ("subject", "summary", "body"):
        _validate_public_content(str(task.get(field) or ""), "the task email")
    for field in ("requirements", "acceptance_criteria", "deliverables"):
        for item in task.get(field) or []:
            _validate_public_content(str(item), f"task {field.replace('_', ' ')}")
    _required_text(task.get("priority"), "task.priority")
    if not isinstance(task.get("deadline_minutes"), int) or task["deadline_minutes"] <= 0:
        raise ScenarioGenerationError("Task deadline_minutes must be a positive integer.")
    _required_text(project.get("display_name"), "project.display_name")
    project_name = _required_text(project.get("name"), "project.name")
    if not PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise ScenarioGenerationError(
            "Project name must be a lowercase hyphenated filesystem-safe slug."
        )
    # Derive the archive filename from the validated technical name instead of
    # trusting a second model-generated spelling of the project identifier.
    project["archive_name"] = f"{project_name}.zip"
    _required_text(project.get("default_branch"), "project.default_branch")

    files = project.get("files")
    if not isinstance(files, list) or not files or len(files) > MAX_FILES:
        raise ScenarioGenerationError("Project must contain between 1 and 12 files.")
    file_paths: set[str] = set()
    file_contents: dict[str, str] = {}
    accepted_extensions = (
        ALLOWED_EXTENSIONS
        if allowed_extensions is None
        else allowed_extensions
    )
    for file_item in files:
        if not isinstance(file_item, dict):
            raise ScenarioGenerationError("Every project file must be an object.")
        path = _safe_relative_path(file_item.get("path"))
        suffix = ".env.example" if path.endswith(".env.example") else os.path.splitext(path)[1]
        if suffix not in accepted_extensions:
            raise ScenarioGenerationError("Scenario contains an unsupported file type.")
        if path in file_paths:
            raise ScenarioGenerationError("Scenario contains duplicate project file paths.")
        file_paths.add(path)
        content = _required_text(file_item.get("content"), f"content for {path}")
        if len(content) > MAX_FILE_CONTENT_LENGTH:
            raise ScenarioGenerationError("Scenario contains an oversized project file.")
        _validate_public_content(content, path)
        comment = CODE_COMMENT_LEAK_PATTERN.search(content) if suffix in CODE_EXTENSIONS_FOR_LEAKS else None
        comment = comment or comment_hint(path, content)
        if comment:
            raise ScenarioGenerationError(_leak_detail(content, comment, path))
        file_contents[path] = content
    if "README.md" not in file_paths and not any(path.endswith(".md") for path in file_paths):
        raise ScenarioGenerationError("Project needs a README or equivalent Markdown context file.")
    _validate_test_command_consistency(files)

    if not isinstance(resources, list):
        raise ScenarioGenerationError("Scenario resources must be a list.")
    resource_ids: set[str] = set()
    resource_names: set[str] = set()
    for resource in resources:
        if not isinstance(resource, dict):
            raise ScenarioGenerationError("Every resource must be an object.")
        resource_id = _required_text(resource.get("id"), "resource.id")
        resource_name = _required_text(resource.get("name"), "resource.name")
        _required_text(resource.get("type"), "resource.type")
        resource_content = _required_text(resource.get("content"), "resource.content")
        _validate_public_content(resource_content)
        if resource_id in resource_ids or resource_name in resource_names:
            raise ScenarioGenerationError("Scenario resources must have unique IDs and names.")
        resource_ids.add(resource_id)
        resource_names.add(resource_name)

    _validate_resource_line_references(resources, file_contents)

    background_emails = public.get("background_emails")
    if not isinstance(background_emails, list):
        raise ScenarioGenerationError("Background emails must be a list.")
    for email in background_emails:
        if not isinstance(email, dict):
            raise ScenarioGenerationError("Every background email must be an object.")
        for field in ("id", "sender_name", "sender_title", "sender_email", "subject", "body"):
            _required_text(email.get(field), f"background_email.{field}")
        _validate_public_content(str(email.get("body") or ""), "a background email")
    if not isinstance(public.get("skill_targets"), list):
        raise ScenarioGenerationError("Skill targets must be a list.")

    attachments = task.get("attachments", [])
    if attachments is not None:
        if not isinstance(attachments, list):
            raise ScenarioGenerationError("Task attachments must be a list when provided.")
        available_attachments = file_paths | resource_ids | resource_names
        for attachment in attachments:
            if not isinstance(attachment, str) or attachment not in available_attachments:
                raise ScenarioGenerationError("Task attachment does not match a generated file or resource.")

    _required_text(private.get("root_cause"), "private_context.root_cause")
    for field in ("acceptable_alternatives", "verification_expectations"):
        if not isinstance(private.get(field), list):
            raise ScenarioGenerationError(f"Private context field '{field}' must be a list.")

    if private_context_validator is None:
        _validate_standard_private_context(private, file_paths)
    else:
        private_context_validator(private, file_paths)

    if len(json.dumps(payload, ensure_ascii=False)) > MAX_SCENARIO_JSON_LENGTH:
        raise ScenarioGenerationError("Scenario payload is too large.")
    return {"public_scenario": deepcopy(public), "private_context": deepcopy(private)}


def generate_workplace_scenario(
    *, career_id: str, position_id: str, company_id: str, attempt_id: str,
    company_name: str | None = None,
    job_context: dict[str, Any] | None = None,
    report: GenerationReport | None = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    """Generate one assignment that passes every gate, within a time budget.

    Raises ScenarioGenerationError when no attempt passes; callers then use
    the validated built-in fallback. ``report`` records what happened.
    """
    blueprint = SCENARIO_BLUEPRINTS.get((career_id, position_id))
    if not blueprint:
        raise ScenarioGenerationError("No scenario blueprint is available for this role.")
    report = report if report is not None else GenerationReport()
    report.kind = "backend"
    report.attempt_id = attempt_id
    report.job_context_source = (job_context or {}).get("source", "")
    _ = company_name  # the in-simulation company is fictional; the listing name is only context

    def build_prompt(feedback):
        return build_backend_prompt_v5(
            role=blueprint["role"],
            difficulty=blueprint["difficulty"],
            competencies=blueprint["competencies"],
            job_context=job_context,
            feedback=feedback,
        )

    def spec_prompt(feedback):
        return build_spec_prompt(
            kind="backend",
            role=blueprint["role"],
            difficulty=blueprint["difficulty"],
            competencies=blueprint["competencies"],
            company_name=None,
            job_context=job_context,
            feedback=feedback,
        )

    scenario = run_task_generation(
        kind="backend",
        report=report,
        single_prompt=build_prompt,
        single_schema=BACKEND_DRAFT_SCHEMA,
        spec_prompt=spec_prompt,
        spec_schema=BACKEND_SPEC_SCHEMA,
        build_schema=BACKEND_BUILD_SCHEMA,
        assemble=lambda draft: assemble_backend(draft, attempt_id=attempt_id, difficulty=blueprint["difficulty"]),
        validate=validate_generated_backend_scenario,
    )
    if scenario is None:
        logger.warning("Backend generation fell back: %s", report.failure_reason)
        raise ScenarioGenerationError(f"Generation failed: {report.failure_reason}")
    return scenario, len(report.attempts)
