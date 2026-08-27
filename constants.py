"""Shared CareerGrid domain identifiers and operational defaults."""

# Career and simulation identifiers shared by routes and persistence.
WORKPLACE_SIMULATION_MODE = "workplace"
FRONTEND_DEVELOPER_POSITION_ID = "frontend-developer"
WORKPLACE_SCENARIO_VERSION = 1
WORKPLACE_FINAL_STEP = 5

# Application limits and integration defaults.
INTERVIEW_UNLOCK_SCORE = 85
MAX_INTERVIEW_AUDIO_BYTES = 15 * 1024 * 1024
MAX_ADZUNA_COMPANY_NAME_LENGTH = 200
ADZUNA_DEFAULT_RESULTS = 5
ADZUNA_REQUEST_TIMEOUT_SECONDS = 15
ADZUNA_SEARCH_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"

# Model fallbacks apply only when GEMINI_MODEL is not configured.
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
LEGACY_INTERVIEW_GEMINI_MODEL = "gemini-2.5-flash"
