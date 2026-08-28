import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  buildScenarioAttachments,
  changedFiles,
  commit,
  createBranch,
  createRepository,
  downloadAttachment,
  extractProjectArchive,
  loadRepository,
  persistRepository,
  push,
  saveFile,
  stage,
} from '../src/simulation/state/repositoryModel.js'

const projectFiles = [
  { content: '# Demo service', path: 'README.md' },
  { content: 'return "before"', path: 'src/service.py' },
]

const scenario = {
  project: {
    archive_name: 'demo-service.zip',
    files: projectFiles,
    name: 'demo-service',
  },
  resources: [{ content: 'request failed', id: 'error-log', name: 'error.log' }],
  scenario_id: 'demo-incident',
}

const options = {
  archiveName: 'demo-service.zip',
  name: 'demo-service',
  path: '/Projects/demo-service',
  requireExtraction: true,
}

function pendingRepository() { return createRepository(projectFiles, options) }

test('scenario attachments preserve the legacy project archive and resource contract', () => {
  const [archive, resource] = buildScenarioAttachments(scenario)

  assert.equal(archive.id, 'scenario-demo-incident-project')
  assert.equal(archive.name, 'demo-service.zip')
  assert.equal(archive.type, 'archive')
  assert.deepEqual(Object.keys(archive.archiveEntries), [
    'demo-service/README.md',
    'demo-service/src/service.py',
  ])
  assert.equal(resource.name, 'error.log')
  assert.equal(resource.type, 'file')
})

test('download and extraction expose the project to Files and VS Code through one repository', () => {
  const [archive] = buildScenarioAttachments(scenario)
  let repository = pendingRepository()

  assert.equal(repository.workspace.projectExtracted, false)
  assert.deepEqual(Object.values(repository.branches.main.workingTree), [])

  repository = downloadAttachment(repository, archive).repository
  assert.equal(repository.workspace.downloadedAttachments[0].name, 'demo-service.zip')

  const result = extractProjectArchive(repository, archive.id)
  repository = result.repository
  const filesVisibleToVSCode = Object.values(repository.branches.main.workingTree)

  assert.equal(result.projectPath, '/Projects/demo-service')
  assert.equal(repository.workspace.projectExtracted, true)
  assert.deepEqual(repository.workspace.extractedProjectPaths, ['/Projects/demo-service'])
  assert.deepEqual(filesVisibleToVSCode, projectFiles)
  assert.deepEqual(repository.branches.main.headSnapshot, repository.branches.main.workingTree)
  assert.equal(repository.branches.main.commits[0].message, 'Initial project files')
})

test('non-archives are not extractable and repeated extraction preserves project edits', () => {
  const [archive, resource] = buildScenarioAttachments(scenario)
  let repository = pendingRepository()
  repository = downloadAttachment(repository, resource).repository
  assert.match(extractProjectArchive(repository, resource.id).error, /cannot be extracted/)

  repository = downloadAttachment(repository, archive).repository
  repository = extractProjectArchive(repository, archive.id).repository
  repository = saveFile(repository, 'src/service.py', 'return "edited"').repository

  const repeated = extractProjectArchive(repository, archive.id)
  assert.equal(repeated.alreadyExtracted, true)
  assert.equal(repeated.repository.branches.main.workingTree['src/service.py'].content, 'return "edited"')
  assert.equal(repeated.repository.workspace.extractedProjectPaths.length, 1)
})

test('downloaded and extracted state survives same-browser resume', () => {
  const values = new Map()
  const storage = {
    getItem: (key) => values.get(key) || null,
    setItem: (key, value) => values.set(key, value),
  }
  const [archive] = buildScenarioAttachments(scenario)
  let repository = downloadAttachment(pendingRepository(), archive).repository
  persistRepository('extract-attempt', repository, storage)

  repository = loadRepository('extract-attempt', projectFiles, options, storage)
  assert.equal(repository.workspace.downloadedAttachments[0].id, archive.id)
  repository = extractProjectArchive(repository, archive.id).repository
  persistRepository('extract-attempt', repository, storage)

  const resumed = loadRepository('extract-attempt', projectFiles, options, storage)
  assert.equal(resumed.workspace.projectExtracted, true)
  assert.equal(resumed.branches.main.workingTree['README.md'].content, '# Demo service')
})

test('the extracted project retains the shared edit, stage, commit, and push workflow', () => {
  const [archive] = buildScenarioAttachments(scenario)
  let repository = downloadAttachment(pendingRepository(), archive).repository
  repository = extractProjectArchive(repository, archive.id).repository
  repository = createBranch(repository, 'feature/fix-service').repository
  repository = saveFile(repository, 'src/service.py', 'return "after"').repository

  assert.deepEqual(changedFiles(repository), ['src/service.py'])
  repository = stage(repository, ['src/service.py']).repository
  assert.deepEqual(repository.branches['feature/fix-service'].stagedPaths, ['src/service.py'])
  repository = commit(repository, 'Fix service response').repository
  repository = push(repository).repository

  assert.equal(repository.branches['feature/fix-service'].headSnapshot['src/service.py'].content, 'return "after"')
  assert.ok(repository.remote.pushedBranches.includes('feature/fix-service'))
})

test('React wires Mail, Files, and VS Code to the shared extraction state', async () => {
  const root = new URL('../src/simulation/', import.meta.url)
  const [desktop, files, mail] = await Promise.all([
    readFile(new URL('SimulationDesktop.jsx', root), 'utf8'),
    readFile(new URL('apps/FilesApp.jsx', root), 'utf8'),
    readFile(new URL('apps/MailApp.jsx', root), 'utf8'),
  ])

  assert.match(mail, /buildScenarioAttachments/)
  assert.match(desktop, /downloadAttachment/)
  assert.match(desktop, /extractProjectArchive/)
  assert.match(desktop, /workspace\?\.projectExtracted/)
  assert.match(files, /Extract to Projects/)
  assert.match(files, /files-action-button/)
})
