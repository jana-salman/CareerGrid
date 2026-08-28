import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        '<!doctype html><div id="react-spa-test">CareerGrid React</div>',
        encoding="utf-8",
    )
    (assets / "app-test.js").write_text("window.CareerGrid = true;", encoding="utf-8")
    application = create_app(
        {
            "FRONTEND_DIST_DIR": dist,
            "SECRET_KEY": "spa-route-test-key",
            "TESTING": True,
        }
    )
    with application.test_client() as test_client:
        yield test_client


def authenticate(client):
    with client.session_transaction() as user_session:
        user_session["user_id"] = "spa-user"
        user_session["user_email"] = "spa@example.com"
        user_session["user_name"] = "SPA User"


@pytest.mark.parametrize("path", ["/login", "/register"])
def test_public_react_routes_serve_the_vite_entry_document(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert "react-spa-test" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/dashboard",
        "/career",
        "/positions/software-developer",
        "/positions/software-developer/backend-developer",
        "/workspace/software-developer/backend-developer/careergrid-demo",
        "/workspace/attempt/attempt-1",
        "/simulation/attempts/attempt-1/report",
        "/interview/interview-1",
        "/interview/interview-1/review",
        "/future/react/deep-link",
    ],
)
def test_authenticated_react_routes_and_deep_links_serve_spa(client, path):
    authenticate(client)

    response = client.get(path)

    assert response.status_code == 200
    assert "react-spa-test" in response.get_data(as_text=True)


def test_vite_assets_are_public_and_served_from_generated_dist(client):
    response = client.get("/assets/app-test.js")

    assert response.status_code == 200
    assert response.mimetype == "application/javascript"
    assert response.get_data(as_text=True) == "window.CareerGrid = true;"


def test_unknown_api_route_remains_json_and_is_not_spa_html(client):
    authenticate(client)

    response = client.get("/api/not-a-real-endpoint")

    assert response.status_code == 404
    assert response.is_json
    assert "react-spa-test" not in response.get_data(as_text=True)


def test_spa_fallback_does_not_swallow_backend_post_routes(client):
    authenticate(client)

    missing_api = client.post("/api/not-a-real-endpoint")
    workplace_action = client.post("/simulation/workplace/start", data={})

    assert missing_api.status_code == 405
    assert missing_api.is_json
    assert "react-spa-test" not in missing_api.get_data(as_text=True)
    assert workplace_action.status_code == 302
    assert "react-spa-test" not in workplace_action.get_data(as_text=True)
