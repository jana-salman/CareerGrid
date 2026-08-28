# CareerGrid React client

This directory contains CareerGrid's React 19 and Vite client. React Router owns all user-facing pages, including authentication, home/catalog, dashboard, workplace, workplace-report, interview, and interview-review routes. Flask remains the API, session, persistence, and AI boundary.

## Local development

Run Flask on `http://127.0.0.1:5000`, then run:

```bash
npm install
npm run dev
```

Vite proxies relative API requests, backend form actions, the legacy-compatible logout route, and `/static` assets to Flask. The shared API helper includes the Flask session cookie. Components must not hard-code a Flask origin, access Firebase directly, or place server secrets in Vite environment variables.

## Structure and responsibilities

- `src/router.jsx` defines client routing.
- `src/pages/` contains route-level views.
- `src/services/` is the only browser networking layer.
- `src/simulation/` contains the desktop applications and simulated repository state.
- Components own presentation and interaction state; Flask owns authentication, authorization, Gemini, Firebase, private prompts/rubrics, scoring, and persistence.
- Git, GitHub, terminal, and filesystem behavior is simulated in browser state and never executes against the developer's machine or a real GitHub account.

## Checks

```bash
npm test
npm run build
npm audit
```

The production build is emitted to ignored `dist/`. Flask serves that directory, including fingerprinted assets and an API-safe React Router fallback, so `npm run build` followed by `python app.py` runs the production-style application without Vite.
