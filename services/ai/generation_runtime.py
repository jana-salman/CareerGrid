"""Bounded, observable model calls for workplace task generation.

Every generation run has an overall time budget, a per-call timeout, and a
maximum number of drafts per step. Errors are classified so that unrecoverable
ones (quota, authentication, unknown model) stop immediately instead of burning
the user's waiting time. Every model call is recorded in a GenerationReport
that is stored with the attempt (never shown to the user), and every candidate
the model returned, accepted or rejected, is written to a local archive with
its validation reasons so it can be inspected later.

A run is a sequence of steps. The single-call pipeline has one step ("draft").
The staged pipeline has two: "spec" (a short, job-specific task specification)
and "build" (the starter project, evidence, and private rubric for that spec).
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from google.genai import types

from config import environment_flag, get_environment_value, get_scenario_model
from services.ai.gemini_service import get_gemini_client
from services.ai.gemini_utils import clean_json_response

logger = logging.getLogger(__name__)

DEFAULT_BUDGET_SECONDS = 240
DEFAULT_MAX_ATTEMPTS = 4
MIN_CALL_SECONDS = 30
OVERLOAD_BACKOFF_SECONDS = 8
MAX_OVERLOAD_RETRIES = 4
MAX_OUTPUT_TOKENS = 32768
THINKING_LEVELS = {"minimal", "low", "medium", "high"}
PIPELINES = {"single", "staged"}
DEFAULT_PIPELINE = "single"  # staged is selectable; see README for measured results
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE_DIR = PROJECT_ROOT / "instance" / "generation_candidates"

# Errors after which another attempt cannot succeed within this request.
FATAL_REASONS = {"quota_exhausted", "auth_failed", "model_unavailable", "not_configured"}
# Failures caused by the API rather than by the content of a draft.
AVAILABILITY_REASONS = FATAL_REASONS | {"timeout", "model_overloaded", "provider_error", "time_budget_exhausted"}


class GenerationAttemptError(Exception):
    """A rejected draft with a machine-readable reason and retry feedback."""

    def __init__(self, reason: str, message: str, feedback: list[str] | None = None, repairs: list[str] | None = None):
        super().__init__(message)
        self.reason = reason
        self.feedback = feedback or [message]
        self.repairs = repairs or []


def _int_setting(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(get_environment_value(name, str(default)) or default)
    except ValueError:
        return default
    return max(minimum, min(maximum, value))


def generation_budget_seconds() -> int:
    return _int_setting("SCENARIO_GENERATION_BUDGET_SECONDS", DEFAULT_BUDGET_SECONDS, 60, 900)


def generation_max_attempts() -> int:
    return _int_setting("SCENARIO_GENERATION_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS, 1, 5)


def generation_pipeline() -> str:
    value = (get_environment_value("SCENARIO_GENERATION_PIPELINE") or DEFAULT_PIPELINE).strip().lower()
    return value if value in PIPELINES else DEFAULT_PIPELINE


def thinking_level() -> str | None:
    value = (get_environment_value("GEMINI_SCENARIO_THINKING") or "").strip().lower()
    return value if value in THINKING_LEVELS else None


def archive_directory() -> Path | None:
    """Where candidates are kept; None when archiving is switched off."""

    if not environment_flag("SCENARIO_CANDIDATE_ARCHIVE", default=True):
        return None
    configured = (get_environment_value("SCENARIO_CANDIDATE_DIR") or "").strip()
    return Path(configured) if configured else DEFAULT_ARCHIVE_DIR


def _safe_message(text: str, limit: int = 300) -> str:
    """Short diagnostic text with anything key-like removed."""

    text = re.sub(r"(key|token)=[^&\s]+", r"\1=[redacted]", str(text))
    text = re.sub(r"AIza[0-9A-Za-z_-]{10,}", "[redacted]", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def classify_exception(error: Exception) -> str:
    text = f"{type(error).__name__} {error}".lower()
    if "resource_exhausted" in text or " 429" in text or "quota" in text:
        return "quota_exhausted"
    if "api key" in text or "permission_denied" in text or " 401" in text or " 403" in text:
        return "auth_failed"
    if "not_found" in text or " 404" in text:
        return "model_unavailable"
    if "gemini_api_key is missing" in text:
        return "not_configured"
    if "timeout" in text or "timed out" in text or "deadline" in text:
        return "timeout"
    if " 503" in text or "unavailable" in text or "overloaded" in text or "high demand" in text:
        return "model_overloaded"
    if isinstance(error, json.JSONDecodeError):
        return "invalid_json"
    return "provider_error"


def failure_category(reason: str) -> str:
    """'availability' (the API), 'quality' (the draft), or '' for success."""

    if not reason:
        return ""
    return "availability" if reason in AVAILABILITY_REASONS else "quality"


@dataclass
class GenerationReport:
    """What happened while generating one attempt's task."""

    model: str = ""
    kind: str = ""
    pipeline: str = ""
    prompt_version: str = ""
    attempt_id: str = ""
    archetype: str = ""
    domain: str = ""
    job_context_source: str = ""
    budget_seconds: int = 0
    attempts: list[dict[str, Any]] = field(default_factory=list)
    outcome: str = "pending"
    failure_reason: str = ""
    started: float = field(default_factory=time.monotonic)
    duration_seconds: float = 0.0
    archive_path: str = ""

    def record(self, *, outcome: str, reason: str = "", detail: str = "", seconds: float = 0.0, stage: str = "draft") -> None:
        self.attempts.append(
            {
                "attempt": len(self.attempts) + 1,
                "stage": stage,
                "outcome": outcome,
                "reason": reason,
                "detail": _safe_message(detail),
                "seconds": round(seconds, 1),
            }
        )

    def finish(self, outcome: str, failure_reason: str = "") -> None:
        self.outcome = outcome
        self.failure_reason = failure_reason
        self.duration_seconds = round(time.monotonic() - self.started, 1)

    @property
    def api_calls(self) -> int:
        return len(self.attempts)

    def to_record(self) -> dict[str, Any]:
        """Firebase-safe internal diagnostics for the attempt record."""

        return {
            "model": self.model,
            "kind": self.kind,
            "pipeline": self.pipeline,
            "prompt_version": self.prompt_version,
            "archetype": self.archetype,
            "domain": self.domain,
            "job_context_source": self.job_context_source,
            "budget_seconds": self.budget_seconds,
            "outcome": self.outcome,
            "failure_reason": self.failure_reason,
            "failure_category": failure_category(self.failure_reason),
            "duration_seconds": self.duration_seconds,
            "api_calls": self.api_calls,
            "candidate_archive": self.archive_path,
            "attempts": list(self.attempts),
        }

    # --- candidate archive -------------------------------------------------

    def _archive_dir(self) -> Path | None:
        root = archive_directory()
        if root is None:
            return None
        if not self.archive_path:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            safe_id = re.sub(r"[^A-Za-z0-9_-]+", "-", self.attempt_id or "attempt")[:40]
            self.archive_path = str(Path(stamp[:8]) / f"{stamp}-{self.kind or 'task'}-{safe_id}")
        return root / self.archive_path

    def archive(self, name: str, payload: dict[str, Any]) -> None:
        """Keep a candidate or summary on disk. Never breaks generation."""

        try:
            directory = self._archive_dir()
            if directory is None:
                return
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f"{name}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
        except OSError as error:  # disk full, read-only host, etc.
            logger.warning("Could not archive generation candidate: %s", error)


def call_model_json(
    prompt: str,
    *,
    schema: dict[str, Any] | None,
    timeout_seconds: float,
    temperature: float,
) -> Any:
    """One schema-constrained model call with a hard timeout."""

    config: dict[str, Any] = {
        "response_mime_type": "application/json",
        "temperature": temperature,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "http_options": types.HttpOptions(timeout=int(timeout_seconds * 1000)),
    }
    if schema is not None:
        config["response_json_schema"] = schema
    level = thinking_level()
    if level:
        config["thinking_config"] = types.ThinkingConfig(thinking_level=level.upper())
    with get_gemini_client() as client:
        response = client.models.generate_content(
            model=get_scenario_model(),
            contents=prompt,
            config=types.GenerateContentConfig(**config),
        )
    text = response.text or ""
    if not text.strip():
        raise GenerationAttemptError("empty_response", "The model returned no content.")
    # strict=False accepts raw newlines inside long string values (README and
    # code samples), which models occasionally emit; nothing else changes.
    return json.loads(clean_json_response(text), strict=False)


@dataclass
class Step:
    """One model-backed stage of a generation run.

    ``build_prompt(previous, feedback)`` writes the prompt from the previous
    step's accepted output; ``accept(previous, draft)`` validates the model's
    draft and returns this step's output, or raises GenerationAttemptError.
    """

    name: str
    build_prompt: Callable[[Any, list[str] | None], str]
    # A schema, or a function of the previous step's output that returns one.
    schema: dict[str, Any] | Callable[[Any], dict[str, Any]] | None
    accept: Callable[[Any, Any], Any]
    max_drafts: int
    temperature: float | None = None


def run_pipeline(*, report: GenerationReport, steps: list[Step], temperature: float) -> Any:
    """Run the steps in order within one time budget. None means fallback."""

    budget = generation_budget_seconds()
    report.budget_seconds = budget
    report.model = get_scenario_model()
    deadline = time.monotonic() + budget
    last_reason = "no_attempt"
    overloads = 0
    previous: Any = None
    for step in steps:
        feedback: list[str] | None = None
        drafts = 0
        accepted = False
        # Drafts count model responses and real failures. Transient "overloaded"
        # errors are retried separately (bounded) so they do not use up drafts.
        while drafts < step.max_drafts and overloads <= MAX_OVERLOAD_RETRIES:
            remaining = deadline - time.monotonic()
            if remaining < MIN_CALL_SECONDS:
                last_reason = "time_budget_exhausted"
                break
            started = time.monotonic()
            draft: Any = None
            returned = False
            try:
                draft = call_model_json(
                    step.build_prompt(previous, feedback),
                    schema=step.schema(previous) if callable(step.schema) else step.schema,
                    timeout_seconds=remaining,
                    temperature=step.temperature if step.temperature is not None else temperature,
                )
                returned = True
                drafts += 1
                output = step.accept(previous, draft)
            except GenerationAttemptError as error:
                last_reason = error.reason
                feedback = error.feedback
                drafts += 0 if returned else 1
                seconds = time.monotonic() - started
                report.record(stage=step.name, outcome="rejected", reason=error.reason, detail="; ".join(error.feedback[:6]), seconds=seconds)
                report.archive(
                    f"{len(report.attempts):02d}-{step.name}-rejected",
                    {"stage": step.name, "outcome": "rejected", "reason": error.reason, "seconds": round(seconds, 1),
                     "problems": error.feedback, "repairs": error.repairs, "draft": draft},
                )
                continue
            except Exception as error:  # provider, network, or parsing failure
                last_reason = classify_exception(error)
                seconds = time.monotonic() - started
                report.record(stage=step.name, outcome="error", reason=last_reason, detail=str(error), seconds=seconds)
                report.archive(
                    f"{len(report.attempts):02d}-{step.name}-error",
                    {"stage": step.name, "outcome": "error", "reason": last_reason, "seconds": round(seconds, 1),
                     "detail": _safe_message(str(error), 600), "draft": draft},
                )
                if last_reason in FATAL_REASONS:
                    break
                if last_reason != "model_overloaded":
                    drafts += 0 if returned else 1
                else:
                    overloads += 1
                    # Back off briefly instead of spending the next call instantly.
                    time.sleep(max(0.0, min(OVERLOAD_BACKOFF_SECONDS * overloads, deadline - time.monotonic() - MIN_CALL_SECONDS)))
                if last_reason == "invalid_json":
                    feedback = ["The response was not complete, valid JSON. Return one complete JSON object."]
                continue
            seconds = time.monotonic() - started
            report.record(stage=step.name, outcome="accepted", seconds=seconds)
            report.archive(
                f"{len(report.attempts):02d}-{step.name}-accepted",
                {"stage": step.name, "outcome": "accepted", "seconds": round(seconds, 1), "draft": draft,
                 "output": output if step is steps[-1] else None},
            )
            previous = output
            accepted = True
            break
        if not accepted:
            report.finish("fallback", last_reason)
            report.archive("summary", report.to_record())
            return None
    report.finish("generated")
    report.archive("summary", report.to_record())
    return previous


def run_generation(
    *,
    report: GenerationReport,
    build_prompt: Callable[[list[str] | None], str],
    build_scenario: Callable[[Any], dict[str, dict[str, Any]]],
    schema: dict[str, Any] | None,
    temperature: float,
) -> dict[str, dict[str, Any]] | None:
    """The single-call pipeline: one draft step holding the whole assignment."""

    report.pipeline = report.pipeline or "single"
    step = Step(
        name="draft",
        build_prompt=lambda _previous, feedback: build_prompt(feedback),
        schema=schema,
        accept=lambda _previous, draft: build_scenario(draft),
        max_drafts=generation_max_attempts(),
    )
    return run_pipeline(report=report, steps=[step], temperature=temperature)
