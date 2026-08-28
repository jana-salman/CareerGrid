import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import { copyPullRequestLink } from '../src/simulation/state/pullRequestClipboard.js'

const url = 'https://github.com/careergrid-sim/backend-service/pull/7'

test('Copy PR Link writes the exact simulated pull request URL without changing PR state', async () => {
  const writes = []
  const pullRequest = Object.freeze({ id: 7, status: 'open', url })
  const before = structuredClone(pullRequest)
  const result = await copyPullRequestLink(pullRequest.url, {
    clipboard: { writeText: async (value) => writes.push(value) },
  })

  assert.deepEqual(writes, [url])
  assert.deepEqual(result, { copied: true, url })
  assert.deepEqual(pullRequest, before)
})

test('Copy PR Link preserves the legacy prompt fallback when Clipboard API fails', async () => {
  const prompts = []
  const result = await copyPullRequestLink(url, {
    clipboard: { writeText: async () => { throw new Error('denied') } },
    prompt: (...values) => prompts.push(values),
  })

  assert.equal(result.copied, false)
  assert.equal(result.usedPrompt, true)
  assert.deepEqual(prompts, [['Copy this pull request link:', url]])
})

test('the React PR detail retains the legacy button placement, label, and toast contract', async () => {
  const github = await readFile(new URL('../src/simulation/apps/GitHubApp.jsx', import.meta.url), 'utf8')
  const urlPosition = github.indexOf('className="github-pr-url"')
  const actionPosition = github.indexOf('Copy PR Link')

  assert.ok(urlPosition >= 0)
  assert.ok(actionPosition > urlPosition)
  assert.match(github, /github-form-actions/)
  assert.match(github, /github-secondary-button/)
  assert.match(github, /Pull request link copied/)
  assert.match(github, /github-toast/)
})
