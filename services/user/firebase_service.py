"""Initialize Firebase Admin and provide Realtime Database references."""

import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db

from config import BASE_DIR



def initialize_firebase():
    """Initialize the Firebase Admin SDK once."""

    if firebase_admin._apps:
        return firebase_admin.get_app()

    credentials_filename = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    database_url = os.getenv("FIREBASE_DATABASE_URL")

    if not credentials_filename:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is not configured."
        )

    if not database_url:
        raise RuntimeError("FIREBASE_DATABASE_URL is not configured.")

    credentials_path = Path(credentials_filename)

    # Convert a relative path into the full file path
    if not credentials_path.is_absolute():
        credentials_path = BASE_DIR / credentials_path

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Firebase credential file was not found: {credentials_path}"
        )

    firebase_credentials = credentials.Certificate(str(credentials_path))

    return firebase_admin.initialize_app(
        firebase_credentials,
        {"databaseURL": database_url},
    )


def get_database_reference(path: str = "/"):
    """Return a reference to a location in Realtime Database."""

    initialize_firebase()
    return db.reference(path)
