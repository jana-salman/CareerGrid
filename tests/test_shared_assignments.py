"""One saved assignment per company/listing and position, reused by attempts.

The model call is mocked; these tests cover persistence, reuse, concurrency,
fallback recovery, versioning, and compatibility with existing attempts.
"""

import threading
import time
from copy import deepcopy
from unittest.mock import Mock

import pytest

import routes.simulations as simulation_routes
from app import create_app
from services.simulation import assignment_library as library
from services.simulation.assignment_library import (
    GenerationResult,
    assignment_identity,
    obtain_assignment,
    request_regeneration,
)
from services.simulation.backend_demo_scenario_service import get_backend_demo_workplace_scenario
from services.simulation.job_context_service import build_catalog_job_context, build_job_context

PRACTICE = dict(career_id="software-developer", position_id="backend-developer", company_id="technova")


def _scenario(tag="generated"):
    scenario = get_backend_demo_workplace_scenario(attempt_id=tag)
    scenario["public_scenario"]["title"] = f"Assignment {tag}"
    return scenario


def _generator(*results, delay=0.0):
    calls = []

    def generate(scenario_id):
        calls.append(scenario_id)
        if delay:
            time.sleep(delay)
        result = results[min(len(calls) - 1, len(results) - 1)]
        return result if isinstance(result, GenerationResult) else GenerationResult(result, 1, {"model": "m"})

    generate.calls = calls
    return generate


def _fallback():
    scenario = _scenario("fallback")
    scenario["public_scenario"]["scenario_id"] = "built-in-fallback"
    return scenario


def _practice_identity():
    return assignment_identity(**PRACTICE, job_context=build_catalog_job_context("backend-developer", "technova"))


def _obtain(generate, store, *, context=None, **kwargs):
    context = context or build_catalog_job_context("backend-developer", "technova")
    identity = assignment_identity(**PRACTICE, job_context=context)
    return obtain_assignment(identity=identity, job_context=context, generate=generate, fallback=_fallback, store=store, **kwargs)


# --- identifiers -----------------------------------------------------------


def test_practice_and_listing_identifiers_are_stable():
    practice = _practice_identity()
    assert practice["key"] == "practice-software-developer-backend-developer-technova"
    assert practice["kind"] == "practice"

    listing = {"title": "Backend Developer", "company": "Acme", "description": "Build Python REST APIs with PostgreSQL. " * 30,
               "url": "https://www.adzuna.com.lb/land/ad/4123?se=abc&utm_source=x"}
    first = assignment_identity(**PRACTICE, job_context=build_job_context("adzuna", listing))
    # The same listing seen through a different search (tracking query) keeps its key.
    same = assignment_identity(**PRACTICE, job_context=build_job_context("adzuna", {**listing, "url": "https://www.adzuna.com.lb/land/ad/4123?se=zzz"}))
    other = assignment_identity(**PRACTICE, job_context=build_job_context("adzuna", {**listing, "url": "https://www.adzuna.com.lb/land/ad/9999"}))
    edited = assignment_identity(**PRACTICE, job_context=build_job_context("adzuna", {**listing, "description": "Maintain Go microservices on Kubernetes. " * 30}))
    other_role = assignment_identity(**{**PRACTICE, "position_id": "frontend-developer"}, job_context=build_job_context("adzuna", listing))
    assert first["kind"] == "listing" and first["key"] == same["key"]
    assert len({first["key"], other["key"], edited["key"], other_role["key"]}) == 4
    for identity in (practice, first):
        assert not any(char in identity["key"] for char in ".#$[]/"), "keys must be valid Firebase keys"


# --- first generation, reuse, and independence ------------------------------


def test_first_launch_generates_once_and_later_launches_reuse_without_a_model_call(assignment_store):
    generate = _generator(_scenario("v1"))
    first = _obtain(generate, assignment_store)
    second = _obtain(generate, assignment_store)
    assert (first.source, first.version) == ("generated", 1)
    assert (second.source, second.version) == ("shared", 1)
    assert generate.calls == ["practice-software-developer-backend-developer-technova-v1"]
    assert second.scenario == first.scenario

    # Each caller gets its own copy: edits never reach the saved assignment.
    second.scenario["public_scenario"]["project"]["files"][0]["content"] = "edited by a participant"
    second.scenario["private_context"]["root_cause"] = "tampered"
    saved = assignment_store.get(f"shared_assignments/{first.key}/versions/v1")
    assert saved["public_scenario"]["project"]["files"][0]["content"] != "edited by a participant"
    assert saved["private_context"]["root_cause"] != "tampered"


@pytest.fixture
def client():
    application = create_app({"TESTING": True, "SECRET_KEY": "shared-assignments"})
    test_client = application.test_client()
    with test_client.session_transaction() as user_session:
        user_session["user_id"] = "user-1"
        user_session["user_email"] = "user@example.com"
    return test_client


@pytest.fixture
def attempts(monkeypatch):
    records = {}

    def create(**kwargs):
        attempt_id = f"attempt-{len(records) + 1}"
        records[attempt_id] = {"simulation_mode": "workplace", "status": "generating", **deepcopy(kwargs)}
        return attempt_id

    def save(**kwargs):
        records[kwargs["attempt_id"]].update(
            status="in_progress",
            public_scenario=deepcopy(kwargs["public_scenario"]),
            private_context=deepcopy(kwargs["private_context"]),
            generation={**deepcopy(kwargs["generation_details"]), "source": kwargs["generation_source"]},
        )

    monkeypatch.setattr(simulation_routes, "create_workplace_simulation_attempt", create)
    monkeypatch.setattr(simulation_routes, "save_workplace_scenario", save)
    monkeypatch.setattr(simulation_routes, "get_simulation_attempt", lambda **kwargs: records.get(kwargs["attempt_id"]))
    return records


def _start(client, request_id, **overrides):
    body = {**PRACTICE, "job_source": "demo", "client_request_id": request_id, **overrides}
    return client.post("/api/simulation/workplace/start", json=body)


def test_separate_attempts_share_one_saved_assignment_with_independent_records(client, attempts, monkeypatch):
    generator = Mock(return_value=(_scenario("shared"), 2))
    monkeypatch.setattr(simulation_routes, "generate_workplace_scenario", generator)

    first = _start(client, "request-aaaa-0001")
    second = _start(client, "request-aaaa-0002")
    assert first.status_code == second.status_code == 201
    assert generator.call_count == 1, "the second attempt must reuse the saved assignment"
    one, two = attempts["attempt-1"], attempts["attempt-2"]
    assert one["public_scenario"] == two["public_scenario"]
    assert one["public_scenario"] is not two["public_scenario"]
    assert one["generation"]["assignment_source"] == "generated" and two["generation"]["assignment_source"] == "shared"
    assert one["generation"]["assignment_version"] == two["generation"]["assignment_version"] == 1
    assert one["generation"]["source"] == two["generation"]["source"] == "gemini"

    # Work in one attempt never changes the other or the saved assignment.
    one["responses"] = {"step_1": {"written_response": "mine"}}
    one["public_scenario"]["task"]["body"] = "changed"
    assert "responses" not in two and two["public_scenario"]["task"]["body"] != "changed"
    third = _start(client, "request-aaaa-0003")
    assert third.status_code == 201 and attempts["attempt-3"]["public_scenario"]["task"]["body"] != "changed"

    # The browser-facing attempt API never includes the private assessment.
    payload = client.get("/api/simulation/attempts/attempt-2").get_json()
    assert "private_context" not in payload and payload["public_scenario"]["title"] == "Assignment shared"


def test_reopening_returns_the_same_attempt_and_try_again_starts_a_clean_one(client, attempts, monkeypatch):
    generator = Mock(return_value=(_scenario("shared"), 1))
    monkeypatch.setattr(simulation_routes, "generate_workplace_scenario", generator)
    _start(client, "request-bbbb-0001")
    attempts["attempt-1"].update(status="completed", responses={"step_5": {"commit_message": "done"}}, evaluation={"overall_score": 70})

    # Reopening (same launch request) keeps the attempt and its work.
    reopened = _start(client, "request-bbbb-0001")
    assert reopened.get_json()["attempt_id"] == "attempt-1"
    assert attempts["attempt-1"]["responses"] == {"step_5": {"commit_message": "done"}}

    # Try again (report button): a new attempt with the same assignment and nothing else.
    retry = client.post("/simulation/workplace/start", data={**PRACTICE, "job_source": "demo", "retry_attempt_id": "attempt-1"})
    assert retry.status_code == 302 and retry.headers["Location"].endswith("/workspace/attempt/attempt-2")
    fresh = attempts["attempt-2"]
    assert fresh["public_scenario"] == attempts["attempt-1"]["public_scenario"]
    assert fresh["status"] == "in_progress" and "responses" not in fresh and "evaluation" not in fresh
    assert fresh["generation"]["reused_from_attempt"] == "attempt-1"
    assert attempts["attempt-1"]["evaluation"] == {"overall_score": 70}

    api_retry = client.post("/api/simulation/attempts/attempt-1/retry")
    assert api_retry.status_code == 201 and attempts["attempt-3"]["public_scenario"] == fresh["public_scenario"]
    assert generator.call_count == 1


# --- concurrency -------------------------------------------------------------


def test_concurrent_requests_generate_only_once(assignment_store):
    generate = _generator(_scenario("v1"), delay=0.3)
    results, errors = [], []

    def launch():
        try:
            results.append(_obtain(generate, assignment_store, sleep=lambda _: time.sleep(0.02)))
        except Exception as error:  # pragma: no cover - reported below
            errors.append(error)

    threads = [threading.Thread(target=launch) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    assert not errors
    assert len(generate.calls) == 1
    assert sorted(item.source for item in results) == ["generated"] + ["shared"] * 5
    assert {item.version for item in results} == {1}
    assert assignment_store.get(f"shared_assignments/{results[0].key}/lock") is None, "the lock is released"


def test_a_waiting_request_uses_the_fallback_if_another_server_never_finishes(assignment_store):
    key = _practice_identity()["key"]
    assignment_store.update(f"shared_assignments/{key}", {"lock": {"token": "other-server", "expires_at": time.time() + 600}})
    generate = _generator(_scenario())
    outcome = _obtain(generate, assignment_store, wait_seconds=0, sleep=lambda _: None)
    assert outcome.source == "fallback" and outcome.reason == "wait_timeout"
    assert generate.calls == []
    # An expired lock (crashed server) does not block generation.
    assignment_store.update(f"shared_assignments/{key}", {"lock": {"token": "other-server", "expires_at": time.time() - 1}})
    assert _obtain(generate, assignment_store).source == "generated"


# --- fallback recovery and versioning ------------------------------------------


def test_failures_use_the_fallback_without_caching_it_and_cool_down(assignment_store):
    failing = _generator(GenerationResult(None, 0, {"failure_reason": "quota_exhausted"}, "quota_exhausted"))
    outcome = _obtain(failing, assignment_store)
    assert outcome.source == "fallback" and outcome.scenario["public_scenario"]["scenario_id"] == "built-in-fallback"
    record = assignment_store.get(f"shared_assignments/{outcome.key}")
    assert "versions" not in record and "current_version" not in record, "a fallback is never saved as generated"
    assert record["failure"]["count"] == 1 and record["failure"]["last_reason"] == "quota_exhausted"
    assert record["fallbacks"]["count"] == 1

    # During the cooldown, launches continue with the fallback without calling Gemini.
    again = _obtain(failing, assignment_store)
    assert again.source == "fallback" and again.reason == "cooldown" and len(failing.calls) == 1
    assert assignment_store.get(f"shared_assignments/{outcome.key}/fallbacks")["count"] == 2

    # After the cooldown the next launch tries again; success clears the failure.
    assignment_store.update(f"shared_assignments/{outcome.key}/failure", {"cooldown_until": time.time() - 1})
    recovered = _obtain(_generator(_scenario("v1")), assignment_store)
    assert (recovered.source, recovered.version) == ("generated", 1)
    assert assignment_store.get(f"shared_assignments/{outcome.key}/failure") is None


def test_cooldown_grows_with_consecutive_failures_and_is_capped(monkeypatch):
    monkeypatch.setenv("ASSIGNMENT_RETRY_COOLDOWN_SECONDS", "600")
    assert [library.cooldown_seconds(n) for n in (1, 2, 3)] == [600, 1200, 2400]
    assert library.cooldown_seconds(20) == library.MAX_COOLDOWN_SECONDS


def test_regeneration_creates_a_new_version_and_keeps_older_attempt_copies(assignment_store):
    first = _obtain(_generator(_scenario("v1")), assignment_store)
    attempt_copy = deepcopy(first.scenario)

    request_regeneration(first.key, "job requirements changed")
    replaced = _obtain(_generator(_scenario("v2")), assignment_store)
    assert (replaced.source, replaced.version) == ("generated", 2)
    record = assignment_store.get(f"shared_assignments/{first.key}")
    assert record["current_version"] == 2 and set(record["versions"]) == {"v1", "v2"}
    assert record["versions"]["v2"]["replace_reason"] == "requested"
    assert record["versions"]["v1"]["public_scenario"] == attempt_copy["public_scenario"]
    assert _obtain(_generator(_scenario("never")), assignment_store).version == 2


def test_a_failed_regeneration_keeps_serving_the_previous_version(assignment_store):
    first = _obtain(_generator(_scenario("v1")), assignment_store)
    request_regeneration(first.key)
    failing = _generator(GenerationResult(None, 0, {}, "timeout"))
    outcome = _obtain(failing, assignment_store)
    assert (outcome.source, outcome.version) == ("shared", 1)
    assert _obtain(failing, assignment_store).version == 1 and len(failing.calls) == 1  # cooldown


def test_only_material_profile_changes_replace_a_practice_assignment(assignment_store):
    context = build_catalog_job_context("backend-developer", "technova")
    _obtain(_generator(_scenario("v1")), assignment_store, context=context)
    reworded = {**context, "description": context["description"].upper() + "  "}
    assert _obtain(_generator(_scenario("x")), assignment_store, context=reworded).version == 1
    changed = {**context, "description": "Build streaming data pipelines in Scala with Kafka and Spark for analytics teams."}
    assert _obtain(_generator(_scenario("v2")), assignment_store, context=changed).version == 2


def test_a_library_version_bump_regenerates_on_next_launch(assignment_store, monkeypatch):
    _obtain(_generator(_scenario("v1")), assignment_store)
    monkeypatch.setattr(library, "ASSIGNMENT_LIBRARY_VERSION", library.ASSIGNMENT_LIBRARY_VERSION + 1)
    assert _obtain(_generator(_scenario("v2")), assignment_store).version == 2


def test_route_fallback_is_recorded_separately_and_not_cached(client, attempts, monkeypatch):
    from services.ai.scenario_generation_service import ScenarioGenerationError

    generator = Mock(side_effect=ScenarioGenerationError("toy"))
    monkeypatch.setattr(simulation_routes, "generate_workplace_scenario", generator)
    response = _start(client, "request-cccc-0001")
    assert response.status_code == 201
    attempt = attempts["attempt-1"]
    assert attempt["generation"]["source"] == "fallback"
    assert attempt["generation"]["assignment_source"] == "fallback"
    assert attempt["generation"]["assignment_version"] is None
    assert "built-in assignment" in attempt["public_scenario"]["simulation_notice"]
    key = attempt["generation"]["assignment_key"]
    assert library.get_store().get(f"shared_assignments/{key}/current_version") is None

    _start(client, "request-cccc-0002")  # inside the cooldown: no second Gemini call
    assert generator.call_count == 1 and attempts["attempt-2"]["generation"]["source"] == "fallback"


# --- compatibility -----------------------------------------------------------------


def test_existing_attempts_keep_working_and_can_be_retried(client, attempts):
    legacy_scenario = _scenario("legacy")
    attempts["legacy-1"] = {
        "simulation_mode": "workplace", **PRACTICE, "status": "in_progress",
        "public_scenario": legacy_scenario["public_scenario"], "private_context": legacy_scenario["private_context"],
        "generation": {"source": "gemini", "archetype": "old rotation", "domain": "old"},
    }
    before = deepcopy(attempts["legacy-1"])
    reopened = client.get("/api/simulation/attempts/legacy-1").get_json()
    assert reopened["public_scenario"]["title"] == "Assignment legacy"

    retry = client.post("/api/simulation/attempts/legacy-1/retry")
    assert retry.status_code == 201
    new = attempts[retry.get_json()["attempt_id"]]
    assert new["public_scenario"] == before["public_scenario"]
    assert attempts["legacy-1"] == before, "the existing attempt is unchanged"
    assert client.post("/api/simulation/attempts/missing/retry").status_code == 404


def test_frontend_restart_reuses_the_assignment_without_generation(client, attempts, monkeypatch):
    from services.simulation.frontend_workplace_scenario_service import deterministic_frontend_scenario

    scenario = deterministic_frontend_scenario("PixelWorks", "x")
    attempts["fe-1"] = {
        "simulation_mode": "workplace", "career_id": "software-developer", "position_id": "frontend-developer",
        "company_id": "pixelworks", "status": "completed", "responses": {"step_1": {}},
        "public_scenario": scenario["public_scenario"], "private_context": scenario["private_context"],
    }
    monkeypatch.setattr(simulation_routes, "generate_frontend_workplace_scenario", Mock(side_effect=AssertionError("no generation")))
    response = client.post("/api/simulation/attempts/fe-1/frontend/restart")
    assert response.status_code == 201
    new = attempts[response.get_json()["attempt_id"]]
    assert new["public_scenario"] == scenario["public_scenario"] and "responses" not in new
