from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_orchestrator_is_scoped_to_frontend_position():
    source = (ROOT / "static/js/simulation/frontend_workplace.js").read_text(encoding="utf-8")
    assert 'workspace.dataset.positionId !== "frontend-developer"' in source


def test_desktop_keeps_existing_apps_and_adds_frontend_layer():
    template = (ROOT / "templates/desktop.html").read_text(encoding="utf-8")
    for app in ("mail", "browser", "vscode", "terminal", "github"):
        assert f'data-app="{app}"' in template
    assert "frontend_workplace.js" in template
