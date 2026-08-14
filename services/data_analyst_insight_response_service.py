import json


class DataAnalystInsightValidationError(ValueError):
    """Raised when the Data Analyst insight response is invalid."""
    pass


VALID_INSIGHTS = {
    "south_revenue_decline",
    "north_order_value_growth",
    "starter_product_decline",
    "overall_growth",
}


VALID_RECOMMENDATIONS = {
    "investigate_south_starter",
    "increase_all_marketing",
    "focus_only_north",
    "no_action",
}


def validate_data_analyst_insight_response(raw_answer):
    """
    Validate the structured response from the
    Data Analyst dashboard analysis task.
    """

    try:
        response = json.loads(raw_answer)

    except (TypeError, json.JSONDecodeError) as exc:
        raise DataAnalystInsightValidationError(
            "Your dashboard analysis could not be read."
        ) from exc


    if not isinstance(response, dict):
        raise DataAnalystInsightValidationError(
            "Invalid dashboard analysis response."
        )


    if response.get("task_type") != "data_analyst_insight":
        raise DataAnalystInsightValidationError(
            "Invalid Data Analyst insight response."
        )


    inspected_kpis = response.get(
        "inspected_kpis",
        []
    )

    inspected_regions = response.get(
        "inspected_regions",
        []
    )

    selected_insight = str(
        response.get(
            "selected_insight",
            ""
        )
    ).strip()

    evidence = response.get(
        "supporting_evidence",
        []
    )

    recommendation = str(
        response.get(
            "recommendation",
            ""
        )
    ).strip()

    analyst_summary = str(
        response.get(
            "analyst_summary",
            ""
        )
    ).strip()


    if not isinstance(inspected_kpis, list):
        raise DataAnalystInsightValidationError(
            "Inspect the dashboard KPIs before continuing."
        )


    required_kpis = {
        "revenue",
        "orders",
        "aov",
    }

    if not required_kpis.issubset(
        set(inspected_kpis)
    ):
        raise DataAnalystInsightValidationError(
            "Inspect Revenue, Orders, and Average Order Value."
        )


    if not isinstance(inspected_regions, list):
        raise DataAnalystInsightValidationError(
            "Review the regional breakdown."
        )


    if len(set(inspected_regions)) < 3:
        raise DataAnalystInsightValidationError(
            "Inspect at least three regions before making a conclusion."
        )


    if selected_insight not in VALID_INSIGHTS:
        raise DataAnalystInsightValidationError(
            "Choose the strongest business insight."
        )


    if not isinstance(evidence, list):
        raise DataAnalystInsightValidationError(
            "Select evidence supporting your conclusion."
        )


    if len(set(evidence)) < 2:
        raise DataAnalystInsightValidationError(
            "Select at least two pieces of supporting evidence."
        )


    if recommendation not in VALID_RECOMMENDATIONS:
        raise DataAnalystInsightValidationError(
            "Choose a business recommendation."
        )


    if len(analyst_summary) < 60:
        raise DataAnalystInsightValidationError(
            "Explain your conclusion in at least 60 characters."
        )


    return {
        "task_type": "data_analyst_insight",
        "issue_id": response.get(
            "issue_id",
            "DA-2104",
        ),
        "inspected_kpis": list(
            dict.fromkeys(inspected_kpis)
        ),
        "inspected_regions": list(
            dict.fromkeys(inspected_regions)
        ),
        "selected_insight": selected_insight,
        "supporting_evidence": list(
            dict.fromkeys(evidence)
        ),
        "recommendation": recommendation,
        "analyst_summary": analyst_summary,
    }
