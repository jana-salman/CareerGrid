import {
  findPullRequestByUrl,
  validatePullRequest,
} from './repositoryModel.js'

function copy(value) { return JSON.parse(JSON.stringify(value)) }

function extractSimulatedPullRequestUrls(body) {
  const matches = String(body || '').match(/https:\/\/github\.com\/careergrid-sim\/[^\r\n]*?\/pull\/\d+(?=$|[\s)\],.!?;:])/gi) || []
  return [...new Set(matches.map((url) => url.replace(/[)\],.!?;:]+$/, '')))]
}

function isAffirmativeSubmissionConfirmation(body) {
  const answer = String(body || '').toLowerCase().replace(/[^a-z0-9\s']/g, ' ').replace(/\s+/g, ' ').trim()
  return /^(?:yes|yep|yeah|yup|correct|affirmative|submit(?: it)?|that's (?:the one|it|final)|yes (?:this is it|that's (?:the pr|it|the one)|review (?:it|this)|final))$/.test(answer)
}

function isSubmissionCancellation(body) {
  const answer = String(body || '').toLowerCase().replace(/[^a-z0-9\s']/g, ' ').replace(/\s+/g, ' ').trim()
  return /^(?:no|nope|cancel|cancel it|not yet|let me correct it|i need to correct it)$/.test(answer)
}

function assessCompletionEmail(repository, body) {
  const text = String(body || '')
  const lower = text.toLowerCase()
  const urls = extractSimulatedPullRequestUrls(text)
  const reportedBranch = text.match(/(?:^|\n)\s*branch\s*:\s*([A-Za-z0-9._/-]+)/i)?.[1] || ''
  const pullRequest = urls.map((url) => findPullRequestByUrl(repository, url)).find(Boolean) || null
  const validatedPullRequest = validatePullRequest(repository, pullRequest)
  const looksLikeSubmission = urls.length > 0 || (Boolean(reportedBranch) && /pull request|github|\bpr\b|pushed/.test(lower))
  const hasSummary = /found|identified|changed|updated|fixed|implemented|investigated|resolved/.test(lower)
    && text.replace(/https?:\/\/\S+/g, '').trim().split(/\s+/).filter(Boolean).length >= 8
  const hasVerification = /test|tested|testing|verify|verified|validation|reviewed|checked/.test(lower)
  const errors = []

  if (looksLikeSubmission && !urls.length) errors.push('missing_pull_request')
  if (urls.length && !pullRequest) errors.push('invalid_pull_request')
  if (pullRequest && !validatedPullRequest) {
    const compare = repository.branches[pullRequest.compareBranch]
    const base = repository.branches[pullRequest.baseBranch]
    if (pullRequest.status !== 'open') errors.push('pull_request_not_open')
    if (!compare) errors.push('missing_compare_branch')
    if (compare && !repository.remote.pushedBranches.includes(pullRequest.compareBranch)) errors.push('branch_not_pushed')
    if (base && compare) {
      const baseIds = new Set(base.commits.map((item) => item.id))
      if (!compare.commits.some((item) => !baseIds.has(item.id))) errors.push('no_compare_commits')
    }
  }
  if (pullRequest && reportedBranch && reportedBranch !== pullRequest.compareBranch) errors.push('branch_mismatch')
  if (looksLikeSubmission && !hasSummary) errors.push('insufficient_summary')
  if (looksLikeSubmission && !hasVerification) errors.push('missing_verification')

  return {
    errors,
    hasSummary,
    hasVerification,
    looksLikeSubmission,
    pullRequest: validatedPullRequest,
    reportedBranch,
    urls,
    validCandidate: looksLikeSubmission && Boolean(validatedPullRequest) && errors.length === 0,
  }
}

function createSubmissionCandidate(repository, threadId, rawMessage, assessment) {
  const next = copy(repository); const key = String(threadId || 'default')
  if (next.submissions[key]) return { repository: next, error: 'This task already has a recorded submission.', existing: next.submissions[key] }
  if (!assessment?.validCandidate || !assessment.pullRequest) return { repository: next, error: 'The completion email is not ready for submission.' }
  const candidate = {
    threadId: key, repositoryPath: next.rootPath, branch: assessment.pullRequest.compareBranch,
    pullRequestId: Number(assessment.pullRequest.id), pullRequestUrl: assessment.pullRequest.url,
    awaitingConfirmation: true, createdAt: new Date().toISOString(), rawMessages: [String(rawMessage)],
    hasSummary: assessment.hasSummary, hasVerification: assessment.hasVerification,
  }
  next.submissionCandidates[key] = candidate
  return { repository: next, candidate }
}

function cancelSubmissionCandidate(repository, threadId) {
  const next = copy(repository); delete next.submissionCandidates[String(threadId || 'default')]
  return { repository: next }
}

function confirmSubmission(repository, threadId, confirmationMessage, messageId = '') {
  const next = copy(repository); const key = String(threadId || 'default'); const existing = next.submissions[key]
  if (existing) return { repository: next, error: 'This task already has a recorded submission.', existing }
  const candidate = next.submissionCandidates[key]
  if (!candidate || !isAffirmativeSubmissionConfirmation(confirmationMessage)) return { repository: next, error: 'Explicit confirmation is required.' }
  const pullRequest = next.pullRequests.find((item) => item.id === candidate.pullRequestId && item.url === candidate.pullRequestUrl)
  if (!validatePullRequest(next, pullRequest)) return { repository: next, error: 'The pull request is no longer valid.' }
  const submission = {
    status: 'submitted', submittedAt: new Date().toISOString(), messageId: String(messageId), threadId: key,
    rawMessage: candidate.rawMessages.join('\n\n'), rawMessages: [...candidate.rawMessages, String(confirmationMessage)],
    confirmationMessage: String(confirmationMessage), repositoryPath: candidate.repositoryPath, branch: candidate.branch,
    pullRequestId: candidate.pullRequestId, pullRequestUrl: candidate.pullRequestUrl,
    extracted: { hasSummary: candidate.hasSummary, hasVerification: candidate.hasVerification },
  }
  next.submissions[key] = submission; delete next.submissionCandidates[key]
  return { repository: next, submission }
}

export {
  assessCompletionEmail,
  cancelSubmissionCandidate,
  confirmSubmission,
  createSubmissionCandidate,
  extractSimulatedPullRequestUrls,
  isAffirmativeSubmissionConfirmation,
  isSubmissionCancellation,
}
