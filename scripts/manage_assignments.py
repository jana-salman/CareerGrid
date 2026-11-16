"""List saved workplace assignments or request their regeneration.

Usage:
    python scripts/manage_assignments.py list
    python scripts/manage_assignments.py regenerate --key practice-software-developer-backend-developer-technova
    python scripts/manage_assignments.py regenerate --career software-developer --position backend-developer --company technova

Regeneration is lazy: the request is recorded, and the next launch for that
company/position generates a new version (one Gemini generation, bounded as
usual). Existing attempts keep the copy they started with; if the new
generation fails, launches keep using the current version. Live-listing
assignments are keyed by the listing's content, so an edited listing gets a
new assignment automatically; use --key (from `list`) to replace one anyway.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from services.simulation.assignment_library import (  # noqa: E402
    assignment_identity,
    list_assignments,
    request_regeneration,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="show saved assignments, versions, failures, and fallbacks")
    regenerate = commands.add_parser("regenerate", help="replace an assignment on its next launch")
    regenerate.add_argument("--key")
    regenerate.add_argument("--career")
    regenerate.add_argument("--position")
    regenerate.add_argument("--company")
    regenerate.add_argument("--reason", default="manual regeneration")
    args = parser.parse_args()

    if args.command == "list":
        rows = list_assignments()
        if not rows:
            print("No saved assignments yet.")
        for row in rows:
            print(
                f"{row['key']}\n  version {row['current_version'] or '-'} of {row['versions']} | "
                f"{row['title'] or '(none yet)'} | created {row['created_at'] or '-'}\n"
                f"  failures {row['failures']} (cooldown until {row['cooldown_until'] or '-'}) | "
                f"fallbacks served {row['fallbacks']} | regeneration requested: {row['regenerate_requested']}"
            )
        return 0

    key = args.key
    if not key:
        if not (args.career and args.position and args.company):
            parser.error("give --key, or --career, --position, and --company for a practice company")
        key = assignment_identity(
            career_id=args.career, position_id=args.position, company_id=args.company, job_context=None
        )["key"]
    request_regeneration(key, args.reason)
    print(f"Regeneration requested for {key}; the next launch generates a new version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
