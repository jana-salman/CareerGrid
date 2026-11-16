# CareerGrid

CareerGrid is an AI-assisted career-practice platform for realistic workplace simulations and structured job interviews.

React owns the user interface, while Flask serves the production build and remains the session, API, persistence, and AI boundary. Firebase Realtime Database stores users and attempts, while Google Gemini generates or evaluates selected scenarios, advisor replies, and interview content.

## Features

* Registration and login with Flask sessions and Werkzeug password hashing
* Career, position, and company selection
* React workplace desktop with simulated Mail, Files, VS Code, Terminal, Browser, Git, and GitHub applications
* Browser-side simulated repository, commits, pushes, and pull requests; CareerGrid never executes real Git commands or contacts GitHub
* Backend Developer scenarios, including a deterministic TechNova demonstration
* Five-step Frontend Developer simulation with a validated deterministic fallback
* Evidence-based workplace evaluation and progressive advisor guidance
* Timed microphone interviews with transcription and speech analysis
* Server-side private rubrics and final interview evaluation
* Dashboard history and browser-safe workplace/interview reports

The normal learning flow is:

```text
Register or log in
        ↓
Choose career, position, and company
        ↓
Complete a workplace simulation
        ↓
Receive an evaluation
        ↓
Unlock the interview at a score of 85 or higher
        ↓
Complete the interview
        ↓
Review the final report and dashboard history
```

## Technology Stack

### Client

* React 19
* React Router
* Vite
* JavaScript
* CareerGrid's shared CSS system
* Browser MediaRecorder and Web Audio APIs for interview capture

The SPA entry point is `frontend/index.html`, routes live in `frontend/src/router.jsx`, and browser API calls go through named modules in `frontend/src/services/`.

Requests use relative `/api/...` URLs and include the existing Flask session cookie.

The production build is served by Flask from the generated `frontend/dist/` directory. Shared styles and images remain under `static/` and retain their existing URLs because the React UI deliberately reuses CareerGrid's established visual system.

### Server

* Python 3.11+
* Flask
* Flask Blueprints
* Flask-Limiter for authentication rate limiting
* Werkzeug password hashing
* Signed Flask sessions
* Firebase Admin SDK
* Firebase Realtime Database
* Google Gen AI SDK (Gemini)
* Requests for Adzuna job listings
* python-dotenv for local configuration

### Tests

* pytest
* Flask test client
* Node's built-in test runner for frontend contracts and simulation state
* Mocked Firebase, Gemini, and external-service boundaries in automated tests

## Architecture

```text
CareerGrid/
├── app.py
│   Flask application factory and entry point
│
├── config.py
│   Environment-backed server configuration
│
├── constants.py
│   Stable application limits and identifiers
│
├── routes/
│   Flask Blueprints and HTTP/API layer
│
│   ├── api.py
│   │   Health and authenticated-session API
│   │
│   ├── auth.py
│   │   Session login, registration, and logout APIs
│   │
│   ├── careers.py
│   │   Career, position, company, and job APIs
│   │
│   ├── dashboard.py
│   │   Attempt-history API
│   │
│   ├── simulations.py
│   │   Workplace simulation APIs and backend actions
│   │
│   ├── interviews.py
│   │   Interview workspace, answer, and review APIs
│   │
│   └── frontend.py
│       Vite asset serving and safe SPA deep-link fallback
│
├── services/
│   Domain logic and external integrations
│
│   ├── ai/
│   │   AI and Gemini application services
│   │
│   │   ├── advisor_service.py
│   │   ├── evaluation_service.py
│   │   ├── gemini_service.py
│   │   ├── gemini_utils.py
│   │   ├── interview_service.py
│   │   └── scenario_generation_service.py
│   │
│   ├── simulation/
│   │   Career, workplace, demo, and persistence services
│   │
│   │   ├── career_service.py
│   │   ├── job_service.py
│   │   ├── simulation_storage.py
│   │   ├── frontend_workplace_scenario_service.py
│   │   ├── frontend_workplace_progress_service.py
│   │   ├── backend_demo_scenario_service.py
│   │   └── backend_demo_interview_service.py
│   │
│   └── user/
│       User and Firebase services
│
│       ├── firebase_service.py
│       └── user_service.py
│
├── ai_prompt/
│   Server-side prompt and rubric definitions
│
│   ├── prompts/
│   │   Versioned Gemini prompt builders
│   │
│   └── rubrics/
│       Versioned private evaluation rubrics
│
├── frontend/
│   React + Vite application
│
│   ├── index.html
│   │   Vite/React entry document
│   │
│   ├── src/
│   │   ├── router.jsx
│   │   │   React Router configuration
│   │   │
│   │   ├── components/
│   │   │   Reusable UI components
│   │   │
│   │   ├── pages/
│   │   │   Authentication, catalog, dashboard, and report pages
│   │   │
│   │   ├── services/
│   │   │   Browser-safe Flask API clients
│   │   │
│   │   ├── interview/
│   │   │   Interview UI and interview-specific frontend logic
│   │   │
│   │   └── simulation/
│   │       Simulated desktop, applications, and repository state
│   │
│   └── tests/
│       React service and simulation contract tests
│
├── static/
│   Shared CSS and images used by React
│
└── tests/
    Flask, API, service, AI, simulation, and persistence tests
```

`app.py` creates the Flask application, loads configuration, registers the route groups from `routes/`, and initializes application-wide integrations such as authentication rate limiting.

Routes handle HTTP requests, session ownership, redirects, backend actions, and browser-safe serialization.

The service layer is divided by responsibility:

* `services/ai/` contains Gemini integration and AI-related business logic.
* `services/simulation/` contains career, workplace, demo, and persistence logic.
* `services/user/` contains Firebase access and user-account logic.
* `ai_prompt/` contains versioned prompt templates and private rubrics used by the server-side AI services.

React Router owns all user-facing routes, including authentication, catalog, dashboard, workplace, reports, and interviews.

During development, Vite proxies API requests, backend actions, and shared static assets to Flask.

In production-style execution, Flask serves Vite's generated `index.html` and fingerprinted assets. Its SPA fallback deliberately excludes `/api`, `/assets`, `/static`, and explicit backend actions so missing API endpoints are not accidentally converted into React pages.

Authentication remains server-side. JSON login and registration requests establish a signed Flask session, while the browser receives only browser-safe user identity data.

## Privacy and AI Boundaries

Gemini calls run only on the Flask server.

Prompt builders and private rubrics are versioned under:

```text
ai_prompt/prompts/
ai_prompt/rubrics/
```

Current versioned modules include:

* `scenario_v1`
* `advisor_v1`
* `workplace_evaluation_v1`
* `workplace_evaluation_v2`
* `interview_v1`
* `workplace_v1`

Each stored workplace scenario separates:

```text
public_scenario
private_context
```

Interview records similarly separate:

```text
public_questions
private_rubrics
```

Candidate-facing endpoints construct explicit browser-safe response objects. Workplace evaluation responses pass through a public-field allow-list before being exposed to React.

Private scenario context, expected solutions, evaluation instructions, prompts, and rubrics remain server-side.

Workplace scenario validation checks:

* public/private data separation
* relative project paths
* allowed text-file types
* duplicate project files
* content-size limits
* resource integrity
* safe simulated commands
* solution-leak patterns
* payload-size limits

Frontend Developer scenarios additionally validate:

* five ordered tasks
* required project files
* inbox and incident linkage
* viewport metadata
* expected patch structure
* controlled terminal commands

Git, GitHub, the terminal, filesystem, repository commits, pushes, and pull requests inside the workplace are simulations implemented by CareerGrid.

They do not:

* execute real operating-system commands
* mutate the CareerGrid source repository
* access the user's local filesystem
* push to a real Git repository
* contact GitHub

## Firebase Data Model

At a high level, CareerGrid stores:

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

Firebase access uses the Admin SDK on the Flask server.

The React client does not receive Firebase credentials and does not connect directly to Firebase Realtime Database.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/jana-salman/CareerGrid.git
cd CareerGrid
```

### 2. Create a Python environment

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

### 3. Install dependencies

For development:

```bash
python -m pip install -r requirements-dev.txt

cd frontend
npm install
cd ..
```

Use `requirements.txt` instead of `requirements-dev.txt` when pytest and other development-only dependencies are not required.

### 4. Configure the Environment

Copy `.env.example` to `.env`, then follow the **API Keys and Credentials Setup** section below to generate and configure the required credentials.

## API Keys and Credentials Setup

Before running CareerGrid, configure the required server-side credentials in a `.env` file.

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

CareerGrid requires:

- Google Gemini API key
- Firebase Realtime Database
- Firebase Admin SDK service-account credentials
- Flask secret key
- Adzuna API credentials


### 1. Google Gemini API Key — Required

CareerGrid uses Google Gemini for:

* workplace scenario generation
* advisor feedback
* workplace evaluation
* interview question generation
* interview evaluation

Create or manage a Gemini API key through Google AI Studio:

* Google AI Studio: https://ai.google.dev/aistudio
* Gemini API documentation: https://ai.google.dev/gemini-api/docs
* API key documentation: https://ai.google.dev/gemini-api/docs/api-key

After creating the key, add it to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

The Gemini API key is used only by the Flask backend and must never be placed in frontend code or Vite environment variables.

### 2. Firebase Realtime Database — Required

CareerGrid uses Firebase Realtime Database to store:

* registered users
* workplace simulation attempts
* interview attempts
* responses
* evaluations

Create a Firebase project:

* Firebase Console: https://console.firebase.google.com/

Then create a Realtime Database for the project.

Documentation:

* Firebase Realtime Database: https://firebase.google.com/docs/database
* Firebase Admin SDK setup: https://firebase.google.com/docs/admin/setup

Copy the Realtime Database URL and add it to `.env`:

```env
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com
```

The exact database URL is displayed in the Realtime Database section of the Firebase Console.

### 3. Firebase Admin SDK Service Account — Required

The Flask backend accesses Firebase through the Firebase Admin SDK.

In the Firebase Console:

1. Open your Firebase project.
2. Open **Project settings**.
3. Select **Service accounts**.
4. Select **Firebase Admin SDK**.
5. Click **Generate new private key**.
6. Download the generated JSON file.
7. Place the JSON file inside the local CareerGrid project directory.

For example:

```text
CareerGrid/
├── firebase-service-account.json
├── app.py
├── frontend/
└── ...
```

Then configure its path in `.env`:

```env
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
```

The Firebase service-account file contains private credentials and must never be committed or publicly uploaded.

### 4. Flask Secret Key — Required

CareerGrid uses signed Flask sessions for authentication.

Generate a secure secret key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated value into `.env`:

```env
SECRET_KEY=your_generated_secret_key_here
```

For local development:

```env
CAREERGRID_ENV=development
FLASK_DEBUG=false
```

When `CAREERGRID_ENV=production`, CareerGrid requires a persistent `SECRET_KEY` and enables production-secure session cookie behavior.

### 5. Adzuna API Credentials 

CareerGrid can use the Adzuna API to retrieve live job listings.

The application can still run without Adzuna credentials because local/demo job data is available as a fallback.

Register for Adzuna developer credentials:

* Adzuna Developer Portal: https://developer.adzuna.com/
* API overview and quick start: https://developer.adzuna.com/overview
* Interactive API documentation: https://developer.adzuna.com/activedocs

After registration, obtain an `app_id` and `app_key`.

Add them to `.env`:

```env
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

If these values are omitted, CareerGrid shows a clear "not configured" message and offers practice (demo) companies, which are labelled as practice simulations, not live vacancies.

Live-listing country and location are configured on the server:

```env
JOB_SEARCH_COUNTRY=us      # at au be br ca ch de es fr gb in it mx nl nz pl sg us za
JOB_SEARCH_LOCATION=       # optional city/region inside that country
```

**Lebanon.** Adzuna does not publish a Lebanon (`lb`) endpoint, so CareerGrid never sends Lebanon requests to Adzuna and never relabels another country's results as Lebanese. Selecting Lebanon shows an honest "unavailable" state unless a Jooble partner key is configured:

```env
JOOBLE_API_KEY=            # optional; request one at https://jooble.org/api/about
```

With a Jooble key, CareerGrid queries Jooble's documented REST API with `location=Lebanon` and keeps only listings whose location is in Lebanon. Jooble's Lebanese coverage has not been verified, so test it with your key before relying on it. Every live card shows its source, location, and a link to the original listing.

When a user picks a live listing, its title and description are sanitized and passed to Gemini only as untrusted reference data, so the task reflects the listing's responsibilities without the employer being presented as the author.

### Final `.env` Example

After completing the setup, `.env` should look similar to:

```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite

# Firebase
GOOGLE_APPLICATION_CREDENTIALS=firebase-service-account.json
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com

# Flask
SECRET_KEY=your_generated_secret_key_here
CAREERGRID_ENV=development
FLASK_DEBUG=false

# Adzuna job listings
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

Never commit:

* `.env`
* Firebase service-account JSON files
* real API keys or credentials



## Running Locally

### Production-style local execution

Build the React frontend:

```bash
cd frontend
npm run build
cd ..
```

Then start Flask from the repository root:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Flask serves the compiled React application and supports direct React Router links and browser refreshes.

After frontend source code changes, run `npm run build` again before using Flask-only production-style execution.

### Frontend development mode

Run Flask in one terminal:

```bash
python app.py
```

Then start Vite in another terminal:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite, normally:

```text
http://127.0.0.1:5173
```

Flask normally listens on:

```text
http://127.0.0.1:5000
```

The Vite proxy forwards API requests, backend actions, and shared static-file requests to Flask.

## Gemini Connectivity Check

The optional live Gemini connectivity check is separate from the automated test suite:

```bash
python test_gemini.py
```

This requires a valid `GEMINI_API_KEY` and network access.

## Tests and Build

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

`npm run build` writes generated assets to:

```text
frontend/dist/
```

`frontend/dist/` and `frontend/node_modules/` are generated or installed artifacts and are not committed.

## Security Notes

* Passwords are stored using Werkzeug password hashing.
* Password hashes are never returned by browser APIs.
* New registrations require passwords of at least 8 characters.
* Login requests are rate-limited to 10 attempts per minute per client address.
* Registration requests are rate-limited to 5 attempts per minute per client address.
* No global API rate limit is applied.
* Flask limits incoming request size before interview audio is processed.
* The interview endpoint retains an additional application-level audio-size validation check.
* Flask session cookies explicitly use `SameSite=Lax`.
* Session cookies use the `Secure` flag when `CAREERGRID_ENV=production`.
* Firebase records are scoped under the authenticated user's server-side identifier.
* Candidate APIs expose allow-listed report fields and public scenario/question data only.
* Private prompts, expected solutions, scenario context, and rubrics remain server-side.
* Gemini and Firebase credentials remain server-side and are never embedded in the React build.
* Simulated terminal commands are validated or interpreted inside the simulation model.
* CareerGrid does not provide arbitrary operating-system shell execution.
* `/api` routes remain isolated from the React SPA fallback.
* `.env`, Firebase service-account files, caches, bytecode, coverage output, local databases, logs, dependencies, and frontend builds are ignored by Git.

## Submitting Workplace Work

The Git-based workplace (Backend Developer) accepts two delivery routes. Both lead to the same confirmation, evaluation, feedback, and personalized roadmap:

* **Pull request:** `git switch -c feature/name` → edit and save → `git add .` → `git commit -m "..."` → `git push` → open a pull request in GitHub → reply to the task email with the PR link → reply `yes` to confirm.
* **Directly on main:** edit and save on `main` → `git add .` → `git commit -m "..."` → `git push` → reply to the task email saying the work is ready on main (no link needed) → reply `yes` to confirm.

Only committed and pushed work is reviewed. When you confirm, the submitted commit, its files, and the original-project baseline are frozen, so later edits cannot change what is evaluated. The comparison baseline is an immutable copy of the starter project taken when it is first extracted. Git workflow is scored separately from technical quality, so delivering to main does not invalidate working code. Questions such as "How do I submit without a PR?" get instructions instead of starting an assessment. If an evaluation fails or is interrupted, reply `retry`.

The Frontend Developer path keeps its five-step task panel. Step 3 reads the files you saved in VS Code, and step 5 lets you deliver by pull request or by pushing to main.

## Workplace Assignment Generation

Each practice company and position, and each live listing and position, has **one saved assignment**. The first launch generates and validates it; every later attempt copies it, with no Gemini call. Each attempt keeps its own copy, workspace (stored in the browser per attempt), submission, feedback and roadmap. Reopening an attempt resumes its work, and **Try Again** on the report starts a clean attempt with the same assignment.

* **Shared assignments** (`services/simulation/assignment_library.py`). Stored server-side under `shared_assignments/<key>` in Firebase (the browser APIs never return it, and private criteria stay there and in the attempt's private context). Keys: `practice-<career>-<position>-<company>`, or for listings `listing-<source>-<position>-<listing ref>-<requirements digest>`, where the listing ref is the provider URL without its tracking query. An edited listing therefore gets its own assignment, and one client cannot overwrite another listing's assignment by sending altered text. A practice company's assignment is replaced when its role profile changes materially (word-overlap similarity below 0.8), when `ASSIGNMENT_LIBRARY_VERSION` is bumped, or on request.
* **Versions.** Replacements are written as `versions/v<n>`; existing attempts keep the copy they started with. If a replacement fails, launches keep using the current version.
* **Concurrency.** One generator per key, claimed with a Firebase transaction (`lock`, expiring after 420 s). Concurrent launches wait for that result instead of generating again; if it never arrives they continue with the fallback.
* **Failures.** A failed generation is never saved as an assignment. The participant continues with the validated built-in assignment (recorded as `generation.source = "fallback"` on the attempt, and counted under `fallbacks` on the key). A cooldown, `ASSIGNMENT_RETRY_COOLDOWN_SECONDS` (default 900, doubling per consecutive failure, capped at 6 h), stops every launch from calling Gemini again.
* **Deliberate regeneration.** `python scripts/manage_assignments.py list` shows keys, versions, failures and fallbacks. `python scripts/manage_assignments.py regenerate --career software-developer --position backend-developer --company technova` (or `--key <key>`) replaces that assignment on its next launch and clears its cooldown.

* **Context.** Live listings pass their title and description to the generator as untrusted data. Adzuna returns only about the first 500 characters, so these are marked as excerpts and the prompt forbids inventing further employer requirements. Practice companies (TechNova, BrightSoft, PixelWorks, CloudByte) pass a defined role profile. The dedicated TechNova "Demo Challenge" card stays a fixed demo, because its interview depends on it.
* **One task per role, no rotation.** The prompt (`ai_prompt/prompts/scenario_v5.py`) asks for one realistic feature request or investigation that fits the job context, at roughly 30–60 minutes of connected work, without per-attempt type rotation or "different from recent tasks" instructions.
* **Structure.** The model fills in a JSON-schema-constrained draft with bounded list sizes: situation, requirements, code, README content, evidence and private rubric. Gemini enforces list sizes but not text lengths, so length is checked by the quality gate. The server assembles IDs, attachments, the inbox, the five Frontend steps and README sections such as Project structure, Verification and Deliverables (`services/ai/scenario_drafts.py`).
* **Pipelines.** `SCENARIO_GENERATION_PIPELINE=single` (default) asks for the whole draft in one call. `staged` first asks for a short task specification, checks it cheaply, then asks for the project, evidence and rubric for that exact plan; for Backend its schema requires one assessment per requirement. In live tests on 2026-11-16 the staged calls were slower (specification 14–182 s, project 101 s to over 165 s) than single drafts (25–33 s), and neither produced an accepted task, so staged is not the default.
* **Repairs never invent.** The server only formats and removes provably false details (a log line number past the end of a file). It never adds assessment criteria, file descriptions or evidence, and never drops a check; a draft with such a gap is rejected and the exact problems are returned to the model.
* **Gates.** `validate_workplace_scenario` and the quality gate in `services/ai/scenario_quality.py` check README sections, connected modules with real behaviour, tests that import the code, evidence, edge-case and preserve requirements, every requirement having a criterion, the starter not already satisfying the task, a title that names the work, and no solution leaks (including hint comments such as `# Should check ...`). Leak rejections quote the offending line.
* **Candidate archive.** Every candidate the model returns, accepted or rejected, is saved with its validation reasons under `instance/generation_candidates/<day>/<run>/` (gitignored), plus a `summary.json`. `python scripts/inspect_candidate.py <run folder>` prints an accepted task's brief, evidence and rubric together and runs its existing tests.
* **Bounded recovery.** `SCENARIO_GENERATION_BUDGET_SECONDS` (default 240) caps the total wait and each model call times out within it. `SCENARIO_GENERATION_MAX_ATTEMPTS` (default 4) caps returned drafts; a rejected draft's reasons are fed back to the next attempt. "Model overloaded" (503) errors back off and retry without using an attempt. Quota, authentication and unknown-model errors stop immediately. The browser gives up after 6 minutes and offers a retry that resumes the same attempt.
* **Fallback.** If no draft passes, a validated built-in assignment is used: the TechNova User Profile incident for Backend, or the product-page checkout incident for Frontend. `tests/test_assignment_projects.py` runs both projects for real.
* **Records.** Each attempt stores internal diagnostics under `generation` in Firebase: model, outcome (`generated`, `fallback` or `predefined_demo`), failure reason, per-attempt reasons and timings, assignment type, domain, context source and prompt version. These are never returned to the browser.

Model choice and its reasoning level are server settings: `GEMINI_SCENARIO_MODEL` and `GEMINI_SCENARIO_THINKING`. Generating a full assignment is the most demanding model call. To compare models on identical inputs with your own key, run `python scripts/compare_generation_models.py <model> [--pipelines single,staged] [--cases ...]`; each run counts against that model's quota and results are appended to `instance/generation_comparison/`.

## Known Limitations

* Career and company coverage is intentionally limited to the scenarios implemented in this project.
* Firebase and Gemini features require network access and valid server credentials.
* Microphone interviews require browser permission and MediaRecorder support.
* Automated tests cannot fully validate real microphones or external speech behavior.
* The simulated terminal supports a controlled command model and is not a real shell.
* GitHub URLs and pull requests created inside the workplace are fictional simulation artifacts.
* The simulated workspace cannot execute tests; verification described by the participant is treated as a written claim, and frontend "automated" results are static checks of submitted files.
* There is no experience-level selector yet; generated tasks target junior/intern level.
* Workspaces saved before this version have no stored original-project baseline. CareerGrid restores it only from the server's original scenario files (and labels it as restored); if that is impossible, direct-to-main submission asks the user to use a pull request instead.
* Production-style Flask execution requires `npm run build` after frontend source changes because `frontend/dist/` remains generated and uncommitted.
* End-to-end behavior with production Firebase/Gemini credentials still requires a properly configured runtime environment.

## Project Status

CareerGrid's main user interface is implemented in React and served by Flask in production-style execution.

The current architecture separates:

```text
React frontend
      ↓
Flask API and session layer
      ↓
Domain services
      ↓
Firebase / Gemini / Adzuna
```

Prompt templates and private rubrics remain isolated under `ai_prompt/`, while executable AI logic is organized under `services/ai/`.

This keeps the browser-facing application separate from persistence, authentication, AI evaluation, and private grading logic.
