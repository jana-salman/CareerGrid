"""One saved, validated assignment per company/listing and position.

The first launch for a company and position generates an assignment, checks
it with the usual validators, and saves it here as version 1. Every later
attempt copies that saved version into its own attempt record, so no Gemini
call is needed and a participant's work can never change the shared copy.

Layout (server-only Firebase path, never sent to the browser)::

    shared_assignments/<key>/
        identity           what the key stands for (kind, ids, listing ref)
        current_version    int; absent until a generation succeeds
        versions/v<n>      public_scenario, private_context, generation details,
                           context_signature, library_version, created_at
        lock               {token, expires_at}: one generator at a time
        failure            {count, last_reason, last_at, cooldown_until}
        fallbacks          {count, last_at, last_reason}: fallback use, kept apart
        regenerate         {requested_at, reason}: an explicit regeneration request

Failures are never cached as assignments. After a failed generation the
participant continues with the validated built-in fallback, and a cooldown
(doubling per consecutive failure) stops every launch from calling Gemini
again. A new version is written only when a generation succeeds, and existing
attempts keep the copy they started with.
"""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import urlsplit

LIBRARY_PATH = "shared_assignments"
# Bump to regenerate every saved assignment on its next launch (for example
# after a prompt or schema change that makes older assignments unsuitable).
ASSIGNMENT_LIBRARY_VERSION = 1

LOCK_SECONDS = 420  # longer than the maximum generation budget plus storage
DEFAULT_COOLDOWN_SECONDS = 900
MAX_COOLDOWN_SECONDS = 6 * 3600
POLL_SECONDS = 2.0
# Practice-company profiles are compared by their significant words: a
# material change (new responsibilities or skills) produces a new version.
MATERIAL_SIMILARITY = 0.8

STOPWORDS = {
    "and", "the", "for", "with", "you", "our", "will", "are", "this", "that", "from", "your",
    "have", "has", "who", "into", "their", "they", "them", "about", "work", "working", "team",
}


class AssignmentUnavailable(RuntimeError):
    """No generated assignment could be produced (the caller uses the fallback)."""


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------


class FirebaseAssignmentStore:
    """Realtime Database paths; transactions make the lock safe across servers."""

    def _ref(self, path: str):
        from services.user.firebase_service import get_database_reference

        return get_database_reference(path)

    def get(self, path: str) -> Any:
        return self._ref(path).get()

    def update(self, path: str, values: dict[str, Any]) -> None:
        self._ref(path).update(values)

    def transaction(self, path: str, update: Callable[[Any], Any]) -> Any:
        return self._ref(path).transaction(update)


class MemoryAssignmentStore:
    """In-process store with the same semantics (tests and local tooling)."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _parts(path: str) -> list[str]:
        return [part for part in path.strip("/").split("/") if part]

    def get(self, path: str) -> Any:
        with self._lock:
            node: Any = self.data
            for part in self._parts(path):
                if not isinstance(node, dict) or part not in node:
                    return None
                node = node[part]
            return deepcopy(node)

    def _set(self, parts: list[str], value: Any) -> None:
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        if value is None:
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = deepcopy(value)

    def update(self, path: str, values: dict[str, Any]) -> None:
        with self._lock:
            base = self._parts(path)
            for key, value in values.items():
                self._set(base + self._parts(key), value)

    def transaction(self, path: str, update: Callable[[Any], Any]) -> Any:
        with self._lock:
            result = update(self.get(path))
            self._set(self._parts(path), result)
            return deepcopy(result)


_store: Any = None
_store_guard = threading.Lock()


def get_store():
    global _store
    with _store_guard:
        if _store is None:
            _store = FirebaseAssignmentStore()
        return _store


def set_store(store) -> None:
    """Replace the backend (tests use MemoryAssignmentStore)."""

    global _store
    with _store_guard:
        _store = store


# ---------------------------------------------------------------------------
# Identifiers and job-requirement signatures
# ---------------------------------------------------------------------------


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")[:60] or "x"


def _digest(value: str, length: int = 20) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def significant_tokens(text: str) -> list[str]:
    return sorted({
        token for token in re.findall(r"[a-z][a-z0-9+#.]{2,}", str(text or "").lower())
        if token not in STOPWORDS
    })


def context_signature(job_context: dict[str, Any] | None) -> dict[str, Any]:
    """What the assignment was based on, in a form that can be compared."""

    context = job_context or {}
    title = " ".join(significant_tokens(context.get("title", "")))
    tokens = significant_tokens(
        " ".join(str(context.get(key) or "") for key in ("title", "description", "responsibilities", "skills"))
    )
    return {"title": title, "tokens": tokens[:400], "digest": _digest(title + "|" + " ".join(tokens))}


def materially_changed(old: dict[str, Any] | None, new: dict[str, Any]) -> bool:
    if not isinstance(old, dict):
        return True
    if old.get("digest") == new.get("digest"):
        return False
    if old.get("title") != new.get("title"):
        return True
    before, after = set(old.get("tokens") or []), set(new.get("tokens") or [])
    if not before and not after:
        return False
    return len(before & after) / max(len(before | after), 1) < MATERIAL_SIMILARITY


def _listing_reference(job_context: dict[str, Any]) -> str:
    """A stable reference to one provider listing (URL without tracking query)."""

    url = str(job_context.get("url") or "").strip()
    if url.startswith(("https://", "http://")):
        parts = urlsplit(url)
        return f"{parts.netloc.lower()}{parts.path.rstrip('/')}"
    return "|".join(" ".join(significant_tokens(job_context.get(key, ""))) for key in ("company", "title", "location"))


def assignment_identity(
    *, career_id: str, position_id: str, company_id: str, job_context: dict[str, Any] | None
) -> dict[str, Any]:
    """Return {key, ...} for a practice company or a live listing.

    Practice companies: one assignment per company and position. Live
    listings: one per listing and position; the key also carries a digest of
    the listing's normalised requirements, so an edited listing gets its own
    assignment and a client cannot overwrite another listing's assignment by
    sending altered text.
    """

    source = str((job_context or {}).get("source") or "")
    if job_context and source not in {"", "catalog"}:
        reference = _listing_reference(job_context)
        signature = context_signature(job_context)
        key = f"listing-{_slug(source)}-{_slug(position_id)}-{_digest(reference)}-{signature['digest'][:10]}"
        return {
            "key": key, "kind": "listing", "career_id": career_id, "position_id": position_id,
            "company_id": company_id, "source": source, "listing_reference": reference,
        }
    return {
        "key": f"practice-{_slug(career_id)}-{_slug(position_id)}-{_slug(company_id)}",
        "kind": "practice", "career_id": career_id, "position_id": position_id,
        "company_id": company_id, "source": source or "catalog",
    }


# ---------------------------------------------------------------------------
# Obtaining an assignment
# ---------------------------------------------------------------------------


@dataclass
class GenerationResult:
    """What a generator returns: a validated scenario, or None on failure."""

    scenario: dict[str, Any] | None
    generation_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    failure_reason: str = ""


@dataclass
class AssignmentOutcome:
    key: str
    source: str  # "shared" (reused), "generated" (new version), "fallback"
    scenario: dict[str, Any]
    version: int | None = None
    generation_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    @property
    def is_fallback(self) -> bool:
        return self.source == "fallback"


def _now() -> float:
    return time.time()


def _iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def cooldown_seconds(failures: int) -> int:
    base = int(os.getenv("ASSIGNMENT_RETRY_COOLDOWN_SECONDS", DEFAULT_COOLDOWN_SECONDS) or DEFAULT_COOLDOWN_SECONDS)
    return min(MAX_COOLDOWN_SECONDS, max(60, base) * 2 ** max(0, failures - 1))


def _current(record: Any) -> tuple[int | None, dict[str, Any] | None]:
    if not isinstance(record, dict):
        return None, None
    number = record.get("current_version")
    versions = record.get("versions") if isinstance(record.get("versions"), dict) else {}
    version = versions.get(f"v{number}") if isinstance(number, int) else None
    if isinstance(version, dict) and isinstance(version.get("public_scenario"), dict) and isinstance(version.get("private_context"), dict):
        return number, version
    return None, None


def needs_regeneration(record: dict[str, Any] | None, version: dict[str, Any] | None, signature: dict[str, Any]) -> str:
    """Why the current version should be replaced ("" when it is fine)."""

    if version is None:
        return "missing"
    if version.get("library_version") != ASSIGNMENT_LIBRARY_VERSION:
        return "library_version"
    # A successful generation clears the request, so its presence means "not yet done".
    if isinstance((record or {}).get("regenerate"), dict):
        return "requested"
    if materially_changed(version.get("context_signature"), signature):
        return "requirements_changed"
    return ""


def _in_cooldown(record: dict[str, Any] | None, now: float) -> bool:
    failure = (record or {}).get("failure")
    return isinstance(failure, dict) and float(failure.get("cooldown_until") or 0) > now


def _claim(store, key: str, now: float) -> str | None:
    token = uuid.uuid4().hex

    def update(current):
        if isinstance(current, dict) and float(current.get("expires_at") or 0) > now:
            return current
        return {"token": token, "expires_at": now + LOCK_SECONDS}

    result = store.transaction(f"{LIBRARY_PATH}/{key}/lock", update)
    return token if isinstance(result, dict) and result.get("token") == token else None


def _release(store, key: str, token: str) -> None:
    def update(current):
        if isinstance(current, dict) and current.get("token") == token:
            return None
        return current

    try:
        store.transaction(f"{LIBRARY_PATH}/{key}/lock", update)
    except Exception:
        pass  # the lock expires on its own


def _shared(key: str, number: int, version: dict[str, Any], source: str = "shared") -> AssignmentOutcome:
    return AssignmentOutcome(
        key=key, source=source, version=number,
        scenario={"public_scenario": deepcopy(version["public_scenario"]), "private_context": deepcopy(version["private_context"])},
        generation_count=int((version.get("generation") or {}).get("attempt_count") or 0) if source == "generated" else 0,
        details=deepcopy(version.get("generation") or {}),
    )


def _record_fallback(store, key: str, reason: str, now: float) -> None:
    try:
        record = store.get(f"{LIBRARY_PATH}/{key}/fallbacks") or {}
        store.update(f"{LIBRARY_PATH}/{key}", {"fallbacks": {
            "count": int(record.get("count") or 0) + 1, "last_at": _iso(now), "last_reason": reason,
        }})
    except Exception:
        pass  # bookkeeping only


def obtain_assignment(
    *,
    identity: dict[str, Any],
    job_context: dict[str, Any] | None,
    generate: Callable[[str], GenerationResult],
    fallback: Callable[[], dict[str, Any]],
    wait_seconds: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    store=None,
) -> AssignmentOutcome:
    """Return the saved assignment, generating it once when needed.

    ``generate(scenario_id)`` runs the bounded generation pipeline. Only one
    caller per key generates at a time; concurrent callers wait for its result
    (up to ``wait_seconds``) instead of starting a second generation.
    """

    store = store or get_store()
    key = identity["key"]
    path = f"{LIBRARY_PATH}/{key}"
    signature = context_signature(job_context)
    wait_seconds = LOCK_SECONDS if wait_seconds is None else wait_seconds
    deadline = _now() + wait_seconds
    while True:
        now = _now()
        record = store.get(path)
        number, version = _current(record)
        reason = needs_regeneration(record, version, signature)
        if not reason:
            return _shared(key, number, version)
        if _in_cooldown(record, now):
            if version is not None:
                return _shared(key, number, version)  # older version stays valid
            _record_fallback(store, key, "cooldown", now)
            return AssignmentOutcome(key=key, source="fallback", scenario=fallback(), reason="cooldown")
        token = _claim(store, key, now)
        if token:
            break
        if _now() >= deadline:
            if version is not None:
                return _shared(key, number, version)
            _record_fallback(store, key, "wait_timeout", now)
            return AssignmentOutcome(key=key, source="fallback", scenario=fallback(), reason="wait_timeout")
        sleep(POLL_SECONDS)

    try:
        # Another server may have finished while this one waited for the lock.
        record = store.get(path)
        number, version = _current(record)
        reason = needs_regeneration(record, version, signature)
        if not reason:
            return _shared(key, number, version)
        next_number = (number or 0) + 1
        try:
            result = generate(f"{key}-v{next_number}")
        except Exception as error:  # a generator bug must not block the participant
            result = GenerationResult(None, failure_reason=f"error:{type(error).__name__}")
        now = _now()
        if result.scenario is None:
            failures = int(((record or {}).get("failure") or {}).get("count") or 0) + 1
            store.update(path, {
                "identity": {k: v for k, v in identity.items() if k != "key"},
                "failure": {
                    "count": failures,
                    "last_reason": result.failure_reason or str(result.details.get("failure_reason") or "generation_failed"),
                    "last_at": _iso(now),
                    "cooldown_until": now + cooldown_seconds(failures),
                },
            })
            if version is not None:
                return _shared(key, number, version)
            _record_fallback(store, key, "generation_failed", now)
            return AssignmentOutcome(
                key=key, source="fallback", scenario=fallback(), details=result.details,
                reason=result.failure_reason or "generation_failed",
            )
        saved = {
            "version": next_number,
            "public_scenario": deepcopy(result.scenario["public_scenario"]),
            "private_context": deepcopy(result.scenario["private_context"]),
            "generation": {**deepcopy(result.details), "attempt_count": result.generation_count},
            "context_signature": signature,
            "library_version": ASSIGNMENT_LIBRARY_VERSION,
            "created_at": _iso(now),
            "replaces": number,
            "replace_reason": reason,
        }
        store.update(path, {
            "identity": {k: v for k, v in identity.items() if k != "key"},
            f"versions/v{next_number}": saved,
            "current_version": next_number,
            "failure": None,
            "regenerate": None,
        })
        return _shared(key, next_number, saved, source="generated")
    finally:
        _release(store, key, token)


# ---------------------------------------------------------------------------
# Deliberate regeneration (scripts/manage_assignments.py)
# ---------------------------------------------------------------------------


def request_regeneration(key: str, reason: str = "manual", store=None) -> None:
    """Replace the assignment on its next launch; existing attempts keep theirs."""

    store = store or get_store()
    store.update(f"{LIBRARY_PATH}/{key}", {
        "regenerate": {"requested_at": _iso(_now()), "reason": str(reason)[:200]},
        "failure": None,
    })


def list_assignments(store=None) -> list[dict[str, Any]]:
    store = store or get_store()
    records = store.get(LIBRARY_PATH) or {}
    rows = []
    for key, record in records.items() if isinstance(records, dict) else []:
        number, version = _current(record)
        failure = record.get("failure") if isinstance(record.get("failure"), dict) else {}
        fallbacks = record.get("fallbacks") if isinstance(record.get("fallbacks"), dict) else {}
        rows.append({
            "key": key,
            "current_version": number,
            "title": ((version or {}).get("public_scenario") or {}).get("title", ""),
            "created_at": (version or {}).get("created_at", ""),
            "versions": len(record.get("versions") or {}) if isinstance(record.get("versions"), dict) else 0,
            "failures": failure.get("count", 0),
            "cooldown_until": _iso(failure["cooldown_until"]) if failure.get("cooldown_until") else "",
            "fallbacks": fallbacks.get("count", 0),
            "regenerate_requested": bool(record.get("regenerate")),
        })
    return sorted(rows, key=lambda row: row["key"])
