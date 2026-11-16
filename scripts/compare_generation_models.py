"""Compare task-generation pipelines and models on the same representative inputs.

Usage (from the project root; uses your .env credentials and never prints them):

    python scripts/compare_generation_models.py MODEL [--pipelines staged,single]
        [--cases backend-practice,backend-listing,frontend-practice]
        [--thinking low]

Runs the real generation code (prompts, schemas, validators, quality gate, time
budget) once per case and pipeline, interleaving pipelines so a quota cut-off
affects both equally. Every API call counts against the model's quota.

Each run prints one JSON line and appends it to
instance/generation_comparison/<date>-<model>.jsonl. Every candidate the model
returned (accepted or rejected, with validation reasons) is kept under
instance/generation_candidates/ for manual inspection.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

parser = argparse.ArgumentParser()
parser.add_argument("model")
parser.add_argument("--pipelines", default="staged,single")
parser.add_argument("--cases", default="backend-practice,backend-listing,frontend-practice")
parser.add_argument("--thinking", default="")
args = parser.parse_args()

os.environ["GEMINI_SCENARIO_MODEL"] = args.model
os.environ["SCENARIO_CANDIDATE_ARCHIVE"] = "1"
if args.thinking:
    os.environ["GEMINI_SCENARIO_THINKING"] = args.thinking
logging.basicConfig(level=logging.ERROR)

from services.ai.generation_runtime import GenerationReport, failure_category  # noqa: E402
from services.ai.scenario_generation_service import ScenarioGenerationError, generate_workplace_scenario  # noqa: E402
from services.ai.scenario_quality import quality_signals  # noqa: E402
from services.simulation.frontend_workplace_scenario_service import generate_frontend_workplace_scenario  # noqa: E402
from services.simulation.job_context_service import build_catalog_job_context, build_job_context  # noqa: E402

LISTING_EXCERPT = build_job_context("adzuna", {
    "title": "Backend Developer",
    "company": "Example Employer",
    "description": (
        "We are looking for a Backend Developer to build and maintain Python REST APIs for our "
        "real-time logistics platform, working with PostgreSQL, integrating partner systems, and "
        "writing automated tests. You will collaborate with frontend and product teams to…"
    ),
})

CASES = {
    "backend-practice": ("backend", "BrightSoft", build_catalog_job_context("backend-developer", "brightsoft"), None),
    "backend-listing": ("backend", "Example Employer", LISTING_EXCERPT, None),
    "frontend-practice": ("frontend", "PixelWorks", build_catalog_job_context("frontend-developer", "pixelworks"), None),
}

out_dir = ROOT / "instance" / "generation_comparison"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / f"{datetime.now(timezone.utc):%Y%m%d}-{args.model}.jsonl"
accepted: dict[tuple[str, str], dict] = {}


def summary_of(scenario):
    public = scenario["public_scenario"]
    return {
        "title": public.get("title", ""),
        "project": public.get("project", {}).get("display_name", ""),
        "summary": public.get("task", {}).get("summary", ""),
    }


def run(case, pipeline):
    kind, company, job_context, repeat_of = CASES[case]
    os.environ["SCENARIO_GENERATION_PIPELINE"] = pipeline
    recent = [accepted[(repeat_of, pipeline)]] if repeat_of and (repeat_of, pipeline) in accepted else None
    report = GenerationReport()
    started = time.monotonic()
    scenario = None
    attempt_id = f"compare-{case}-{pipeline}-{int(time.time())}"
    try:
        if kind == "backend":
            scenario, _ = generate_workplace_scenario(
                career_id="software-developer", position_id="backend-developer", company_id=company.lower(),
                attempt_id=attempt_id, company_name=company, job_context=job_context,
                report=report)
        else:
            scenario, count = generate_frontend_workplace_scenario(
                company_name=company, attempt_id=attempt_id, job_context=job_context,
                report=report)
            scenario = scenario if count else None
    except ScenarioGenerationError:
        scenario = None
    row = {
        "model": args.model, "thinking": args.thinking, "pipeline": pipeline, "case": case,
        "outcome": report.outcome, "failure_reason": report.failure_reason,
        "failure_category": failure_category(report.failure_reason),
        "seconds": round(time.monotonic() - started, 1), "api_calls": report.api_calls,
        "with_history": bool(recent),
        "attempts": [(item["stage"], item["outcome"], item["reason"], item["seconds"]) for item in report.attempts],
        "archive": report.archive_path,
    }
    if scenario:
        row.update(summary_of(scenario))
        row["signals"] = quality_signals(scenario)
        accepted[(case, pipeline)] = summary_of(scenario)
    print(json.dumps(row), flush=True)
    with out_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


pipelines = [item for item in args.pipelines.split(",") if item]
for index, case in enumerate(item for item in args.cases.split(",") if item):
    # Alternate which pipeline goes first so neither always gets the fresher quota.
    for pipeline in pipelines if index % 2 == 0 else list(reversed(pipelines)):
        run(case, pipeline)
