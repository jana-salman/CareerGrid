import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('simulation-only body styling is scoped and cleaned up on workspace unmount', async () => {
  const [desktop, desktopCss] = await Promise.all([
    read('src/simulation/SimulationDesktop.jsx'),
    read('../static/css/simulation/desktop.css'),
  ])

  assert.doesNotMatch(desktopCss, /\r?\nbody\s*\{\s*overflow:\s*hidden;/)
  assert.match(desktopCss, /body\.simulation-route,[\s\S]*?body:has\(#careergrid-workspace\)[\s\S]*?overflow:\s*hidden;/)
  assert.match(desktop, /document\.body\.classList\.add\('simulation-route'\)/)
  assert.match(desktop, /document\.body\.classList\.remove\('simulation-route'\)/)
})

test('company page keeps the legacy scrolling layout and job actions', async () => {
  const company = await read('src/pages/CompanyPage.jsx')

  assert.match(company, /className="career-page"/)
  assert.match(company, /Back to Positions/)
  assert.match(company, /className="job-list"/)
  assert.match(company, /className="job-status"/)
  assert.match(company, /company\.status/)
  assert.match(company, /Enter Workspace/)
  assert.match(company, /catalog\?\.companies\.map/)
})

test('Dashboard remains in its dark shell while loading and preserves all history controls', async () => {
  const dashboard = await read('src/pages/DashboardPage.jsx')
  const shellStart = dashboard.indexOf('<div className="career-page dashboard-page">')
  const loadingBranch = dashboard.indexOf('!dashboard ?')

  assert.ok(shellStart >= 0 && shellStart < loadingBranch)
  assert.match(dashboard, /className="history-panel dashboard-loading"/)
  assert.match(dashboard, /Loading your dashboard…/)
  for (const text of [
    'Welcome back',
    'Simulations',
    'Completed',
    'Average Score',
    'Your Simulations',
    'View Feedback',
    'Resume Workspace',
  ]) assert.ok(dashboard.includes(text), `Dashboard must retain ${text}`)
})

test('Dashboard Home returns to authenticated Home while Careers remains separate', async () => {
  const [dashboard, home] = await Promise.all([
    read('src/pages/DashboardPage.jsx'),
    read('src/pages/HomePage.jsx'),
  ])

  assert.match(dashboard, /<Link to="\/">Home<\/Link>/)
  assert.doesNotMatch(dashboard, /<Link to="\/career">Home<\/Link>/)
  assert.match(home, /<Link to="\/career">Careers<\/Link>/)
})

test('Dashboard is prefetched, rendered from session-scoped memory, and refreshed in place', async () => {
  const [careerNav, dashboard, home] = await Promise.all([
    read('src/components/CareerNav.jsx'),
    read('src/pages/DashboardPage.jsx'),
    read('src/pages/HomePage.jsx'),
  ])

  assert.match(careerNav, /prefetchDashboard\(\)/)
  assert.match(careerNav, /<Link to="\/dashboard"/)
  assert.doesNotMatch(careerNav, /<a href="\/dashboard"/)
  assert.match(home, /setDashboardSession\(session\.user\.id\)/)
  assert.match(home, /prefetchDashboard\(\)/)
  assert.match(home, /onClick=\{clearDashboardCache\}/)
  assert.match(dashboard, /useState\(\(\) => getCachedDashboard\(\)\)/)
  assert.match(dashboard, /refreshDashboard\(\)/)
  assert.match(dashboard, /onClick=\{clearDashboardCache\}/)
})

test('workspace and Mail identity come from the authenticated session API', async () => {
  const [desktop, mail] = await Promise.all([
    read('src/simulation/SimulationDesktop.jsx'),
    read('src/simulation/apps/MailApp.jsx'),
  ])

  assert.match(desktop, /getAuthenticatedSession\(\)/)
  assert.match(desktop, /setUserIdentity\(authenticatedSession\.user\)/)
  assert.match(desktop, /<strong>\{userName\}<\/strong>/)
  assert.match(desktop, /<div className="user-avatar">\{userInitial\}<\/div>/)
  assert.match(mail, /sender: userName/)
  assert.match(mail, /<strong>\{userName\}<\/strong>/)
  assert.doesNotMatch(desktop, /<strong>User<\/strong>|<div className="user-avatar">U<\/div>/)
  assert.doesNotMatch(mail, /<strong>User<\/strong>|sender: 'You'/)
})
