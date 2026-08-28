from unittest.mock import Mock

import pytest

import app as careergrid_app
import routes.careers as career_routes
import routes.simulations as simulation_routes


@pytest.fixture
def client():
    careergrid_app.app.config.update(TESTING=True)
    with careergrid_app.app.test_client() as test_client:
        with test_client.session_transaction() as user_session:
            user_session["user_id"] = "availability-user"
            user_session["user_email"] = "availability@example.com"
            user_session["user_name"] = "Availability User"
        yield test_client


def test_career_cards_only_link_to_an_implemented_path(client):
    response = client.get("/api/careers")
    careers = response.get_json()["careers"]

    assert response.status_code == 200
    availability = {item["id"]: item["available"] for item in careers}
    assert availability == {
        "software-developer": True,
        "ui-ux-designer": False,
        "data-analyst": False,
    }


def test_implemented_developer_positions_remain_active(client):
    response = client.get("/api/careers/software-developer/positions")
    positions = response.get_json()["positions"]

    assert response.status_code == 200
    assert {(item["id"], item["available"]) for item in positions} == {
        ("backend-developer", True),
        ("frontend-developer", True),
    }


@pytest.mark.parametrize(
    ("career_id", "titles", "expected_count"),
    [
        (
            "ui-ux-designer",
            ("UX Designer", "UI Designer"),
            2,
        ),
        ("data-analyst", ("Data Analyst",), 1),
    ],
)
def test_unfinished_positions_render_disabled_coming_soon_controls(
    client,
    career_id,
    titles,
    expected_count,
):
    response = client.get(f"/api/careers/{career_id}/positions")
    positions = response.get_json()["positions"]

    assert response.status_code == 200
    assert tuple(item["title"] for item in positions) == titles
    assert len(positions) == expected_count
    assert all(item["available"] is False for item in positions)


@pytest.mark.parametrize(
    ("path", "expected_location"),
    [
        (
            "/positions/ui-ux-designer/ux-designer",
            "/positions/ui-ux-designer",
        ),
        (
            "/workspace/data-analyst/data-analyst/insightlab",
            "/positions/data-analyst",
        ),
    ],
)
def test_direct_unfinished_workflow_urls_redirect_safely(
    client,
    path,
    expected_location,
):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith(expected_location)


def test_unfinished_position_cannot_create_an_attempt(client, monkeypatch):
    create_attempt = Mock(
        side_effect=AssertionError("Coming Soon role created an attempt")
    )
    monkeypatch.setattr(
        simulation_routes,
        "create_workplace_simulation_attempt",
        create_attempt,
    )

    response = client.post(
        "/simulation/workplace/start",
        data={
            "career_id": "ui-ux-designer",
            "position_id": "ui-designer",
            "company_id": "pixelcraft",
            "job_source": "demo",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/positions/ui-ux-designer"
    )
    create_attempt.assert_not_called()


@pytest.mark.parametrize(
    "position_id",
    ["backend-developer", "frontend-developer"],
)
def test_implemented_company_routes_still_render(
    client,
    monkeypatch,
    position_id,
):
    monkeypatch.setattr(career_routes, "fetch_adzuna_jobs", lambda *args, **kwargs: [])

    response = client.get(
        f"/positions/software-developer/{position_id}"
    )

    assert response.status_code == 200
