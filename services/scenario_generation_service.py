"""Gemini generation and validation for workplace simulation scenarios."""

import json
import os
import posixpath
import re
from collections.abc import Callable, Collection
from copy import deepcopy
from typing import Any

from google.genai import types

from ai.prompts.scenario_v1 import build_backend_scenario_prompt
from config import get_gemini_model
from services.gemini_service import get_gemini_client


class ScenarioGenerationError(RuntimeError):
    """Raised when a workplace scenario cannot be generated safely."""


SCENARIO_BLUEPRINTS = {
    ("software-developer", "backend-developer"): {
        "role": "junior/intern Backend Developer",
        "competencies": [
            "reading logs and error evidence",
            "tracing request and data flow",
            "identifying one focused root cause",
            "modifying a small number of files",
            "basic verification reasoning",
            "a Git and pull-request workflow",
            "communicating findings clearly",
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
    re.compile(r"\bfix\s+(?:this|it|here)\b", re.IGNORECASE),
    re.compile(r"\b(?:this\s+)?line(?:\s+\d+)?(?:\s+below)?\s+(?:causes|is\s+causing)\s+the\s+(?:crash|error)\b", re.IGNORECASE),
    re.compile(r"\bthis\s+is\s+the\s+bug\b", re.IGNORECASE),
    re.compile(r"\bchange\s+this\s+line\b", re.IGNORECASE),
    re.compile(r"\broot\s+cause\s+is\b", re.IGNORECASE),
    re.compile(r"\bsolution\s+is\b", re.IGNORECASE),
    re.compile(r"\bincorrect\s+(?:value|field)\b", re.IGNORECASE),
)
SOURCE_LINE_REFERENCE_PATTERN = re.compile(
    r"(?P<filename>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+):(?P<line>[1-9][0-9]*)(?::[0-9]+)?"
)


def _clean_json_response(response_text: str) -> str:
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


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


def _validate_public_content(text: str) -> None:
    if any(pattern.search(text) for pattern in FORBIDDEN_CONTENT_PATTERNS):
        raise ScenarioGenerationError("Scenario contains unsafe shell content.")
    if any(pattern.search(text) for pattern in SOLUTION_LEAK_PATTERNS):
        raise ScenarioGenerationError("Public scenario content reveals the solution.")


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
            if not candidates:
                candidates = basenames.get(posixpath.basename(referenced), [])
            if len(candidates) != 1:
                raise ScenarioGenerationError(
                    "Resource trace refers to a missing or ambiguous project file."
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
        if path not in file_paths:
            raise ScenarioGenerationError("Expected change refers to a missing project file.")
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
        _validate_public_content(content)
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
    max_attempts: int = 3,
) -> tuple[dict[str, dict[str, Any]], int]:
    """Generate one coherent scenario, retrying only malformed/invalid outputs."""
    blueprint = SCENARIO_BLUEPRINTS.get((career_id, position_id))
    if not blueprint:
        raise ScenarioGenerationError("No scenario blueprint is available for this role.")
    model = get_gemini_model()
    prompt = build_backend_scenario_prompt(
        blueprint=blueprint,
        company_id=company_id,
        attempt_id=attempt_id,
    )
    for generation_attempt in range(1, max_attempts + 1):
        try:
            with get_gemini_client() as client:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.7),
                )
            payload = json.loads(_clean_json_response(response.text or ""))
            return validate_workplace_scenario(payload), generation_attempt
        except (ScenarioGenerationError, json.JSONDecodeError, ValueError, TypeError) as error:
            if generation_attempt == max_attempts:
                raise ScenarioGenerationError("Gemini did not produce a valid workplace scenario.") from error
        except Exception as error:
            if generation_attempt == max_attempts:
                raise ScenarioGenerationError("Gemini could not generate a workplace scenario.") from error
    raise ScenarioGenerationError("Gemini could not generate a workplace scenario.")
