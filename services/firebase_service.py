import os
from pathlib import Path

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, db


# Main CareerGrid folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load private settings from CareerGrid/.env
load_dotenv(BASE_DIR / ".env", override=True)


def initialize_firebase():
    """Initialize the Firebase Admin SDK once."""

    if firebase_admin._apps:
        return firebase_admin.get_app()

    credentials_filename = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    database_url = os.getenv("FIREBASE_DATABASE_URL")

    if not credentials_filename:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is missing from the .env file."
        )

    if not database_url:
        raise RuntimeError(
            "FIREBASE_DATABASE_URL is missing from the .env file."
        )

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
        {
            "databaseURL": database_url
        }
    )


def get_database_reference(path: str = "/"):
    """Return a reference to a location in Realtime Database."""

    initialize_firebase()
    return db.reference(path)