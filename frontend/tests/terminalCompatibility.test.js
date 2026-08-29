import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  commit,
  createBranch,
  createRepository,
  push,
  saveFile,
  stage,
  switchBranch,
} from '../src/simulation/state/repositoryModel.js'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('Workspace Guide ends after its existing instruction cards', async () => {
  const guide = await read('src/simulation/apps/AdvisorApp.jsx')

  assert.match(guide, /guideSteps\.map/)
  assert.doesNotMatch(guide, /Ask your advisor|Ask advisor|requestAdvisorGuidance|<textarea|<form/)
})

test('Terminal exposes the legacy simulated command and keyboard contracts', async () => {
  const terminal = await read('src/simulation/apps/TerminalApp.jsx')

  for (const command of [
    'git switch -c <branch>',
    'git switch <branch>',
    'git checkout -b <branch>',
    'git add <file>',
    'git add .',
    'git commit -m "message"',
    'git log',
    'git log --oneline',
    'git push',
  ]) assert.ok(terminal.includes(command), `Terminal help must include ${command}`)

  for (const key of ['ArrowUp', 'ArrowDown', 'Tab']) {
    assert.ok(terminal.includes(`event.key === '${key}'`), `Terminal must handle ${key}`)
  }
  for (const key of ['l', 'c', 'a', 'e', 'u', 'r']) {
    assert.ok(terminal.includes(`key === '${key}'`), `Terminal must handle Ctrl+${key.toUpperCase()}`)
  }

  assert.match(terminal, /event\.ctrlKey && event\.shiftKey/)
  assert.match(terminal, /onKeyDown=\{handleKeyDown\}/)
  assert.match(terminal, /setCwd\(target\)/)
  assert.doesNotMatch(terminal, /child_process|execSync|spawn\(|github\.com\/api|api\.github\.com/)
})

test('Terminal Git workflow continues to update only the simulated repository model', () => {
  let repository = createRepository(
    [{ path: 'profile.py', content: 'before' }],
    { name: 'user-profile-service', path: '/Projects/user-profile-service' },
  )

  repository = createBranch(repository, 'new-branch').repository
  repository = saveFile(repository, 'profile.py', 'after').repository
  repository = stage(repository, ['profile.py']).repository
  const committed = commit(repository, 'fixing-User-Profile-Api')
  assert.equal(committed.error, undefined)
  repository = committed.repository
  repository = push(repository).repository

  assert.equal(repository.currentBranch, 'new-branch')
  assert.equal(repository.branches['new-branch'].commits.at(-1).message, 'fixing-User-Profile-Api')
  assert.ok(repository.remote.pushedBranches.includes('new-branch'))

  repository = switchBranch(repository, 'main').repository
  assert.equal(repository.currentBranch, 'main')
  repository = switchBranch(repository, 'new-branch').repository
  assert.equal(repository.currentBranch, 'new-branch')
})
