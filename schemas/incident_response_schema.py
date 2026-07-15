from typing import Literal

from pydantic import BaseModel, Field


class IncidentResponse(BaseModel):
    """Validated response for the incident investigation task."""

    task_type: Literal["incident_investigation"]

    incident_id: Literal["INC-2048"]

    selected_root_cause: Literal[
        "database_connection",
        "missing_product_id",
        "invalid_quantity",
    ]

    technical_finding: str = Field(
        min_length=20,
        max_length=1500,
    )