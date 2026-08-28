import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  commit,
  createBranch,
  createPullRequest,
  createRepository,
  push,
  saveFile,
  stage,
} from '../src/simulation/state/repositoryModel.js'
import {
  buildEvaluationEvidence,
  markEvaluationFailed,
  markEvaluationPending,
  recordEvaluation,
} from '../src/simulation/state/evaluationEvidence.js'
import {
  assessCompletionEmail,
  confirmSubmission,
  createSubmissionCandidate,
} from '../src/simulation/state/submissionWorkflow.js'

function completedWorkflow() {
  let repository = createRepository([
    { path: 'api/users.py', content: 'def find_user():\n    return None\n' },
    { path: 'tests/test_users.py', content: 'def test_missing():\n    assert True\n' },
  ], { name: 'users-api', path: '/Projects/users-api' })
  repository = createBranch(repository, 'feature/user-errors').repository
  repository = saveFile(repository, 'api/users.py', 'def find_user():\n    return {"error": "not found"}\n').repository
  repository = saveFile(repository, 'tests/test_users.py', 'def test_missing():\n    assert find_user()["error"] == "not found"\n').repository
  repository = stage(repository, '.').repository
  repository = commit(repository, 'Handle missing users').repository
  repository = push(repository).repository
  const prResult = createPullRequest(repository, {
    baseBranch: 'main',
    compareBranch: 'feature/user-errors',
    description: 'Return a safe missing-user response and verify it.',
    title: 'Handle missing users',
  })
  repository = prResult.repository
  const email = [
    'Branch: feature/user-errors',
    'I implemented the missing-user response and updated its regression coverage.',
    'I tested and verified the successful and missing-user paths.',
    prResult.pullRequest.url,
  ].join('\n')
  const assessment = assessCompletionEmail(repository, email)
  repository = createSubmissionCandidate(repository, 'task-users', email, assessment).repository
  const confirmed = confirmSubmission(repository, 'task-users', 'yes', 'confirmation-1')
  return { pullRequest: prResult.pullRequest, repository: confirmed.repository, submission: confirmed.submission }
}

const attempt = {
  attempt_id: 'attempt-users',
  career_id: 'software-engineering',
  company_id: 'demo-company',
  position_id: 'backend-developer',
}
const taskMessage = {
  body: 'Investigate the missing-user response and deliver a tested pull request.',
  deadline: 'Today',
  id: 'task-users',
  replies: [],
  role: 'Engineering Manager',
  sender: 'Jordan Lee',
  subject: 'Missing user response',
}

test('evaluation evidence uses committed branch snapshots for accurate before and after content', () => {
  const { pullRequest, repository, submission } = completedWorkflow()
  const evidence = buildEvaluationEvidence({ attempt, repository, submission, taskMessage })

  assert.deepEqual(evidence.changed_files, [
    {
      after: 'def find_user():\n    return {"error": "not found"}\n',
      before: 'def find_user():\n    return None\n',
      path: 'api/users.py',
    },
    {
      after: 'def test_missing():\n    assert find_user()["error"] == "not found"\n',
      before: 'def test_missing():\n    assert True\n',
      path: 'tests/test_users.py',
    },
  ])
  assert.equal(evidence.repository.branch, 'feature/user-errors')
  assert.equal(evidence.repository.commits.at(-1).message, 'Handle missing users')
  assert.ok(evidence.repository.pushed_branches.includes('feature/user-errors'))
  assert.equal(evidence.pull_request.url, pullRequest.url)
  assert.equal(evidence.final_communication.has_summary, true)
  assert.equal(evidence.final_communication.has_verification, true)
})

test('evaluation evidence contains safe user/workspace data and excludes private grading context', () => {
  const { repository, submission } = completedWorkflow()
  const evidence = buildEvaluationEvidence({ attempt, repository, submission, taskMessage })
  const serialized = JSON.stringify(evidence)

  for (const privateField of ['private_context', 'private_expected_solution', 'rubric', 'expected_patch', 'gemini_api_key']) {
    assert.equal(serialized.includes(privateField), false)
  }
  assert.equal(evidence.workspace.position_id, 'backend-developer')
  assert.equal(evidence.submission.confirmationMessage, 'yes')
})

test('evaluation state prevents duplicates and records failure or success explicitly', () => {
  const { repository } = completedWorkflow()
  const pending = markEvaluationPending(repository, 'task-users')
  assert.equal(pending.repository.evaluations['task-users'].status, 'pending')
  assert.match(markEvaluationPending(pending.repository, 'task-users').error, /already in progress/)

  const failed = markEvaluationFailed(pending.repository, 'task-users', 'Service unavailable').repository
  assert.equal(failed.evaluations['task-users'].status, 'failed')

  const completed = recordEvaluation(failed, 'task-users', { overall_score: 88 }).repository
  assert.equal(completed.evaluations['task-users'].data.overall_score, 88)
  assert.match(markEvaluationPending(completed, 'task-users').error, /already complete/)
})

test('the full general workflow remains separate from the five-step frontend workflow', async () => {
  const { repository, submission } = completedWorkflow()
  const evidence = buildEvaluationEvidence({ attempt, repository, submission, taskMessage })
  assert.equal(evidence.changed_files.length, 2)
  assert.equal(repository.submissions['task-users'].status, 'submitted')

  const taskPanel = await readFile(new URL('../src/simulation/TaskPanel.jsx', import.meta.url), 'utf8')
  const desktop = await readFile(new URL('../src/simulation/SimulationDesktop.jsx', import.meta.url), 'utf8')
  const mail = await readFile(new URL('../src/simulation/apps/MailApp.jsx', import.meta.url), 'utf8')
  assert.match(taskPanel, /saveFrontendSimulationProgress/)
  assert.match(desktop, /position_id === 'frontend-developer'/)
  assert.match(mail, /position_id !== 'frontend-developer'/)
  assert.match(mail, /processCompletionReply/)
  assert.match(mail, /evaluateWorkplaceSimulation/)
  assert.match(mail, /navigate\(`\/simulation\/attempts\/\$\{encodeURIComponent\(attempt\.attempt_id\)\}\/report`\)/)
})
