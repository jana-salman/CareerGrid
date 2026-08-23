"""Persist CareerGrid user accounts in Firebase Realtime Database."""

import hashlib
from datetime import datetime, timezone
from typing import Any

from services.firebase_service import get_database_reference


def normalize_email(email: str) -> str:
    """Return an email in a consistent format."""

    return email.strip().lower()


def create_email_key(email: str) -> str:
    """
    Create a Firebase-safe identifier from an email address.

    Firebase keys cannot safely contain every character used in email
    addresses, such as periods, so we create a SHA-256 identifier.
    """

    normalized_email = normalize_email(email)

    return hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Retrieve one registered user by email."""

    normalized_email = normalize_email(email)
    user_id = create_email_key(normalized_email)

    user_data = get_database_reference(f"users/{user_id}").get()

    if not isinstance(user_data, dict):
        return None

    return {"id": user_id, **user_data}


def create_user(
    full_name: str,
    email: str,
    password_hash: str,
) -> dict[str, Any]:
    """Create and store a new user in Firebase."""

    normalized_email = normalize_email(email)
    user_id = create_email_key(normalized_email)

    user_reference = get_database_reference(f"users/{user_id}")

    if user_reference.get() is not None:
        raise ValueError("An account with this email already exists.")

    user_data = {
        "full_name": full_name.strip(),
        "email": normalized_email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    user_reference.set(user_data)

    return {"id": user_id, **user_data}
