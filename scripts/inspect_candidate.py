"""Inspect an archived, accepted generation candidate.

Usage:
    python scripts/inspect_candidate.py instance/generation_candidates/<day>/<run>

Prints the brief, requirements, evidence, file list, and private rubric side
by side for manual review, then writes the starter project to a temporary
directory and runs its existing tests (pytest or node --test). The existing
tests must pass on the starter; the starter-gap checks and patch checks are
re-evaluated against the starter files.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.ai.scenario_quality import check_passes, quality_signals  # noqa: E402

run_dir = Path(sys.argv[1])
accepted = sorted(run_dir.glob("*-accepted.json"))
final = next((json.loads(path.read_text(encoding="utf-8")) for path in reversed(accepted)), None)
if not final or not final.get("output"):
    sys.exit(f"No accepted scenario in {run_dir}")
scenario = final["output"]
public, private = scenario["public_scenario"], scenario["private_context"]
task = public["task"]
files = {item["path"]: item["content"] for item in public["project"]["files"]}

print("=" * 80)
print("TITLE:", public["title"])
print("COMPANY:", public["company_name"], "| PROJECT:", public["project"]["display_name"])
print("\nEMAIL:\n", task["body"])
print("\nREQUIREMENTS:")
for number, item in enumerate(task["requirements"], 1):
    print(f"  {number}. {item}")
print("ACCEPTANCE:", *[f"\n  - {item}" for item in task["acceptance_criteria"]])
print("DELIVERABLES:", *[f"\n  - {item}" for item in task["deliverables"]])
print("\nFILES:")
for path, content in files.items():
    print(f"  {path} ({len(content.splitlines())} lines)")
print("\nEVIDENCE:")
for item in public["resources"]:
    print(f"--- {item['name']} ---\n{item['content']}\n")
print("PRIVATE ROOT CAUSE:", private.get("root_cause"))
for key in ("expected_changes", "assessment_criteria", "expected_patch"):
    if private.get(key):
        print(f"\n{key.upper()}:\n", json.dumps(private[key], indent=1))
checks = private.get("starter_gap_checks") or private.get("patch_checks") or []
print("\nCHECKS ON THE STARTER (False = the work is still to do):")
for check in checks:
    print(f"  {check['id']}: passes_on_starter={check_passes(check, files)} {json.dumps(check['any_of'])[:200]}")
print("\nSIGNALS:", json.dumps(quality_signals(scenario)))

with tempfile.TemporaryDirectory() as directory:
    for path, content in files.items():
        target = Path(directory) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    if "package.json" in files:
        command = ["node", "--test"]
    else:
        command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True, timeout=120)
    print("\nSTARTER TESTS:", " ".join(command[-3:]), "-> exit", result.returncode)
    print("\n".join((result.stdout + result.stderr).strip().splitlines()[-15:]))
