import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  commit,
  createBranch,
  createPullRequest,
  createRepository,
  diff,
  loadRepository,
  persistRepository,
  push,
  saveFile,
  stage,
  switchBranch,
  validatePullRequest,
} from '../src/simulation/state/repositoryModel.js'

const files = [
  { path: 'src/app.py', content: 'before app' },
  { path: 'src/utils.py', content: 'before utils' },
]

function featureRepository({ pushBranch = true } = {}) {
  let repository = createRepository(files, { name: 'backend-api', path: '/Projects/backend-api' })
  repository = createBranch(repository, 'feature/fix-users').repository
  repository = saveFile(repository, 'src/app.py', 'after app').repository
  repository = stage(repository, ['src/app.py']).repository
  repository = commit(repository, 'Fix user lookup').repository
  if (pushBranch) repository = push(repository).repository
  return repository
}

test('branches keep independent working trees and block unsafe switching', () => {
  let repository = createRepository(files)
  repository = createBranch(repository, 'feature/api').repository
  repository = saveFile(repository, 'src/app.py', 'feature content').repository

  const blocked = switchBranch(repository, 'main')
  assert.match(blocked.error, /Commit or discard/)

  repository = stage(repository, '.').repository
  repository = commit(repository, 'Update API').repository
  repository = switchBranch(repository, 'main').repository
  assert.equal(repository.branches.main.workingTree['src/app.py'].content, 'before app')
  assert.equal(repository.branches['feature/api'].workingTree['src/app.py'].content, 'feature content')
})

test('staging records the staged snapshot rather than later unstaged edits', () => {
  let repository = createRepository(files)
  repository = createBranch(repository, 'feature/staged-snapshot').repository
  repository = saveFile(repository, 'src/app.py', 'staged content').repository
  repository = stage(repository, ['src/app.py']).repository
  repository = saveFile(repository, 'src/app.py', 'later working content').repository

  const result = commit(repository, 'Commit staged content')
  const branch = result.repository.branches['feature/staged-snapshot']

  assert.equal(result.filesChanged, 1)
  assert.equal(branch.headSnapshot['src/app.py'].content, 'staged content')
  assert.equal(branch.workingTree['src/app.py'].content, 'later working content')
  assert.deepEqual(diff(result.repository), [{
    after: 'later working content',
    before: 'staged content',
    path: 'src/app.py',
  }])
})

test('push and pull request records preserve the simulated repository contract', () => {
  let repository = featureRepository()
  const result = createPullRequest(repository, {
    baseBranch: 'main',
    compareBranch: 'feature/fix-users',
    description: 'Fixes lookup handling and verifies missing users.',
    title: 'Fix user lookup',
  })
  repository = result.repository

  assert.equal(result.pullRequest.id, 1)
  assert.equal(result.pullRequest.url, 'https://github.com/careergrid-sim/backend-api/pull/1')
  assert.deepEqual(
    Object.keys(result.pullRequest).slice(0, 8),
    ['repositoryPath', 'baseBranch', 'compareBranch', 'id', 'url', 'status', 'title', 'description'],
  )
  assert.equal(repository.remote.branchHeads['feature/fix-users'], repository.branches['feature/fix-users'].commits.at(-1).id)
  assert.equal(validatePullRequest(repository, result.pullRequest)?.id, 1)
})

test('invalid Git and pull request operations are rejected', () => {
  const repository = createRepository(files)
  assert.match(createBranch(repository, 'bad branch').error, /Invalid branch/)
  assert.match(switchBranch(repository, 'missing').error, /does not exist/)
  assert.match(commit(repository, 'Nothing').error, /No staged changes/)

  const unpushed = featureRepository({ pushBranch: false })
  assert.match(createPullRequest(unpushed, {
    baseBranch: 'main',
    compareBranch: 'feature/fix-users',
    title: 'Fix user lookup',
  }).error, /Push this branch/)
})

test('repository persistence restores workflow state for an attempt', () => {
  const values = new Map()
  const storage = {
    getItem: (key) => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
  }
  const repository = featureRepository()

  persistRepository('attempt-42', repository, storage)
  const restored = loadRepository('attempt-42', [], {}, storage)

  assert.deepEqual(restored, repository)
  assert.equal(restored.currentBranch, 'feature/fix-users')
  assert.equal(restored.branches['feature/fix-users'].headSnapshot['src/app.py'].content, 'after app')
})
