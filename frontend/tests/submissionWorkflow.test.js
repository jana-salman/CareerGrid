import assert from 'node:assert/strict'
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
  assessCompletionEmail,
  cancelSubmissionCandidate,
  confirmSubmission,
  createSubmissionCandidate,
} from '../src/simulation/state/submissionWorkflow.js'

function pullRequestRepository() {
  let repository = createRepository(
    [{ path: 'server.py', content: 'return old_value' }],
    { name: 'backend-service', path: '/Projects/backend-service' },
  )
  repository = createBranch(repository, 'feature/fix-response').repository
  repository = saveFile(repository, 'server.py', 'return new_value').repository
  repository = stage(repository, '.').repository
  repository = commit(repository, 'Fix response value').repository
  repository = push(repository).repository
  const created = createPullRequest(repository, {
    baseBranch: 'main',
    compareBranch: 'feature/fix-response',
    description: 'Correct response value and preserve the endpoint contract.',
    title: 'Fix response value',
  })
  return { pullRequest: created.pullRequest, repository: created.repository }
}

function validEmail(pullRequest) {
  return [
    'Branch: feature/fix-response',
    'I fixed the incorrect response value and updated the endpoint behavior safely.',
    'I tested and verified both successful and missing-record responses.',
    pullRequest.url,
  ].join('\n')
}

test('a valid completion email creates a candidate but requires confirmation', () => {
  const { pullRequest, repository } = pullRequestRepository()
  const email = validEmail(pullRequest)
  const assessment = assessCompletionEmail(repository, email)

  assert.equal(assessment.validCandidate, true)
  assert.equal(assessment.pullRequest.id, pullRequest.id)

  const created = createSubmissionCandidate(repository, 'task-1', email, assessment)
  assert.equal(created.candidate.awaitingConfirmation, true)
  assert.equal(created.repository.submissions['task-1'], undefined)
  assert.match(confirmSubmission(created.repository, 'task-1', 'maybe').error, /Explicit confirmation/)
})

test('completion validation rejects missing and arbitrary pull request URLs', () => {
  const { repository } = pullRequestRepository()
  const missing = assessCompletionEmail(repository, 'Branch: feature/fix-response\nI fixed and tested the response, and the PR was pushed.')
  const arbitrary = assessCompletionEmail(repository, [
    'I fixed and tested the response behavior across all requested cases.',
    'https://github.com/careergrid-sim/not-this-repository/pull/99',
  ].join('\n'))

  assert.ok(missing.errors.includes('missing_pull_request'))
  assert.ok(arbitrary.errors.includes('invalid_pull_request'))
  assert.equal(arbitrary.validCandidate, false)
})

test('completion validation enforces current commit, push, branch, summary, and verification evidence', () => {
  const { pullRequest, repository } = pullRequestRepository()

  const unpushed = structuredClone(repository)
  unpushed.remote.pushedBranches = []
  assert.ok(assessCompletionEmail(unpushed, validEmail(pullRequest)).errors.includes('branch_not_pushed'))

  const noCommit = structuredClone(repository)
  noCommit.branches['feature/fix-response'].commits = structuredClone(noCommit.branches.main.commits)
  assert.ok(assessCompletionEmail(noCommit, validEmail(pullRequest)).errors.includes('no_compare_commits'))

  const wrongBranch = validEmail(pullRequest).replace('Branch: feature/fix-response', 'Branch: feature/other')
  assert.ok(assessCompletionEmail(repository, wrongBranch).errors.includes('branch_mismatch'))

  const weakSummary = `Fixed it. Tested it. ${pullRequest.url}`
  assert.ok(assessCompletionEmail(repository, weakSummary).errors.includes('insufficient_summary'))

  const noVerification = `I fixed the incorrect response value and updated the endpoint behavior safely. ${pullRequest.url}`
  assert.ok(assessCompletionEmail(repository, noVerification).errors.includes('missing_verification'))
})

test('candidate cancellation permits a corrected submission', () => {
  const { pullRequest, repository } = pullRequestRepository()
  const email = validEmail(pullRequest)
  const assessment = assessCompletionEmail(repository, email)
  const created = createSubmissionCandidate(repository, 'task-1', email, assessment)
  const cancelled = cancelSubmissionCandidate(created.repository, 'task-1')

  assert.equal(cancelled.repository.submissionCandidates['task-1'], undefined)
  assert.equal(createSubmissionCandidate(cancelled.repository, 'task-1', email, assessment).candidate.awaitingConfirmation, true)
})

test('explicit confirmation records exactly one safe submission', () => {
  const { pullRequest, repository } = pullRequestRepository()
  const email = validEmail(pullRequest)
  const assessment = assessCompletionEmail(repository, email)
  const candidate = createSubmissionCandidate(repository, 'task-1', email, assessment)
  const confirmed = confirmSubmission(candidate.repository, 'task-1', 'yes', 'message-2')

  assert.equal(confirmed.submission.status, 'submitted')
  assert.equal(confirmed.submission.pullRequestUrl, pullRequest.url)
  assert.equal(confirmed.repository.submissionCandidates['task-1'], undefined)

  const duplicate = confirmSubmission(confirmed.repository, 'task-1', 'yes', 'message-3')
  assert.match(duplicate.error, /already has a recorded submission/)
  assert.deepEqual(duplicate.existing, confirmed.submission)
})
