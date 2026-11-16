import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  readableList,
  roadmapForDisplay,
  safeExternalUrl,
} from '../src/pages/reportRoadmap.js'

const readSource = (path) => readFile(new URL(path, import.meta.url), 'utf8')

const resource = {
  id: 'pytest-parametrize',
  title: 'How to parametrize fixtures and test functions',
  provider: 'pytest documentation',
  url: 'https://docs.pytest.org/en/stable/how-to/parametrize.html',
  relevance: 'Covers the empty and duplicate inputs you missed.',
}

test('roadmap steps are readable sentences, never object text', () => {
  const { status, items } = roadmapForDisplay({
    personalized_roadmap: [{
      skill: 'Edge-case testing',
      evidence: 'tests/test_orders.py has no empty-cart case.',
      gap: 'Empty input is untested.',
      next_steps: ['Add a parametrized test.', "{'skill': 'Other', 'next_steps': ['x']}", { step: 'object' }, 'Add a parametrized test.', 42],
      resources: [resource],
    }],
  })
  assert.equal(status, 'available')
  assert.deepEqual(items[0].steps, ['Add a parametrized test.', '42'])
  assert.ok(!JSON.stringify(items).includes("{'skill'"))
})

test('each skill renders once with only its own content', () => {
  const { items } = roadmapForDisplay({
    personalized_roadmap: [
      { skill: 'Git workflow', evidence: 'Pushed to main.', gap: '', next_steps: ['Use a branch.'], resources: [] },
      { skill: 'git workflow', evidence: 'dup', gap: '', next_steps: ['Write the PR description.'], resources: [resource] },
      { skill: 'Communication', evidence: 'Short reply.', gap: '', next_steps: ['Name the files changed.'], resources: [] },
    ],
  })
  assert.deepEqual(items.map((item) => item.skill), ['Git workflow', 'Communication'])
  assert.deepEqual(items[0].steps, ['Use a branch.', 'Write the PR description.'])
  assert.deepEqual(items[1].steps, ['Name the files changed.'])
  assert.equal(items[1].resources.length, 0)
})

test('learning links are limited to safe http(s) URLs', () => {
  assert.equal(safeExternalUrl(resource.url), resource.url)
  for (const unsafe of ['javascript:alert(1)', 'data:text/html,x', 'https://user:pw@example.com', ' ', 'ftp://example.com', 'https://a.b/x y']) {
    assert.equal(safeExternalUrl(unsafe), '', unsafe)
  }
  const { items } = roadmapForDisplay({
    personalized_roadmap: [{
      skill: 'Testing', evidence: 'e', gap: 'g', next_steps: ['s'],
      resources: [{ ...resource, url: 'javascript:alert(1)' }, resource, resource, { title: '', url: 'https://x.org' }],
    }],
  })
  assert.deepEqual(items[0].resources, [{
    url: resource.url, title: resource.title, provider: resource.provider, relevance: resource.relevance,
  }])
})

test('an unrecoverable or empty roadmap is reported as unavailable, not invented', () => {
  assert.equal(roadmapForDisplay({ roadmap_status: 'unavailable', personalized_roadmap: [] }).status, 'unavailable')
  assert.equal(roadmapForDisplay({ personalized_roadmap: [{ skill: 'x', next_steps: ["{'a': 1}"] }] }).status, 'unavailable')
  assert.equal(roadmapForDisplay({}).status, 'none')
  assert.deepEqual(readableList(['A', 'a', { text: 'obj' }, "{'k': 1}", '', 'B']), ['A', 'B'])
})

test('the report renders clickable, accessible links in new tabs and keeps retry on the same assignment', async () => {
  const report = await readSource('../src/pages/WorkplaceReportPage.jsx')
  assert.match(report, /href=\{resource\.url\}/)
  assert.match(report, /target="_blank"/)
  assert.match(report, /rel="noopener noreferrer"/)
  assert.match(report, /\(opens in a new tab\)/)
  assert.match(report, /No suitable free learning resource is listed for this skill yet\./)
  assert.match(report, /Roadmap Unavailable/)
  assert.match(report, /name="retry_attempt_id" value=\{attemptId\}/)
  assert.doesNotMatch(report, /evaluation\.personalized_roadmap\.map/)
})
