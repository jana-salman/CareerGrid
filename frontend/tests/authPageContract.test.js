import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('React owns login and registration with the legacy visual contract', async () => {
  const [layout, login, register, router] = await Promise.all([
    read('src/components/AuthLayout.jsx'),
    read('src/pages/LoginPage.jsx'),
    read('src/pages/RegisterPage.jsx'),
    read('src/router.jsx'),
  ])

  assert.match(router, /path="\/login" element=\{<LoginPage \/>\}/)
  assert.match(router, /path="\/register" element=\{<RegisterPage \/>\}/)
  assert.match(layout, /\/static\/css\/auth\/login\.css/)
  assert.match(layout, /document\.body\.classList\.add\('careergrid-login'\)/)
  assert.match(layout, /document\.body\.classList\.remove\('careergrid-login'\)/)
  for (const className of ['login-shell', 'login-intro', 'career-puzzle', 'login-benefits', 'login-panel', 'login-card']) {
    assert.ok(layout.includes(className), `auth layout must retain .${className}`)
  }
  assert.match(login, /login\(\{ email, password \}\)/)
  assert.match(register, /register\(\{ fullName, email, password \}\)/)
  assert.doesNotMatch(`${login}${register}`, /localStorage|sessionStorage|Bearer|JWT/)
})

test('scenario generation failure remains a React-owned user-facing state', async () => {
  const [failurePage, desktop] = await Promise.all([
    read('src/pages/ScenarioUnavailablePage.jsx'),
    read('src/simulation/SimulationDesktop.jsx'),
  ])

  assert.match(failurePage, /Workspace scenario unavailable/)
  assert.match(failurePage, /Start a new attempt/)
  assert.match(desktop, /\['generating', 'generation_failed'\]/)
  assert.match(desktop, /<ScenarioUnavailablePage attempt=\{attempt\} \/>/)
})
