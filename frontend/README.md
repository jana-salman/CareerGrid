# CareerGrid React foundation

This directory is the incremental React/Vite frontend for CareerGrid. The
existing Flask/Jinja frontend remains the working application until individual
pages are migrated and verified.

## Local development

Run Flask on `http://127.0.0.1:5000`, then start Vite from this directory:

```bash
npm install
npm run dev
```

Browser requests to relative `/api/...` paths are proxied to Flask. The shared
request helper always includes the existing Flask session cookie. Do not add
hardcoded Flask origins to components and do not place secrets in Vite
environment variables.

## Frontend responsibilities

- Components and pages render browser UI and hold interaction state.
- `routeDefinitions.js` preserves the current CareerGrid URL shapes.
- `services/` is the only frontend networking layer. Components should call a
  named service function instead of calling `fetch()` directly.
- Gemini, Firebase, persistence, authentication checks, private prompts,
  rubrics, and scoring remain in Flask.

## State guidance for page migration

- Use `useState` for state owned by one page or component.
- Derive values during rendering instead of storing duplicate state.
- Use `useEffect` only to synchronize with an external system or to perform
  lifecycle-bound data loading. Do not use effects for ordinary calculations.
- Introduce a custom hook only when real components repeat stateful behavior.
- Introduce React Context only for state genuinely shared across a meaningful
  section of the application, such as authenticated session identity after
  migrated pages need it.
- Keep server data in the page or feature that loads it until multiple distant
  consumers demonstrate a need for shared ownership.

No global Context provider or custom state hook exists yet because the
placeholder routes do not share application state. Add them when migrated UI
creates a concrete requirement. Redux and other global state libraries are not
part of this architecture.
