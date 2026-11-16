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
ADZUNA_SEARCH_URL_TEMPLATE = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
# Country endpoints Adzuna publishes for its Jobs search API. Lebanon is not
# one of them; requests for "lb" are reported as unsupported, never re-routed.
ADZUNA_SUPPORTED_COUNTRIES = {
    "at": "Austria",
    "au": "Australia",
    "be": "Belgium",
    "br": "Brazil",
    "ca": "Canada",
    "ch": "Switzerland",
    "de": "Germany",
    "es": "Spain",
    "fr": "France",
    "gb": "United Kingdom",
    "in": "India",
    "it": "Italy",
    "mx": "Mexico",
    "nl": "Netherlands",
    "nz": "New Zealand",
    "pl": "Poland",
    "sg": "Singapore",
    "us": "United States",
    "za": "South Africa",
}
JOB_SEARCH_DEFAULT_COUNTRY = "us"
# Countries offered in the selector that need a provider other than Adzuna.
JOB_SEARCH_EXTRA_COUNTRIES = {"lb": "Lebanon"}
# Jooble's documented REST endpoint (POST, key in the path). Lebanese coverage
# is not confirmed, so results are kept only when their location is in Lebanon.
JOOBLE_SEARCH_URL_TEMPLATE = "https://jooble.org/api/{api_key}"
LEBANON_LOCATION_TERMS = (
    "lebanon", "beirut", "tripoli", "sidon", "saida", "jounieh", "byblos",
    "jbeil", "zahle", "tyre", "baabda", "metn", "keserwan", "aley", "nabatieh",
    "batroun", "dbayeh", "antelias", "hazmieh",
)
MAX_JOB_CONTEXT_PROMPT_LENGTH = 2500

# Bounds for client-supplied workplace evaluation evidence.
MAX_EVALUATION_FILES = 40
MAX_EVALUATION_EVIDENCE_CHARS = 400_000

# Model fallbacks apply only when GEMINI_MODEL is not configured.
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
LEGACY_INTERVIEW_GEMINI_MODEL = "gemini-2.5-flash"
