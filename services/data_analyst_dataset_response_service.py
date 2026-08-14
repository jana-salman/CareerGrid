import json


class DataAnalystDatasetValidationError(ValueError):
    """Raised when the Data Analyst dataset response is invalid."""
    pass


VALID_ROOT_CAUSES = {
    "duplicate_transactions",
    "missing_region",
    "incorrect_unit_price",
    "date_format_issue",
}


def validate_data_analyst_dataset_response(raw_answer):
    """
    Validate the structured response submitted by the
    Data Analyst dataset investigation task.
    """

    try:
        response = json.loads(raw_answer)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DataAnalystDatasetValidationError(
            "Your dataset investigation could not be read."
        ) from exc

    if not isinstance(response, dict):
        raise DataAnalystDatasetValidationError(
            "Invalid dataset investigation response."
        )

    if response.get("task_type") != "data_analyst_dataset":
        raise DataAnalystDatasetValidationError(
            "Invalid Data Analyst task response."
        )

    inspected_summary = bool(
        response.get("inspected_summary")
    )

    checked_duplicates = bool(
        response.get("checked_duplicates")
    )

    checked_missing_values = bool(
        response.get("checked_missing_values")
    )

    selected_rows = response.get(
        "selected_rows",
        []
    )

    selected_root_cause = response.get(
        "selected_root_cause",
        ""
    )

    analyst_finding = str(
        response.get(
            "analyst_finding",
            ""
        )
    ).strip()

    if not inspected_summary:
        raise DataAnalystDatasetValidationError(
            "Inspect the dataset summary before continuing."
        )

    if not checked_duplicates:
        raise DataAnalystDatasetValidationError(
            "Run the duplicate check before continuing."
        )

    if not checked_missing_values:
        raise DataAnalystDatasetValidationError(
            "Check for missing values before continuing."
        )

    if not isinstance(selected_rows, list):
        raise DataAnalystDatasetValidationError(
            "Select the suspicious dataset records."
        )

    normalized_rows = []

    for row_id in selected_rows:
        try:
            row_number = int(row_id)
        except (TypeError, ValueError):
            continue

        if row_number not in normalized_rows:
            normalized_rows.append(row_number)

    if len(normalized_rows) < 2:
        raise DataAnalystDatasetValidationError(
            "Select at least two suspicious records."
        )

    if selected_root_cause not in VALID_ROOT_CAUSES:
        raise DataAnalystDatasetValidationError(
            "Choose the most likely root cause."
        )

    if len(analyst_finding) < 40:
        raise DataAnalystDatasetValidationError(
            "Write an analyst finding of at least 40 characters."
        )

    return {
        "task_type": "data_analyst_dataset",
        "issue_id": response.get(
            "issue_id",
            "DA-2104",
        ),
        "inspected_summary": inspected_summary,
        "checked_duplicates": checked_duplicates,
        "checked_missing_values": checked_missing_values,
        "selected_rows": normalized_rows,
        "selected_root_cause": selected_root_cause,
        "analyst_finding": analyst_finding,
    }