import json
import os
from typing import Any

from google.genai import types

from services.gemini_service import get_gemini_client


class RoadmapGenerationError(Exception):
    """Raised when Gemini cannot create a valid roadmap."""


def _clean_json_response(response_text: str) -> str:
    """Remove optional Markdown fences from Gemini's response."""

    cleaned = response_text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def _clean_string_list(
    value: Any,
    field_name: str,
) -> list[str]:
    """Validate and clean a list of strings."""

    if not isinstance(value, list):
        raise RoadmapGenerationError(
            f"Roadmap field '{field_name}' must be a list."
        )

    cleaned = [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]

    if not cleaned:
        raise RoadmapGenerationError(
            f"Roadmap field '{field_name}' cannot be empty."
        )

    return cleaned


def _validate_roadmap(
    roadmap: dict[str, Any],
) -> dict[str, Any]:
    """Validate Gemini's roadmap structure."""

    required_fields = {
        "title",
        "overview",
        "duration_weeks",
        "focus_areas",
        "phases",
        "recommended_resources",
    }

    missing_fields = required_fields - roadmap.keys()

    if missing_fields:
        raise RoadmapGenerationError(
            "Roadmap is missing: "
            f"{', '.join(sorted(missing_fields))}"
        )

    title = roadmap.get("title")
    overview = roadmap.get("overview")

    if not isinstance(title, str) or not title.strip():
        raise RoadmapGenerationError(
            "Roadmap title is invalid."
        )

    if not isinstance(overview, str) or not overview.strip():
        raise RoadmapGenerationError(
            "Roadmap overview is invalid."
        )

    roadmap["title"] = title.strip()
    roadmap["overview"] = overview.strip()

    try:
        duration_weeks = int(
            roadmap.get("duration_weeks", 0)
        )
    except (TypeError, ValueError) as error:
        raise RoadmapGenerationError(
            "Roadmap duration is invalid."
        ) from error

    roadmap["duration_weeks"] = max(
        1,
        min(52, duration_weeks),
    )

    focus_areas = roadmap.get("focus_areas")

    if not isinstance(focus_areas, list) or not focus_areas:
        raise RoadmapGenerationError(
            "Roadmap focus areas are invalid."
        )

    normalized_focus_areas = []

    allowed_priorities = {
        "high",
        "medium",
        "low",
    }

    for area in focus_areas:
        if not isinstance(area, dict):
            raise RoadmapGenerationError(
                "Each focus area must be an object."
            )

        skill = str(
            area.get("skill", "")
        ).strip()

        reason = str(
            area.get("reason", "")
        ).strip()

        priority = str(
            area.get("priority", "")
        ).strip().lower()

        if not skill or not reason:
            raise RoadmapGenerationError(
                "Every focus area needs a skill and reason."
            )

        if priority not in allowed_priorities:
            priority = "medium"

        normalized_focus_areas.append({
            "skill": skill,
            "reason": reason,
            "priority": priority,
        })

    roadmap["focus_areas"] = normalized_focus_areas

    phases = roadmap.get("phases")

    if not isinstance(phases, list) or not phases:
        raise RoadmapGenerationError(
            "Roadmap phases are invalid."
        )

    normalized_phases = []

    for index, phase in enumerate(phases, start=1):
        if not isinstance(phase, dict):
            raise RoadmapGenerationError(
                "Each roadmap phase must be an object."
            )

        phase_title = str(
            phase.get("title", "")
        ).strip()

        if not phase_title:
            raise RoadmapGenerationError(
                f"Roadmap Phase {index} has no title."
            )

        try:
            phase_duration = int(
                phase.get("duration_weeks", 1)
            )
        except (TypeError, ValueError):
            phase_duration = 1

        normalized_phases.append({
            "phase": index,
            "title": phase_title,
            "duration_weeks": max(
                1,
                min(12, phase_duration),
            ),
            "goals": _clean_string_list(
                phase.get("goals"),
                f"phase_{index}.goals",
            ),
            "activities": _clean_string_list(
                phase.get("activities"),
                f"phase_{index}.activities",
            ),
            "success_criteria": _clean_string_list(
                phase.get("success_criteria"),
                f"phase_{index}.success_criteria",
            ),
        })

    roadmap["phases"] = normalized_phases

    resources = roadmap.get("recommended_resources")

    if not isinstance(resources, list):
        raise RoadmapGenerationError(
            "Recommended resources must be a list."
        )

    normalized_resources = []

    for resource in resources:
        if not isinstance(resource, dict):
            continue

        resource_title = str(
            resource.get("title", "")
        ).strip()

        resource_type = str(
            resource.get("type", "")
        ).strip()

        purpose = str(
            resource.get("purpose", "")
        ).strip()

        search_query = str(
            resource.get("search_query", "")
        ).strip()

        if resource_title and resource_type and purpose:
            normalized_resources.append({
                "title": resource_title,
                "type": resource_type,
                "purpose": purpose,
                "search_query": search_query,
            })

    roadmap["recommended_resources"] = (
        normalized_resources
    )

    return roadmap


def generate_personalized_roadmap(
    *,
    evaluation: dict[str, Any],
    career_name: str,
    position_title: str,
    company_name: str,
) -> dict[str, Any]:
    """
    Generate a personalized learning roadmap from the
    completed simulation evaluation.
    """

    if not isinstance(evaluation, dict):
        raise RoadmapGenerationError(
            "A valid simulation evaluation is required."
        )

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    )

    roadmap_context = {
        "career": career_name,
        "position": position_title,
        "company": company_name,
        "evaluation": evaluation,
    }

    context_json = json.dumps(
        roadmap_context,
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""
You are creating a personalized learning roadmap for a user
who completed a CareerGrid workplace simulation.

Use the user's evaluation to create an actionable roadmap
for improving performance in the selected career and position.

Context:
{context_json}

Return valid JSON only with exactly this structure:

{{
  "title": "Personalized Backend Developer Roadmap",
  "overview": "A concise explanation of the roadmap.",
  "duration_weeks": 6,
  "focus_areas": [
    {{
      "skill": "Input Validation",
      "reason": "Why this skill is important for this user.",
      "priority": "high"
    }}
  ],
  "phases": [
    {{
      "phase": 1,
      "title": "Foundation",
      "duration_weeks": 2,
      "goals": [
        "A specific learning goal"
      ],
      "activities": [
        "A practical activity or small project"
      ],
      "success_criteria": [
        "A measurable way to verify progress"
      ]
    }}
  ],
  "recommended_resources": [
    {{
      "title": "Resource topic",
      "type": "documentation",
      "purpose": "Why this resource would help",
      "search_query": "A safe search phrase for finding it"
    }}
  ]
}}

Rules:
1. Base the roadmap on the supplied evaluation.
2. Prioritize areas_for_improvement and recommended_skills.
3. Use strengths to avoid unnecessary beginner work.
4. Include between 2 and 4 focus areas.
5. Include exactly 3 progressive learning phases.
6. Keep the total duration between 4 and 12 weeks.
7. Make activities practical and appropriate for the role.
8. Make success criteria measurable.
9. Do not invent URLs.
10. Do not return HTML or Markdown.
11. Return JSON only.
"""

    try:
        with get_gemini_client() as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

    except Exception as error:
        raise RoadmapGenerationError(
            "Gemini could not generate the roadmap."
        ) from error

    if not response.text:
        raise RoadmapGenerationError(
            "Gemini returned an empty roadmap."
        )

    try:
        roadmap = json.loads(
            _clean_json_response(response.text)
        )
    except json.JSONDecodeError as error:
        raise RoadmapGenerationError(
            "Gemini returned invalid roadmap JSON."
        ) from error

    if not isinstance(roadmap, dict):
        raise RoadmapGenerationError(
            "Gemini roadmap must be a JSON object."
        )

    return _validate_roadmap(roadmap)