# CareerGrid

CareerGrid is an AI-powered career simulation platform designed to help students practice realistic workplace tasks and structured job interviews.

The platform is built with Flask and combines an interactive simulated workplace, Firebase Realtime Database, and Google Gemini. It allows students to practice job-related tasks, receive AI-assisted feedback, complete interviews, and review their previous performance.

## Main Features

* Secure registration and login using Werkzeug password hashing
* Career, position, and company/job selection
* AI-generated Backend Developer workplace scenarios using Google Gemini
* Deterministic TechNova Backend demo for presentations
* Five-step Frontend Developer workplace simulation with a fallback scenario when AI generation is unavailable
* Simulated Mail, Files, VS Code, Terminal, Browser, Git, and GitHub tools
* Workplace and interview attempts stored in Firebase Realtime Database
* AI-assisted workplace feedback and progressive advisor guidance
* Timed microphone-based interviews with transcription and speech analysis
* Server-side interview rubrics and final AI evaluation
* Dashboard history for saved attempts and reports

## How CareerGrid Works

CareerGrid guides the user through a complete career-practice journey:

1. Register or log in to an account.
2. Choose a career, position, and company.
3. Complete a realistic workplace simulation using the simulated desktop tools.
4. Submit the work and receive an AI-generated performance evaluation.
5. Achieve a workplace score of at least **85** to unlock the interview stage.
6. Complete the timed microphone-based job interview.
7. Receive the final AI evaluation and review saved results from the dashboard.

```text
Register / Login
        ↓
Choose Career, Position & Company
        ↓
Complete Workplace Simulation
        ↓
Receive AI Evaluation
        ↓
Score ≥ 85
        ↓
Complete Job Interview
        ↓
View Final Report & Dashboard History
```

## Technology Stack

### Backend

* Python 3.11+
* Flask
* Werkzeug
* Firebase Admin SDK
* Firebase Realtime Database
* Google Gen AI SDK (Gemini)
* Requests for optional Adzuna job listings
* python-dotenv for local environment configuration

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 Templates
* Browser MediaRecorder API
* Web Audio API

### Testing

* pytest
* Flask test client
* Mocked Firebase, Gemini, and external-service boundaries

### Version Control

* Git
* GitHub

## Architecture

CareerGrid separates browser presentation, Flask route handling, backend services, storage, and testing while keeping the project within a single Flask application.

```text
CareerGrid/

├── app.py
│   # Flask application setup and main application routes
│
├── routes/
│   └── auth.py
│       # Authentication Blueprint
│
├── services/
│   ├── scenario_generation_service.py
│   ├── frontend_workplace_scenario_service.py
│   ├── backend_demo_scenario_service.py
│   ├── evaluation_service.py
│   ├── advisor_service.py
│   ├── interview_service.py
│   ├── simulation_storage.py
│   ├── firebase_service.py
│   ├── gemini_service.py
│   └── user_service.py
│
├── templates/
│   # Jinja pages and simulation windows
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── tests/
│   # Automated tests
│
├── .env.example
│   # Example environment configuration
│
├── requirements.txt
│   # Runtime dependencies
│
└── requirements-dev.txt
    # Runtime and testing dependencies
```

`app.py` acts as the main route coordinator because the workplace and interview flows share application state and endpoints.

Authentication is separated into its own Blueprint, while larger features such as scenario generation, evaluation, Firebase storage, interviews, and advisor guidance are organized into service modules.

## Workplace Scenario Validation

Backend and Frontend workplace scenarios use the shared validation pipeline in:

```text
services/scenario_generation_service.py
```

The validation flow is:

```text
Backend Scenario Service
        ↓
validate_workplace_scenario()

Frontend Scenario Service
        ↓
validate_workplace_scenario()
        ↓
validate_frontend_requirements()
```

The shared validator checks:

* Public and private context separation
* Relative project paths and path traversal
* Allowed text-file extensions
* Unique project files
* File content size limits
* Project naming and archive consistency
* Resource and attachment integrity
* Unsafe shell content
* Solution-leak patterns
* Scenario payload size

The Frontend validator also checks career-specific requirements such as:

* Required HTML, CSS, JavaScript, and package files
* Frontend-only file extensions
* Five ordered workplace tasks
* Valid application names
* Five inbox emails and one linked critical incident
* Allowed simulated terminal commands
* Viewport metadata
* Firebase-safe expected-patch keys

## AI and Evaluation Flow

### Workplace Scenarios

* Normal Backend Developer jobs use Gemini scenario generation.
* The TechNova presentation job uses a predefined and validated Backend scenario.
* Frontend Developer jobs use Gemini generation with a deterministic five-step fallback when generation or validation fails.

All scenarios follow the same Firebase attempt lifecycle.

Only validated public scenario information is returned to the user. Private evaluation information remains on the server.

### Workplace Evaluation

The submission system evaluates actual user work, including:

* Changed files
* Commits
* Pull-request information
* Verification results
* Communication responses

The user's work is compared with private server-side expectations.

Google Gemini then produces the final evidence-based performance report.

### Interviews

Normal interviews use seven Gemini-generated questions.

The TechNova demo uses four predefined interview questions.

The interview system includes:

* Microphone recording
* Timed questions
* Transcription
* Spoken-answer analysis
* Per-answer evaluation
* Firebase storage
* Final AI-generated interview evaluation

A workplace score of at least **85** is required to unlock the interview.

## Firebase Data Structure

CareerGrid uses Firebase Realtime Database with the following high-level structure:

```text
users/{user_id}/
├── full_name
├── email
├── password_hash
│
├── simulation_attempts/{attempt_id}/
│   ├── public_scenario
│   ├── private_context
│   ├── responses
│   └── evaluation
│
└── interview_attempts/{interview_id}/
    ├── public_questions
    ├── private_rubrics
    ├── answers
    └── evaluation
```

Private scenario information and interview rubrics remain server-side and are not included in candidate-facing browser data.

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/jana-salman/CareerGrid.git
cd CareerGrid
```

## 2. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

For normal application use:

```bash
python -m pip install -r requirements.txt
```

For development and testing:

```bash
python -m pip install -r requirements-dev.txt
```

## 4. Configure Environment Variables

CareerGrid uses environment variables for API keys, database configuration, and application settings.

For security reasons, real credentials are **not included in the repository**.

A `.env.example` file is included in the project root. It contains all required environment variable names with placeholder values.

Create a copy of:

```text
.env.example
```

and rename the copy to:

```text
.env
```

Then replace the placeholder values with your own configuration:

```env
CAREERGRID_ENV=development
FLASK_DEBUG=false

SECRET_KEY=replace_with_a_long_random_secret

GEMINI_API_KEY=replace_with_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite

ADZUNA_APP_ID=replace_with_adzuna_app_id
ADZUNA_APP_KEY=replace_with_adzuna_app_key

FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
```

You can generate a suitable Flask secret key using:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

When `SECRET_KEY` is not provided during development, CareerGrid creates a temporary random key. This means sessions may reset when the application restarts.

When:

```env
CAREERGRID_ENV=production
```

a `SECRET_KEY` is required.

Adzuna credentials are optional. If they are not provided or the API is unavailable, CareerGrid continues using local/demo job information.

> **Important:** Never commit your `.env` file, Firebase service-account JSON file, API keys, passwords, or other private credentials to GitHub. These files are excluded through `.gitignore`.

The `.env.example` file contains placeholder values only and is safe to keep in the repository.

## 5. Firebase Setup

1. Create or select a Firebase project.
2. Enable **Firebase Realtime Database**.
3. Create a Firebase Admin service account.
4. Download the JSON credential file.
5. Save it as:

```text
firebase-service-account.json
```

in the project root, or store it somewhere else on your computer.

6. Set:

```env
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
```

or provide the path to the file if it is stored somewhere else.

7. Add your Firebase Realtime Database URL:

```env
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com
```

Firebase credential filenames and common Firebase service-account file patterns are excluded through `.gitignore`.

## 6. Gemini Setup

1. Create a Gemini API key using Google AI Studio or an appropriate Google Cloud project.
2. Add the API key to your local `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

3. Configure the Gemini model:

```env
GEMINI_MODEL=gemini-3.1-flash-lite
```

To perform the optional live Gemini connectivity check:

```bash
python test_gemini.py
```

This command uses the external Gemini API and is separate from the offline automated test suite.

## Running CareerGrid

Start the Flask application with:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

in your browser.

Debug mode is disabled by default.

To enable it during local development, set:

```env
FLASK_DEBUG=true
```

## Running Tests and Checks

Run the automated test suite:

```bash
python -m pytest -q
```

Run Python compilation checks:

```bash
python -m compileall -q .
```

If Node.js is installed, JavaScript files can also be checked using:

```bash
node --check <path-to-file.js>
```

Tests cover areas including:

* Scenario validation and privacy
* Deterministic demo behavior
* Frontend five-step progression
* Firebase storage contracts
* Workplace evaluation
* Interview question selection
* Dynamic interview completion

## Security

CareerGrid includes several security measures:

* Passwords are stored using Werkzeug password hashing.
* User IDs are generated as Firebase-safe SHA-256 identifiers based on normalized email addresses.
* Firebase data is stored under user-specific paths.
* Candidate-facing APIs do not expose private evaluation context.
* Interview rubrics remain server-side.
* Generated paths, files, resources, commands, and attachments are validated.
* `.env`, Firebase service-account credentials, caches, bytecode, coverage files, and local databases are excluded from Git.

## Creating a Clean Project ZIP

A clean ZIP file can be created using:

```bash
git archive --format=zip --output CareerGrid-submission.zip HEAD
```

This exports only tracked source files and does not include:

* `.git`
* Ignored credentials
* `.env`
* Cache directories
* Generated local files

## Known Limitations and Future Improvements

* Career coverage is currently limited to the careers implemented within the scope of the university project.
* Gemini and Firebase features require internet access and valid credentials.
* Microphone functionality depends on browser permission and MediaRecorder support.
* The simulated terminal supports a controlled command set rather than executing arbitrary local programs.
* Some large simulation modules could be divided into smaller modules in future versions to improve maintainability.

## Final Submission

The final submitted version of CareerGrid is marked in the GitHub repository using the tag:

```text
v1
```
