import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  changedFiles,
  commit,
  createRepository,
  push,
  saveFile,
  stage,
} from '../src/simulation/state/repositoryModel.js'

const vscodePath = new URL('../src/simulation/apps/VSCodeApp.jsx', import.meta.url)

test('VS Code saves Ctrl+S and Meta+S through the existing shared save callback', async () => {
  const source = await readFile(vscodePath, 'utf8')

  assert.match(source, /event\.ctrlKey \|\| event\.metaKey/)
  assert.match(source, /event\.key\.toLowerCase\(\) === 's'/)
  assert.match(source, /event\.preventDefault\(\)/)
  assert.match(source, /onSave\(current\.path, buffer\)/)
  assert.match(source, /onKeyDown=\{handleEditorKeyDown\}/)
})

test('a VS Code save remains compatible with the simulated Git workflow', () => {
  let repository = createRepository(
    [{ path: 'app.py', content: 'before' }],
    { name: 'user-profile-service', path: '/Projects/user-profile-service' },
  )

  repository = saveFile(repository, 'app.py', 'after').repository
  assert.deepEqual(changedFiles(repository), ['app.py'])

  repository = stage(repository, '.').repository
  repository = commit(repository, 'fix user profile api').repository
  repository = push(repository).repository

  assert.equal(repository.branches.main.workingTree['app.py'].content, 'after')
  assert.equal(repository.branches.main.headSnapshot['app.py'].content, 'after')
  assert.equal(repository.branches.main.commits.at(-1).message, 'fix user profile api')
  assert.ok(repository.remote.pushedBranches.includes('main'))
})
