# CareerGrid

CareerGrid is an AI-assisted career-practice platform for realistic workplace simulations and structured job interviews. The current application combines a React/Vite client with a Flask API and server-rendered authentication/fallback pages. Firebase Realtime Database stores users and attempts, while Google Gemini generates or evaluates selected scenarios, advisor replies, and interview content.

## Features

- Registration and login with Flask sessions and Werkzeug password hashing
- Career, position, and company selection
- React workplace desktop with simulated Mail, Files, VS Code, Terminal, Browser, Git, and GitHub applications
- In-memory simulated repository, commits, pushes, and pull requests; the browser never runs Git or contacts GitHub
- Backend Developer scenarios, including a deterministic TechNova demonstration
- Five-step Frontend Developer simulation with a validated deterministic fallback
- Evidence-based workplace evaluation and progressive advisor guidance
- Timed microphone interviews with transcription and speech analysis
- Server-side private rubrics and final interview evaluation
- Dashboard history and browser-safe workplace/interview reports

The normal learning flow is:

```text
Register or log in
       -> choose career, position, and company
       -> complete a workplace simulation
       -> receive an evaluation
       -> unlock the interview at a score of 85 or higher
       -> complete the interview
       -> review the final report and dashboard history
```

## Technology stack

### Client

- React 19
- React Router
- Vite
- JavaScript and the existing CareerGrid CSS system
- Browser MediaRecorder and Web Audio APIs for interview capture

The SPA entry point is `frontend/index.html`, routes live in `frontend/src/router.jsx`, and all browser API calls go through named modules in `frontend/src/services/`. Requests use relative `/api/...` URLs and include the existing Flask session cookie.

Flask/Jinja templates and legacy static JavaScript are intentionally retained for login, registration, server-side failure pages, and verified page/workspace fallbacks. Shared styles under `static/css/` are also loaded by the React entry point, so they are part of the active client.

### Server

- Python 3.11+
- Flask and feature Blueprints
- Werkzeug password hashing and signed Flask sessions
- Firebase Admin SDK and Firebase Realtime Database
- Google Gen AI SDK (Gemini)
- Requests for optional Adzuna job listings
- python-dotenv for local configuration

### Tests

- pytest and the Flask test client
- Node's built-in test runner for frontend contracts and simulation state
- Mocked Firebase, Gemini, and external-service boundaries in automated tests

## Architecture

```text
CareerGrid/
├── app.py                         Flask application factory and entry point
├── config.py                      Environment-backed server configuration
├── constants.py                   Stable application limits and identifiers
├── routes/                        Flask Blueprints
│   ├── api.py                     Health and authenticated-session API
│   ├── auth.py                    Login, registration, and logout
│   ├── careers.py                 Catalog pages and APIs
│   ├── dashboard.py               Attempt history page and API
│   ├── simulations.py             Workplace pages and APIs
│   └── interviews.py              Interview workspace, answer, and review APIs
├── services/                      Domain logic and external integrations
├── ai/
│   ├── prompts/                   Versioned Gemini prompt builders
│   └── rubrics/                   Versioned, server-only private rubrics
├── frontend/
│   ├── index.html                 Vite/React entry document
│   ├── src/router.jsx             React Router configuration
│   ├── src/pages/                 Catalog, dashboard, interview, and report pages
│   ├── src/services/              Browser-safe Flask API clients
│   └── src/simulation/            Simulated desktop, apps, and repository state
├── templates/                     Auth, error, and Flask fallback views
├── static/                        Shared CSS, fallback JS, and images
├── tests/                         Flask/service tests
└── frontend/tests/                React service and simulation contract tests
```

`app.py` creates the Flask application and registers the route groups from `routes/`. Routes handle HTTP, session ownership, and browser-safe serialization. Services own scenario generation, validation, evaluation, interview behavior, persistence, and external integrations.

React Router owns the migrated client routes for the home/catalog journey, dashboard, workplace, workplace report, interview, and interview review. Vite proxies API, authentication, start-workflow, and static-asset requests to Flask during development. Authentication itself remains server-side: the browser receives only the signed-in user's display identity from `/api/auth/session`, never credentials or password hashes.

## Privacy and AI boundaries

Gemini calls run only on the Flask server. Prompt builders and rubrics are versioned under `ai/prompts/` and `ai/rubrics/`; their current identifiers include `scenario_v1`, `advisor_v1`, `workplace_evaluation_v2`, `interview_v1`, and `workplace_v1`.

Each stored workplace scenario separates `public_scenario` from `private_context`. Interview records similarly separate `public_questions` from `private_rubrics`. Candidate-facing endpoints construct explicit browser-safe response objects, and workplace evaluation responses pass through a public-field allow-list. Private context may be used internally by server-side advisor and evaluation services but is not returned to the React client.

Workplace scenario validation checks public/private separation, relative project paths, allowed text files, duplicate files, content limits, resource integrity, safe simulated commands, solution-leak patterns, and payload size. Frontend scenarios add five ordered tasks, required project files, inbox/incident linkage, viewport metadata, and expected-patch validation.

Git, GitHub, the terminal, filesystem, and pull requests inside the workplace are simulations implemented as browser state. They do not execute local commands, mutate the real repository, or call GitHub.

## Firebase data model

At a high level, CareerGrid stores:

```text
users/{user_id}/
├── full_name
├── email
├── password_hash
├── simulation_attempts/{attempt_id}/
│   ├── public_scenario
│   ├── private_context
│   ├── responses
│   └── evaluation
└── interview_attempts/{interview_id}/
    ├── public_questions
    ├── private_rubrics
    ├── answers
    └── evaluation
```

Firebase access uses the Admin SDK on the server. The browser does not receive Firebase credentials or connect directly to the database.

## Installation

### 1. Create a Python environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements-dev.txt
cd frontend
npm install
cd ..
```

Use `requirements.txt` instead of `requirements-dev.txt` when pytest is not needed.

### 3. Configure the environment

Copy `.env.example` to `.env` and replace the placeholders:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite

GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com

SECRET_KEY=replace_with_a_long_random_secret
CAREERGRID_ENV=development
FLASK_DEBUG=false

ADZUNA_APP_ID=optional_adzuna_app_id
ADZUNA_APP_KEY=optional_adzuna_app_key
```

`GEMINI_API_KEY`, Firebase configuration, and `SECRET_KEY` are server-only. Do not expose them through Vite variables. Adzuna credentials are optional; local/demo jobs remain available when they are missing or the service is unavailable.

Generate a Flask secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Development uses a temporary random secret if `SECRET_KEY` is absent, which resets sessions when Flask restarts. Production refuses to start without `SECRET_KEY`.

Create a Firebase Realtime Database, download an Admin SDK service-account file, and point `GOOGLE_APPLICATION_CREDENTIALS` to it. `.env`, common Firebase credential filenames, virtual environments, `frontend/node_modules/`, and `frontend/dist/` are ignored by Git.

## Running locally

Start Flask from the repository root:

```bash
python app.py
```

In another terminal, start Vite:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite (normally `http://127.0.0.1:5173`). Flask normally listens on `http://127.0.0.1:5000`; the Vite proxy forwards API, auth, form-action, and shared-static requests there.

The optional live Gemini connectivity check is separate from the automated suite:

```bash
python test_gemini.py
```

## Tests and build

From the repository root:

```bash
python -m pytest -q
python -m compileall -q .
```

From `frontend/`:

```bash
npm test
npm run build
npm audit
```

`npm run build` writes generated assets to `frontend/dist/`. That directory and `frontend/node_modules/` are build/install artifacts and are not committed.

## Security notes

- Passwords are stored using Werkzeug hashing; password hashes are never returned by browser APIs.
- Firebase records are scoped under the authenticated user's server-side identifier.
- Candidate APIs expose allow-listed report fields and public scenario/question data.
- Private prompts, expected solutions, scenario context, and rubrics stay on the server.
- Simulated commands are validated or interpreted in browser state; the app does not offer arbitrary shell execution.
- `.env`, Firebase service-account files, caches, bytecode, coverage output, databases, logs, dependencies, and frontend builds are ignored.

## Known limitations

- Career and company coverage is intentionally limited to the scenarios included in this project.
- Firebase and Gemini features require network access and valid server credentials.
- Adzuna listings are optional and can fall back to local/demo data.
- Microphone interviews require browser permission and MediaRecorder support; automated tests do not validate real microphones or speech services.
- The simulated terminal supports a controlled command model and is not a real shell. GitHub URLs and pull requests are fictional simulation artifacts.
- Flask/Jinja fallback views remain during the incremental migration and may not match every React interaction exactly.
- Vite's production build is verified, but Flask does not currently serve `frontend/dist/`; deployment must add SPA hosting and deep-link fallback routing.
- End-to-end behavior with production Firebase/Gemini credentials still requires a configured manual environment.
