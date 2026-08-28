import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const readSource = (path) => readFile(new URL(path, import.meta.url), 'utf8')

test('React workplace report preserves the legacy report sections and class contract', async () => {
  const report = await readSource('../src/pages/WorkplaceReportPage.jsx')

  for (const className of [
    'review-page',
    'review-nav',
    'review-container',
    'review-header',
    'score-section',
    'performance-grid',
    'feedback-columns',
    'advisor-section',
    'next-step-list',
    'next-actions',
  ]) {
    assert.match(report, new RegExp(className))
  }

  assert.match(report, /CareerGrid · Task Review Report/)
  assert.match(report, /← Back to workspace/)
  assert.match(report, /Performance Breakdown/)
  assert.match(report, /Recommended Next Steps/)
})

test('report route restores legacy scrolling without leaking report state', async () => {
  const [index, report, reportCss, desktop, desktopCss] = await Promise.all([
    readSource('../index.html'),
    readSource('../src/pages/WorkplaceReportPage.jsx'),
    readSource('../../static/css/task_review.css'),
    readSource('../src/simulation/SimulationDesktop.jsx'),
    readSource('../../static/css/simulation/desktop.css'),
  ])

  assert.match(index, /\/static\/css\/task_review\.css/)
  assert.match(desktopCss, /body\s*\{[\s\S]*?overflow:\s*hidden;/)
  assert.match(reportCss, /body\.workplace-report-route\s*\{[\s\S]*?overflow-y:\s*auto;/)
  assert.match(report, /document\.body\.classList\.add\('workplace-report-route'\)/)
  assert.match(report, /document\.body\.classList\.remove\('workplace-report-route'\)/)
  assert.match(report, /document\.head\.appendChild\(stylesheet\)/)
  assert.match(report, /originalPosition\.parentNode\.replaceChild\(stylesheet, originalPosition\)/)
  assert.match(desktop, /originalPosition\.parentNode\.replaceChild\(theme, originalPosition\)/)
})

test('workplace report preserves all legacy actions and retry inputs', async () => {
  const report = await readSource('../src/pages/WorkplaceReportPage.jsx')

  assert.match(report, /report\.interview_unlocked &&/)
  assert.match(report, /\/simulation\/attempts\/\$\{encodeURIComponent\(attemptId\)\}\/interview\/start/)
  assert.match(report, /Start Job Interview/)
  assert.match(report, /action="\/simulation\/workplace\/start"/)
  for (const field of ['career_id', 'position_id', 'company_id', 'job_source']) {
    assert.match(report, new RegExp(`name="${field}"`))
  }
  assert.match(report, /Try Again/)
  assert.match(report, /to="\/career">[\s\S]*Explore Careers/)
  assert.match(report, /to="\/dashboard">View Dashboard →/)
})

test('Vite proxies only the existing legacy interview start action to Flask', async () => {
  const config = await readSource('../vite.config.js')

  assert.match(config, /\^\/simulation\/attempts\/\[\^\/\]\+\/interview\/start\$/)
  assert.doesNotMatch(config, /\/interview\/\*|\/simulation\/attempts':/)
})
