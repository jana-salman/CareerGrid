import json


class DataAnalystCleaningValidationError(ValueError):
    """Raised when a Data Analyst cleaning response is invalid."""
    pass


VALID_DUPLICATE_ACTIONS = {
    "remove_duplicate",
    "keep_both",
    "aggregate_records",
}

VALID_MISSING_REGION_ACTIONS = {
    "fill_from_reference",
    "leave_missing",
    "drop_record",
}


def validate_data_analyst_cleaning_response(raw_answer):
    """
    Validate the structured response submitted by the
    Data Analyst data-cleaning workspace.
    """

    try:
        response = json.loads(raw_answer)

    except (TypeError, json.JSONDecodeError) as exc:
        raise DataAnalystCleaningValidationError(
            "Your data-cleaning response could not be read."
        ) from exc

    if not isinstance(response, dict):
        raise DataAnalystCleaningValidationError(
            "Invalid data-cleaning response."
        )

    if response.get("task_type") != "data_analyst_cleaning":
        raise DataAnalystCleaningValidationError(
            "Invalid Data Analyst cleaning task response."
        )

    duplicate_action = str(
        response.get(
            "duplicate_action",
            ""
        )
    ).strip()

    missing_region_action = str(
        response.get(
            "missing_region_action",
            ""
        )
    ).strip()

    inspected_reference = bool(
        response.get(
            "inspected_reference"
        )
    )

    preview_applied = bool(
        response.get(
            "preview_applied"
        )
    )

    cleaning_note = str(
        response.get(
            "cleaning_note",
            ""
        )
    ).strip()

    preview_row_count = response.get(
        "preview_row_count"
    )

    preview_revenue = response.get(
        "preview_revenue"
    )

    if duplicate_action not in VALID_DUPLICATE_ACTIONS:
        raise DataAnalystCleaningValidationError(
            "Choose how you would handle the duplicate transaction."
        )

    if missing_region_action not in VALID_MISSING_REGION_ACTIONS:
        raise DataAnalystCleaningValidationError(
            "Choose how you would handle the missing region."
        )

    if not inspected_reference:
        raise DataAnalystCleaningValidationError(
            "Inspect the trusted reference data before continuing."
        )

    if not preview_applied:
        raise DataAnalystCleaningValidationError(
            "Apply the cleaning preview before continuing."
        )

    if len(cleaning_note) < 40:
        raise DataAnalystCleaningValidationError(
            "Explain your cleaning decision in at least 40 characters."
        )

    try:
        preview_row_count = int(preview_row_count)
        preview_revenue = float(preview_revenue)

    except (TypeError, ValueError) as exc:
        raise DataAnalystCleaningValidationError(
            "The cleaning preview contains invalid values."
        ) from exc

    return {
        "task_type": "data_analyst_cleaning",
        "issue_id": response.get(
            "issue_id",
            "DA-2104",
        ),
        "duplicate_action": duplicate_action,
        "missing_region_action": missing_region_action,
        "inspected_reference": inspected_reference,
        "preview_applied": preview_applied,
        "preview_row_count": preview_row_count,
        "preview_revenue": preview_revenue,
        "cleaning_note": cleaning_note,
    }