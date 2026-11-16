"""Shared test setup."""

import pytest

from services.simulation import assignment_library


@pytest.fixture(autouse=True)
def assignment_store():
    """Shared assignments live in memory during tests, never in real Firebase."""

    store = assignment_library.MemoryAssignmentStore()
    assignment_library.set_store(store)
    yield store
    assignment_library.set_store(None)


@pytest.fixture(autouse=True)
def no_candidate_archive(monkeypatch):
    """Tests never write generation candidates into instance/; archive tests opt in."""

    monkeypatch.setenv("SCENARIO_CANDIDATE_ARCHIVE", "0")
