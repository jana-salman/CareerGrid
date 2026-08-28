# CareerGrid React client

This directory contains CareerGrid's React 19 and Vite client. React Router owns the migrated home/catalog, dashboard, workplace, workplace-report, interview, and interview-review routes. Flask remains the API, authentication, persistence, and AI boundary; Jinja templates remain available for auth and verified fallbacks.

## Local development

Run Flask on `http://127.0.0.1:5000`, then run:

```bash
npm install
npm run dev
```

Vite proxies relative API requests, auth routes, server form actions, and `/static` assets to Flask. The shared API helper includes the Flask session cookie. Components must not hard-code a Flask origin, access Firebase directly, or place server secrets in Vite environment variables.

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

The production build is emitted to ignored `dist/`. The current Flask application does not serve that directory, so deployment requires separate SPA hosting (including deep-link fallback) or explicit Flask build integration.
