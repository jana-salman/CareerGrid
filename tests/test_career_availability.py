from unittest.mock import Mock

import pytest

import app as careergrid_app


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
    response = client.get("/career")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/positions/software-developer"' in page
    assert 'href="/positions/ui-ux-designer"' not in page
    assert 'href="/positions/data-analyst"' not in page
    assert page.count("Coming Soon") == 2
    assert page.count("coming-soon-control") == 2
    assert page.count("disabled") == 2


def test_implemented_developer_positions_remain_active(client):
    response = client.get("/positions/software-developer")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/positions/software-developer/backend-developer"' in page
    assert 'href="/positions/software-developer/frontend-developer"' in page
    assert "Coming Soon" not in page


@pytest.mark.parametrize(
    ("path", "titles", "expected_count"),
    [
        (
            "/positions/ui-ux-designer",
            ("UX Designer", "UI Designer"),
            2,
        ),
        ("/positions/data-analyst", ("Data Analyst",), 1),
    ],
)
def test_unfinished_positions_render_disabled_coming_soon_controls(
    client,
    path,
    titles,
    expected_count,
):
    response = client.get(path)
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert all(title in page for title in titles)
    assert page.count("Coming Soon") == expected_count
    assert page.count("coming-soon-control") == expected_count
    assert page.count("disabled") == expected_count
    assert "View Companies" not in page


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
        careergrid_app,
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
    monkeypatch.setattr(careergrid_app, "fetch_adzuna_jobs", lambda *args, **kwargs: [])

    response = client.get(
        f"/positions/software-developer/{position_id}"
    )

    assert response.status_code == 200
