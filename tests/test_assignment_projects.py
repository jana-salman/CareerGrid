"""Execute the built-in starter projects for real (outside CareerGrid).

These tests prove the demo/fallback assignments are coherent: the starter's
own tests pass, the reported defects reproduce exactly as the evidence says,
and a reasonable fix satisfies the acceptance criteria and the private checks.
The reference fixes live only here, never in user-visible files.
"""

import json
import shutil
import subprocess
import sys

import pytest

from services.ai.scenario_quality import check_passes
from services.simulation.backend_demo_scenario_service import get_backend_demo_workplace_scenario
from services.simulation.frontend_workplace_scenario_service import deterministic_frontend_scenario


def _write(root, files):
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def _run(cwd, *args):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)


PROBE = (
    "import json\n"
    "from app import create_app\n"
    "client = create_app().test_client()\n"
    "urls = ['/api/users/101', '/api/users/1842', '/api/users/103', '/api/users/118', '/api/users/230',\n"
    "        '/api/users/207', '/api/users?team=platform', '/api/users?team=platform&page=5&page_size=2']\n"
    "out = {}\n"
    "for url in urls:\n"
    "    response = client.get(url)\n"
    "    out[url] = [response.status_code, response.get_json(silent=True)]\n"
    "print(json.dumps(out))\n"
)


def _backend_reference_fix(files):
    fixed = dict(files)
    fixed["services/visibility.py"] = files["services/visibility.py"] + (
        "\n\ndef is_available(user):\n"
        "    return user.get(\"active\", False) and not user.get(\"deleted_at\")\n"
    )
    fixed["services/user_service.py"] = files["services/user_service.py"].replace(
        "from services.visibility import is_listed",
        "from services.visibility import is_available, is_listed",
    ).replace(
        'if user["id"] == user_id), None)',
        'if user["id"] == user_id and is_available(user)), None)',
    ).replace(
        "    total = len(users)\n    listed = [user for user in users if is_listed(user)]",
        "    listed = [user for user in users if is_available(user) and is_listed(user)]\n    total = len(listed)",
    )
    fixed["api/profiles.py"] = files["api/profiles.py"].replace(
        "    user = find_user(user_id)\n",
        "    user = find_user(user_id)\n    if user is None:\n"
        "        raise ApiError(404, \"user_not_found\", \"User not found.\")\n",
    )
    fixed["tests/test_profiles.py"] = files["tests/test_profiles.py"] + (
        "\n\n@pytest.mark.parametrize('user_id', [1842, 103, 118])\n"
        "def test_unavailable_profiles_return_404(client, user_id):\n"
        "    response = client.get(f'/api/users/{user_id}')\n"
        "    assert response.status_code == 404\n"
        "    assert response.get_json()['error']['code'] == 'user_not_found'\n"
    )
    return fixed


def test_backend_demo_project_runs_and_matches_its_evidence(tmp_path):
    pytest.importorskip("flask")
    scenario = get_backend_demo_workplace_scenario(attempt_id="exec")
    files = {item["path"]: item["content"] for item in scenario["public_scenario"]["project"]["files"]}

    starter = tmp_path / "starter"
    _write(starter, files)
    result = _run(starter, sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "5 passed" in result.stdout

    observed = json.loads(_run(starter, sys.executable, "-c", PROBE).stdout)
    assert observed["/api/users/101"][0] == 200
    assert observed["/api/users/1842"][0] == 500          # Case 1 in production-error.log
    assert observed["/api/users/103"][0] == 200           # Case 2
    assert observed["/api/users/118"][0] == 200           # SUP-2291: closed account still opens
    assert observed["/api/users?team=platform"][1]["total"] == 5   # SUP-2291 "of 5"
    assert len(observed["/api/users?team=platform"][1]["items"]) == 4

    fixed_files = _backend_reference_fix(files)
    fixed = tmp_path / "fixed"
    _write(fixed, fixed_files)
    result = _run(fixed, sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider")
    assert result.returncode == 0, result.stdout + result.stderr
    after = json.loads(_run(fixed, sys.executable, "-c", PROBE).stdout)
    for url in ("/api/users/1842", "/api/users/103", "/api/users/118"):
        assert after[url] == [404, {"error": {"code": "user_not_found", "message": "User not found."}}]
    assert after["/api/users/230"][0] == 200                       # private profile preserved
    assert "email" not in after["/api/users/207"][1]               # contact hiding preserved
    assert [item["id"] for item in after["/api/users?team=platform"][1]["items"]] == [101, 241]
    assert after["/api/users?team=platform"][1]["total"] == 2
    assert after["/api/users?team=platform&page=5&page_size=2"][1] == {"items": [], "page": 5, "page_size": 2, "total": 2}

    checks = scenario["private_context"]["starter_gap_checks"]
    assert not any(check_passes(check, files) for check in checks)
    assert all(check_passes(check, fixed_files) for check in checks)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_frontend_fallback_project_tests_run_and_scripts_parse(tmp_path):
    scenario = deterministic_frontend_scenario("Example", "exec")
    files = {item["path"]: item["content"] for item in scenario["public_scenario"]["project"]["files"]}
    _write(tmp_path, files)
    for path in files:
        if path.endswith(".js"):
            assert _run(tmp_path, "node", "--check", path).returncode == 0, path
    result = _run(tmp_path, "node", "--test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "pass 3" in result.stdout
